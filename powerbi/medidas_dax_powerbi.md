# Medidas DAX para el análisis de clústeres

Crear estas medidas en la tabla de hechos `Fact_Empresas`. Configurar las
columnas monetarias y los ratios como números decimales. Los ratios
`Margen_Neto` y `Nivel_Endeudamiento` se pueden formatear como porcentaje.

## Medidas base

```DAX
Empresas =
COUNTROWS ( Fact_Empresas )

Empresas con cluster =
CALCULATE (
    [Empresas],
    Fact_Empresas[Cluster_ID_Modelo] <> -1
)

Ingresos totales =
SUM ( Fact_Empresas[INGRESOS OPERACIONALES] )

Ingresos promedio =
AVERAGE ( Fact_Empresas[INGRESOS OPERACIONALES] )

Ganancia total =
SUM ( Fact_Empresas[GANANCIA (PÉRDIDA)] )

Activos totales =
SUM ( Fact_Empresas[TOTAL ACTIVOS] )

Pasivos totales =
SUM ( Fact_Empresas[TOTAL PASIVOS] )

Patrimonio total =
SUM ( Fact_Empresas[TOTAL PATRIMONIO] )
```

## Ratios financieros

```DAX
Margen neto ponderado =
DIVIDE ( [Ganancia total], [Ingresos totales] )

Nivel de endeudamiento ponderado =
DIVIDE ( [Pasivos totales], [Activos totales] )

Margen neto promedio =
AVERAGE ( Fact_Empresas[Margen_Neto] )

Endeudamiento promedio =
AVERAGE ( Fact_Empresas[Nivel_Endeudamiento] )

Margen neto mediano =
MEDIAN ( Fact_Empresas[Margen_Neto] )
```

Los ratios ponderados son los recomendados para las tarjetas y comparaciones
entre clústeres: evitan que una empresa pequeña tenga el mismo peso que una
empresa de ingresos muy altos.

## Distribución y comparación entre clústeres

```DAX
Participación de empresas =
DIVIDE (
    [Empresas con cluster],
    CALCULATE (
        [Empresas con cluster],
        REMOVEFILTERS ( Dim_Cluster )
    )
)

Participación de ingresos =
DIVIDE (
    [Ingresos totales],
    CALCULATE (
        [Ingresos totales],
        REMOVEFILTERS ( Dim_Cluster )
    )
)

Ingreso promedio del total =
CALCULATE (
    [Ingresos promedio],
    REMOVEFILTERS ( Dim_Cluster )
)

Índice de escala vs total =
DIVIDE ( [Ingresos promedio], [Ingreso promedio del total] )

Ranking de clúster por ingresos =
RANKX (
    ALL ( Dim_Cluster[Cluster_ID_Modelo], Dim_Cluster[Cluster_Nombre] ),
    [Ingresos totales],
    , DESC,
    DENSE
)
```

## Uso recomendado en el informe

- Usar `Dim_Cluster[Cluster_Nombre]` como eje o segmentador y `Dim_Cluster[Cluster_ID_Modelo]` como identificador técnico.
- Mostrar `Ingresos totales`, `Margen neto ponderado`, `Nivel de endeudamiento ponderado` y `Participación de empresas` en las tarjetas.
- Usar los campos de `Dim_Sector`, `Dim_Geografia` y `Dim_Periodo` como filtros.
- El archivo `perfil_kpis_clusters.csv` es una tabla resumen estática para validación narrativa; las medidas anteriores deben usarse para que los resultados respondan a filtros.
