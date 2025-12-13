import yaml
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Clase de configuración que carga las variables de entorno desde un archivo .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Credenciales de Base de Datos
    db_host: str
    db_user: str
    db_password: str
    db_port: int
    db_service_name: str


# Instancia única de la configuración
settings = Settings()  # type: ignore


def load_config_yaml(config_path: Path = Path("config/config.yaml")) -> dict:
    """
    Loads configuration from a YAML file.

    Args:
        config_path: The path to the YAML configuration file.

    Returns:
        A dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config if config is not None else {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML configuration file {config_path}: {e}")