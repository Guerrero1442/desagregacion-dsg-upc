import pandas as pd
from loguru import logger

from config.settings import settings
from desagregacion_dsg_upc import (
    DatabaseError,
    fetch_data_in_chunks,
    get_db_connection,
    setup_logging,
)


def main():
    """
    Punto de entrada principal de la aplicación.
    """
    setup_logging()

    logger.info("Iniciando la aplicación.")
    dfs_chunk = []

    try:
        # Probar la conexión a la base de datos
        with get_db_connection() as connection:
            logger.success("¡Conexión a la base de datos exitosa!")
            # Puedes ejecutar una consulta simple aquí si lo deseas
            # result = connection.execute(text("SELECT 1 FROM DUAL"))
            # logger.info(f"Resultado de la consulta de prueba: {result.scalar_one()}")
            for chunk in fetch_data_in_chunks(
                connection, settings.processing.query_input
            ):
                dfs_chunk.append(chunk)
        df_desagregacion_db = pd.concat(dfs_chunk)

        # Procesar el DataFrame completo aquí
        logger.info(f"Procesando DataFrame de tamaño {len(df_desagregacion_db)}")

    except DatabaseError as e:
        logger.error(f"Error de base de datos: {e}")
    except Exception as e:
        logger.exception(f"Ocurrió un error inesperado en la aplicación: {e}")

    logger.info("La aplicación ha finalizado.")


if __name__ == "__main__":
    main()
