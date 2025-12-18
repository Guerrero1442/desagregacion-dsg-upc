import pandas as pd

from desagregacion_dsg_upc import settings

from .base import ReglaDesagregacion


class ReglaConsultaPsicologiaCantidadMayor15(ReglaDesagregacion):
    """
    Aplica a: Consultas de Psicología con cantidad procedimiento > 15
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

        mask_cantidad = df[settings.processing.column_desagregacion] > 15

        return mask_consulta & mask_psicologia & mask_cantidad

    def _calcular_parametros(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["intervalo_dias"] = 1

        df["cantidad_modificada"] = round(
            df[settings.processing.column_desagregacion] / 8, 0
        )

        df["divisor_costo"] = df["cantidad_modificada"]

        df["divisor_valor_liquidado"] = df[settings.processing.column_desagregacion]

        df["cantidad"] = (
            df[settings.processing.column_desagregacion] / df["cantidad_modificada"]
        )

        return df

    def _desagregar(
        self,
        df: pd.DataFrame,
        column_desagregar: str,
        columns_dinero: list[str],
        column_fecha: str,
    ):
        columna_valor_liquidado = settings.processing.column_valor_liquidado

        cols_dinero_standar = [
            c for c in columns_dinero if c != columna_valor_liquidado
        ]

        df_resultado = super()._desagregar(
            df, "cantidad_modificada", cols_dinero_standar, column_fecha
        )

        if columna_valor_liquidado in df.columns:
            df_resultado[columna_valor_liquidado] = (
                df_resultado[columna_valor_liquidado]
                / df_resultado["divisor_valor_liquidado"]
            ).round(1)
        return df_resultado
