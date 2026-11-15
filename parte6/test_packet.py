from packet import IPPacket, create_packet, parse_packet


def main() -> None:
    """
    Verifica que create_packet reconstruye el mismo paquete que recibe parse_packet.
    """
    # 127.0.0.1;8885;10;347;0;5;0;hola!
    IP_packet_v1: bytes = (b"\x7f\x00\x00\x01" + b"\x22\xb5" + b"\x0a" + b"\x01\x5b"
                           + b"\x00\x00\x00\x00" + b"\x00\x00\x00\x05" + b"\x00" + b"hola!")
    parsed_IP_packet: IPPacket = parse_packet(IP_packet_v1)
    IP_packet_v2: bytes = create_packet(parsed_IP_packet)
    print(parsed_IP_packet)
    print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))


if __name__ == "__main__":
    main()
