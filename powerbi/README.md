# Archivo Power BI

Coloque aquí `empresas_segmentacion.pbix` antes de publicar el repositorio.
El archivo no estaba disponible en la carpeta de trabajo durante la
organización inicial.

La fuente esperada es:

```text
../data/dataset_empresas_clusters_powerbi.csv
```

Si el repositorio se clona en otra ruta, actualice la consulta de Power Query
desde **Transformar datos > Configuración de origen de datos > Cambiar origen**.

## Configuración importante del CSV

El delimitador es coma (`,`), la codificación es UTF-8 y el calificador de
texto es comilla doble (`"`). Use `QuoteStyle.Csv`, no `QuoteStyle.None`.
Configure `NIT` como **Texto**: contiene comas de formato y no es una medida
para sumar.

Si necesita reconstruir la consulta manualmente, la lectura base debe ser
equivalente a:

```powerquery
Csv.Document(
    File.Contents("C:\\ruta\\al\\repositorio\\data\\dataset_empresas_clusters_powerbi.csv"),
    [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
)
```

El pipeline normaliza saltos de línea embebidos en `RAZÓN SOCIAL` para evitar
que Power Query confunda una parte del nombre con un nuevo registro.
