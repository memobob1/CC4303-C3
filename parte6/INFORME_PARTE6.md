# Informe Actividad 6: Fragmentación

**Curso:** CC4303 Redes
**Integrantes:** César Barrueto, Jaime Sepúlveda
**Profesora:** Ivana Bachmann
**Auxiliar:** Julián Ferreira
**Fecha:** 16 de noviembre de 2026

**Declaración de uso de IA:** Usamos herramientas de IA como apoyo para la documentación del código, la redacción de este informe, la preparación y ejecución de tests para comprobar los resultados, y el debug de errores y problemas.

---

## 1. Cómo ejecutar las pruebas

Desde `parte6/`, un router por terminal:

```
python3 router.py 127.0.0.1 8881 rutas_R1_v3_mtu.txt
python3 router.py 127.0.0.1 8882 rutas_R2_v3_mtu.txt
python3 router.py 127.0.0.1 8883 rutas_R3_v3_mtu.txt
python3 router.py 127.0.0.1 8884 rutas_R4_v3_mtu.txt
python3 router.py 127.0.0.1 8885 rutas_R5_v3_mtu.txt
```

Para enviar un paquete (el tamaño se calcula solo a partir del mensaje):

```
python3 enviar.py "IP;puerto;TTL;ID;offset;FLAG" "mensaje" IP_primer_router puerto_primer_router
python3 enviar.py "127.0.0.1;8885;10;347;0;0" "hola!" 127.0.0.1 8881
```

## 2. Explicación del código

Partimos de una copia de la actividad Forwarding básico con TTL (`parte5/`) y mantuvimos su estructura: cada router es un proceso con un socket UDP y su tabla de rutas, `check_routes` elige el siguiente salto con round-robin entre las rutas de un mismo destino, y el TTL baja en 1 en cada salto (con TTL 0 el paquete se descarta). Sobre esa base agregamos lo siguiente.

### 2.1 `packet.py`: agregamos elementos en el header

El header pasa de 7 a 18 bytes:

| IP | Puerto | TTL | ID | Offset | Tamaño | FLAG | mensaje |
|---|---|---|---|---|---|---|---|
| 4 | 2 | 1 | 2 | 4 | 4 | 1 | resto |

Agregando los siguientes elementos:

- **ID:** identifica a todos los fragmentos que pertenecen al mismo paquete.
- **Offset:** en qué byte del mensaje original empieza el mensaje de este fragmento.
- **Tamaño:** largo del mensaje sin header.
- **FLAG:** 1 si vienen más fragmentos después, 0 si es el último.

`IPPacket` tiene los atributos nuevos `id`, `offset` y `flag`. `from_bytes` lee los campos uno tras otro y `to_bytes` los escribe en el mismo orden (big-endian).

- Usamos ID de 2 bytes, porque la prueba usa ID 347, que no cabe en 1 byte. Offset de 4 bytes, igual que Tamaño, porque el offset puede llegar al largo del mensaje. FLAG como entero de 1 byte, más simple de leer que un bit suelto.
- el Tamaño no se guarda como atributo; se calcula con `len(message)` al crear el paquete, así nunca queda desactualizado al fragmentar.
- El mensaje se guarda como `bytes` y no como texto, porque la fragmentación corta por bytes. Solo se pasa a texto al imprimir.

### 2.2 `router.py`: Ahora agregamos las MTU en las rutas

`read_routes_file` lee un sexto campo adicional, el MTU, y cada ruta se guarda como el par (siguiente salto, MTU). `check_routes` retorna ese par, o `None` si no hay ruta.

- Ahora el MTU va junto al siguiente salto porque es una propiedad del enlace, no del router.
- Decidimos que si una línea de la tabla no trae `/` (como la de R5 en el enunciado), se toma como `/32`, o sea una IP exacta, para que el router no se caiga.



Ahora se fragmenta antes de reenviar: Cuando el paquete no es para el router, se baja el TTL, se llama a `fragment_IP_packet` con el MTU que entregó `check_routes` y se envía cada fragmento al mismo siguiente salto.

- Con esto TTL se baja antes de fragmentar, así todos los fragmentos llevan el TTL ya descontado.

Se agregaron diccionario de fragmentos y re-ensamblaje: El router tiene `self.fragments: dict[int, list[bytes]]`, con el ID como llave. Cada vez que llega algo dirigido a él, `store_and_reassemble` lo agrega a la lista de su ID e intenta re-ensamblar. Si sale un paquete, imprime el mensaje.

