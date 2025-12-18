from datetime import datetime

import pandas as pd
import pytest

from desagregacion_dsg_upc.rules.consulta_psicologia_cantidad_mayor_15 import (
    ReglaConsultaPsicologiaCantidadMayor15,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """DataFrame de ejemplo para los tests de psicología mayor a 15."""
    data = {
        "DESCRIPCION_CUP": [
            "CONSULTA DE PSICOLOGIA CLINICA",  # Cumple: CONSULTA + PSICOLOGIA + >15
            "CONSULTA PSICOLOGIA CONTROL",  # No Cumple: Cantidad <= 15
            "CONSULTA MEDICINA GENERAL",  # No Cumple: Falta PSICOLOGIA
            "TERAPIA FISICA",  # No Cumple: Falta CONSULTA y PSICOLOGIA
            "CONSULTA PSICOLOGIA GRUPAL",  # Cumple: CONSULTA + PSICOLOGIA + >15
        ],
        "CANTIDAD_PROCEDIMIENTO": [
            16,
            15,
            16,
            10,
            24,
        ],
        "VALOR_NETO": [
            1600.0,
            15000.0,
            16000.0,
            2000.0,
            2400.0,
        ],
        "FECHA_INICIO_TRATAMIENTO": [
            datetime(2025, 1, 1),
            datetime(2025, 2, 1),
            datetime(2025, 3, 1),
            datetime(2025, 4, 1),
            datetime(2025, 5, 1),
        ],
        "VALOR_LIQUIDADO": [  # Adding this as it's handled specifically in _desagregar
            1600.0,
            15000.0,
            16000.0,
            2000.0,
            2400.0,
        ],
        "OTRA_COLUMNA": ["A", "B", "C", "D", "E"],
    }
    return pd.DataFrame(data)


def test_identificar_registros_correctos(settings_mock, sample_df):
    """Verifica que la regla identifique solo las consultas de psicología con cantidad > 15."""
    rule = ReglaConsultaPsicologiaCantidadMayor15()
    mask = rule.identificar(sample_df)

    # Esperamos True para registros 0 (16) y 4 (24)
    # Registro 1 es 15 (False)
    # Registro 2 no es psicologia (False)
    # Registro 3 no es consulta/psicologia (False)
    expected_mask = pd.Series(
        [True, False, False, False, True],
        name=settings_mock.processing.column_desagregacion,
    )

    pd.testing.assert_series_equal(mask, expected_mask, check_names=False)
    assert mask.sum() == 2


def test_desagregacion_completa_psicologia_mayor_15(settings_mock, sample_df):
    """
    Test de punta a punta que ejecuta la desagregación de psicología > 15 y valida el resultado.
    """
    rule = ReglaConsultaPsicologiaCantidadMayor15()

    mask_a_procesar = rule.identificar(sample_df)
    df_a_procesar = sample_df[mask_a_procesar].copy()
    df_resto = sample_df[~mask_a_procesar].copy()

    df_procesado = rule.ejecutar_desagregacion(df_a_procesar)

    df_final = pd.concat([df_resto, df_procesado])

    # Original rows: 5
    # Row 0 (A): Quantity 16. 16 / 8 = 2 rows.
    # Row 4 (E): Quantity 24. 24 / 8 = 3 rows.
    # Resto: 3 rows.
    # Total = 3 + 2 + 3 = 8.
    assert len(df_final) == 8

    # Check case A (Quantity 16)
    df_desagregado_a = df_procesado[df_procesado["OTRA_COLUMNA"] == "A"]
    assert len(df_desagregado_a) == 2

    # Check Logic:
    # cantidad_modificada = round(16/8, 0) = 2.0
    # divisor_costo = 2.0
    # VALOR_NETO = 1600 / 2.0 = 800.0
    assert all(df_desagregado_a["VALOR_NETO"] == 800.0)
    assert all(df_desagregado_a[settings_mock.processing.column_desagregacion] == 8)

    # VALOR_LIQUIDADO logic:
    # value = value / divisor_valor_liquidado (original 16)
    # 1600 / 16 = 100.
    assert all(
        df_desagregado_a[settings_mock.processing.column_valor_liquidado] == 100.0
    )

    # Check dates increment (interval 1 day)
    expected_dates_a = [
        pd.Timestamp("2025-01-01") + pd.Timedelta(days=i) for i in range(2)
    ]
    assert (
        df_desagregado_a[settings_mock.processing.column_fecha].tolist()
        == expected_dates_a
    )

    # Check case E (Quantity 24)
    df_desagregado_e = df_procesado[df_procesado["OTRA_COLUMNA"] == "E"]
    assert len(df_desagregado_e) == 3

    # cantidad_modificada = round(24/8, 0) = 3.0
    # divisor_costo = 3.0
    # VALOR_NETO = 2400 / 3.0 = 800.0
    assert all(df_desagregado_e["VALOR_NETO"] == 800.0)

    # Cantidad Procedure becomes 3.0
    assert all(df_desagregado_e[settings_mock.processing.column_desagregacion] == 8)

    # VALOR_LIQUIDADO = 2400 / 24 = 100.
    assert all(
        df_desagregado_e[settings_mock.processing.column_valor_liquidado] == 100.0
    )
