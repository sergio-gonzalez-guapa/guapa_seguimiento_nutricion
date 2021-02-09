
historia_bloques = ''' select
        bloque,
        t2.descripcion as gruposiembra,
        grupoforza,
        date(primera) as inicio_PC,
        date(produccion_semilla) inicio_SM_PC,
        date(segunda) inicio_SC,
        date(produccion_semilla2) inicio_SM_SC,
        date(barrido) as barrido
        from (
            SELECT descripcion as bloque,
            gruposiembra,
            grupoforza,
            max (CASE WHEN t1.Estado = '1' THEN FechaEstado ELSE NULL END) as primera,
            max (CASE WHEN t1.Estado = '2' THEN FechaEstado ELSE NULL END) as segunda,
            max (CASE WHEN t1.Estado = '3' THEN FechaEstado ELSE NULL END) as produccion_semilla,
            max (CASE WHEN t1.Estado = '4' THEN FechaEstado ELSE NULL END) as barrido,
            /*
            max (CASE WHEN t1.Estado = '5' THEN FechaEstado ELSE NULL END) as presiembra,
            max (CASE WHEN t1.Estado = '6' THEN FechaEstado ELSE NULL END) as sindefinir,*/
            max (CASE WHEN t1.Estado = '7' THEN FechaEstado ELSE NULL END) as produccion_semilla2

            FROM (
                select t1.codigo,descripcion,gruposiembra,grupoforza
                 from siembra as t1 inner join blocks as t2 on t1.blocknumber=t2.codigo
                 where descripcion like %s) as t2 

        left join siembrafechaestados as t1 on
        t1.codigo=t2.codigo
        GROUP BY descripcion,gruposiembra, grupoforza
                ) as t1
        left join grupossiembra as t2
        on t1.gruposiembra=t2.codigo
        order by bloque '''


lotes_historia = '''
    select distinct
    concat('lote ',substring(descripcion,1,2), ' año 20',substring(descripcion,5,2)) as label,
    concat(substring(descripcion,1,2),'__',substring(descripcion,5,2)) as value
    from blocks
    where codigo in (select blocknumber from siembra)
    order by 1'''

grupossiembra = '''
    select codigo,
    descripcion,
    fecha
    from grupossiembra
    where fecha >= '2014-03-01'::date
    order by fecha'''

df_formulas = '''
    select codigo,
    descripcion
    from formulas'''

bloques_por_gs = '''
select codigo,
descripcion
from blocks
where gruposiembra =%s
'''

bloques_detallado_por_gs = '''
select codigo as blocknumber,
descripcion,
lote,
area,
gruposiembra
from blocks where gruposiembra = %s'''

cedulas = '''
select codigo,
blocknumber
from MANTENIMIENTOCAMPOS_DETALLEBLOCKS
where blocknumber in %s
'''

info_siembras_por_bloque = '''
select blocknumber,
plantcant,
finiciosiembra,
finduccion
from siembra
where blocknumber in %s 
'''

aplicaciones = '''
select codigo,
formula,
apldate 
from mantenimientocampos 
where codigo in %s  
'''

insumos_por_formula  = '''
select t1.codigo,
insumo,
descripcion as descripcion_formula
from formulas_det as t1 
inner join formulas as t2
on t1.codigo=t2.codigo
where t1.codigo in %s 
'''

info_bloques = '''
    SELECT
    blocknumber,
	t1.descripcion
    ,finiciosiembra::date as fecha_siembra
    ,case when t3.fecha is not null then DATE_PART('day',t3.fecha::timestamp - finiciosiembra::timestamp)
    else 0 
    end AS dias_hasta_siembra_grupo
    ,case when t4.fecha>finduccion then t4.fecha::date else finduccion::date
     end as finduccion
    ,case when
    DATE_PART('day',fpoda::timestamp - finduccion::timestamp)>250 then
     t5.fecha::date
      else fpoda::date
      end as fecha_sm1

    ,t7.fecha::date as fecha_inicio_sc
    ,t6.fecha::date as finduccion2
	,plantcant as poblacion
	,area
    ,drenajes/area as drenajes
    ,t3.descripcion as grupo_siembra
    ,t4.descripcion as grupo_forza
    ,t5.descripcion as grupo_semillero
    ,t6.descripcion as grupo_forza2
    ,t7.descripcion as grupo_cosecha2
	,t8.descripcion as rango_semilla
  FROM blocks as t1
  inner join siembra as t2
  on t1.codigo = t2.blocknumber
  left join grupossiembra as t3
  on t1.gruposiembra=t3.codigo
  left join gruposforza as t4
  on t1.grupoforza=t4.codigo
  left join grupossemillero as t5
  on t1.gruposemillero=t5.codigo
  left join gruposforza2 as t6
  on t1.grupoforza2=t6.codigo
  left join grupos2dacosecha as t7
  on t1.grupo2dacosecha=t7.codigo
  left join tipossemilla as t8
  on t2.seedtype=t8.codigo
  where drenajes<area
  order by finiciosiembra
  '''


