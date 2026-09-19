# Archivo Power BI

El archivo `empresas_segmentacion.pbix` es la base del modelo de datos y del
dashboard. Contiene `Fact_Empresas` y las dimensiones `Dim_Cluster`,
`Dim_Sector`, `Dim_Geografia`, `Dim_CIIU` y `Dim_Periodo`.

## Bootstrap para el equipo

1. Clonar el repositorio o descargarlo como ZIP y extraerlo en una carpeta
   local.
2. Abrir `empresas_segmentacion.pbix` con Power BI Desktop.
3. Seleccionar **Transformar datos > Administrar parámetros**.
4. Editar `pRutaDatos` e indicar la ruta absoluta a la carpeta `data` dentro
   de la copia local del repositorio. Ejemplo:

   ```text
   C:\Users\Nombre\Documents\business-inteligence-project\data
   ```

5. Seleccionar **Cerrar y aplicar** y después **Actualizar**.
6. Confirmar que las seis consultas cargaron sin errores:

   ```text
   Fact_Empresas
   Dim_Cluster
   Dim_Sector
   Dim_Geografia
   Dim_CIIU
   Dim_Periodo
   ```

7. Actualizar el reporte y validar la interacción de filtros en las páginas
   `Contexto Nacional`, `Segmentación K-MEANS` y `Análisis Financiero`. Las
   medidas DAX utilizadas están documentadas en
   [medidas_dax_powerbi.md](medidas_dax_powerbi.md).

`File.Contents()` requiere una ruta absoluta; por eso no se debe sustituir el
valor del parámetro por una ruta relativa como `data/dataset_empresas_clusters_powerbi.csv`.
Las dimensiones son referencias de `Fact_Empresas`, por lo que solo hay que
configurar `pRutaDatos` una vez.

Este dataset es un derivado del conjunto público de Datos Abiertos Colombia:
[10.000 Empresas más Grandes del País](https://www.datos.gov.co/Comercio-Industria-y-Turismo/10-000-Empresas-mas-Grandes-del-Pa-s/6cat-2gcs/about_data).

## Configuración importante del CSV

El delimitador es coma (`,`), la codificación es UTF-8 y el calificador de
texto es comilla doble (`"`). Use `QuoteStyle.Csv`, no `QuoteStyle.None`.
Configure `NIT` como **Texto**: contiene comas de formato y no es una medida
para sumar.

Si necesita reconstruir la consulta manualmente, la lectura base debe ser
equivalente a:

```powerquery
Csv.Document(
    File.Contents(pRutaDatos & "\\dataset_empresas_clusters_powerbi.csv"),
    [Delimiter = ",", Columns = 19, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
)
```

El pipeline normaliza saltos de línea embebidos en `RAZÓN SOCIAL` para evitar
que Power Query confunda una parte del nombre con un nuevo registro.

## Páginas del reporte

El PBIX contiene tres páginas de análisis:

1. **Contexto Nacional:** presenta los KPIs globales y permite filtrar por
   región, departamento, macrosector y supervisor.
2. **Segmentación K-MEANS:** permite comparar la distribución, escala,
   endeudamiento y perfil financiero de los clústeres.
3. **Análisis Financiero:** compara margen, endeudamiento, ganancia y
   patrimonio por clúster, con una dispersión de escala y resultado.
