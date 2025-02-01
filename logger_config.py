import logging

# Configurar el logger
logging.basicConfig(
    filename="error.log",  # Archivo donde se guardarán los errores
    level=logging.ERROR,  # Solo registra errores y niveles superiores
    format="%(asctime)s - %(levelname)s - %(message)s",  # Formato del log
    datefmt="%Y-%m-%d %H:%M:%S"  # Formato de fecha y hora
)
# Crear el logger
logger = logging.getLogger(__name__)