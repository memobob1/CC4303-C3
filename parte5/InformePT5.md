# CC4303-C3

# Informe parte 5: Forwarding básico

Integrantes: César Barrueto, Jaime Sepúlveda
Fecha: 16/11/2026
Profesora: Ivana Bachmann.
Auxiliar: Julián Ferreira

Enlace de github: [https://github.com/memobob1/CC4303-C3/tree/main/parte5](https://github.com/memobob1/CC4303-C3/tree/main/parte5)

Disclaimer Uso de IA:

## Comparación entre la tabla de rutas de esta actividad y la real

- La tabla de rutas real agrupa rangos de direcciones IP utilizando una IP específica y una máscara. Por otro lado, nuestra tabla de rutas utiliza una única IP
  y un rango de puertos para agrupar las direcciones IP de los distintos routers. La tabla de rutas de la actividad también incluye la máscara, pero
  no es importante, ya que la IP siempre es la misma.
- Para avanzar por la red, la tabla de rutas real devuelve la IP del siguiente router y la interfaz de salida desde donde será enviado el paquete.
  Por el contrario, en nuestra tabla de rutas se devuelve la IP y el puerto del siguiente router (socket UDP).

## Round Robin y la clase RoutesToArea

Para implementar Round Robin es necesario que el router pueda alternar entre las rutas que se dirigen a una misma área de la red. Eso implica
que el router debe poder recordar cuál fue la última ruta que utilizó para mandar mensajes a una red determinada.

Nosotros creamos la clase RoutesToArea que agrupa todas las rutas posibles, desde un router en específico, para dirigirse a la misma red.
Esta clase es la que se encarga de alternar entre routers (con Round Robin) y devolver la siguiente ruta a usar.
También tiene la capacidad de identificar si la dirección final de un paquete pertenece a su red.

### Atríbutos de la clase RoutesToArea:

- ip: Un string con la IP de la red de destino.
- bits_to_compare: Un entero con el largo del prefijo CIDR (cuántos bits de la IP definen la red).
- first_port: Un entero con el primer puerto del rango de destino.
- last_port: Un entero con el último puerto del rango de destino.
- possible_routes: La lista de rutas (IP, puerto) que existen para viajar la red de destino.
- next_hop_idx: Un entero con el índice de la próxima ruta a usar para viajar a la red (round-robin).

### Métodos de la clase RoutesToArea:

- add_route: Recibe una ruta (IP, puerto) y la añade a la lista de "possible_routes". Se utiliza cuando se instancia esta clase para añadir
  todas las rutas de la tabla de rutas.
  
- contains_address: Recibe una dirección final (IP, puerto) y revisa si esa dirección pertenece a la red asociada a esta clase, utilizando:
  
  ```
  ip[:self.bits_to_compare] == self.ip[:self.bits_to_compare] and self.first_port <= port <= self.last_port
  ```
  La primera igualdad siempre se cumple pues en esta actividad utilizamos la misma IP para todos los routers.
  
- get_next_hop: Devuelve la i-ésima ruta almacenada en "possible_routes", donde el valor de i es "next_hop_idx". Luego, actualiza "next_hop_id" para
  que apunte hacia la siguiente ruta de la lista:
  
  ```
  self.next_hop_idx = (self.next_hop_idx + 1) % len(self.possible_routes)
  ```
  Esa línea de código permite implementar Round Robin y alternar entre las distintas rutas.

## Script para enviar mensajes

Cuando los routers ya están encendidos en otras consolas, nuestro script "enviar.py" permite enviar un mensaje desde un router
determinado hacia otro router. El comando para usarlo (en una terminal aparte) es de la siguiente forma:
```
python3 enviar.py "IP_final;puerto_final;tiempo_de_vida" "mensaje" IP_envio puerto_envio
```
Por ejemplo, para enviar el mensaje "The Apothecary Diaries" desde R1 hacia R4, con un TTL de 15, se ejecuta:
```
python3 enviar.py "127.0.0.1;8884;15" "The Apothecary Diaries" 127.0.0.1 8881
```

## El router default

En esta actividad nuestro router default se encuentra en la dirección (127.0.0.1, 7000). Queremos que los routers solamente envíen mensajes a esta dirección
cuando ninguna de las otras rutas de la tabla de rutas permitan llegar a la dirección final. Por lo tanto, la ruta default se debe revisar al final,
es decir, la ruta default debe ubicarse en la última línea de todas las tablas de rutas.

Por ejemplo, la tabla de rutas de R2 luce de la siguiente forma:
```
# archivo rutas_R2_v3.txt
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8883 8885 127.0.0.1 8883
127.0.0.1/24 8883 8885 127.0.0.1 8884
127.0.0.1/0 0 65535 127.0.0.1 7000
```
Notar que la ruta default acepta todas las IPs (la máscara es 0), y todos los puertos posibles (desde el puerto 0 hasta el puerto 65535).