- Al re-ensamblar se borra el ID del diccionario. Si no, al mandar otra vez un paquete con el mismo ID se mezclarían fragmentos viejos con nuevos y nunca se volvería a completar.



### 2.3 `fragmentation.py`: Se agrega `fragment_IP_packet`

Función cuyo propóstio es verificar si el paquete completo cabe en el MTU, en ese caso, retorna `[IP_packet]`. Si no, corta el mensaje en trozos de `MTU - 18` bytes y a cada trozo le pone su propio header con el offset y el FLAG ajustados.

- El offset de cada trozo es `offset_original + inicio_del_trozo`, así sigue apuntando a la posición en el mensaje original aunque se esté re-fragmentando un fragmento.
- Ahora todos los trozos llevan FLAG 1, menos el último, que hereda el FLAG del paquete que se cortó. Si se corta un fragmento del medio (FLAG 1), su último trozo sigue en 1 porque detrás vienen más.
- La función siempre retorna una lista, para que el router mande "cada fragmento" sin distinguir casos.

También se añadió la función `reassemble_IP_packet`que ordena los fragmentos por offset y los pega revisando que cada uno empiece justo donde terminó el anterior (`offset == largo pegado hasta ahora`) y que el último tenga FLAG 0. Si falta alguno, retorna `None`. Si está completo, retorna el paquete con offset 0, FLAG 0 y el mensaje entero.

- Con esto, un paquete sin fragmentar es el único con offset 0 y FLAG 0 a la vez, así que una lista de 1 elemento se resuelve con las mismas dos revisiones: si es un paquete entero entonces se retorna, si es un fragmento suelto da `None`.


### Otros archivos

- `enviar.py` y `prueba_router.py`: reciben el header como `"IP;puerto;TTL;ID;offset;FLAG"`.
- `rutas_R1_v3_mtu.txt` a `rutas_R5_v3_mtu.txt`: tablas del enunciado con el MTU de cada enlace.

## 3. Pruebas por paso

| Paso | Prueba | Resultado |
|---|---|---|
| 1 | `parse_packet` y `create_packet` inclyuendo los nuevos headers `IP_packet_v1` (`127.0.0.1;8885;10;347;0;5;0;hola!`) | `IP_packet_v1 == IP_packet_v2 ? True` |
| 2 | Testea si los 5 routers con las tablas + MTU envían paquetes entre ellos| No se cae; `check_routes` entrega (siguiente salto, MTU) y sigue alternando rutas |
| 3 | Testea la fragmentación de `fragment_IP_packet` con `hola!` (23 bytes) y MTU 50 (no fragmenta), y con un paquete de 150 bytes y MTU 100 (fragmenta)| Lista de 1; lista de 2 fragmentos de 100 y 68 bytes |
| 5 | Agregamos tests de fragmentar con MTU 50 y re-ensamblar, también desordenado y re-fragmentado (100 y luego 50) | `IP_packet_v1 = IP_packet_v2 ? True` en todos los casos; `None` si falta un fragmento |
| 7 | 2 paquetes (ID 1 e ID 2) fragmentados y enviados a R5 en orden, en desorden e intercalando ID | En las 3 rondas R5 imprime los 2 mensajes completos, una vez cada uno |

## 4. Pruebas con 5 routers

### 4.Tests de 1 TTL y round-robin sin fragmentación

Enviamos 3 veces `hola!` (ID 347, TTL 10, 23 bytes en total) de R1 a R5. Como 23 bytes caben en todos los enlaces, nunca se fragmenta ("en 1 fragmento(s)") y llegan los 3. R2 alterna su salida entre R3 y R4:

```
R2: Redirigiendo paquete hola! ... desde ('127.0.0.1', 8882) hacia ('127.0.0.1', 8883) en 1 fragmento(s)
R2: Redirigiendo paquete hola! ... desde ('127.0.0.1', 8882) hacia ('127.0.0.1', 8884) en 1 fragmento(s)
R2: Redirigiendo paquete hola! ... desde ('127.0.0.1', 8882) hacia ('127.0.0.1', 8883) en 1 fragmento(s)
R5: Ha recibido el mensaje: hola!   (x3)
```

