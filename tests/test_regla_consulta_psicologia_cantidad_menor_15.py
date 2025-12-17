from datetime import datetime

import pandas as pd
import pytest

from desagregacion_dsg_upc.rules.consulta_psicologia_cantidad_menor_15 import (
    ReglaConsultaPsicologiaCantidadMenor15,
)


# --- Mock de Settings ---
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
        "desagregacion_dsg_upc.rules.consulta_psicologia_cantidad_menor_15.settings",
        mocked_settings,
    )
    monkeypatch.setattr("desagregacion_dsg_upc.rules.base.settings", mocked_settings)
    return mocked_settings


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """DataFrame de ejemplo para los tests de psicología."""
    data = {
        "DESCRIPCION_CUP": [
            "CONSULTA DE PSICOLOGIA CLINICA",  # Cumple: CONSULTA + PSICOLOGIA + <15
            "CONSULTA PSICOLOGIA CONTROL",  # Cumple: CONSULTA + PSICOLOGIA + <15
            "CONSULTA MEDICINA GENERAL",  # No Cumple: Falta PSICOLOGIA
            "TERAPIA FISICA",  # No Cumple: Falta CONSULTA y PSICOLOGIA
            "CONSULTA PSICOLOGIA GRUPAL",  # No Cumple: Cantidad 15 (debe ser < 15)
        ],
        "CANTIDAD_PROCEDIMIENTO": [
            5,
            14,
            5,
            10,
            15,
        ],
        "VALOR_NETO": [
            5000.0,
            14000.0,
            5000.0,
            2000.0,
            15000.0,
        ],
        "FECHA_INICIO_TRATAMIENTO": [
            datetime(2025, 1, 1),
            datetime(2025, 2, 1),
            datetime(2025, 3, 1),
            datetime(2025, 4, 1),
            datetime(2025, 5, 1),
        ],
        "OTRA_COLUMNA": ["A", "B", "C", "D", "E"],
    }
    return pd.DataFrame(data)


def test_identificar_registros_correctos(settings_mock, sample_df):
    """Verifica que la regla identifique solo las consultas de psicología con cantidad < 15."""
    rule = ReglaConsultaPsicologiaCantidadMenor15()
    mask = rule.identificar(sample_df)

    # Esperamos True solo para los registros 0 y 1
    expected_mask = pd.Series(
        [True, True, False, False, False], name="CANTIDAD_PROCEDIMIENTO"
    )

    pd.testing.assert_series_equal(mask, expected_mask, check_names=False)
    assert mask.sum() == 2


def test_desagregacion_completa_psicologia(settings_mock, sample_df):
    """
    Test de punta a punta que ejecuta la desagregación de psicología y valida el resultado.
    Verifica que el intervalo sea de 1 día.
    """
    rule = ReglaConsultaPsicologiaCantidadMenor15()

    mask_a_procesar = rule.identificar(sample_df)
    df_a_procesar = sample_df[mask_a_procesar].copy()

    df_procesado = rule.ejecutar_desagregacion(df_a_procesar)

    # --- Verificación Caso A (Cantidad 5) ---
    df_desagregado_a = df_procesado[df_procesado["OTRA_COLUMNA"] == "A"]
    assert len(df_desagregado_a) == 5
    # Validar valores monetarios (5000 / 5 = 1000)
    assert all(df_desagregado_a["VALOR_NETO"] == 1000.0)
    # Validar cantidad unitaria
    assert all(df_desagregado_a["CANTIDAD_PROCEDIMIENTO"] == 1)

    # Validar fechas (Intervalo de 1 día)
    expected_dates_a = [
        pd.Timestamp("2025-01-01"),
        pd.Timestamp("2025-01-02"),
        pd.Timestamp("2025-01-03"),
        pd.Timestamp("2025-01-04"),
        pd.Timestamp("2025-01-05"),
    ]
    assert df_desagregado_a["FECHA_INICIO_TRATAMIENTO"].tolist() == expected_dates_a

    # --- Verificación Caso B (Cantidad 14) ---
    df_desagregado_b = df_procesado[df_procesado["OTRA_COLUMNA"] == "B"]
    assert len(df_desagregado_b) == 14

    # Validar valores monetarios (14000 / 14 = 1000)
    assert all(df_desagregado_b["VALOR_NETO"] == 1000.0)

    # Validar las primeras fechas para asegurar el intervalo
    fechas_b = df_desagregado_b["FECHA_INICIO_TRATAMIENTO"].tolist()
    assert fechas_b[0] == pd.Timestamp("2025-02-01")
    assert fechas_b[1] == pd.Timestamp("2025-02-02")
    assert fechas_b[-1] == pd.Timestamp("2025-02-14")
