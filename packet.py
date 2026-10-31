IP_SIZE: int = 4
PORT_SIZE: int = 2
HEADER_SIZE: int = IP_SIZE + PORT_SIZE


class IPPacket:
    """
    Paquete IP del mini-Internet ya parseado.

    Atributos:
        ip (str): IP de destino final, en formato a.b.c.d.
        port (int): Puerto de destino final.
        message (str): Contenido del paquete, sin headers.
    """

    def __init__(self, ip: str, port: int, message: str) -> None:
        """
        Crea un paquete con su destino final y su mensaje.

        Parámetros:
            ip (str): IP de destino final, en formato a.b.c.d.
            port (int): Puerto de destino final.
            message (str): Contenido del paquete, sin headers.
        """
        self.ip: str = ip
        self.port: int = port
        self.message: str = message

    @classmethod
    def from_bytes(cls, raw: bytes) -> "IPPacket":
        """
        Construye un paquete a partir de los bytes recibidos por el socket.

        Parámetros:
            raw (bytes): IP (4 bytes) + puerto (2 bytes) + mensaje.

        Retorna:
            IPPacket: El paquete con sus campos separados.
        """
        # Cada uno de los 4 primeros bytes es un número de la IP a.b.c.d
        a: int = raw[0]
        b: int = raw[1]
        c: int = raw[2]
        d: int = raw[3]
        ip: str = f"{a}.{b}.{c}.{d}"
        port: int = int.from_bytes(raw[IP_SIZE:HEADER_SIZE], "big")
        message: str = raw[HEADER_SIZE:].decode()
        return cls(ip, port, message)

    def to_bytes(self) -> bytes:
        """
        Codifica el paquete como IP (4 bytes) + puerto (2 bytes) + mensaje.

        Retorna:
            bytes: El paquete listo para enviarse por el socket.
        """
        octets: list[str] = self.ip.split(".")
        ip: bytes = bytes([int(octets[0]), int(octets[1]), int(octets[2]), int(octets[3])])
        # big-endian: orden de bytes de red, el mismo que usa IP real
        port: bytes = self.port.to_bytes(PORT_SIZE, "big")
        return ip + port + self.message.encode()

    def __str__(self) -> str:
        """
        Retorna:
            str: El paquete en formato ip;puerto;mensaje, como en la guía.
        """
        return f"{self.ip};{self.port};{self.message}"


def parse_packet(IP_packet: bytes) -> IPPacket:
    """
    Extrae los headers y el mensaje de un paquete en bytes.

    Parámetros:
        IP_packet (bytes): Paquete recibido por el socket.

    Retorna:
        IPPacket: El paquete parseado.
    """
    return IPPacket.from_bytes(IP_packet)


def create_packet(parsed_IP_packet: IPPacket) -> bytes:
    """
    Crea el paquete en bytes a partir de un paquete parseado.

    Parámetros:
        parsed_IP_packet (IPPacket): Paquete retornado por parse_packet.

    Retorna:
        bytes: El paquete codificado.
    """
    return parsed_IP_packet.to_bytes()
