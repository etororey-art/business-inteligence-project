# Guía de apoyo para el informe del proyecto

Este documento sirve como base para elaborar el informe en Word o PDF. Debe
adaptarse con las capturas reales del equipo desde Power BI y con la narrativa
que decidan presentar.

## 1. Problema propuesto

### Contexto

El grupo de las 10.000 empresas más grandes de Colombia reúne organizaciones
con escalas, sectores, rentabilidades y estructuras de endeudamiento muy
distintas. Un ranking por ingresos no permite identificar, por sí solo, cuáles
empresas combinan rentabilidad con solidez financiera, cuáles dependen más del
apalancamiento y cuáles presentan señales que requieren revisión.

### Pregunta de análisis

> ¿Qué perfiles empresariales pueden identificarse en las empresas más grandes
> de Colombia en 2024 al combinar su escala de ingresos, margen neto y nivel de
> endeudamiento?

### Objetivo general

Segmentar las empresas mediante K-Means para caracterizar grupos con patrones
similares de escala, rentabilidad y endeudamiento, y presentar los resultados
en un dashboard interactivo de Power BI.

### Objetivos específicos

1. Limpiar y preparar la información financiera para su consumo analítico.
2. Calcular el margen neto y el nivel de endeudamiento de cada empresa.
3. Evaluar diferentes valores de K mediante WCSS y Silhouette Score.
4. Identificar perfiles empresariales y compararlos por sector y geografía.
5. Entregar un dashboard que ayude a explorar los resultados y detectar
   segmentos que merecen atención.

## 2. Justificación de la selección de datos

