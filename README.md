# Segmentación Estratégica del Tejido Empresarial Colombiano 2024

Proyecto de analítica empresarial que transforma el listado de las 10.000
empresas más grandes de Colombia en un modelo de segmentación K-Means listo
para Power BI. El pipeline usa Python, pandas, NumPy y scikit-learn; el
consumo analítico se realiza en Power BI mediante medidas DAX.

> Antes de publicar el repositorio, confirme que la redistribución pública del
> dataset original y del archivo `.pbix` cumple con las condiciones de la
> fuente de datos y con las políticas de la organización.

## Arquitectura del repositorio

```text
.
├── data/
│   ├── 10.000_Empresas_mas_Grandes_del_País_20260913.csv  # fuente original
│   ├── dataset_empresas_clusters_powerbi.csv               # dataset para Power BI
│   ├── perfil_kpis_clusters.csv                            # KPIs por cluster
│   └── evaluacion_kmeans.csv                               # WCSS, Silhouette y selección de K
├── images/
│   ├── grafica_codo_kmeans.png
│   └── dispersion_clusters_kmeans.png
├── powerbi/
│   ├── empresas_segmentacion.pbix                           # agregar aquí el PBIX
│   ├── medidas_dax_powerbi.md
│   └── README.md
├── src/
│   └── pipeline_clusters_empresas.py
├── .gitignore
├── requirements.txt
└── README.md
```

El archivo `.pbix` no estaba disponible en la carpeta de trabajo al momento
de preparar esta estructura. Debe copiarse como
`powerbi/empresas_segmentacion.pbix` antes del commit inicial; `.gitignore` no
lo excluye.

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
2. Si Power BI solicita la ruta de origen, seleccionar
   `data/dataset_empresas_clusters_powerbi.csv` desde **Transformar datos >
   Configuración de origen de datos > Cambiar origen**.
3. Confirmar que las columnas monetarias sean tipo decimal y que
   `Año de Corte`, `Cluster_ID` y `CIIU` tengan el tipo esperado.
4. Crear las medidas DAX siguientes en la tabla `EmpresasClusters`.

### Medidas DAX base

```DAX
Total Empresas =
COUNTROWS ( EmpresasClusters )

Total Ingresos =
SUM ( EmpresasClusters[INGRESOS OPERACIONALES] )

Total Ganancia =
SUM ( EmpresasClusters[GANANCIA (PÉRDIDA)] )

Empresas Modeladas =
CALCULATE (
    [Total Empresas],
    NOT ISBLANK ( EmpresasClusters[Cluster_ID] )
)

Margen Neto Global =
DIVIDE ( [Total Ganancia], [Total Ingresos] )

Endeudamiento Promedio =
AVERAGE ( EmpresasClusters[Nivel_Endeudamiento] )

% Empresas del Cluster =
DIVIDE (
    [Empresas Modeladas],
    CALCULATE (
        [Empresas Modeladas],
        REMOVEFILTERS (
            EmpresasClusters[Cluster_ID],
            EmpresasClusters[Cluster_Nombre]
        )
    )
)
```

Para tarjetas corporativas se recomienda usar `Margen Neto Global`, que es un
ratio ponderado por ingresos. Para comparar la distribución de segmentos,
usar `% Empresas del Cluster` con `Cluster_Nombre` en el eje o como filtro.
El archivo `powerbi/medidas_dax_powerbi.md` contiene medidas adicionales para
participación de ingresos, ranking y comparación contra el total.

## Diseño sugerido del dashboard

### Página 1 — Contexto Nacional

- Tarjetas: `Total Empresas`, `Total Ingresos`, `Total Ganancia`, `Margen Neto Global`.
- Mapa o matriz por `REGIÓN`, `DEPARTAMENTO DOMICILIO` y `MACROSECTOR`.
- Barras de ingresos y ganancia por macrosector.
- Segmentadores de año, región, supervisor y macrosector.

### Página 2 — Segmentación K-Means

- Barras de cantidad de empresas por `Cluster_Nombre`.
- Dispersión o matriz de `Margen_Neto` frente a `Nivel_Endeudamiento`.
- Tarjetas de margen, endeudamiento, ingresos y participación para el cluster seleccionado.
- Incorporar `images/grafica_codo_kmeans.png` y
  `images/dispersion_clusters_kmeans.png` como apoyo metodológico.

### Página 3 — Explorador de Empresas

- Tabla detallada con `RAZÓN SOCIAL`, `NIT`, `MACROSECTOR`, región, ingresos,
  ganancia, margen, endeudamiento y cluster.
- Filtros por cluster, sector, departamento, ciudad y rango de ingresos.
- Formato condicional para margen negativo, endeudamiento alto y empresas sin
  datos financieros suficientes.

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
