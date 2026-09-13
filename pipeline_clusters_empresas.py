"""ETL, segmentación K-means y exportables para Power BI.

Ejemplo:
    python pipeline_clusters_empresas.py \
        --input "10.000_Empresas_mas_Grandes_del_País_20260913.csv"

El script conserva todas las filas del año más reciente en el dataset final.
Las filas sin datos financieros suficientes quedan con Cluster_ID vacío y
Cluster_Nombre = "Sin datos financieros"; no se fuerzan a un clúster artificial.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import RobustScaler


RANDOM_STATE = 42
MONETARY_COLUMNS = [
    "INGRESOS OPERACIONALES",
    "GANANCIA (PÉRDIDA)",
    "TOTAL ACTIVOS",
    "TOTAL PASIVOS",
    "TOTAL PATRIMONIO",
]
YEAR_COLUMN = "Año de Corte"
MODEL_COLUMNS = ["Log_Ingresos", "Margen_Neto", "Nivel_Endeudamiento"]


def limpiar_numero(valor: object) -> float:
    """Convierte valores monetarios/numéricos colombianos a float.

    Admite, entre otros, "$144.82", "$1,234.56", "$1.234,56", "(12.5)"
    y valores vacíos. No debe usarse para identificadores que deban conservar
    ceros iniciales.
    """
    if pd.isna(valor):
        return np.nan

    texto = str(valor).strip()
    if not texto or texto.lower() in {"nan", "none", "null", "-", "—"}:
        return np.nan

    negativo = texto.startswith("(") and texto.endswith(")")
    texto = texto.replace("(", "").replace(")", "")
    texto = re.sub(r"[^0-9,.-]", "", texto)
    if not texto or texto in {"-", ".", ","}:
        return np.nan

    # Si aparecen ambos separadores, el último se interpreta como decimal.
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        partes = texto.split(",")
        if len(partes[-1]) in (1, 2):
            texto = "".join(partes[:-1]) + "." + partes[-1]
        else:
            texto = "".join(partes)
    # Un punto único se conserva como decimal: el archivo fuente usa $144.82.
    elif texto.count(".") > 1:
        partes = texto.split(".")
        texto = "".join(partes[:-1]) + "." + partes[-1]

    try:
        numero = float(texto)
    except ValueError:
        return np.nan
    return -numero if negativo else numero


def cargar_y_limpiar(input_path: Path) -> pd.DataFrame:
    """Carga el CSV, convierte finanzas y conserva el periodo más reciente."""
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")

    try:
        df = pd.read_csv(input_path, encoding="utf-8-sig", dtype=str)
    except UnicodeDecodeError as exc:
        raise ValueError(
            "El CSV no está en UTF-8. Revise la codificación antes de continuar."
        ) from exc

    requeridas = set(MONETARY_COLUMNS + [YEAR_COLUMN])
    faltantes = sorted(requeridas.difference(df.columns))
    if faltantes:
        raise ValueError(
            "Faltan columnas obligatorias: " + ", ".join(faltantes)
        )

    for columna in MONETARY_COLUMNS:
        df[columna] = df[columna].map(limpiar_numero)

    df[YEAR_COLUMN] = df[YEAR_COLUMN].map(limpiar_numero).round().astype("Int64")
    anios_validos = df[YEAR_COLUMN].dropna()
    if anios_validos.empty:
        raise ValueError(f"La columna '{YEAR_COLUMN}' no contiene años válidos.")

    anio_reciente = int(anios_validos.max())
    df = df.loc[df[YEAR_COLUMN].eq(anio_reciente)].copy()
    if df.empty:
        raise ValueError("No hay registros para el año más reciente disponible.")

    ingresos = df["INGRESOS OPERACIONALES"]
    activos = df["TOTAL ACTIVOS"]
    df["Margen_Neto"] = df["GANANCIA (PÉRDIDA)"].div(ingresos.where(ingresos.ne(0)))
    df["Nivel_Endeudamiento"] = df["TOTAL PASIVOS"].div(activos.where(activos.ne(0)))
    # Logaritmo solo para modelar escala; se conserva el ingreso original.
    df["Log_Ingresos"] = np.log1p(ingresos.clip(lower=0))
    return df


def obtener_datos_modelo(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve el subconjunto modelable y sus variables continuas."""
    mascara = df[MODEL_COLUMNS].replace([np.inf, -np.inf], np.nan).notna().all(axis=1)
    model_df = df.loc[mascara].copy()
    if len(model_df) < 3:
        raise ValueError(
            "Se necesitan al menos 3 empresas con ingresos, activos y ratios válidos."
        )
    return model_df, model_df[MODEL_COLUMNS].astype(float)


