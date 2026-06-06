import os
import random
from datetime import datetime
from faker import Faker
from pymongo import MongoClient
from bson.objectid import ObjectId

def ejecutar_ingesta():
    # 1. CONFIGURACIÓN DE CONEXIÓN
    # Lee directamente de las variables de entorno del clúster de Databricks
    MONGO_URL = os.environ.get("MONGO_URL")
    DB_NAME = os.environ.get("DB_NAME", "cac_valleverde")

    if not MONGO_URL:
        raise ValueError("Error: La variable de entorno MONGO_URL no está configurada en Databricks.")

    try:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        col_agricultores = db['agricultores']
        col_acopios = db['acopios']
        
        print(f"Conectado exitosamente a la base de datos: {DB_NAME}")
        
    except Exception as e:
        print(f"Error conectando a MongoDB Atlas: {e}")
        return

    fake = Faker()

    # 2. GESTIÓN DE AGRICULTORES (Evitar duplicados masivos)
    agricultores_existentes = list(col_agricultores.find())
    
    # Si la base de datos es nueva, creamos 5 agricultores semilla
    if len(agricultores_existentes) == 0:
        print("No se encontraron agricultores. Generando 5 perfiles semilla...")
        tipos_cacao = ["CCN51", "Criollo", "Trinitario", "Forastero"]
        sectores = ["Alto Saposoa", "Bellavista", "Juanjui", "Huicungo", "Pachiza"]
        certificaciones_posibles = [["Orgánico"], ["Fair Trade"], ["Orgánico", "Fair Trade"], []]

        for i in range(5):
            agricultor = {
                "_id": str(ObjectId()),
                "agricultor_id": f"agr_{random.randint(1000, 9999)}",
                "nombre_completo": fake.name(),
                "dni_ruc": str(random.randint(40000000, 79999999)),
                "codigo_productor": f"VALLE-VERDE-{100+i}",
                "sector_comunidad": random.choice(sectores),
                "tipo_cacao": random.choice(tipos_cacao),
                "certificaciones": random.choice(certificaciones_posibles)
            }
            agricultores_existentes.append(agricultor)
            
        col_agricultores.insert_many(agricultores_existentes)
        print("✅ Agricultores semilla insertados.")

    # 3. GENERACIÓN DE ACOPIOS EN TIEMPO REAL (25 Registros)
    print("Generando 25 registros de acopio en tiempo real...")
    lista_acopios = []
    precio_base_mercado = 12.00 

    for i in range(25):
        agric_elegido = random.choice(agricultores_existentes)
        # ESTO ES CLAVE: Usamos la hora exacta de la ejecución para simular el tiempo real
        fecha_actual = datetime.now() 
        
        cantidad_sacos = random.randint(1, 8)
        detalle_sacos = []
        peso_bruto_total = 0.0
        tara_saco_unitaria = 0.5
        
        for n in range(cantidad_sacos):
            peso_saco = round(random.uniform(45.0, 65.0), 2)
            detalle_sacos.append({
                "nro_saco": n + 1,
                "peso_bruto_kg": peso_saco
            })
            peso_bruto_total += peso_saco
            
        tara_total = cantidad_sacos * tara_saco_unitaria
        peso_neto_total = round(peso_bruto_total - tara_total, 2)
        peso_bruto_total = round(peso_bruto_total, 2)

        humedad = round(random.uniform(6.0, 10.0), 1)
        impurezas = round(random.uniform(0.5, 3.0), 1)
        
        estado = "Aprobado"
        if humedad > 8.0:
            estado = "Observado (Requiere secado)"
            
        bono_cert = 1.50 if "Orgánico" in agric_elegido.get("certificaciones", []) else 0.0
        descuento_hum = 0.50 if humedad > 8.0 else 0.0
        
        precio_final = precio_base_mercado + bono_cert - descuento_hum
        monto_total = round(peso_neto_total * precio_final, 2)
        
        acopio = {
            "codigo_ticket": f"TK-JOB-{fecha_actual.strftime('%Y%m%d%H%M%S')}-{str(i+1).zfill(2)}",
            "fecha_registro": fecha_actual,
            "operario_id": f"usr_op_{random.randint(1, 3)}",
            "agricultor": {
                "agricultor_id": agric_elegido.get("agricultor_id"),
                "nombre_completo": agric_elegido.get("nombre_completo"),
                "dni_ruc": agric_elegido.get("dni_ruc"),
                "codigo_productor": agric_elegido.get("codigo_productor"),
                "certificaciones": agric_elegido.get("certificaciones"),
                "sector_comunidad": agric_elegido.get("sector_comunidad"),
                "tipo_cacao": agric_elegido.get("tipo_cacao")
            },
            "datos_pesaje": {
                "cantidad_sacos": cantidad_sacos,
                "detalle_sacos": detalle_sacos,
                "peso_bruto_total_kg": peso_bruto_total,
                "tara_total_kg": tara_total,
                "peso_neto_total_kg": peso_neto_total
            },
            "control_calidad": {
                "porcentaje_humedad": humedad,
                "porcentaje_impurezas": impurezas,
                "grado_fermentacion": random.choice(["Tipo 1 (Premium)", "Tipo 2 (Estándar)"]),
                "estado_lote": estado
            },
            "valores_comerciales": {
                "precio_base_por_kilo": precio_base_mercado,
                "bonificacion_certificacion": bono_cert,
                "descuento_humedad": descuento_hum,
                "precio_final_por_kilo": precio_final,
                "monto_total_pagar": monto_total
            },
            "trazabilidad": {
                "codigo_lote_exportacion": f"LOTE-EXP-{fecha_actual.strftime('%Y%m%d')}-{random.randint(1,5)}",
                "ubicacion_almacen": random.choice(["ZONA-A-SECO", "ZONA-B-SECADO", "ZONA-C-CUARENTENA"])
            },
            "metadata_sistema": {
                "dispositivo_registro": "Databricks-AutoJob",
                "estado_pago": "Pendiente",
                "ultima_modificacion": fecha_actual
            }
        }
        lista_acopios.append(acopio)

    col_acopios.insert_many(lista_acopios)
    print(f"✅ Job finalizado: Se insertaron {len(lista_acopios)} nuevos registros de acopio.")
    
    client.close()

# Ejecutar la función principal
if __name__ == "__main__":
    ejecutar_ingesta()