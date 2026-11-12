import socket
import sys
from packet import IPPacket, parse_packet, create_packet

BUFFER_SIZE: int = 4096

class RoutesToArea:
    def __init__(self, ip: str, bits_to_compare: int, first_port: int, last_port: int):
        self.ip: str = ip
        self.bits_to_compare: int = bits_to_compare
        self.first_port: int = first_port
        self.last_port: int = last_port
        self.possible_routes: list[tuple[str, int]] = []
        self.next_hop_idx = 0

    def add_route(self, route: tuple[str, int]) -> None:
        self.possible_routes.append(route)

    def contains_address(self, address: tuple[str, int]) -> bool:
        ip: str = address[0]
        port: int = address[1]
        return (ip[:self.bits_to_compare] == self.ip[:self.bits_to_compare]
                and port in range(self.first_port, self.last_port + 1))

    def get_next_hop(self) -> tuple[str, int]:
        next_hop: tuple[str, int] = self.possible_routes[self.next_hop_idx]
        self.next_hop_idx = (self.next_hop_idx + 1) % len(self.possible_routes)
        return next_hop

class Router:
    """
    Router del mini-Internet simulado con un socket UDP.

    Atributos:
        ip (str): IP en la que escucha el router.
        port (int): Puerto en el que escucha el router.
        routes_file (str): Nombre del archivo con la tabla de rutas.
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
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))

    def read_routes_file(self):

        routes_by_destination_area: dict[tuple[str, int, int, int], list[tuple[str, int]]] = {}

        with open(self.routes_file_name, "r") as file:

            for route_line in file:
                split_route_line: list[str] = route_line.split(" ")

                ip_and_bits: list[str] = split_route_line[0].split("/")
                ip: str = ip_and_bits[0]
                bits_to_compare: int = int(ip_and_bits[1])

                initial_port: int = int(split_route_line[1])
                last_port: int = int(split_route_line[2])

                next_hop_ip: str = split_route_line[3]
                next_hop_port: int = int(split_route_line[4])

                key = (ip, bits_to_compare, initial_port, last_port)
                routes_by_destination_area.setdefault(key, []).append((next_hop_ip, next_hop_port))

        for (ip, bits_to_compare, initial_port, last_port) in routes_by_destination_area:

            destination_area: RoutesToArea = RoutesToArea(ip, bits_to_compare, initial_port, last_port)

            for (hop_ip, hop_port) in routes_by_destination_area[(ip, bits_to_compare, initial_port, last_port)]:
                destination_area.add_route((hop_ip, hop_port))

            self.destination_areas.append(destination_area)
                
    def check_routes(self, destination_address: tuple[str, int]):
        for area in self.destination_areas:
            if area.contains_address(destination_address):
                return area.get_next_hop()

        return None

    def run(self) -> None:
        """
        Escucha de forma bloqueante en un loop infinito e imprime cada paquete recibido.
        """
        while True:
            packet: bytes
            packet, _ = self.socket.recvfrom(BUFFER_SIZE)
            parsed_ip_packet = parse_packet(packet)
            destination_address: tuple[str, int] = (parsed_ip_packet.ip, parsed_ip_packet.port)

            if (self.ip, self.port) == destination_address:
                print(f"Ha recibido el mensaje: {parsed_ip_packet.message}")
                continue

            next_address = self.check_routes(destination_address)
            truncated_message: str = f"'{parsed_ip_packet.message[:20]}...'"

            if next_address:
                print(f"Redirigiendo paquete {truncated_message} con destino final {destination_address}"
                      + f" desde {(self.ip, self.port)} hacia {next_address}")
                self.socket.sendto(packet, next_address)
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
