"""
Módulo para leer la configuración de usuarios desde Google Sheets.
Usa mapeo flexible de columnas para tolerar los encabezados largos de Google Forms.
"""
import gspread
import unicodedata
import os
import json
import re
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def limpiar_texto_abc(texto):
    if not texto:
        return ""
    texto = str(texto).strip().upper()
    
    texto = re.sub(r'CA[^A-Z0-9]?UELAS', 'CANUELAS', texto)
    texto = texto.replace("CAÑUELAS", "CANUELAS")
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode("utf-8")
    
    if texto == "9 DE JULIO":
        texto = "N DE JULIO"
    elif "JOSE C" in texto and "PAZ" in texto:
        texto = "JOSE C PAZ"

    texto = texto.replace(".", " ").replace(",", " ")
    texto = re.sub(r'\s+', ' ', texto).strip()
    texto = texto.replace("CANUELAS", "CAÑUELAS")

    return texto

def coincide_distrito(buscado, leido):
    if not buscado or not leido:
        return False
        
    buscado_norm = limpiar_texto_abc(buscado)
    leido_norm = limpiar_texto_abc(leido)
    
    expansiones = {
        "ALMTE": "ALMIRANTE",
        "PTE": "PRESIDENTE",
        "GRL": "GENERAL",
        "GRAL": "GENERAL",
        "VTE": "VICENTE",
        "CNEL": "CORONEL",
        "CAP": "CAPITAN"
    }
    
    palabras_buscado = buscado_norm.split()
    palabras_clave_buscado = []
    
    for p in palabras_buscado:
        if p in expansiones:
            p = expansiones[p]
        if len(p) > 2:
            palabras_clave_buscado.append(p)
            
    if not palabras_clave_buscado:
        palabras_clave_buscado = palabras_buscado
        
    palabras_leido = leido_norm.split()
    texto_leido_completo = " " + " ".join(palabras_leido) + " "
    
    for clave in palabras_clave_buscado:
        if clave not in palabras_leido and clave not in texto_leido_completo:
            return False
            
    return True

def parsear_fecha(fecha_str):
    if not fecha_str:
        return None
    formatos = [
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_str.strip(), fmt)
        except ValueError:
            pass
    return None

