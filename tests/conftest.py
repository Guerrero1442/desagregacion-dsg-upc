import pytest


class MockProcessingConfig:
    def __init__(self):
        self.column_descripcion_cups = "DESCRIPCION_CUP"
        self.column_desagregacion = "CANTIDAD_PROCEDIMIENTO"
        self.columns_dinero = ["VALOR_NETO"]
        self.column_fecha = "FECHA_INICIO_TRATAMIENTO"
        self.column_valor_liquidado = "VALOR_LIQUIDADO"
        self.column_codigo_osi = "CODIGO_OSI"


class MockSettings:
    def __init__(self):
        self.processing = MockProcessingConfig()


@pytest.fixture
def settings_mock(monkeypatch):
    """Fixture para mockear el objeto settings."""
    mocked_settings = MockSettings()

    # Lista de todos los lugares donde tu código importa 'settings'
    # Debes agregar aquí las rutas de importación de tus nuevas reglas a medida que las crees
    modules_to_patch = [
        "desagregacion_dsg_upc.rules.base.settings",
        "desagregacion_dsg_upc.rules.consulta_cantidad_menor.settings",
        "desagregacion_dsg_upc.rules.consulta_psicologia_cantidad_menor_igual_15.settings",
        "desagregacion_dsg_upc.rules.consulta_psicologia_cantidad_mayor_15.settings",
        "desagregacion_dsg_upc.rules.contiene_domicili.settings",
        "desagregacion_dsg_upc.rules.contiene_curaci.settings",
        "desagregacion_dsg_upc.rules.contiene_terapia_codigo_osi.settings",
        # "desagregacion_dsg_upc.rules.nueva_regla.settings",
    ]

    for module_path in modules_to_patch:
        # 'raising=False' evita que falle si el módulo aún no ha sido importado o no existe
        monkeypatch.setattr(module_path, mocked_settings, raising=False)

    return mocked_settings
