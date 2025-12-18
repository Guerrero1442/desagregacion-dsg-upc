import pandas as pd

from desagregacion_dsg_upc import settings

from .base import ReglaDesagregacion


class ReglaConsultaCantidadMenor(ReglaDesagregacion):
    """
    Aplica a: Consultas con cantidad procedimiento <= 6
    Logica Fecha: Se espacian cada (30 / cantidad procedimiento) dias.
    """

    def identificar(self, df: pd.DataFrame) -> pd.Series:
        mask_consulta = (
            df[settings.processing.column_descripcion_cups]
            .astype(str)
            .str.contains("CONSULTA", case=False, na=False)
        )

        mask_cantidad = df[settings.processing.column_desagregacion] <= 6

        return mask_consulta & mask_cantidad

    def _calcular_parametros(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["intervalo_dias"] = round(
            30 / df[settings.processing.column_desagregacion], 0
        )

        df["divisor_costo"] = df[settings.processing.column_desagregacion]

        df["cantidad"] = 1

        return df
