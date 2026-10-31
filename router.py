import sys


class Router:
    def __init__(self, ip: str, port: int, routes_file: str) -> None:
        self.ip: str = ip
        self.port: int = port
        self.routes_file: str = routes_file


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit("Uso: python3 router.py router_IP router_puerto router_rutas.txt")
    ip: str = sys.argv[1]
    port: int = int(sys.argv[2])
    routes_file: str = sys.argv[3]
    router: Router = Router(ip, port, routes_file)
    print(f"Router escuchando en ({router.ip}, {router.port}) con tabla {router.routes_file}")


if __name__ == "__main__":
    main()
