# Medidas DAX para el análisis de clústeres

Importar `dataset_empresas_clusters_powerbi.csv` como la tabla `EmpresasClusters`.
Configurar las columnas monetarias y los ratios como números decimales. Los
ratios `Margen_Neto`, `Nivel_Endeudamiento` y `Distribucion_Pct` se pueden
formatear como porcentaje.

## Medidas base

```DAX
Empresas =
COUNTROWS ( EmpresasClusters )

Empresas con cluster =
CALCULATE (
    [Empresas],
    NOT ISBLANK ( EmpresasClusters[Cluster_ID] )
)

Ingresos totales =
SUM ( EmpresasClusters[INGRESOS OPERACIONALES] )

Ingresos promedio =
AVERAGE ( EmpresasClusters[INGRESOS OPERACIONALES] )

Ganancia total =
SUM ( EmpresasClusters[GANANCIA (PÉRDIDA)] )

Activos totales =
SUM ( EmpresasClusters[TOTAL ACTIVOS] )

Pasivos totales =
SUM ( EmpresasClusters[TOTAL PASIVOS] )

Patrimonio total =
SUM ( EmpresasClusters[TOTAL PATRIMONIO] )
```

## Ratios financieros

```DAX
Margen neto ponderado =
DIVIDE ( [Ganancia total], [Ingresos totales] )

Nivel de endeudamiento ponderado =
DIVIDE ( [Pasivos totales], [Activos totales] )

Margen neto promedio =
AVERAGE ( EmpresasClusters[Margen_Neto] )

Endeudamiento promedio =
AVERAGE ( EmpresasClusters[Nivel_Endeudamiento] )

Margen neto mediano =
MEDIAN ( EmpresasClusters[Margen_Neto] )
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
        REMOVEFILTERS ( EmpresasClusters[Cluster_ID], EmpresasClusters[Cluster_Nombre] )
    )
)

Participación de ingresos =
DIVIDE (
    [Ingresos totales],
    CALCULATE (
        [Ingresos totales],
        REMOVEFILTERS ( EmpresasClusters[Cluster_ID], EmpresasClusters[Cluster_Nombre] )
    )
)

Ingreso promedio del total =
CALCULATE (
    [Ingresos promedio],
    REMOVEFILTERS ( EmpresasClusters[Cluster_ID], EmpresasClusters[Cluster_Nombre] )
)

Índice de escala vs total =
DIVIDE ( [Ingresos promedio], [Ingreso promedio del total] )

Ranking de clúster por ingresos =
RANKX (
    ALL ( EmpresasClusters[Cluster_ID], EmpresasClusters[Cluster_Nombre] ),
    [Ingresos totales],
    , DESC,
    DENSE
)
```

## Uso recomendado en el informe

- Usar `Cluster_Nombre` como eje o segmentador y `Cluster_ID` como identificador técnico.
- Mostrar `Ingresos totales`, `Margen neto ponderado`, `Nivel de endeudamiento ponderado` y `Participación de empresas` en las tarjetas.
- Usar `MACROSECTOR`, `REGIÓN`, `DEPARTAMENTO DOMICILIO` y `Año de Corte` como filtros.
- El archivo `perfil_kpis_clusters.csv` es una tabla resumen estática para validación narrativa; las medidas anteriores deben usarse para que los resultados respondan a filtros.
