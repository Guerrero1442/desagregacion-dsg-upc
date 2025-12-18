import pandas as pd

from desagregacion_dsg_upc import settings

from .base import ReglaDesagregacion


class ReglaDescripcionCuraci(ReglaDesagregacion):
    """
    Aplica a: Descripción que contengan curaci
    """

    def identificar(self, df: pd.DataFrame) -> pd.Series:
        mask_curaci = (
            df[settings.processing.column_descripcion_cups]
            .astype(str)
            .str.contains("CURACI", case=False, na=False)
        )

        return mask_curaci

    def _calcular_parametros(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["intervalo_dias"] = 1

        df["divisor_costo"] = df[settings.processing.column_desagregacion]

        df["cantidad"] = 1

        return df
