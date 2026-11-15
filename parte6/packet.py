IP_SIZE: int = 4
PORT_SIZE: int = 2
TTL_SIZE: int = 1
ID_SIZE: int = 2
OFFSET_SIZE: int = 4
SIZE_SIZE: int = 4
FLAG_SIZE: int = 1
HEADER_SIZE: int = IP_SIZE + PORT_SIZE + TTL_SIZE + ID_SIZE + OFFSET_SIZE + SIZE_SIZE + FLAG_SIZE


class IPPacket:
    """
    Paquete IP (o fragmento) del mini-Internet ya parseado.

    Atributos:
        ip (str): IP de destino final, en formato a.b.c.d.
        port (int): Puerto de destino final.
        ttl (int): El tiempo de vida (time to live) del paquete.
        id (int): Identificador común a todos los fragmentos de un mismo paquete.
        offset (int): Posición en bytes donde empieza este mensaje dentro del paquete original.
        flag (int): 1 si quedan fragmentos después de este, 0 si es el último.
        message (bytes): Contenido del paquete, sin headers.
    """

    def __init__(self, ip: str, port: int, ttl: int, id: int, offset: int, flag: int, message: bytes) -> None:
        """
        Crea un paquete con su destino final, sus datos de fragmentación y su mensaje.

        Parámetros:
            ip (str): IP de destino final, en formato a.b.c.d.
            port (int): Puerto de destino final.
            ttl (int): El tiempo de vida (time to live) del paquete.
            id (int): Identificador común a todos los fragmentos de un mismo paquete.
            offset (int): Posición en bytes donde empieza este mensaje dentro del paquete original.
            flag (int): 1 si quedan fragmentos después de este, 0 si es el último.
            message (bytes): Contenido del paquete, sin headers.
        """
        self.ip: str = ip
        self.port: int = port
        self.ttl: int = ttl
        self.id: int = id
        self.offset: int = offset
        self.flag: int = flag
        self.message: bytes = message

    @classmethod
    def from_bytes(cls, raw: bytes) -> "IPPacket":
        """
        Construye un paquete a partir de los bytes recibidos por el socket.

        Parámetros:
            raw (bytes): Header de 18 bytes (IP, puerto, TTL, ID, offset, tamaño, flag) + mensaje.

        Retorna:
            IPPacket: El paquete con sus campos separados.
        """
        # Cada uno de los 4 primeros bytes es un número de la IP a.b.c.d
        a: int = raw[0]
        b: int = raw[1]
        c: int = raw[2]
        d: int = raw[3]
        ip: str = f"{a}.{b}.{c}.{d}"

        start: int = IP_SIZE
        port: int = int.from_bytes(raw[start:start + PORT_SIZE], "big")
        start += PORT_SIZE
        ttl: int = int.from_bytes(raw[start:start + TTL_SIZE], "big")
        start += TTL_SIZE
        id: int = int.from_bytes(raw[start:start + ID_SIZE], "big")
        start += ID_SIZE
        offset: int = int.from_bytes(raw[start:start + OFFSET_SIZE], "big")
        start += OFFSET_SIZE
        size: int = int.from_bytes(raw[start:start + SIZE_SIZE], "big")
        start += SIZE_SIZE
        flag: int = int.from_bytes(raw[start:start + FLAG_SIZE], "big")

        message: bytes = raw[HEADER_SIZE:HEADER_SIZE + size]
        return cls(ip, port, ttl, id, offset, flag, message)

    def to_bytes(self) -> bytes:
        """
        Codifica el paquete como header de 18 bytes + mensaje.

        Retorna:
            bytes: El paquete listo para enviarse por el socket.
        """
        octets: list[str] = self.ip.split(".")
        ip: bytes = bytes([int(octets[0]), int(octets[1]), int(octets[2]), int(octets[3])])
        # big-endian: orden de bytes de red, el mismo que usa IP real
        port: bytes = self.port.to_bytes(PORT_SIZE, "big")
        ttl: bytes = self.ttl.to_bytes(TTL_SIZE, "big")
        id: bytes = self.id.to_bytes(ID_SIZE, "big")
        offset: bytes = self.offset.to_bytes(OFFSET_SIZE, "big")
        size: bytes = len(self.message).to_bytes(SIZE_SIZE, "big")
        flag: bytes = self.flag.to_bytes(FLAG_SIZE, "big")
        return ip + port + ttl + id + offset + size + flag + self.message

    def __str__(self) -> str:
        """
        Retorna:
            str: El paquete en formato ip;puerto;ttl;id;offset;tamaño;flag;mensaje.
        """
        return (f"{self.ip};{self.port};{self.ttl};{self.id};{self.offset};"
                f"{len(self.message)};{self.flag};{self.message.decode()}")


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
