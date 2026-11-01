# CC4303-C3

Control 3 Redes: Actividad Forwarding básico. Simulamos un mini-Internet donde cada router es un proceso con un socket UDP y su tabla de rutas.

## Estado actual

Listos los pasos 2 a 5 de la Parte I. Falta del paso 6 en adelante.

## Archivos

- `packet.py`: formato del paquete (header de 6 bytes: IP + puerto). Incluye `parse_packet` y `create_packet`.
- `test_packet.py`: prueba que `parse_packet` y `create_packet` son inversas.
- `router.py`: router que escucha en un socket UDP. Por ahora solo imprime lo que recibe.
- `enviar.py`: envía un mensaje a un destino final pasando por un primer router.

## Cómo seguir

- Paso 6: crear `check_routes` en un `routing.py`. Recorre la tabla en orden y retorna el siguiente salto o `None`. El CIDR se calcula a mano (no se puede importar `ipaddress`).
- Paso 7: en el router, imprimir el mensaje si es para él o reenviarlo según `check_routes`.
- Pasos 8 y 9: round-robin por área y ruta default al final de cada tabla.
- Parte II: agregar TTL al header.
