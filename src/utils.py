import sys

from loguru import logger


def setup_logging(
    log_file_path: str = "logs/app_{time}.log",
    rotation: str = "500 MB",
    retention: str = "10 days",
    level: str = "INFO",
    console_log_level: str = "INFO",
):
    """
    Configura Loguru para el registro de eventos en la consola y en un archivo.

    Args:
        log_file_path (str): Ruta y nombre del archivo de log. Puede incluir '{time}' para rotación.
        rotation (str): Criterio de rotación del archivo de log (ej. "500 MB", "1 day").
        retention (str): Criterio de retención de los archivos de log (ej. "10 days", "1 week").
        level (str): Nivel mínimo de los mensajes que se escribirán en el archivo de log.
        console_log_level (str): Nivel mínimo de los mensajes que se mostrarán en la consola.
    """
    # Eliminar el handler por defecto de Loguru para configurar los nuestros
    logger.remove()

    # Añadir sink para la consola
    logger.add(
        sys.stderr,
        level=console_log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # Añadir sink para el archivo, con rotación y retención
    logger.add(
        log_file_path,
        rotation=rotation,
        retention=retention,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
    )

    logger.info("Configuración de logging inicializada.")
