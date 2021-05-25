consulta_modelo_v1 = ''' 
WITH bloques_a_predecir as ( 
    select blocknumber, 
        desarrollo,
        fecha_siembra,
        grupo_forza,
        finduccion

    from blocks_desarrollo
    where bloque in %s
 ), areas as (
    SELECT  t1.blocknumber,
    desarrollo,
    t1.fecha_siembra,
    dias_hasta_siembra_grupo,
    t1.grupo_forza,
    t1.finduccion,
    t1.finduccion + INTERVAL '140 day' as mean_fecha_cosecha,
    descripcion,
    area,
    drenajes,
    poblacion,
    rango_semilla
    FROM bloques_a_predecir as t1
    left join blocks_detalle as t2
    on t1.blocknumber=t2.blocknumber 
),
resultados_pc as (
Select blocknumber as bloque,
'SC' as tipo,
kilos_cosechados as kilos_pc,
frutas as frutas_pc,
fecha_siembra as fecha_siembra_pc
from blocks_desarrollo where blocknumber in (select blocknumber from bloques_a_predecir where desarrollo ='SC') and desarrollo ='PC'),

tabla_principal as (
SELECT blocknumber,
      descripcion,
      desarrollo,
      CONCAT(desarrollo,blocknumber) as llave,
      fecha_siembra,
      fecha_siembra_pc,
      dias_hasta_siembra_grupo,
      grupo_forza,
      finduccion,
      mean_fecha_cosecha,
      area as Area,
      drenajes,
      poblacion/area as densidad,
      kilos_pc/area as productividad_pc,
      frutas_pc/poblacion as recuperacion_pc,
      rango_semilla

FROM areas 
LEFT JOIN resultados_pc
ON blocknumber=bloque
AND desarrollo=tipo
),

/*Esta parte del peso de forza se podría agregar a blocks_desarrollo dentro del ETL nocturno */
pesoplanta_filtrado as (
    SELECT llave,
    fecha,
    valor,
    finduccion,
    max(fecha) OVER (PARTITION BY llave) as max_fecha
    FROM pesoplanta as t1
    INNER JOIN blocks_desarrollo AS t2
    ON t1.llave=t2.bloque
    WHERE fecha<finduccion OR finduccion is NULL
    ),
  
peso_agrupado as (
  SELECT llave,
  AVG(valor)/1000 as peso_forza
  FROM pesoplanta_filtrado
  where fecha=max_fecha
  GROUP BY llave
),

cosecha_real as (
  select CONCAT(desarrollo,blocknumber) as llave,
  kilos_cosechados,
  frutas
  from cosecha_resumen
)

SELECT blocknumber,
      descripcion,
      desarrollo,
      t1.llave,
      fecha_siembra,
      fecha_siembra_pc,
      dias_hasta_siembra_grupo,
      grupo_forza,
      finduccion,
      mean_fecha_cosecha,
      area as Area,
      drenajes,
      densidad,
      productividad_pc,
      recuperacion_pc,
      rango_semilla,
      peso_forza,
      kilos_cosechados,
      frutas
      
      FROM tabla_principal AS t1
      LEFT JOIN peso_agrupado AS t2
      ON t1.llave = t2.llave
      LEFT JOIN cosecha_real AS t3
      on t1.llave=t3.llave
 
  '''