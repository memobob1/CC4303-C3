import socket
import sys

from packet import IPPacket, create_packet


def parse_header(header: str) -> tuple[str, int, int]:
    """
    Separa el destino final escrito como "IP;puerto;ttl".

    Parámetros:
        header (str): Destino final y tiempo de vida en formato "IP;puerto;ttl".

    Retorna:
        tuple[str, int, int]: La IP de destino, el puerto de destino y el tiempo de vida del paquete.
    """
    parts: list[str] = header.split(";")
    return parts[0], int(parts[1]), int(parts[2])


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
    Lee el destino final, el mensaje y la dirección de envío desde sys.argv y envía el paquete.
    """
    if len(sys.argv) != 5:
        sys.exit('Uso: python3 enviar.py "IP_final;puerto_final;tiempo_de_vida" "mensaje" IP_envio puerto_envio')
    ip, port, ttl = parse_header(sys.argv[1])
    message: str = sys.argv[2]
    send_address: tuple[str, int] = (sys.argv[3], int(sys.argv[4]))
    packet: IPPacket = IPPacket(ip, port, ttl, message)
    send_packet(packet, send_address)


if __name__ == "__main__":
    main()
