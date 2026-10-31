from packet import IPPacket, create_packet, parse_packet


def main() -> None:
    """
    Verifica que create_packet reconstruye el mismo paquete que recibe parse_packet.
    """
    IP_packet_v1: bytes = b"\x7f\x00\x00\x01\x22\xb2hola"  # 127.0.0.1;8882;hola
    parsed_IP_packet: IPPacket = parse_packet(IP_packet_v1)
    IP_packet_v2: bytes = create_packet(parsed_IP_packet)
    print(parsed_IP_packet)
    print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))


if __name__ == "__main__":
    main()
