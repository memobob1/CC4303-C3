import socket
import sys
from packet import IPPacket, parse_packet, create_packet
from fragmentation import fragment_IP_packet, reassemble_IP_packet

BUFFER_SIZE: int = 4096


def ip_to_int(ip: str) -> int:
    """
    Funcion de ayuda que convierte una IP a.b.c.d en un solo número de 32 bits. (Para comparar IPS bit a bit).

    Parámetros:
        ip (str): IP en formato a.b.c.d.

    Retorna:
        int: La IP como número, para poder compararla bit a bit.
    """
    octets: list[str] = ip.split(".")
    number: int = 0
    for octet in octets:
        # Corremos 8 bits a la izquierda para dejar espacio para el siguiente número
        number = (number << 8) + int(octet)
    return number


class RoutesToArea:
    """
    Grupo de rutas de la tabla que llevan a una misma área de destino (red + rango de puertos).

    Atributos:
        ip (str): IP de la red de destino.
        bits_to_compare (int): Largo del prefijo CIDR (cuántos bits de la IP definen la red).
        first_port (int): Primer puerto del rango de destino.
        last_port (int): Último puerto del rango de destino.
        possible_routes (list[tuple[tuple[str, int], int]]): Pares (siguiente salto, MTU del enlace).
        next_hop_idx (int): Índice de la próxima ruta a usar (round-robin).
    """

    def __init__(self, ip: str, bits_to_compare: int, first_port: int, last_port: int) -> None:
        """
        Crea el área sin rutas.

        Parámetros:
            ip (str): IP de la red de destino.
            bits_to_compare (int): Largo del prefijo CIDR.
            first_port (int): Primer puerto del rango de destino.
            last_port (int): Último puerto del rango de destino.
        """
        self.ip: str = ip
        self.bits_to_compare: int = bits_to_compare
        self.first_port: int = first_port
        self.last_port: int = last_port
        self.possible_routes: list[tuple[tuple[str, int], int]] = [] # Lista de pares (siguiente salto, MTU del enlace)
        self.next_hop_idx: int = 0

    def add_route(self, next_hop: tuple[str, int], mtu: int) -> None:
        """
        Agrega una ruta posible hacia el área (agregando el siguiente salto y su MTU).

        Parámetros:
            next_hop (tuple[str, int]): Dirección (IP, puerto) del siguiente salto.
            mtu (int): MTU del enlace hacia ese salto.
        """
        self.possible_routes.append((next_hop, mtu)) # agregamos el siguiente salto y su MTU a la lista de rutas posibles

    def contains_address(self, address: tuple[str, int]) -> bool:
        """
        Indica si una dirección pertenece al área.

        Parámetros:
            address (tuple[str, int]): Dirección (IP, puerto) de destino.

        Retorna:
            bool: True si la IP está en la red y el puerto en el rango.
        """
        ip: str = address[0]
        port: int = address[1]
        # Si hacemos un shift a la derecha se borran los bits de host y quedan solo los de red
        shift: int = 32 - self.bits_to_compare
        same_network: bool = (ip_to_int(ip) >> shift) == (ip_to_int(self.ip) >> shift)

        # retornamos si es la misma red y si el puerto está dentro del rango
        return same_network and self.first_port <= port <= self.last_port

    def get_next_hop(self) -> tuple[tuple[str, int], int]:
        """
        Entrega la siguiente ruta según round-robin.

        Retorna:
            tuple[tuple[str, int], int]: El siguiente salto y el MTU de su enlace.
        """
        
        # guardamos en route la tupla (siguiente salto, MTU) de la lista de rutas posibles en el índice next_hop_idx 
        route: tuple[tuple[str, int], int] = self.possible_routes[self.next_hop_idx]
        self.next_hop_idx = (self.next_hop_idx + 1) % len(self.possible_routes) # actualizamos el índice del siguiente salto para la próxima vez (round-robin)
        return route


