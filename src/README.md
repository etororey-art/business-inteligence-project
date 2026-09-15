# Pipeline de ETL y segmentación K-Means

`pipeline_clusters_empresas.py` prepara el dataset empresarial para Power BI,
calcula ratios financieros y segmenta las empresas mediante K-Means.

El script se ejecuta desde la raíz del repositorio y escribe los resultados en
`data/` e `images/`. El equipo de Power BI solo necesita consumir los CSV
generados; no necesita ejecutar Python para construir el dashboard.

## Fuente y trazabilidad

El archivo fuente proviene de Datos Abiertos Colombia:
[10.000 Empresas más Grandes del País](https://www.datos.gov.co/Comercio-Industria-y-Turismo/10-000-Empresas-mas-Grandes-del-Pa-s/6cat-2gcs/about_data).

La copia usada por el pipeline está en
`data/10.000_Empresas_mas_Grandes_del_País_20260913.csv`. El script filtra al
periodo más reciente encontrado, por lo que la ejecución actual procesa 2024.

## Flujo de procesamiento

1. Carga el CSV fuente en UTF-8.
2. Normaliza espacios y saltos de línea en los campos de texto para asegurar
   un registro físico por empresa en el CSV de salida.
3. Convierte las columnas financieras con formatos como `$144.82`,
   `$1.234,56`, `$1,234.56` y valores negativos entre paréntesis.
4. Conserva el año de corte más reciente disponible.
5. Calcula las variables de negocio:
   - `Margen_Neto = GANANCIA (PÉRDIDA) / INGRESOS OPERACIONALES`
   - `Nivel_Endeudamiento = TOTAL PASIVOS / TOTAL ACTIVOS`
   - `Log_Ingresos = log(1 + INGRESOS OPERACIONALES)`
6. Excluye solo del entrenamiento las empresas sin las tres variables válidas;
   se mantienen en el archivo final como `Sin datos financieros`.
7. Evalúa K entre 2 y 10 con WCSS (método del codo) y Silhouette Score.
8. Entrena K-Means con `RobustScaler`, `k-means++`, `n_init=10` y
   `random_state=42`.
9. Exporta los datasets para Power BI y las gráficas de respaldo técnico.

## Ejecución

Instalar las dependencias una sola vez desde la raíz del repositorio:

```powershell
python -m pip install -r requirements.txt
```

Ejecutar el pipeline completo:

```powershell
python src/pipeline_clusters_empresas.py `
  --input data/10.000_Empresas_mas_Grandes_del_País_20260913.csv `
  --output-dir data `
  --image-dir images `
  --final-k 5
```

Parámetros disponibles:

| Parámetro | Valor predeterminado | Descripción |
|---|---:|---|
| `--input` | CSV fuente en `data/` | Archivo original de empresas. |
| `--output-dir` | `data` | Carpeta de salida de los CSV. |
| `--image-dir` | `images` | Carpeta de salida de las gráficas. |
| `--min-k` | `2` | Menor K evaluado. |
| `--max-k` | `10` | Mayor K evaluado. |
| `--final-k` | `5` | K usado para asignar el clúster final. |

## Columnas requeridas en el archivo fuente

```text
INGRESOS OPERACIONALES
GANANCIA (PÉRDIDA)
TOTAL ACTIVOS
TOTAL PASIVOS
TOTAL PATRIMONIO
Año de Corte
```

Las columnas `NIT` y `CIIU` se conservan como texto para evitar perder formato
o alterar identificadores durante la importación en Power BI.

## Selección de K y nombres de negocio

El pipeline registra ambos diagnósticos en `evaluacion_kmeans.csv`:

- K=2 maximiza el Silhouette Score, pero está influido por tres observaciones
  extremas y produce un segmento dominante poco útil para negocio.
- K=5 coincide con el diagnóstico del codo y se usa como configuración final
  para obtener segmentos más interpretables en el dashboard.

Los nombres se asignan con los promedios del clúster y estos umbrales:

- Rentable: margen neto igual o superior a 5%.
- Endeudamiento alto: nivel de endeudamiento igual o superior a 70%.
- Escala alta: ingresos medios iguales o superiores a la mediana entre
  clústeres.

Los nombres posibles son `Líderes Rentables`, `Rentables Apalancadas`,
`Especialistas Sólidas`, `En Riesgo Financiero`, `Grandes en Transición`,
`Base Operativa` y `Sin datos financieros`.

## Salidas

| Archivo | Contenido |
|---|---|
| `data/dataset_empresas_clusters_powerbi.csv` | Dataset final: columnas fuente, ratios, variables del modelo y clúster. |
| `data/perfil_kpis_clusters.csv` | Conteos, totales, promedios, medianas y ratios ponderados por clúster. |
| `data/evaluacion_kmeans.csv` | WCSS, Silhouette, diagnóstico del codo y K seleccionado. |
| `images/grafica_codo_kmeans.png` | Curvas del codo y Silhouette. |
| `images/dispersion_clusters_kmeans.png` | Proyección PCA de las empresas segmentadas. |

Los CSV se escriben con codificación `utf-8-sig`, compatible con Power BI y
Excel en entornos Windows.

## Manejo de errores frecuentes

- **Columnas obligatorias ausentes:** comprobar los nombres del CSV fuente.
- **Año inválido:** revisar el formato de `Año de Corte`; se admiten valores
  como `2,024`.
- **Error al importar en Power BI:** configurar coma como delimitador,
  UTF-8 como codificación, `QuoteStyle.Csv` y `NIT` como texto.
- **Empresa sin clúster:** revisar ingresos o activos nulos/cero; el registro
  se conserva para trazabilidad, pero no se fuerza al modelo.
