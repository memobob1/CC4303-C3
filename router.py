import socket
import sys

# Sobra para líneas de texto; lo que exceda el buffer en UDP se pierde
BUFFER_SIZE: int = 4096


class Router:
    def __init__(self, ip: str, port: int, routes_file: str) -> None:
        self.ip: str = ip
        self.port: int = port
        self.routes_file: str = routes_file
        # UDP: igual que IP, no garantiza entrega ni orden
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))

    def run(self) -> None:
        while True:
            packet: bytes
            packet, _ = self.socket.recvfrom(BUFFER_SIZE)
            print(packet)


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit("Uso: python3 router.py router_IP router_puerto router_rutas.txt")
    ip: str = sys.argv[1]
    port: int = int(sys.argv[2])
    routes_file: str = sys.argv[3]
    router: Router = Router(ip, port, routes_file)
    print(f"Router escuchando en ({router.ip}, {router.port}) con tabla {router.routes_file}")
    router.run()


if __name__ == "__main__":
    main()
