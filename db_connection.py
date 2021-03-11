
import psycopg2
import credentials as cred
import pandas as pd

def crear_nueva_conexion():
    
    return  psycopg2.connect(user=cred.user,
                                password=cred.password,
                                host=cred.host,
                                port=cred.port,
                                database=cred.database,
                                sslmode=cred.sslmode,
                                connect_timeout=cred.connect_timeout,
                                sslrootcert = cred.sslrootcert)


#Aquí hacer la función que abre y cierra conexión y que escriba el log

def query(consulta,params=None):
    try:
        conn = crear_nueva_conexion()
        data = pd.read_sql_query(sql = consulta,con = conn, params=params)
        
    except Exception as e:
        print(e)
        conn.rollback()
        return pd.DataFrame({"hubo":["error"],"un":["grave"]})
    else:
        conn.commit()
        return data
    finally:
        conn.close()
    
def execute(consulta):
    try:
        conn = crear_nueva_conexion()
        cur = conn.cursor()
        cur.execute(consulta)

    except Exception as e:
        print(e)
        conn.rollback()
    else:
        conn.commit()
        print("instrucción ejecutada correctamente")
    finally:
        conn.close()


    