El TTL también se sigue respetando con fragmentos: en las pruebas con TTL 10 algunos fragmentos se descartan con `Se recibió paquete ... con TTL 0` (como se mostrará en 4.2).

### 4.Tests de 2 Paquete de 150 bytes desde R1 a R5

Paquete de 150 bytes en total (18 de header + 132 de mensaje). Log de un envío (resumido):

```
R1: Redirigiendo paquete 'abcdefghij...' ... hacia ('127.0.0.1', 8882) en 2 fragmento(s)
R2: Redirigiendo paquete 'abcdefghij...' ... hacia ('127.0.0.1', 8883) en 3 fragmento(s)
R2: Redirigiendo paquete 'cdefghijab...' ... hacia ('127.0.0.1', 8884) en 1 fragmento(s)
...
R5: Ha recibido el mensaje: abcdefghijabcdefghij... (132 letras, completo)
```

- R1 a R2 (MTU 100): 150 > 100, se corta en 2: 82 bytes de mensaje (offset 0, FLAG 1) y 50 bytes (offset 82, FLAG 0).
- R2 a R3 (MTU 50): el fragmento de 82 se **re-fragmenta** en 3 (32 + 32 + 18).
- R2 a R4 (MTU 80): el fragmento de 50 bytes de mensaje (68 en total) cabe y pasa entero.
- R5 junta los pedazos, que llegan desordenados y por caminos distintos, y imprime el mensaje completo.

Enviamos el paquete 10 veces con TTL 10: R5 re-ensambló 7 y 3 se perdieron porque algún fragmento llegó a TTL 0. Con TTL 30 llegaron los 10.

### 4.3 Preguntas

**¿Su código logra re-fragmentar un fragmento?** Sí. En R2 el fragmento de 82 bytes de mensaje que viene de R1 no cabe en el enlace hacia R3 (MTU 50) y se corta en 3 fragmentos con offsets [0, 32, 64]. El último de ellos queda con FLAG 1 porque hereda el FLAG del fragmento original, y así R5 sabe que todavía faltan los bytes desde el 82.

**¿Cómo cambia el comportamiento si se envía desde otros routers?** Cambia dónde y en cuántos pedazos se fragmenta, porque depende del MTU del primer enlace y del camino que toca, por ejemplo:

- **Desde R5 a R1:** si sale por R4 (MTU 140), se corta en solo 2 fragmentos (122 + 10 bytes de mensaje), y después de R4 a R2 (MTU 80) re-fragmenta el de 122. Si sale por R3 (MTU 55), se corta en 4 fragmentos de hasta 37 bytes.
- **Desde R3 a R1:** si sale por R2 (MTU 50) se corta en 5 fragmentos; si sale por R5 (MTU 55), en 4. Luego de R2 a R1 (MTU 100) no necesita cortar nada.
- Eso sí, en todos los casos el mensaje llegó completo a R1.

Observaciones:

- El round-robin se aplica a cada paquete que pasa por el router, y cada fragmento también es un paquete, así que **fragmentos de un mismo paquete pueden viajar por caminos distintos** y llegan desordenados. Por eso el re-ensamblaje ordena por offset.
- Los fragmentos **nunca se vuelven a unir en el camino**: aunque después pasen por un enlace más grande (R4 → R5 con MTU 140), siguen chicos. Solo se unen en el destino final (sigue el principio end-to-end).
- En este ejemplo, R3 y R4 también tienen rutas hacia R5 que vuelven por R2, así que algunos fragmentos dan vueltas y gastan TTL. **Si se pierde un solo fragmento, se pierde el paquete entero**, porque el destino nunca puede completarlo. Mientras más fragmentos, más probable es que alguno se pierda.

## 5. Limitaciones y conclusión

- Al cortar por bytes, una letra de 2 bytes (tilde o ñ) puede quedar partida entre dos fragmentos, y el `decode()` del router intermedio fallaría al imprimirla. En las pruebas usamos mensajes sin tildes.
- Los fragmentos de un paquete que nunca se completa quedan guardados en el diccionario del destino.

Nuestro mini-Internet ahora fragmenta los paquetes según el MTU de cada enlace, puede re-fragmentar fragmentos y los re-ensambla en el destino aunque lleguen desordenados o intercalados con otros paquetes, manteniendo el TTL y el round-robin de la actividad anterior.
