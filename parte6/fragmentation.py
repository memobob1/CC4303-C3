from packet import HEADER_SIZE, IPPacket, create_packet, parse_packet


"""
Archivo de funciones para fragmentar paquetes IP. Se utiliza en router.py para fragmentar paquetes que no caben en el MTU del siguiente salto.
"""

def fragment_IP_packet(IP_packet: bytes, MTU: int) -> list[bytes]:
    """
    Corta un paquete (o fragmento) en fragmentos que quepan por un enlace de cierto MTU.

    Parámetros:
        IP_packet (bytes): Paquete completo, con header.
        MTU (int): Tamaño máximo en bytes (header incluido) que deja pasar el enlace.

    Retorna:
        list[bytes]: Los fragmentos en orden; [IP_packet] si el paquete ya cabe.
    """

    # Si el paquete ya cabe en el MTU, no hay que fragmentarlo, solo devolvemos en una lista
    if len(IP_packet) <= MTU:
        return [IP_packet]

    # si no cabe, lo fragmentamos en trozos de tamaño MTU - HEADER_SIZE, y creamos un nuevo paquete para cada trozo
    packet: IPPacket = parse_packet(IP_packet)
    chunk_size: int = MTU - HEADER_SIZE
    fragments: list[bytes] = []
    start: int = 0 # indice del primer byte del trozo que vamos a cortar

    # mientras queden bytes por cortar, cortamos un trozo y creamos un nuevo paquete con ese trozo (con su respectivo header y offset)
    while start < len(packet.message):
        chunk: bytes = packet.message[start : start + chunk_size] # se corta un trozo del mensaje original
        end: int = start + len(chunk)

        # Los trozos intermedios dejan su FLAG en 1, y el último trozo en 0
        flag: int = 1
        if end == len(packet.message):
            flag = packet.flag # copio el flag original del paquete, que debería ser 0

        # Armamos el fragmento con el mismo header que el paquete original, pero con el offset actualizado y el flag correspondiente
        fragment: IPPacket = IPPacket(packet.ip, packet.port, packet.ttl, packet.id,
                                      packet.offset + start, flag, chunk)
        fragments.append(create_packet(fragment))
        start = end

    return fragments
