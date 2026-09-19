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

## 3. ETL, carga y modelo de datos

El proceso se divide en dos capas complementarias. Python realiza la preparación
del archivo fuente y el modelamiento K-Means; Power BI carga el archivo final,
construye el modelo estrella y presenta los resultados. Esta separación debe
explicarse de forma explícita en el informe para no atribuir a Power Query
transformaciones que se ejecutan en el script.

### 3.1 Extracción y transformaciones en Python

El archivo fuente `10.000_Empresas_mas_Grandes_del_País_20260913.csv` se
procesa en `src/pipeline_clusters_empresas.py`. Las transformaciones iniciales
se ejecutan principalmente en las siguientes funciones:

| Función | Transformación realizada | Resultado |
|---|---|---|
| `limpiar_numero()` | Elimina símbolos monetarios, interpreta separadores de miles y decimales, reconoce negativos entre paréntesis y convierte vacíos o textos no válidos en nulos. | Valores financieros comparables en formato numérico. |
| `cargar_y_limpiar()` | Lee el CSV con codificación UTF-8, valida las columnas requeridas, normaliza espacios y saltos de línea de campos de texto, convierte las cinco columnas financieras y `Año de Corte` a valores numéricos. | Base limpia y tipificada. |
| `cargar_y_limpiar()` | Conserva únicamente el año de corte más reciente disponible, que en la ejecución actual es 2024. | Universo analítico de 10.000 empresas del período seleccionado. |
| `cargar_y_limpiar()` | Calcula `Margen_Neto`, `Nivel_Endeudamiento` y `Log_Ingresos`. | Variables financieras y de escala para el análisis. |
| `obtener_datos_modelo()` | Reemplaza infinitos por nulos y selecciona solo filas con las tres variables del modelo disponibles. | Subconjunto válido para entrenar K-Means. |
| `evaluar_k()` y `ejecutar()` | Escalan las variables con `RobustScaler`, evalúan K entre 2 y 10 con WCSS y Silhouette, entrenan K-Means y asignan el clúster. | Segmentación reproducible y diagnóstico para seleccionar K. |
| `construir_resumen()` y `ejecutar()` | Construyen el resumen por clúster y exportan los archivos para Power BI. | Dataset final, KPIs por clúster y evaluación del modelo. |

Las empresas que no tienen ingresos, activos o ratios suficientes no se borran
del archivo final. Se excluyen únicamente del entrenamiento y se identifican
como `Sin datos financieros`. El script tampoco elimina duplicados ni imputa
valores nulos; esa condición debe declararse como una decisión de calidad de
datos y, si se requiere una regla de deduplicación, debe implementarse y
documentarse por separado.

La salida de Python se compone de:

- `dataset_empresas_clusters_powerbi.csv`: tabla de detalle enriquecida con
  indicadores y clúster asignado; es el origen de `Fact_Empresas`.
- `perfil_kpis_clusters.csv`: resumen estático de empresas, ingresos, ganancia,
  margen y endeudamiento por clúster; sirve para validar la narrativa.
- `evaluacion_kmeans.csv`: métricas WCSS, Silhouette y selección de K.
- Dos gráficas metodológicas: el diagnóstico del codo/Silhouette y la
  proyección PCA de los clústeres.

### 3.2 Carga, transformación y modelo en Power BI

Power BI carga `dataset_empresas_clusters_powerbi.csv` mediante el parámetro
`pRutaDatos`, que permite definir la ubicación local de la carpeta `data`. En
Power Query se configura la lectura con delimitador coma, codificación UTF-8 y
`QuoteStyle.Csv`; también se preservan `NIT` y `CIIU` como texto para evitar
alterar identificadores.

En esta capa se realizan las transformaciones necesarias para el modelo
analítico, no el entrenamiento de K-Means:

1. Se carga la tabla `Fact_Empresas` desde el CSV procesado por Python y se
   validan los tipos de datos de montos, ratios, año e identificadores.
2. Se crean o ajustan los campos técnicos requeridos por el modelo, como
   `Cluster_ID_Modelo` y `GeoKey`.
3. Se generan como referencias de la tabla de hechos las dimensiones
   `Dim_Cluster`, `Dim_Periodo`, `Dim_Sector`, `Dim_Geografia` y `Dim_CIIU`.
4. Se definen relaciones uno a muchos, con dirección de filtro única desde las
   dimensiones hacia `Fact_Empresas`.
5. Se crean medidas DAX, por ejemplo `Ingresos totales`, `Ganancia total`,
   `Margen neto ponderado` y `Nivel de endeudamiento ponderado`, para que los
   resultados respondan a los segmentadores del dashboard.

Las medidas DAX pertenecen a la capa semántica del modelo: calculan indicadores
en tiempo de consulta y no reemplazan las transformaciones ni el algoritmo que
se ejecutan en Python.

### Texto sugerido para el informe

> El ETL se implementó en dos etapas. En Python se realizó la extracción del
> CSV público, la normalización de campos de texto y valores financieros, la
> selección del período 2024, el cálculo de indicadores y la segmentación
> K-Means. Luego se exportó un dataset enriquecido para Power BI. En Power Query
> se configuró la carga del archivo final, se validaron los tipos de datos y se
> construyó un modelo estrella con dimensiones de clúster, período, sector,
> geografía y CIIU. Finalmente, las medidas DAX permitieron que los KPIs y los
> visuales se actualizaran de forma interactiva según los filtros aplicados.

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
5. Página **Contexto Nacional**, mostrando las tarjetas, filtros y la matriz
   Región/Macrosector.
6. Página **Segmentación K-MEANS**, mostrando el perfil financiero, la
   distribución y la dispersión de clústeres.
7. Página **Análisis Financiero**, mostrando la comparación de margen,
   endeudamiento, ganancia y patrimonio por clúster.

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

## 6. Dashboard implementado y narrativa

La narrativa del reporte se organiza en las tres páginas implementadas:

1. **Contexto Nacional:** responde cuántas empresas, ingresos, ganancia,
   patrimonio y margen se analizan; los filtros y la matriz permiten ubicar los
   resultados por territorio, macrosector y supervisor.
2. **Segmentación K-MEANS:** muestra cómo se distribuyen las empresas entre
   perfiles y compara sus ingresos promedio, endeudamiento y margen neto.
3. **Análisis Financiero:** profundiza la comparación de margen, endeudamiento,
   ganancia y patrimonio por clúster para orientar la revisión de perfiles.

Texto sugerido para presentar el dashboard:

> El dashboard inicia con un panorama nacional filtrable, continúa con la
> comparación de los perfiles descubiertos por K-Means y finaliza con el
> análisis financiero por clúster. Esta secuencia permite pasar de una visión
> agregada a una lectura específica de rentabilidad, endeudamiento, ganancia y
> patrimonio, sin interpretar los clústeres pequeños como tendencias generales.

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
