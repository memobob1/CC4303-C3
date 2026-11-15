import socket
import sys

from packet import IPPacket, create_packet


def parse_header(header: str) -> tuple[str, int, int, int, int, int]:
    """
    Separa el header escrito como "IP;puerto;ttl;id;offset;flag".

    Parámetros:
        header (str): Destino final y datos del paquete en formato "IP;puerto;ttl;id;offset;flag".

    Retorna:
        tuple[str, int, int, int, int, int]: IP y puerto de destino, tiempo de vida, ID, offset y flag.
    """
    parts: list[str] = header.split(";")
    return parts[0], int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])


def send_packet(packet: IPPacket, address: tuple[str, int]) -> None:
    """
    Envía un paquete por UDP a la dirección indicada.

    Parámetros:
        packet (IPPacket): Paquete a enviar.
        address (tuple[str, int]): Par (IP, puerto) al que se envía el paquete.
    """
    sender: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender.sendto(create_packet(packet), address)
    sender.close()


def main() -> None:
    """
    Lee el header, el mensaje y la dirección de envío desde sys.argv y envía el paquete.
    """
    if len(sys.argv) != 5:
        sys.exit('Uso: python3 enviar.py "IP_final;puerto_final;ttl;id;offset;flag" "mensaje" IP_envio puerto_envio')
    ip, port, ttl, id, offset, flag = parse_header(sys.argv[1])
    message: bytes = sys.argv[2].encode()
    send_address: tuple[str, int] = (sys.argv[3], int(sys.argv[4]))
    packet: IPPacket = IPPacket(ip, port, ttl, id, offset, flag, message)
    send_packet(packet, send_address)


if __name__ == "__main__":
    main()
