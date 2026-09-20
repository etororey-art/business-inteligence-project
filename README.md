# Segmentación Estratégica del Tejido Empresarial Colombiano 2024

Proyecto de analítica empresarial que transforma el listado de las 10.000
empresas más grandes de Colombia en un modelo de segmentación K-Means listo
para Power BI. El pipeline usa Python, pandas, NumPy y scikit-learn; el
consumo analítico se realiza en Power BI mediante medidas DAX.

> Antes de publicar el repositorio, confirme que la redistribución pública del
> dataset original y del archivo `.pbix` cumple con las condiciones de la
> fuente de datos y con las políticas de la organización.

## Fuente de datos

La fuente primaria es el conjunto público de Datos Abiertos Colombia:
[10.000 Empresas más Grandes del País](https://www.datos.gov.co/Comercio-Industria-y-Turismo/10-000-Empresas-mas-Grandes-del-Pa-s/6cat-2gcs/about_data).

La versión descargada y utilizada en este proyecto se conserva como
`data/10.000_Empresas_mas_Grandes_del_País_20260913.csv`. El pipeline conserva
el año de corte más reciente disponible en la fuente (2024) y genera los
archivos derivados para Power BI.

El [Informe Final](business-inteligence-project\docs\Informe_Final.docx) contiene el informe detallado con todos los resultados obtenidos durante el académico.

## Arquitectura del repositorio

```text
.
├── data/
│   ├── 10.000_Empresas_mas_Grandes_del_País_20260913.csv  # fuente original
│   ├── dataset_empresas_clusters_powerbi.csv               # dataset para Power BI
│   ├── perfil_kpis_clusters.csv                            # KPIs por cluster
│   └── evaluacion_kmeans.csv                               # WCSS, Silhouette y selección de K
├── docs/
│   └── guia_informe_proyecto.md                             # apoyo para el informe académico
├── images/
│   ├── grafica_codo_kmeans.png
│   └── dispersion_clusters_kmeans.png
├── powerbi/
│   ├── empresas_segmentacion.pbix                           # archivo base del dashboard
│   ├── medidas_dax_powerbi.md
│   └── README.md
├── src/
│   └── pipeline_clusters_empresas.py
├── .gitignore
├── requirements.txt
└── README.md
```

## Inicio rápido para el equipo de Power BI

### Opción A — Clonar con Git

```bash
git clone https://github.com/etororey-art/business-inteligence-project.git
cd business-inteligence-project
```

### Opción B — Descargar como ZIP

1. Abrir [el repositorio en GitHub](https://github.com/etororey-art/business-inteligence-project).
2. Seleccionar **Code > Download ZIP**.
3. Extraer el ZIP en una carpeta local.

Después, para trabajar con Power BI:

1. Abrir `powerbi/empresas_segmentacion.pbix`.
2. En **Transformar datos > Administrar parámetros**, actualizar el parámetro
   `pRutaDatos` con la ruta absoluta de la carpeta `data` de la copia local
   del repositorio. Por ejemplo:

   ```text
   C:\Users\Nombre\Downloads\business-inteligence-project\data
   ```

3. Seleccionar **Cerrar y aplicar** y después **Actualizar**.
4. Confirmar que las columnas monetarias sean tipo decimal y que
   `Año de Corte`, `Cluster_ID` y `CIIU` tengan el tipo esperado.
5. Actualizar el reporte y confirmar que las tarjetas, gráficos y
   segmentadores respondan a los filtros. Las medidas DAX usadas por el
   dashboard se documentan en la
   [guía de medidas DAX](powerbi/medidas_dax_powerbi.md).

La guía detallada de arranque, incluyendo la configuración de `pRutaDatos`,
está disponible en [powerbi/README.md](powerbi/README.md).

## Dashboard implementado

### Página 1 — Contexto Nacional

- Tarjetas de empresas, ingresos totales, ganancia total, patrimonio total y
  margen neto ponderado.
- Barras de distribución de empresas y de ingresos/ganancia por macrosector.
- Matriz `Región/Macrosector` para comparar empresas, ingresos y ganancia.
- Segmentadores de región, departamento, macrosector y supervisor.

### Página 2 — Segmentación K-Means

- Segmentador para explorar cada clúster.
- Barras de distribución de empresas, ingresos promedio y endeudamiento promedio
  por clúster.
- Dispersión de margen neto ponderado frente a endeudamiento promedio.
- Tabla de perfil financiero con empresas, ingresos promedio y endeudamiento
  promedio por clúster.

### Página 3 — Análisis Financiero

- Tarjetas de ganancia total y margen neto ponderado.
- Comparación por clúster de margen neto ponderado, endeudamiento promedio,
  ganancia total y patrimonio total.
- Dispersión para relacionar número de empresas, ingresos promedio y ganancia
  total de cada clúster.

Las gráficas `images/grafica_codo_kmeans.png` y
`images/dispersion_clusters_kmeans.png` se conservan como respaldo metodológico
del modelo y pueden incluirse en el informe o la presentación.

## Ficha técnica del modelo ML

- **Periodo:** 2024, el año más reciente disponible en la fuente.
- **Registros del periodo:** 10.000.
- **Empresas válidas para K-Means:** 9.756.
- **Registros conservados sin cluster:** 244, por activos iguales a cero o
  ratios no modelables. No se eliminan del CSV final y quedan como
  `Sin datos financieros`.
- **Variables:** `Log_Ingresos`, `Margen_Neto` y `Nivel_Endeudamiento`.
- **Normalización:** `RobustScaler`.
- **Algoritmo:** `KMeans(init="k-means++", n_init=10, random_state=42)`.
- **Rango evaluado:** K=2 a K=10.
- **Criterio final:** K=5 para segmentación de negocio, coincidente con el
  diagnóstico del codo. K=2 obtiene el mayor Silhouette (0.9854), pero
  separa principalmente 3 observaciones extremas y deja un único segmento
  masivo; K=5 ofrece una lectura más accionable para el dashboard.
- **Umbrales de nombres de negocio:** margen rentable `>= 5%` y
  endeudamiento alto `>= 70%`.

Los 3 extremos no se borran de la fuente ni del dataset final: se mantienen
para trazabilidad y quedan asignados por el modelo K=5. La evaluación completa
se encuentra en `data/evaluacion_kmeans.csv`.

## Reproducir el pipeline

Con Python 3.10 o superior:

```powershell
python -m pip install -r requirements.txt
python src/pipeline_clusters_empresas.py `
  --input data/10.000_Empresas_mas_Grandes_del_País_20260913.csv `
  --output-dir data `
  --image-dir images `
  --final-k 5
```

El pipeline exporta los tres CSV en `data/` y las gráficas en `images/`, todos
con codificación `utf-8-sig` para facilitar su consumo en Power BI.