def evaluar_k(
    features: pd.DataFrame,
    min_k: int = 2,
    max_k: int = 10,
    silhouette_sample_size: int = 5_000,
) -> tuple[pd.DataFrame, int, np.ndarray]:
    """Calcula WCSS y Silhouette para cada K y escoge el mayor Silhouette."""
    if min_k < 2:
        raise ValueError("min_k debe ser como mínimo 2.")

    escalador = RobustScaler()
    X = escalador.fit_transform(features)
    max_k_real = min(max_k, len(features) - 1)
    if max_k_real < min_k:
        raise ValueError("No hay suficientes observaciones para evaluar el rango de K.")

    filas: list[dict[str, float | int]] = []
    for k in range(min_k, max_k_real + 1):
        modelo = KMeans(
            n_clusters=k,
            init="k-means++",
            random_state=RANDOM_STATE,
            n_init=10,
        )
        etiquetas = modelo.fit_predict(X)
        muestra = min(silhouette_sample_size, len(features))
        silueta = silhouette_score(
            X,
            etiquetas,
            sample_size=muestra if muestra < len(features) else None,
            random_state=RANDOM_STATE,
        )
        filas.append({"K": k, "WCSS": float(modelo.inertia_), "Silhouette_Score": float(silueta)})

    evaluacion = pd.DataFrame(filas)
    # Distancia a la recta entre el primer y el último punto de WCSS. Es un
    # diagnóstico reproducible del codo sin añadir una dependencia externa.
    x = np.linspace(0.0, 1.0, len(evaluacion))
    y = (evaluacion["WCSS"] - evaluacion["WCSS"].min()) / (
        evaluacion["WCSS"].max() - evaluacion["WCSS"].min()
    )
    if np.isclose(y.max(), y.min()):
        evaluacion["Codo_Distancia"] = 0.0
    else:
        # Distancia vertical a la línea normalizada que une ambos extremos.
        linea = y.iloc[0] + (y.iloc[-1] - y.iloc[0]) * x
        evaluacion["Codo_Distancia"] = linea - y.to_numpy()
    k_codo = int(evaluacion.loc[evaluacion["Codo_Distancia"].idxmax(), "K"])
    evaluacion["Es_Codo"] = evaluacion["K"].eq(k_codo)
    k_optimo = int(evaluacion.loc[evaluacion["Silhouette_Score"].idxmax(), "K"])
    return evaluacion, k_optimo, X


def guardar_graficas(
    evaluacion: pd.DataFrame,
    X: np.ndarray,
    etiquetas: np.ndarray,
    output_dir: Path,
) -> None:
    """Guarda diagnóstico del codo, silueta y proyección 2D de los clústeres."""
    sns.set_theme(style="whitegrid", context="notebook")
    figura, ejes = plt.subplots(1, 2, figsize=(14, 5))
    ejes[0].plot(evaluacion["K"], evaluacion["WCSS"], marker="o", linewidth=2)
    ejes[0].set(title="Método del codo", xlabel="Número de clústeres (K)", ylabel="WCSS / Inercia")
    ejes[1].plot(
        evaluacion["K"], evaluacion["Silhouette_Score"], marker="o", color="#e67e22", linewidth=2
    )
    ejes[1].set(title="Coeficiente de Silhouette", xlabel="Número de clústeres (K)", ylabel="Silhouette Score")
    figura.tight_layout()
    figura.savefig(output_dir / "grafica_codo_kmeans.png", dpi=300, bbox_inches="tight")
    plt.close(figura)

    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    proyeccion = pca.fit_transform(X)
    figura, eje = plt.subplots(figsize=(10, 7))
    dispersion = eje.scatter(
        proyeccion[:, 0], proyeccion[:, 1], c=etiquetas, cmap="tab10", alpha=0.65, s=18
    )
    eje.set_title("Proyección PCA de empresas por clúster")
    eje.set_xlabel(f"Componente 1 ({pca.explained_variance_ratio_[0]:.1%} varianza)")
    eje.set_ylabel(f"Componente 2 ({pca.explained_variance_ratio_[1]:.1%} varianza)")
    figura.colorbar(dispersion, ax=eje, label="Cluster_ID")
    figura.tight_layout()
    figura.savefig(output_dir / "dispersion_clusters_kmeans.png", dpi=300, bbox_inches="tight")
    plt.close(figura)


