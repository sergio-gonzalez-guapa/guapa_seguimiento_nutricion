from datetime import date
from datetime import timedelta
import pandas as pd

def seleccionar_variables (df):

    variables = ['mean_fecha_cosecha', 'descripcion', 'fecha_siembra','dias_hasta_siembra_grupo',
     'finduccion', 'area', 'drenajes', 'rango_semilla','peso_forza', 'densidad', 'llave','grupo_forza',
     'kilos_cosechados','frutas','fecha_siembra_pc','productividad_pc','recuperacion_pc','desarrollo']

    return df[variables].copy()


def proporcion_dias_trimestre(startdate, enddate,trimestre):
    if trimestre==1:
        start_tuple=(1,1)
        end_tuple=(3,31)
    elif trimestre==2:
        start_tuple=(4,1)
        end_tuple=(6,30)
    elif trimestre==3:
        start_tuple=(7,1)
        end_tuple=(9,30)
    elif trimestre==4:
        start_tuple=(10,1)
        end_tuple=(12,31)
    else:
        raise NameError ("Ingrese un trimestre válido")

    dias_trimestre = 0
    for year in range(startdate.year, enddate.year+1):
        start_period = startdate if year == startdate.year else date(year, 1, 1)
        end_period = enddate if year == enddate.year else date(year, 12, 31)

        year_first_tuple_day = date(year, *start_tuple)
        year_last_tuple_day = date(year, *end_tuple)

        if (start_period.month >3*trimestre) or (end_period.month < (1+3*(trimestre-1))):
            dias_trimestre+=0
        else:
            dias_trimestre+=(min(year_last_tuple_day, end_period) - max(year_first_tuple_day, start_period)).days
    
    return dias_trimestre/(enddate-startdate).days

def cambiar_formatos_de_variables(df):

    #Mapear ancho y media de rangos semilla
    dict_media_rango_semilla = {'CM COLINO MEDIO ENTRE 300-500 G':400,'CG COLINO GRANDE ENTRE 501-700 G':600,
'RANGO 1 ( DE 300 A 700)':500,'RANGO 2 (DE 701 A 1000':850,'RANGO 3 (DE 1001 A 1500)':1250,'R-1 (DE 250 A 550)':400,
 'R-2 (DE 551 A 900)':725,'RANG. 1 (DE 400 A 600)':500,'RANG. 2 (DE 601 A 900)':750,'RG. 1 (250 A 600)':425,
 'R-3 ( DE 901 A 1500)':1200,'RANGO 2 (RAIZ)':700,'R.2 (601-900)':750,'R.3 (901-1200)':1050,'R.1 (450-600)':525,
 'R.0 (250-450)':350,'R3: (601-900)':750,'R2: (451-600)':525,'R:4 (901-1200)':1050,'R1: (250-450)':350}

    dict_ancho_rango_semilla = {'CM COLINO MEDIO ENTRE 300-500 G':200,'CG COLINO GRANDE ENTRE 501-700 G':200,
    'RANGO 1 ( DE 300 A 700)':400,'RANGO 2 (DE 701 A 1000':300,'RANGO 3 (DE 1001 A 1500)':500,'R-1 (DE 250 A 550)':300,
    'R-2 (DE 551 A 900)':350,'RANG. 1 (DE 400 A 600)':200,'RANG. 2 (DE 601 A 900)':300,'RG. 1 (250 A 600)':350,
    'R-3 ( DE 901 A 1500)':600,'RANGO 2 (RAIZ)':200,'R.2 (601-900)':300,'R.3 (901-1200)':300,'R.1 (450-600)':150,
    'R.0 (250-450)':200,'R3: (601-900)':300,'R2: (451-600)':150,'R:4 (901-1200)':300,'R1: (250-450)':200}

    df["media_rango_semilla"]=df.rango_semilla.map(dict_media_rango_semilla)
    df["ancho_rango_semilla"]=df.rango_semilla.map(dict_ancho_rango_semilla)

    #Cálculo de edades
    df["fecha_siembra"] =  pd.to_datetime(df['fecha_siembra'], format='%Y-%m-%d')
    df["mean_fecha_cosecha"] = pd.to_datetime(df['mean_fecha_cosecha'], format='%Y-%m-%d')
    df["finduccion"] = pd.to_datetime(df['finduccion'], format='%Y-%m-%d')
    df["edad_forza"]=(df["finduccion"] - df["fecha_siembra"]).dt.days/30
    df["edad_cosecha"]=(df["mean_fecha_cosecha"]-df["finduccion"]).dt.days/30
    df["fecha_siembra_pc"] =  pd.to_datetime(df['fecha_siembra_pc'], format='%Y-%m-%d')
    df["edad_inicio_sc"]=(df["fecha_siembra"]-df["fecha_siembra_pc"]).dt.days/30

    return df.copy()


def crear_variables_de_proporciones_trimestrales(df):
    #Debo considerar hacer las variables de proporcion_preforza corrigiendo aquellos bloques con edad de forza mayor a 1 año

    df["proporcion_posforza_t1"] = df.apply(lambda row: proporcion_dias_trimestre(row["finduccion"].date(),
    row["mean_fecha_cosecha"].date(),1),axis=1)
    #Se omiten proporcion_porforza t2 y t3 por la correlación con los otros trimestres
    df["proporcion_posforza_t4"] = df.apply(lambda row: proporcion_dias_trimestre(row["finduccion"].date(),
    row["mean_fecha_cosecha"].date(),4),axis=1)

    return df

def quitar_variables_restantes(df):
    #Este método debe retornar la tupla
    df_dropped = df.drop(["fecha_siembra","finduccion","mean_fecha_cosecha","rango_semilla","fecha_siembra_pc"],axis=1).copy()
    df_pc = df_dropped.query("desarrollo=='PC'").drop(["productividad_pc","recuperacion_pc","edad_inicio_sc"],axis=1)
    df_sc= df_dropped.query("desarrollo=='SC'").drop(["dias_hasta_siembra_grupo"],axis=1)

    return df_pc,df_sc

def aplicar_pipeline(df):
    desarrollos = df.desarrollo.unique()

    for desarrollo in desarrollos:
        if desarrollo not in ['PC','SC']:
            raise NameError (f"El dataframe tiene un desarrollo incorrecto:{desarrollo}")

    df1 = seleccionar_variables (df)
    print("Variables seleccionadas correctamente")
    df2 = cambiar_formatos_de_variables (df1)
    print("formatos ajustados correctamente")
    df3 = crear_variables_de_proporciones_trimestrales (df2)
    print("Variables de invierno/verano creadas correctamente")
    df_pc,df_sc = quitar_variables_restantes (df3)
    print("Variables sobrantes eliminadas correctamente")
    return df_pc,df_sc 