La fuente seleccionada es el conjunto público de Datos Abiertos Colombia:
[10.000 Empresas más Grandes del País](https://www.datos.gov.co/Comercio-Industria-y-Turismo/10-000-Empresas-mas-Grandes-del-Pa-s/6cat-2gcs/about_data).

La selección se justifica porque:

- Es una fuente pública y verificable, apropiada para un proyecto académico.
- Incluye identificador de empresa, razón social, supervisor, sector, región,
  departamento, ciudad y año de corte.
- Contiene las variables financieras necesarias para el análisis: ingresos,
  ganancia o pérdida, activos, pasivos y patrimonio.
- Permite analizar el tejido empresarial desde perspectivas geográficas,
  sectoriales y financieras.
- Incluye varios años; el proyecto conserva 2024 por ser el periodo más
  reciente disponible en el archivo descargado.

Texto sugerido para el informe:

> Se eligió esta fuente porque ofrece información financiera y descriptiva de
> empresas de gran relevancia económica en Colombia. La disponibilidad de
> ingresos, ganancia, activos y pasivos permitió construir indicadores de
> rentabilidad y endeudamiento, mientras que las variables sectoriales y
> geográficas hicieron posible contextualizar los clústeres en Power BI.

## 3. ETL y modelo de datos en Power BI

### Extracción

La tabla de hechos se carga desde
`data/dataset_empresas_clusters_powerbi.csv`. El PBIX usa el parámetro
`pRutaDatos` para que cada integrante pueda indicar la carpeta `data` de su
copia local del repositorio.

### Transformaciones realizadas

Documenten las acciones que se observan en Power Query:

- Uso de coma como delimitador, UTF-8 y `QuoteStyle.Csv`.
- `NIT` y `CIIU` configurados como texto.
- Normalización de saltos de línea y espacios en los campos de texto.
- Conversión de columnas financieras a número decimal.
- Conservación del año de corte más reciente: 2024.
- Manejo de empresas sin ratios modelables como `Sin datos financieros`, sin
  eliminarlas del archivo final.
- Creación de `Cluster_ID_Modelo` y `GeoKey`.

### Modelo estrella

El modelo se compone de `Fact_Empresas` y estas dimensiones:

```text
Dim_Cluster    1 ── * Fact_Empresas
Dim_Periodo    1 ── * Fact_Empresas
Dim_Sector     1 ── * Fact_Empresas
Dim_Geografia  1 ── * Fact_Empresas
Dim_CIIU       1 ── * Fact_Empresas
```

Las relaciones deben tener dirección de filtro única desde las dimensiones
hacia la tabla de hechos. Esta estructura evita ambigüedad de filtros y hace
que las medidas respondan correctamente a los segmentadores.

### Capturas recomendadas para el informe

1. Parámetro `pRutaDatos` y consulta `Fact_Empresas` en Power Query.
2. Pasos de limpieza y tipos de datos de la consulta.
3. Vista de modelo con las cinco dimensiones y sus relaciones 1:*.
4. Una medida DAX creada, por ejemplo `Margen neto ponderado`.

## 4. Descripción del algoritmo K-Means

El algoritmo se implementó en Python con `pandas`, `scikit-learn` y
`RobustScaler`. K-Means agrupa observaciones similares minimizando la distancia
interna de cada grupo. No predice una variable objetivo; por ello se usa como
una técnica de segmentación exploratoria.

Las variables usadas fueron:

| Variable | Fórmula o transformación | Propósito |
|---|---|---|
| `Log_Ingresos` | `log(1 + ingresos operacionales)` | Representar escala y reducir asimetría. |
| `Margen_Neto` | ganancia o pérdida / ingresos | Medir rentabilidad. |
| `Nivel_Endeudamiento` | pasivos / activos | Medir proporción de activos financiada con deuda. |

Se usó `RobustScaler` para reducir el efecto de escalas y valores extremos,
K-Means con inicialización `k-means++`, `n_init=10` y `random_state=42` para
hacer el resultado reproducible.

### Selección de K

Se evaluaron valores de K entre 2 y 10. El método del codo señala K=5. Aunque
K=2 obtiene el Silhouette Score máximo de 0,9854, esa solución separa sobre
todo tres empresas con ratios extremos y deja un único grupo masivo. Se eligió
K=5 por coincidir con el codo y permitir una lectura más accionable de los
perfiles empresariales. El Silhouette de K=5 es 0,8396.

Es importante escribir esta decisión como una compensación entre una métrica
estadística y la utilidad del segmento para negocio; no como una afirmación de
que K=5 sea la única solución posible.

## 5. Interpretación de resultados

Los siguientes valores provienen de `data/perfil_kpis_clusters.csv`. Los
márgenes y niveles de endeudamiento ponderados se calculan con los totales del
clúster, por lo que son más adecuados para comparar segmentos de tamaños
distintos.

| Perfil | Empresas | Participación | Margen neto ponderado | Endeudamiento ponderado | Lectura inicial |
|---|---:|---:|---:|---:|---|
| Grandes en Transición | 9.390 | 96,25% | 3,74% | 58,93% | Segmento dominante: margen moderado y deuda relevante; permite analizar eficiencia y estructura financiera por sector. |
| Líderes Rentables 2 | 359 | 3,68% | 69,60% | 18,52% | Grupo rentable y con apalancamiento relativamente bajo; útil como referencia comparativa. |
| Líderes Rentables | 4 | 0,04% | 443,28% | 28,13% | Casos atípicos de alta rentabilidad; deben revisarse individualmente antes de generalizar conclusiones. |
| Especialistas Sólidas | 1 | 0,01% | 1.950,00% | 14,58% | Observación extrema; el margen puede estar influido por una base de ingresos muy baja. |
| En Riesgo Financiero | 2 | 0,02% | -1.100,00% | 160,26% | Pérdidas y pasivos superiores a activos; requiere validación de datos y análisis individual. |

Texto sugerido para la interpretación:

> El análisis revela que la mayor parte de las empresas se concentra en el
> perfil Grandes en Transición. Este segmento registra un margen neto ponderado
> positivo, aunque moderado, y una proporción relevante de pasivos sobre activos.
> Por tanto, la principal oportunidad del dashboard es comparar este grupo por
> macrosector y geografía para detectar dónde existen mejores prácticas de
> rentabilidad o mayor presión financiera.

> Los clústeres de pocos registros deben interpretarse como empresas atípicas,
> no como tendencias generales de la economía. En especial, los márgenes muy
> elevados o negativos pueden surgir cuando la ganancia o pérdida es grande en
> comparación con ingresos pequeños. Estos casos se conservan por trazabilidad,
> pero requieren una revisión individual antes de emitir recomendaciones.

## 6. Recomendaciones para el dashboard y la narrativa

La historia visual puede seguir esta secuencia:

1. **Panorama nacional:** ¿cuántas empresas, ingresos y ganancia se analizan?
2. **Segmentación:** ¿cómo se distribuyen las empresas entre perfiles y qué
   diferencia sus márgenes y endeudamiento?
3. **Exploración:** ¿qué sectores, territorios y empresas explican cada
   perfil?
4. **Acción:** ¿qué grupos requieren seguimiento, comparación o validación?

Recomendaciones derivadas del análisis:

- Comparar `Grandes en Transición` por `Dim_Sector` y `Dim_Geografia` para
  identificar oportunidades de mejora de margen y gestión de deuda.
- Usar `Líderes Rentables 2` como referencia de rentabilidad y bajo
  endeudamiento, sin asumir causalidad.
- Revisar los casos de `En Riesgo Financiero` y los clústeres extremadamente
  rentables a nivel de empresa antes de tomar decisiones.
- Incluir una nota metodológica que indique que la segmentación no es un modelo
  de predicción de quiebra, crédito o fraude.

## 7. Limitaciones y trabajo futuro

- El análisis utiliza un corte anual, por lo que no permite concluir tendencias
  temporales todavía.
- Los ratios financieros pueden ser sensibles a ingresos bajos o cercanos a
  cero; por ello aparecen observaciones extremas.
- K-Means depende de las variables seleccionadas y de K; los resultados no son
  una verdad absoluta sino una herramienta exploratoria.
- Como mejora futura, se pueden limitar ratios extremos por percentiles,
  incorporar logaritmo de activos y comparar el resultado con otros algoritmos
  de agrupamiento.

## 8. Lista de verificación de entregables

- [ ] Informe Word o PDF con introducción, selección de datos, ETL, algoritmo,
  resultados, conclusiones y capturas reales.
- [ ] `powerbi/empresas_segmentacion.pbix` con el modelo, medidas DAX y tres
  páginas de dashboard.
- [ ] Código Python en `src/pipeline_clusters_empresas.py`.
- [ ] Presentación breve con problema, fuente, proceso, hallazgos, limitaciones
  y recomendaciones.
