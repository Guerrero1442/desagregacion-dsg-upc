import socket
from contextlib import contextmanager
from typing import Generator

import oracledb
import pandas as pd
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy.engine import Connection, Engine

from config.settings import settings
from src.exceptions import ConfigError, DatabaseError


@contextmanager
def get_db_connection() -> Generator[Connection, None, None]:
    """
    Establishes a database connection using SQLAlchemy and provides it via a context manager.

    Args:
        config: A dictionary containing database connection parameters.
                Expected keys: 'host', 'port', 'service_name', 'user', 'password'.

    Yields:
        A SQLAlchemy Connection object.

    Raises:
        DatabaseError: If there's an issue connecting to the database.
    """
    conn = None
    try:
        # Construct Oracle connection string for SQLAlchemy
        # Example: oracle+oracledb://user:pass@host:port/?service_name=service
        connection_string = (
            f"oracle+oracledb://{settings.db_user}:{settings.db_password}@"
            f"{settings.db_host}:{settings.db_port}/?service_name={settings.db_service_name}"
        )

        engine: Engine = create_engine(connection_string)
        logger.info("Attempting to establish database connection.")
        conn = engine.connect()
        logger.info("Database connection established successfully.")
        yield conn
    except ConfigError as e:
        logger.error(f"Configuration error for database connection: {e}")
        raise e
    except sqlalchemy_exc.DatabaseError as e:
        # Extraer el error original para un manejo específico
        if isinstance(e.orig, oracledb.Error):
            error_obj = e.orig.args[0]
            if hasattr(error_obj, "code") and error_obj.code == 257:
                msg = (
                    f"Error de archivador de Oracle (ORA-{error_obj.code}): {error_obj.message}. "
                    "La base de datos no puede aceptar nuevas conexiones. "
                    "Contacte al DBA para resolver el problema."
                )
                logger.critical(msg)
                raise DatabaseError(msg) from e

        # Para otros errores de DB, registrar y relanzar
        logger.error(f"Error de base de datos no controlado: {e}")
        raise DatabaseError(f"Error de base de datos no controlado: {e}") from e
    except socket.gaierror as e:
        logger.error(f"No se encuentra conectado al servidor de base de datos: {e}")
        raise DatabaseError(
            f"No se encuentra conectado al servidor de base de datos: {e}"
        ) from e
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred during database connection setup: {e}"
        )
        raise DatabaseError(f"An unexpected database error occurred: {e}") from e
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")


def fetch_data_in_chunks(
    conn: Connection, query: str, chunk_size: int = 10000
) -> Generator[pd.DataFrame, None, None]:
    """
    Fetches data from the database in chunks using pandas.

    Args:
        conn: An active SQLAlchemy Connection object.
        query: The SQL query to execute.
        chunk_size: The number of rows to fetch per chunk.

    Yields:
        pd.DataFrame: A DataFrame containing a chunk of data.

    Raises:
        DatabaseError: If there's an issue executing the query or fetching data.
    """
    logger.info(
        f"Fetching data in chunks with query: {query[:100]}..."
    )  # Log first 100 chars of query
    try:
        # Use pandas read_sql with chunksize for efficient memory usage
        for chunk in pd.read_sql_query(
            text(query), conn, chunksize=chunk_size, dtype="str"
        ):
            yield chunk
        logger.info("Finished fetching data in chunks.")
    except Exception as e:
        logger.exception(
            f"Error fetching data in chunks with query: {query[:100]}... Error: {e}"
        )
        raise DatabaseError(f"Failed to fetch data in chunks: {e}") from e
