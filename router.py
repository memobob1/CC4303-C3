import socket
import sys

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
            print(packet)


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
    main()
