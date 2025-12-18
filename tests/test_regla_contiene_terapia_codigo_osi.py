from datetime import datetime
import pandas as pd
import pytest
from desagregacion_dsg_upc.rules.contiene_terapia_codigo_osi import ReglaDescripcionTerapiaFiltroCodigos

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """DataFrame de ejemplo para los tests de reglas que contienen 'TERAPIA' o códigos específicos."""
    data = {
        "DESCRIPCION_CUP": [
            "TERAPIA FISICA",  # Cumple: Contiene TERAPIA
            "CONSULTA MEDICA GENERAL",  # No Cumple
            "SESION DE TERAPIA OCUPACIONAL",  # Cumple: Contiene TERAPIA
            "PROCEDIMIENTO ESPECIAL",  # No cumple por descripción, pero veremos el código
            "OTRO SERVICIO",  # No cumple
        ],
        "CODIGO_OSI": [
            12345,
            67890,
            11111,
            999301,  # Cumple: Código en lista
            1003524, # Cumple: Código en lista
        ],
        "CANTIDAD_PROCEDIMIENTO": [
            2,
            1,
            3,
            4,
            1,
        ],
        "VALOR_NETO": [
            2000.0,
            1500.0,
            3000.0,
            4000.0,
            1000.0,
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
    """Verifica que la regla identifique registros por descripción 'TERAPIA' o por códigos OSI."""
    rule = ReglaDescripcionTerapiaFiltroCodigos()
    mask = rule.identificar(sample_df)

    # Esperamos True para:
    # 0 (TERAPIA)
    # 2 (TERAPIA)
    # 3 (Código 999301)
    # 4 (Código 1003524)
    expected_mask = pd.Series(
        [True, False, True, True, True],
        name=settings_mock.processing.column_desagregacion,
    )

    pd.testing.assert_series_equal(mask, expected_mask, check_names=False)
    assert mask.sum() == 4

def test_desagregacion_completa_terapia_codigos(settings_mock, sample_df):
    """
    Test de punta a punta que ejecuta la desagregación y valida el resultado.
    """
    rule = ReglaDescripcionTerapiaFiltroCodigos()

    mask_a_procesar = rule.identificar(sample_df)
    df_a_procesar = sample_df[mask_a_procesar].copy()
    df_resto = sample_df[~mask_a_procesar].copy()

    df_procesado = rule.ejecutar_desagregacion(df_a_procesar)

    df_final = pd.concat([df_resto, df_procesado])

    # Original rows: 5
    # Row 0 (A): Qty 2 -> 2 rows
    # Row 1 (B): Resto -> 1 row
    # Row 2 (C): Qty 3 -> 3 rows
    # Row 3 (D): Qty 4 -> 4 rows
    # Row 4 (E): Qty 1 -> 1 row (aunque se procesa, Qty 1 no expande pero se recalcula)
    # Total = 1 + 2 + 3 + 4 + 1 = 11.
    assert len(df_final) == 11

    # Check case A (Quantity 2)
    df_desagregado_a = df_procesado[df_procesado["OTRA_COLUMNA"] == "A"]
    assert len(df_desagregado_a) == 2
    assert all(df_desagregado_a["VALOR_NETO"] == 1000.0)
    assert all(df_desagregado_a["CANTIDAD_PROCEDIMIENTO"] == 1)
    
    expected_dates_a = [pd.Timestamp("2025-01-01") + pd.Timedelta(days=i) for i in range(2)]
    assert df_desagregado_a["FECHA_INICIO_TRATAMIENTO"].tolist() == expected_dates_a

    # Check case D (Código OSI 999301, Qty 4)
    df_desagregado_d = df_procesado[df_procesado["OTRA_COLUMNA"] == "D"]
    assert len(df_desagregado_d) == 4
    assert all(df_desagregado_d["VALOR_NETO"] == 1000.0)
    assert all(df_desagregado_d["CANTIDAD_PROCEDIMIENTO"] == 1)

    expected_dates_d = [pd.Timestamp("2025-04-01") + pd.Timedelta(days=i) for i in range(4)]
    assert df_desagregado_d["FECHA_INICIO_TRATAMIENTO"].tolist() == expected_dates_d
