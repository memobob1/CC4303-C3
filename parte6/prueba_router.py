import sys
from packet import IPPacket
from enviar import parse_header, send_packet

def main() -> None:
    """
    Lee el destino final y la dirección de envío desde sys.argv y envía cada línea del archivo
    'texto_de_prueba.txt' usando paquetes IP.
    """
    if len(sys.argv) != 4:
        sys.exit('Uso: python3 prueba_router.py "IP_final;puerto_final;ttl;id;offset;flag" IP_envio puerto_envio')

    ip, port, ttl, id, offset, flag = parse_header(sys.argv[1])
    send_address: tuple[str, int] = (sys.argv[2], int(sys.argv[3]))

    with open("texto_de_prueba.txt", "r") as file:
        for line in file:
            message: bytes = line.encode()
            packet: IPPacket = IPPacket(ip, port, ttl, id, offset, flag, message)
            send_packet(packet, send_address)


if __name__ == "__main__":
    main()