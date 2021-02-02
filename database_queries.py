
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

# ssl_args ={"sslmode":'verify-ca',"sslrootcert": "gcp postgres/server-ca.pem","sslcert": "gcp postgres/client-cert.pem","sslkey":"gcp postgres/client-key.pem"}
# pool = sqlalchemy.create_engine(
#     # Equivalent URL:
#     # mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
#     sqlalchemy.engine.url.URL(
#         drivername="postgresql+psycopg2",
#         username="postgres",  # e.g. "my-database-user"
#         password="Guapa.2020*",  # e.g. "my-database-password"
#         host="35.237.147.235",  # e.g. "127.0.0.1"
#         port="5432",  # e.g. 3306
#         database='ppc',  # e.g. "my-database-name"
#     ),connect_args=ssl_args
# )
# #Corrección para ejecución rápida de comandos sql
# @event.listens_for(pool, 'before_cursor_execute')
# def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
#     if executemany:
#         cursor.fast_executemany = True
#         cursor.commit()

# categorias_insumos.to_sql(name="categoria_insumos",con=pool,if_exists='replace',index=False,method='multi')


## Extraer información tabla bloques:
##Falta corregir join de grupossiembra


# def retorna_info_aplicaciones_preforza_por_bloque(bloque):

#   ## Extraer información tabla bloques:
#   df_resultado_union_bloque_siembra = pd.DataFrame(columns=["Seleccione","bloque"])
  
#   if bloque =="":
#       return df_resultado_union_bloque_siembra,df_resultado_union_bloque_siembra

#   try:
    
#     cedulas = pd.read_sql_query('''select codigo from MANTENIMIENTOCAMPOS_DETALLEBLOCKs where blocknumber = %s ''',
#     con = connection,params =[bloque])

#     if cedulas.empty==False:
#         finduccion = pd.read_sql_query('''select finduccion from siembra where blocknumber = %s ''',
#         con = connection,params =[bloque]).iat[0,0]

#         formulas = pd.read_sql_query('''select codigo, formula,apldate from mantenimientocampos where codigo in %s  ''', con = connection,params =[tuple(set(cedulas.codigo.to_list()))])
#         detalle_formulas = pd.read_sql_query('''
#         select formula,t1.descripcion as descripcion_formula, t2.descripcion as etapa from 
#         (select codigo as formula, descripcion,etapa from formulas where codigo in %s) as t1
#         left join etapasaplicacion as t2 on  t1.etapa=t2.codigo
        
#          ''', con = connection,params =[tuple(set(formulas.formula.to_list()))])
#         formulas_con_detalle = formulas.merge(detalle_formulas,how="left",on="formula")

#         df_union_formulas_cedulas = formulas_con_detalle.merge(cedulas, how="inner",on="codigo")
#         df_union_formulas_cedulas.sort_values(by=["apldate"],inplace=True)
#         df_union_formulas_cedulas.query("apldate<@finduccion",inplace=True)

#         #Definir categoría de la aplicación
#         if df_union_formulas_cedulas.empty==False:
#             insumos_por_formulas_seleccionadas = pd.read_sql_query('''select codigo,insumo from formulas_det where codigo in %s ''',
#             con = connection,params =[tuple(set(df_union_formulas_cedulas.formula.to_list()))])
#             insumos_por_formulas_seleccionadas = insumos_por_formulas_seleccionadas.merge(categorias_insumos,how="inner",on="insumo")
#             categoria_por_aplicacion = insumos_por_formulas_seleccionadas[["codigo","categorias_por_insumo"]].drop_duplicates()
#         else:
#             return df_resultado_union_bloque_siembra
      
#     return df_union_formulas_cedulas,categoria_por_aplicacion
#   except Exception as e:

#       print("hubo un error", e)
#       connection.rollback()
#       return df_resultado_union_bloque_siembra,df_resultado_union_bloque_siembra


# def retorna_resumen_aplicaciones_por_bloque(bloque):

    
#     ## Extraer información tabla bloques:
#     df_formulas, df_categorias = retorna_info_aplicaciones_preforza_por_bloque(bloque)
  
#     if df_formulas.empty ==True:
#         return df_formulas
#     else: 
#         df_categorias.rename(columns={"codigo":"formula","categorias_por_insumo":"categoria"},inplace=True)
        
#         df_formulas_con_categorias = df_formulas.merge(df_categorias,how="left",on="formula")
#         df_formulas_con_categorias = df_formulas_con_categorias[["apldate","categoria"]]
#         df_formulas_con_categorias.sort_values(by=["categoria","apldate"],inplace=True)
#         df_formulas_con_categorias["diff"]=df_formulas_con_categorias.groupby("categoria")["apldate"].diff()/np.timedelta64(1, 'D')

#         df_resultado = df_formulas_con_categorias.groupby(["categoria"])["diff"].agg(num_aplicaciones="count",
#         dias_prom="mean",max_dias="max",min_dias="min").reset_index().round(2)
#         return df_resultado
