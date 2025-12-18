import pandas as pd

from desagregacion_dsg_upc import settings

from .base import ReglaDesagregacion


class ReglaDescripcionTerapiaFiltroCodigos(ReglaDesagregacion):
    """
    Aplica a: Descripción que contengan terapia o que los codigos sean cualquiera de estos
    (999301, 1003524, 991800)
    """

    def identificar(self, df: pd.DataFrame) -> pd.Series:
        mask_terapia = (
            df[settings.processing.column_descripcion_cups]
            .astype(str)
            .str.contains("TERAPIA", case=False, na=False)
        )

        mask_codigo = df[settings.processing.column_codigo_osi].isin(
            [999301, 1003524, 991800]
        )

        return mask_terapia | mask_codigo

    def _calcular_parametros(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["intervalo_dias"] = 1

        df["divisor_costo"] = df[settings.processing.column_desagregacion]

        df["cantidad"] = 1

        return df
