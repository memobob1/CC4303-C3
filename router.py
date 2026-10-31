import sys


class Router:
    def __init__(self, ip: str, port: int, routes_file: str):
        self.ip = ip
        self.port = port
        self.routes_file = routes_file


def main():
    if len(sys.argv) != 4:
        sys.exit("Uso: python3 router.py router_IP router_puerto router_rutas.txt")
    ip, port, routes_file = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    router = Router(ip, port, routes_file)
    print(f"Router escuchando en ({router.ip}, {router.port}) con tabla {router.routes_file}")


if __name__ == "__main__":
    main()
