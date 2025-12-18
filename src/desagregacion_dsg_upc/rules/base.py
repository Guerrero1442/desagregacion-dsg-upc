from abc import ABC, abstractmethod

import pandas as pd

from desagregacion_dsg_upc import settings


class ReglaDesagregacion(ABC):
    @abstractmethod
    def identificar(self, df: pd.DataFrame) -> pd.Series:
        pass

    @abstractmethod
    def _calcular_parametros(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

    def _desagregar(
        self,
        df: pd.DataFrame,
        column_desagregar: str,
        columns_dinero: list[str],
        column_fecha: str,
    ):
        df_expanded = df.loc[df.index.repeat(df[column_desagregar])].copy()

        df_expanded["secuencia"] = df_expanded.groupby(level=0).cumcount()

        for col in columns_dinero:
            df_expanded[col] = (df_expanded[col] / df_expanded["divisor_costo"]).round(
                1
            )

        dias_a_sumar = pd.to_timedelta(
            df_expanded["secuencia"] * df_expanded["intervalo_dias"], unit="D"
        )

        df_expanded[column_fecha] = df_expanded[column_fecha] + dias_a_sumar

        df_expanded[settings.processing.column_desagregacion] = df_expanded[
            "cantidad"
        ].astype(int)

        return df_expanded

    def ejecutar_desagregacion(self, df: pd.DataFrame):
        mask = self.identificar(df)

        df_subset = pd.DataFrame(df[mask].copy())

        if df_subset.empty:
            return df

        df_params = self._calcular_parametros(df_subset)
        df_final = self._desagregar(
            df_params,
            settings.processing.column_desagregacion,
            settings.processing.columns_dinero,
            settings.processing.column_fecha,
        )

        return df_final