def nombres_de_negocio(
    model_df: pd.DataFrame,
    etiquetas: np.ndarray,
) -> dict[int, str]:
    """Bautiza segmentos según escala, rentabilidad y endeudamiento relativos."""
    perfiles = model_df.assign(Cluster_ID=etiquetas).groupby("Cluster_ID").agg(
        Ingresos_Medios=("INGRESOS OPERACIONALES", "mean"),
        Margen_Medio=("Margen_Neto", "mean"),
        Endeudamiento_Medio=("Nivel_Endeudamiento", "mean"),
    )
    mediana_ingresos = perfiles["Ingresos_Medios"].median()
    resultado: dict[int, str] = {}
    usados: dict[str, int] = {}

    for cluster_id, perfil in perfiles.sort_values("Ingresos_Medios", ascending=False).iterrows():
        escala_alta = perfil["Ingresos_Medios"] >= mediana_ingresos
        # Umbrales de negocio explícitos: evitan llamar "en riesgo" a un
        # clúster solo porque otro contiene valores extremos de rentabilidad.
        margen_negativo = perfil["Margen_Medio"] < 0
        rentable = perfil["Margen_Medio"] >= 0.05
        endeudada = perfil["Endeudamiento_Medio"] >= 0.70

        if margen_negativo and endeudada:
            nombre = "En Riesgo Financiero"
        elif margen_negativo:
            nombre = "Baja Rentabilidad"
        elif rentable and not endeudada and escala_alta:
            nombre = "Líderes Rentables"
        elif rentable and endeudada:
            nombre = "Rentables Apalancadas"
        elif rentable:
            nombre = "Especialistas Sólidas"
        elif endeudada:
            nombre = "En Riesgo Financiero"
        elif escala_alta:
            nombre = "Grandes en Transición"
        else:
            nombre = "Base Operativa"

        usados[nombre] = usados.get(nombre, 0) + 1
        repeticion = usados[nombre]
        resultado[int(cluster_id)] = nombre if repeticion == 1 else f"{nombre} {repeticion}"
    return resultado


def construir_resumen(df: pd.DataFrame) -> pd.DataFrame:
    """Construye la tabla ancha de KPIs por clúster para Power BI."""
    agrupado = df.groupby(["Cluster_ID", "Cluster_Nombre"], observed=True, dropna=False)
    resumen = agrupado.agg(
        Empresas=("Cluster_ID", "size"),
        Ingresos_Totales=("INGRESOS OPERACIONALES", "sum"),
        Ingresos_Promedio=("INGRESOS OPERACIONALES", "mean"),
        Ingresos_Mediana=("INGRESOS OPERACIONALES", "median"),
        Ganancia_Total=("GANANCIA (PÉRDIDA)", "sum"),
        Ganancia_Promedio=("GANANCIA (PÉRDIDA)", "mean"),
        Activos_Totales=("TOTAL ACTIVOS", "sum"),
        Pasivos_Totales=("TOTAL PASIVOS", "sum"),
        Patrimonio_Total=("TOTAL PATRIMONIO", "sum"),
        Margen_Neto_Promedio=("Margen_Neto", "mean"),
        Margen_Neto_Mediana=("Margen_Neto", "median"),
        Nivel_Endeudamiento_Promedio=("Nivel_Endeudamiento", "mean"),
        Nivel_Endeudamiento_Mediana=("Nivel_Endeudamiento", "median"),
    ).reset_index()
    resumen["Margen_Neto_Ponderado"] = resumen["Ganancia_Total"].div(
        resumen["Ingresos_Totales"].where(resumen["Ingresos_Totales"].ne(0))
    )
    resumen["Nivel_Endeudamiento_Ponderado"] = resumen["Pasivos_Totales"].div(
        resumen["Activos_Totales"].where(resumen["Activos_Totales"].ne(0))
    )
    resumen["Distribucion_Pct"] = resumen["Empresas"] / resumen["Empresas"].sum()
    return resumen.sort_values("Cluster_ID", na_position="last")


