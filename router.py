import socket
import sys
from packet import IPPacket, parse_packet, create_packet

BUFFER_SIZE: int = 4096


class Router:
    """
    Router del mini-Internet simulado con un socket UDP.

    Atributos:
        ip (str): IP en la que escucha el router.
        port (int): Puerto en el que escucha el router.
        routes_file (str): Nombre del archivo con la tabla de rutas.
        socket (socket.socket): Socket UDP asociado a (ip, port).
    """

    def __init__(self, ip: str, port: int, routes_file: str) -> None:
        """
        Crea el router y asocia su socket UDP a (ip, port).

        Parámetros:
            ip (str): IP en la que escucha el router.
            port (int): Puerto en el que escucha el router.
            routes_file (str): Nombre del archivo con la tabla de rutas.
        """
        self.ip: str = ip
        self.port: int = port
        self.routes_file: str = routes_file
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))

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

            next_address = check_routes("a", destination_address)
            truncated_message: str = f"'{parsed_ip_packet.message[:20]}...'"

            if next_address:
                print(f"Redirigiendo paquete {truncated_message} con destino final {destination_address}"
                      + f" desde {(self.ip, self.port)} hacia {next_address}")
            else:
                print(f"No hay rutas hacia {destination_address} para paquete {truncated_message}")


def check_routes(routes_file_name: str, destination_address: tuple[str, int]):

    final_ip: str = destination_address[0]
    final_port: int = destination_address[1]

    with open(routes_file_name, "r") as file:
        for line in file:
            split_line: list[str] = line.split(" ")

            ip_line: list[str] = split_line[0].split("/")
            route_ip: str = ip_line[0]
            bits_to_compare: int = int(ip_line[1])

            route_initial_port: int = int(split_line[1])
            route_last_port: int = int(split_line[2])

            if (
                route_ip[:bits_to_compare] == final_ip[:bits_to_compare]
                and final_port in range(route_initial_port, route_last_port + 1)
            ):
                next_hop_ip: str = split_line[3]
                next_hop_port: int = int(split_line[4])
                return next_hop_ip, next_hop_port

    return None

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
    print(f"Router escuchando en ({router.ip}, {router.port}) con tabla {router.routes_file}")
    router.run()


if __name__ == "__main__":
    #main()
    print(check_routes("rutas_R2_V2.txt", ("127.0.0.1", 8881)))