class Router:
    """
    Router del mini-Internet simulado con un socket UDP.

    Atributos:
        ip (str): IP en la que escucha el router.
        port (int): Puerto en el que escucha el router.
        routes_file_name (str): Nombre del archivo con la tabla de rutas.
        destination_areas (list[RoutesToArea]): Áreas de destino leídas de la tabla, en orden.
        fragments (dict[int, list[bytes]]): Fragmentos recibidos para este router, agrupados por ID.
        socket (socket.socket): Socket UDP asociado a (ip, port).
    """

    def __init__(self, ip: str, port: int, routes_file_name: str) -> None:
        """
        Crea el router y asocia su socket UDP a (ip, port).

        Parámetros:
            ip (str): IP en la que escucha el router.
            port (int): Puerto en el que escucha el router.
            routes_file_name (str): Nombre del archivo con la tabla de rutas.
        """
        self.ip: str = ip
        self.port: int = port
        self.routes_file_name: str = routes_file_name
        self.destination_areas: list[RoutesToArea] = []
        self.read_routes_file()
        self.fragments: dict[int, list[bytes]] = {} # diccionario que guarda los fragmentos recibidos para este router, agrupados por ID
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))

    def read_routes_file(self) -> None:
        """
        Lee la tabla de rutas y agrupa sus líneas por área de destino, además guardando el MTU de cada ruta.
        """
        routes_by_destination_area: dict[tuple[str, int, int, int], list[tuple[tuple[str, int], int]]] = {}

        with open(self.routes_file_name, "r") as file:

            for route_line in file:
                split_route_line: list[str] = route_line.split()
                # si la línea está vacía, la ignoramos
                if len(split_route_line) == 0:
                    continue

                ip_and_bits: list[str] = split_route_line[0].split("/")
                ip: str = ip_and_bits[0]
                # Si la ip no tiene máscara, asumimos que es /32
                bits_to_compare: int = 32
                # pero si tiene máscara, la usamos
                if len(ip_and_bits) == 2:
                    bits_to_compare = int(ip_and_bits[1])

                initial_port: int = int(split_route_line[1])
                last_port: int = int(split_route_line[2])

                next_hop_ip: str = split_route_line[3]
                next_hop_port: int = int(split_route_line[4])
                mtu: int = int(split_route_line[5]) # agregamos el MTU de la ruta a la tupla (siguiente salto, MTU) que se guardará en la lista de rutas posibles

                key: tuple[str, int, int, int] = (ip, bits_to_compare, initial_port, last_port)
                routes_by_destination_area.setdefault(key, []).append(((next_hop_ip, next_hop_port), mtu))

        for (ip, bits_to_compare, initial_port, last_port) in routes_by_destination_area:

            destination_area: RoutesToArea = RoutesToArea(ip, bits_to_compare, initial_port, last_port)

            for (next_hop, mtu) in routes_by_destination_area[(ip, bits_to_compare, initial_port, last_port)]:
                destination_area.add_route(next_hop, mtu) # agregamos el siguiente salto y su MTU a la lista de rutas posibles del área de destino

            self.destination_areas.append(destination_area)

    def check_routes(self, destination_address: tuple[str, int]) -> tuple[tuple[str, int], int] | None:
        """
        Busca en la tabla la primera área que contiene al destino y entrega su siguiente ruta.

        Parámetros:
            destination_address (tuple[str, int]): Dirección (IP, puerto) de destino final.

        Retorna:
            tuple[tuple[str, int], int] | None: El siguiente salto y el MTU de su enlace, o None si no hay ruta.
        """
        for area in self.destination_areas:
            if area.contains_address(destination_address):
                return area.get_next_hop()

        return None

    def store_and_reassemble(self, packet: bytes, packet_id: int) -> None:
        """
        Guarda un fragmento (o paquete) dirigido a este router e intenta rearmar su paquete original.
        Si queda completo, imprime el mensaje.

        Parámetros:
            packet (bytes): Fragmento o paquete recibido.
            packet_id (int): ID del paquete al que pertenece.
        """

        # Si el ID no existe en el diccionario, lo agregamos con lista vacía
        if packet_id not in self.fragments:
            self.fragments[packet_id] = []
        self.fragments[packet_id].append(packet) # agregamos el fragmento en su diccionario correspondiente al ID

        full_packet: bytes | None = reassemble_IP_packet(self.fragments[packet_id]) # usamos reassemble_IP_packet para intentar rearmar el paquete original
        if full_packet is not None:
            # Aca borramos el ID para poder recibir otro paquete con el mismo ID más adelante
            del self.fragments[packet_id]
            print(f"Ha recibido el mensaje: {parse_packet(full_packet).message.decode()}")

        # si no se pudo rearmar el paquete, no hacemos nada y esperamos a que lleguen más fragmentos

    def run(self) -> None:
        """
        Escucha de forma bloqueante en un loop infinito e imprime cada paquete recibido.
        """
        while True:
            packet: bytes
            packet, _ = self.socket.recvfrom(BUFFER_SIZE)
            parsed_ip_packet = parse_packet(packet)
            destination_address: tuple[str, int] = (parsed_ip_packet.ip, parsed_ip_packet.port)
            message: str = parsed_ip_packet.message.decode()

            # Esto es solo cosmético para que los mensajes no sean demasiado largos en la salida
            if len(message) > 25:
                truncated_message: str = f"'{message[:22]}...'"
            else:
                truncated_message: str = message

            if (parsed_ip_packet.ttl <= 0):
                print(f"Se recibió paquete {truncated_message} con TTL 0")
                continue

            elif (self.ip, self.port) == destination_address:
                self.store_and_reassemble(packet, parsed_ip_packet.id) # si el paquete es para este router, lo guardamos y tratamos de rearmarlo
                continue

            route: tuple[tuple[str, int], int] | None = self.check_routes(destination_address)

            # si encontramos una ruta hacia el destino, enviamos el paquete al siguiente salto y decrementamos el TTL
            if route:
                next_address: tuple[str, int] = route[0]
                mtu: int = route[1]
                parsed_ip_packet.ttl -= 1
                packet = create_packet(parsed_ip_packet)

                # fragmentamos el paquete si es necesario y lo enviamos al siguiente salto
                fragments: list[bytes] = fragment_IP_packet(packet, mtu)
                print(f"Redirigiendo paquete {truncated_message} con destino final {destination_address}"
                      + f" desde {(self.ip, self.port)} hacia {next_address} en {len(fragments)} fragmento(s)")
                for fragment in fragments:
                    # enviamos cada fragmento al siguiente salto
                    self.socket.sendto(fragment, next_address)
            
            # si no, imprimimos que no hay rutas hacia el destino
            else:
                print(f"No hay rutas hacia {destination_address} para paquete {truncated_message}")

def main() -> None:
    """
    Lee router_IP, router_puerto y router_rutas.txt desde sys.argv y echa a correr el router.
    """
    if len(sys.argv) != 4:
        sys.exit("Uso: python3 router.py router_IP router_puerto router_rutas.txt")
    ip: str = sys.argv[1]
    port: int = int(sys.argv[2])
    routes_file: str = sys.argv[3]
    router: Router = Router(ip, port, routes_file)
    print(f"Router escuchando en ({router.ip}, {router.port}) con tabla {router.routes_file_name}")
    router.run()


if __name__ == "__main__":
    main()

# python3 router.py 127.0.0.1 8881 rutas_R1_v3_mtu.txt
# python3 router.py 127.0.0.1 8882 rutas_R2_v3_mtu.txt
# python3 router.py 127.0.0.1 8883 rutas_R3_v3_mtu.txt
# python3 router.py 127.0.0.1 8884 rutas_R4_v3_mtu.txt
# python3 router.py 127.0.0.1 8885 rutas_R5_v3_mtu.txt
