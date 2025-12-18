import pandas as pd

from desagregacion_dsg_upc import settings

from .base import ReglaDesagregacion


class ReglaConsultaPsicologiaCantidadMenor15(ReglaDesagregacion):
    """
    Aplica a: Consultas de Psicología con cantidad procedimiento <= 15
    Logica Fecha: Se suma 1 dia por cada procedimiento
    """

    def identificar(self, df: pd.DataFrame) -> pd.Series:
        mask_consulta = (
            df[settings.processing.column_descripcion_cups]
            .astype(str)
            .str.contains("CONSULTA", case=False, na=False)
        )

        mask_psicologia = (
            df[settings.processing.column_descripcion_cups]
            .astype(str)
            .str.contains("PSICOLOGIA", case=False, na=False)
        )

        mask_cantidad = df[settings.processing.column_desagregacion] <= 15

        return mask_consulta & mask_psicologia & mask_cantidad

    def _calcular_parametros(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["intervalo_dias"] = 1

        df["divisor_costo"] = df[settings.processing.column_desagregacion]

        df["cantidad"] = 1

        return df