def ejecutar(input_path: Path, output_dir: Path, min_k: int, max_k: int) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = cargar_y_limpiar(input_path)
    model_df, variables = obtener_datos_modelo(df)
    evaluacion, k_optimo, X = evaluar_k(variables, min_k=min_k, max_k=max_k)

    escalador = RobustScaler()
    X_final = escalador.fit_transform(variables)
    modelo_final = KMeans(
        n_clusters=k_optimo,
        init="k-means++",
        random_state=RANDOM_STATE,
        n_init=10,
    )
    etiquetas = modelo_final.fit_predict(X_final)
    nombres = nombres_de_negocio(model_df, etiquetas)

    df["Cluster_ID"] = pd.Series(pd.array([pd.NA] * len(df), dtype="Int64"), index=df.index)
    df["Cluster_Nombre"] = "Sin datos financieros"
    df.loc[model_df.index, "Cluster_ID"] = etiquetas
    df.loc[model_df.index, "Cluster_Nombre"] = pd.Series(etiquetas, index=model_df.index).map(nombres)

    resumen = construir_resumen(df.loc[model_df.index].copy())
    evaluacion.to_csv(output_dir / "evaluacion_kmeans.csv", index=False, encoding="utf-8-sig")
    df.to_csv(output_dir / "dataset_empresas_clusters_powerbi.csv", index=False, encoding="utf-8-sig")
    resumen.to_csv(output_dir / "perfil_kpis_clusters.csv", index=False, encoding="utf-8-sig")
    guardar_graficas(evaluacion, X_final, etiquetas, output_dir)

    return {
        "anio": int(df[YEAR_COLUMN].max()),
        "filas_periodo": len(df),
        "filas_modeladas": len(model_df),
        "k_optimo": k_optimo,
        "k_codo": int(evaluacion.loc[evaluacion["Es_Codo"], "K"].iloc[0]),
        "silhouette_optimo": float(
            evaluacion.loc[evaluacion["K"].eq(k_optimo), "Silhouette_Score"].iloc[0]
        ),
        "evaluacion": evaluacion,
        "resumen": resumen,
    }


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Segmentación K-means de las empresas más grandes del país.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("10.000_Empresas_mas_Grandes_del_País_20260913.csv"),
        help="Ruta al CSV fuente.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("."), help="Carpeta de salida.")
    parser.add_argument("--min-k", type=int, default=2, help="K mínimo a evaluar (por defecto: 2).")
    parser.add_argument("--max-k", type=int, default=10, help="K máximo a evaluar (por defecto: 10).")
    return parser.parse_args()


def main() -> int:
    args = argumentos()
    try:
        resultado = ejecutar(args.input, args.output_dir, args.min_k, args.max_k)
    except (FileNotFoundError, ValueError, OSError, ImportError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Año procesado: {resultado['anio']}")
    print(f"Filas del periodo: {resultado['filas_periodo']}")
    print(f"Filas modeladas: {resultado['filas_modeladas']}")
    print(f"K sugerido por codo: {resultado['k_codo']}")
    print(f"K óptimo por Silhouette: {resultado['k_optimo']}")
    print(f"Silhouette Score: {resultado['silhouette_optimo']:.4f}")
    print(f"Archivos exportados en: {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
