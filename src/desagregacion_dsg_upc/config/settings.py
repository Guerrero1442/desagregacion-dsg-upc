from typing import Any, Tuple, Type

import yaml
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class YamlSettingsSource(PydanticBaseSettingsSource):
    def get_field_value(self, field: Any, field_name: str) -> Tuple[Any, str, bool]:
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        try:
            with open("config.yaml", "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}


class ProcessingConfig(BaseModel):
    query_input: str
    output_file: str
    columns_dinero: list[str]
    column_fecha: str
    column_desagregacion: str
    column_descripcion_cups: str
    column_valor_liquidado: str
    column_codigo_osi: str


class Settings(BaseSettings):
    processing: ProcessingConfig

    db_host: str
    db_user: str
    db_password: str
    db_port: int
    db_service_name: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlSettingsSource(settings_cls),
        )


settings = Settings()  # type: ignore