def obtener_usuarios_desde_sheets():
    try:
        google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        
        if google_creds_json:
            print("[GOOGLE SHEETS] Leyendo credenciales desde variable de entorno (Nube).")
            creds_dict = json.loads(google_creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
        else:
            print("[GOOGLE SHEETS] Variable GOOGLE_CREDENTIALS no encontrada, buscando archivo (Local).")
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPES)

        client = gspread.authorize(creds)
        db_lector = client.open("DB_Lector_ABC")
        
        sheet = db_lector.worksheet("Respuestas de formulario 1")
        registros = sheet.get_all_records()

        if not registros:
            print("[GOOGLE SHEETS] La hoja está vacía o no tiene registros.")
            return [], []

        encabezados = list(registros[0].keys())
        # FIX: Inicializar todas las variables necesarias para prever excepciones de UnbundLocalError
        col_nombre    = None
        col_email     = None
        col_estado    = None
        col_pago      = None
        col_plan      = None
        col_materias  = None
        col_fecha     = None
        col_venc      = None
        cols_distritos = []

        for i, enc in enumerate(encabezados):
            enc_lower = enc.lower().strip()
            if "nombre" in enc_lower and col_nombre is None:
                col_nombre = enc
            elif "email" in enc_lower and col_email is None:
                col_email = enc
            elif "estado de pago" in enc_lower and col_pago is None:
                col_pago = enc
            elif "plan" in enc_lower and col_plan is None:
                col_plan = enc
            elif "vencimiento" in enc_lower and col_venc is None:
                col_venc = enc
            elif "estado" in enc_lower and "pago" not in enc_lower and col_estado is None:
                col_estado = enc
            elif ("código" in enc_lower or "codigo" in enc_lower or "materias" in enc_lower) and col_materias is None:
                col_materias = enc
            elif ("marca" in enc_lower and "temporal" in enc_lower) or ("fecha" in enc_lower and col_fecha is None):
                col_fecha = enc
            elif "distrito" in enc_lower:
                cols_distritos.append(enc)

        # Si no encontramos columna explícita de vencimiento, usamos la Col N (índice 13)
        if not col_venc and len(encabezados) > 13:
            col_venc = encabezados[13]

        historial_usuarios = {}

        for reg in registros:
            email = str(reg.get(col_email, "")).strip().lower()
            if not email:
                continue

            nombre = str(reg.get(col_nombre, "")).strip() if col_nombre else ""
            estado_raw = str(reg.get(col_estado, "")).strip() if col_estado else ""
            pago_raw = str(reg.get(col_pago, "")).strip() if col_pago else ""
            plan_raw = str(reg.get(col_plan, "")).strip() if col_plan else "Premium" # Default para los viejos
            materias_str = str(reg.get(col_materias, "")).strip() if col_materias else ""
            fecha_raw = str(reg.get(col_fecha, "")).strip() if col_fecha else ""
            venc_raw = str(reg.get(col_venc, "")).strip() if col_venc else ""
            
            fecha_registro = parsear_fecha(fecha_raw) if fecha_raw else None
            fecha_vencimiento = parsear_fecha(venc_raw) if venc_raw else None

            distritos_crudos = []
            for col_d in cols_distritos:
                val = str(reg.get(col_d, "")).strip()
                if val:
                    distritos_crudos.append(val)

            distritos = [limpiar_texto_abc(d) for d in distritos_crudos if d.strip()]
            materias  = [limpiar_texto_abc(m) for m in materias_str.split(",") if m.strip()]

            if email in historial_usuarios:
                fila_anterior = historial_usuarios[email]
                if not distritos and fila_anterior['distritos']:
                    distritos = fila_anterior['distritos']
                if not materias and fila_anterior['materias']:
                    materias = fila_anterior['materias']
                if not nombre and fila_anterior['nombre']:
                    nombre = fila_anterior['nombre']
                if not fecha_registro and fila_anterior['fecha_registro']:
                    fecha_registro = fila_anterior['fecha_registro']
                if not fecha_vencimiento and fila_anterior.get('fecha_vencimiento'):
                    fecha_vencimiento = fila_anterior['fecha_vencimiento']

            historial_usuarios[email] = {
                "nombre": nombre if nombre else "Colega",
                "email": email,
                "estado_raw": estado_raw,
                "pago_raw": pago_raw,
                "plan_raw": plan_raw,
                "distritos": distritos,
                "materias": materias,
                "fecha_registro": fecha_registro,
                "fecha_vencimiento": fecha_vencimiento
            }

        usuarios = []
        usuarios_vencidos = []
        fecha_evaluacion = datetime.now()

        for email, datos in historial_usuarios.items():
            estado_val = datos["estado_raw"].lower()
            pago_val = datos["pago_raw"].upper()
            plan_val = datos["plan_raw"].title()

            if estado_val == "baja":
                continue

            es_desarrollador = (pago_val == "DESARROLLADOR" or estado_val == "desarrollador")
            es_pagado = (pago_val == "PAGADO")
            
            # FIX: Evaluacion de caida al plan Gratis puramente a traves de la fecha parseada
            if plan_val == "Premium" and not es_desarrollador:
                if datos["fecha_vencimiento"]:
                    if datos["fecha_vencimiento"] < fecha_evaluacion:
                        es_pagado = False
                        pago_val = "PENDIENTE"
                        usuarios_vencidos.append(datos)
                else:
                    if datos["fecha_registro"] and (fecha_evaluacion - datos["fecha_registro"]).days > 30:
                        es_pagado = False
                        pago_val = "PENDIENTE"
                        usuarios_vencidos.append(datos)

            acceso_total = es_desarrollador or (plan_val == "Premium" and es_pagado)
            
            if not acceso_total:
                datos["distritos"] = [datos["distritos"][0]] if datos["distritos"] else []
                datos["materias"]  = [datos["materias"][0]] if datos["materias"] else []
                
            if not datos["distritos"] or not datos["materias"]:
                continue

            usuarios.append({
                "nombre":   datos["nombre"],
                "email":    datos["email"],
                "distritos": datos["distritos"],
                "materias":  datos["materias"],
                "fecha_registro": datos["fecha_registro"]
            })

        print(f"[GOOGLE SHEETS] Obtenidos {len(usuarios)} usuarios válidos tras procesar Freemium.")
        return usuarios, usuarios_vencidos

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[GOOGLE SHEETS ERROR] Error al intentar leer DB_Lector_ABC: {e}")
        return [], []
