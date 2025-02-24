# PokeGramBot
# Telegram Bot - Juego de Captura de Pokémon

Este es un bot de Telegram que permite a los usuarios capturar, ver e interactuar con Pokémones virtuales. El bot tiene varios comandos para interactuar con el juego, incluyendo capturar Pokémones aleatorios, ver tu colección, una pokedex, y más.

## Características

- **/ayuda**: Muestra la lista de comandos.
- **/captura**: Muestra la probabilidad de captura de los Pokémones..
- **/capturados**: Te muestra por privado una lista detallada de tus Pokémones.
- **/combate**: Inicia un combate con un Pokémon aleatorio tuyo. El perdedor pierde su Pokémon. Hay una chance de que el ganador se quede con el pokémon del perdedor.
- **/iniciar**: El bot saludará.
- **/jugadores**: Muestra una lista con todos los jugadores del grupo.
- **/mercader**: Llama al mercader.
- **/micoleccion**: Muestra cuantos pokemones vas atrapando.
- **/mispokemones**: Muestra cuantos pokemones tienes en total.
- **/mistitutlos**: Muestra tus títulos con sus descripciones.
- **/perfil**: Muestra tu perfil o el de algún otro jugador.
- **/pokedex**: Muestra los datos de Pokémon a partir de su ID o Nombre.
- **/registrar**: Registra tu nombre de usuario.
- **/spawn**: Spawnea un Pokémon aleatorio.
- **/teelijo**: Invoca uno de tus Pokémones de forma aleatoria.
- **/titulos**: Muestra un listado de todos los títulos y cómo conseguirlos.
- **/yoteelijo**: Invoca un Pokémon a partir de su ID o Nombre.

Además de eso, el bot solamente funciona entre las 10:00 AM y las 22:59 PM (GMT-3). También manda un spawn automático cada 10 minutos.

## Importante
El bot tiene algunas funciones que el usuario que desee usarlo debería eliminar en caso de que no las quiera. Como la función de reemplazar '(?' con un mensaje inapropiado que. También hay una función que elimina un pokémon aleatorio de un usuario que escriba '( ?' en un mensaje.

Se espera que el usuario que desee utilizar el bot tenga conocimientos de programación suficientes para poder implementarlo en su propio grupo.
## Requisitos

- Python 3.8+
- `python-telegram-bot` libreria
- `pytz` para el manejo de timezone
- MongoDB para el almacenamiento de las bases de datos

### Instalación de dependencias

Para instalar las librerias necesarias, ejecute el siguiente comando:

```bash
pip install -r requirements.txt
