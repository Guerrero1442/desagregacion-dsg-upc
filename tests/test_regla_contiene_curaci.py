from datetime import datetime
import pandas as pd
import pytest
from desagregacion_dsg_upc.rules.contiene_curaci import ReglaDescripcionCuraci

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """DataFrame de ejemplo para los tests de reglas que contienen 'CURACI'."""
    data = {
        "DESCRIPCION_CUP": [
            "CURACION DE HERIDA",  # Cumple: Contiene CURACI
            "CONSULTA MEDICA GENERAL",  # No Cumple
            "PROCEDIMIENTO DE CURACION",  # Cumple
            "SERVICIO DE URGENCIAS",  # No Cumple
            "MATERIAL DE CURACION",  # Cumple
        ],
        "CANTIDAD_PROCEDIMIENTO": [
            3,
            1,
            5,
            1,
            2,
        ],
        "VALOR_NETO": [
            3000.0,
            1500.0,
            5000.0,
            2000.0,
            2000.0,
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
    """Verifica que la regla identifique solo las descripciones que contienen CURACI."""
    rule = ReglaDescripcionCuraci()
    mask = rule.identificar(sample_df)

    # Esperamos True para registros 0, 2 y 4
    expected_mask = pd.Series(
        [True, False, True, False, True],
        name=settings_mock.processing.column_desagregacion,
    )

    pd.testing.assert_series_equal(mask, expected_mask, check_names=False)
    assert mask.sum() == 3

def test_desagregacion_completa_curaci(settings_mock, sample_df):
    """
    Test de punta a punta que ejecuta la desagregación de registros CURACI y valida el resultado.
    Debe separar 1 a 1 segun la cantidad.
    """
    rule = ReglaDescripcionCuraci()

    mask_a_procesar = rule.identificar(sample_df)
    df_a_procesar = sample_df[mask_a_procesar].copy()
    df_resto = sample_df[~mask_a_procesar].copy()

    df_procesado = rule.ejecutar_desagregacion(df_a_procesar)

    df_final = pd.concat([df_resto, df_procesado])

    # Original rows: 5
    # Row 0 (A): Quantity 3. Expands to 3 rows.
    # Row 2 (C): Quantity 5. Expands to 5 rows.
    # Row 4 (E): Quantity 2. Expands to 2 rows.
    # Resto (B, D): 2 rows.
    # Total = 2 + 3 + 5 + 2 = 12.
    assert len(df_final) == 12

    # Check case A (Quantity 3)
    df_desagregado_a = df_procesado[df_procesado["OTRA_COLUMNA"] == "A"]
    assert len(df_desagregado_a) == 3
    
    # Logic:
    # divisor_costo = original quantity = 3.
    # VALOR_NETO = 3000 / 3 = 1000.0
    assert all(df_desagregado_a["VALOR_NETO"] == 1000.0)
    
    # Cantidad becomes 1
    assert all(df_desagregado_a["CANTIDAD_PROCEDIMIENTO"] == 1)

    # Check dates increment (interval 1 day)
    expected_dates_a = [pd.Timestamp("2025-01-01") + pd.Timedelta(days=i) for i in range(3)]
    assert df_desagregado_a["FECHA_INICIO_TRATAMIENTO"].tolist() == expected_dates_a

    # Check case C (Quantity 5)
    df_desagregado_c = df_procesado[df_procesado["OTRA_COLUMNA"] == "C"]
    assert len(df_desagregado_c) == 5
    
    # VALOR_NETO = 5000 / 5 = 1000.0
    assert all(df_desagregado_c["VALOR_NETO"] == 1000.0)
    
    # Cantidad = 1
    assert all(df_desagregado_c["CANTIDAD_PROCEDIMIENTO"] == 1)

    # Check dates increment
    expected_dates_c = [pd.Timestamp("2025-03-01") + pd.Timedelta(days=i) for i in range(5)]
    assert df_desagregado_c["FECHA_INICIO_TRATAMIENTO"].tolist() == expected_dates_c
