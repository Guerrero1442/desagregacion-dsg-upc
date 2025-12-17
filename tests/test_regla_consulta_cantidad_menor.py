from datetime import datetime

import pandas as pd
import pytest

from desagregacion_dsg_upc import ReglaConsultaCantidadMenor


# --- Mock de Settings ---
# Para evitar depender de archivos externos como .env o config.yaml en los tests.
class MockProcessingConfig:
    def __init__(self):
        self.column_descripcion_cups = "DESCRIPCION_CUP"
        self.column_desagregacion = "CANTIDAD_PROCEDIMIENTO"
        self.columns_dinero = ["VALOR_NETO"]
        self.column_fecha = "FECHA_INICIO_TRATAMIENTO"


class MockSettings:
    def __init__(self):
        self.processing = MockProcessingConfig()


@pytest.fixture
def settings_mock(monkeypatch):
    """Fixture para mockear el objeto settings."""
    mocked_settings = MockSettings()

    monkeypatch.setattr(
        "desagregacion_dsg_upc.rules.consulta_cantidad_menor.settings", mocked_settings
    )
    monkeypatch.setattr("desagregacion_dsg_upc.rules.base.settings", mocked_settings)
    return mocked_settings


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """DataFrame de ejemplo para los tests."""
    data = {
        "DESCRIPCION_CUP": [
            "CONSULTA DE PRUEBA",
            "CONSULTA CON CANTIDAD ALTA",
            "OTRO PROCEDIMIENTO",
            "CONSULTA ADICIONAL",
        ],
        "CANTIDAD_PROCEDIMIENTO": [3, 10, 5, 1],
        "VALOR_NETO": [3000.0, 5000.0, 1000.0, 1500.0],
        "FECHA_INICIO_TRATAMIENTO": [
            datetime(2025, 1, 1),
            datetime(2025, 2, 1),
            datetime(2025, 3, 1),
            datetime(2025, 4, 1),
        ],
        "OTRA_COLUMNA": ["A", "B", "C", "D"],
    }
    return pd.DataFrame(data)


def test_identificar_registros_correctos(settings_mock, sample_df):
    """Verifica que la regla identifique solo las filas que debe procesar."""
    rule = ReglaConsultaCantidadMenor()
    mask = rule.identificar(sample_df)

    expected_mask = pd.Series(
        [True, False, False, True], name=settings_mock.processing.column_desagregacion
    )

    pd.testing.assert_series_equal(mask, expected_mask, check_names=False)
    assert mask.sum() == 2


def test_desagregacion_completa_de_consulta(settings_mock, sample_df):
    """
    Test de punta a punta que ejecuta la desagregación y valida el resultado.
    """
    processing = settings_mock.processing
    rule = ReglaConsultaCantidadMenor()

    mask_a_procesar = rule.identificar(sample_df)
    df_a_procesar = sample_df[mask_a_procesar].copy()
    df_resto = sample_df[~mask_a_procesar].copy()

    df_procesado = rule.ejecutar_desagregacion(df_a_procesar)

    df_final = pd.concat([df_resto, df_procesado]).sort_index()

    assert len(df_final) == 6

    df_desagregado_1 = df_procesado[df_procesado["OTRA_COLUMNA"] == "A"]
    assert len(df_desagregado_1) == 3

    assert all(df_desagregado_1[processing.columns_dinero[0]] == 1000.0)

    assert all(df_desagregado_1[processing.column_desagregacion] == 1)

    expected_dates_1 = [
        pd.Timestamp("2025-01-01"),
        pd.Timestamp("2025-01-11"),
        pd.Timestamp("2025-01-21"),
    ]
    assert df_desagregado_1[processing.column_fecha].tolist() == expected_dates_1

    df_desagregado_2 = df_procesado[df_procesado["OTRA_COLUMNA"] == "D"]
    assert len(df_desagregado_2) == 1

    assert all(df_desagregado_2[processing.columns_dinero[0]] == 1500.0)

    assert all(df_desagregado_2[processing.column_desagregacion] == 1)

    expected_dates_2 = [pd.Timestamp("2025-04-01")]
    assert df_desagregado_2[processing.column_fecha].tolist() == expected_dates_2

    assert len(df_resto) == 2
    assert (
        "CONSULTA CON CANTIDAD ALTA"
        in df_resto[processing.column_descripcion_cups].values
    )
    assert "OTRO PROCEDIMIENTO" in df_resto[processing.column_descripcion_cups].values
