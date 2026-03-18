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

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def limpiar_texto_abc(texto):
    if not texto:
        return ""
    texto = str(texto).strip().upper()
    
    # 1. Pre-limpieza del Efecto Cañuelas (caracteres rotos del ABC)
    # Atrapa CA#UELAS, CAUELAS, CA UELAS, y CAÑUELAS
    texto = re.sub(r'CA[^A-Z0-9]?UELAS', 'CANUELAS', texto)
    texto = texto.replace("CAÑUELAS", "CANUELAS")
    
    # 2. Descompone los caracteres especiales (ej: á -> a + ´)
    texto = unicodedata.normalize('NFD', texto)
    
    # 3. Codifica a ASCII ignorando los caracteres extraños (las tildes sueltas)
    texto = texto.encode('ascii', 'ignore').decode("utf-8")
    
    # 4. Excepciones Estrictas del ABC
    if texto == "9 DE JULIO":
        texto = "N DE JULIO"
    elif "JOSE C" in texto and "PAZ" in texto:
        texto = "JOSE C PAZ"

    # 5. Limpieza general de puntos y caracteres especiales que puedan fallar
    texto = texto.replace(".", " ").replace(",", " ")
    
    # 6. Remover múltiples espacios
    texto = re.sub(r'\s+', ' ', texto).strip()

    # 7. Post-limpieza: Restaurar la Ñ de Cañuelas como estándar absoluto para la DB
    texto = texto.replace("CANUELAS", "CAÑUELAS")

    return texto

def coincide_distrito(buscado, leido):
    if not buscado or not leido:
        return False
        
    buscado_norm = limpiar_texto_abc(buscado)
    leido_norm = limpiar_texto_abc(leido)
    
    # Expansión de prefijos/abreviaturas seguras multiletra
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
        # 1. Expandimos si está en nuestro diccionario seguro
        if p in expansiones:
            p = expansiones[p]
            
        # 2. Descartar palabras de 1 o 2 caracteres (elimina L., T., V., DE, LA, EL...)
        if len(p) > 2:
            palabras_clave_buscado.append(p)
            
    # Fallback si por alguna razón purgaron todo 
    # (ej: todas las palabras del distrito tenían <= 2 letras)
    if not palabras_clave_buscado:
        palabras_clave_buscado = palabras_buscado
        
    palabras_leido = leido_norm.split()
    texto_leido_completo = " " + " ".join(palabras_leido) + " "
    
    # Verificamos que todas las palabras clave estén presentes en lo leído 
    # (ya sea como palabra aislada o subcadena)
    for clave in palabras_clave_buscado:
        if clave not in palabras_leido and clave not in texto_leido_completo:
            return False
            
    return True


from datetime import datetime, timedelta

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
    """
    Se conecta a la planilla 'DB_Lector_ABC' y lee la hoja 'Respuestas de formulario 1'.
    Retorna (usuarios_validos, usuarios_vencidos) para manejar el modelo Freemium.
    """
    try:
        # Lógica de Seguridad: Primero la Nube, luego el archivo Local
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

        # --- Leer Pagos_MP para fechas de vencimiento ---
        ultimos_pagos = {}
        try:
            sheet_pagos = db_lector.worksheet("Pagos_MP")
            pagos_records = sheet_pagos.get_all_values()
            for row in pagos_records:
                if len(row) >= 2:
                    fecha_str, email_pago = row[0], row[1].strip().lower()
                    fecha_obj = parsear_fecha(fecha_str)
                    if fecha_obj:
                        if email_pago not in ultimos_pagos or fecha_obj > ultimos_pagos[email_pago]:
                            ultimos_pagos[email_pago] = fecha_obj
        except Exception as e:
            print(f"[GOOGLE SHEETS] No se pudo leer Pagos_MP o está vacía: {e}")

        if not registros:
            print("[GOOGLE SHEETS] La hoja está vacía o no tiene registros.")
            return [], []

        # --- Mapeo flexible de encabezados ---
        encabezados = list(registros[0].keys())
        col_nombre    = None
        col_email     = None
        col_estado    = None
        col_pago      = None
        col_plan      = None
        col_materias  = None
        cols_distritos = []

        for enc in encabezados:
            enc_lower = enc.lower().strip()
            if "nombre" in enc_lower and col_nombre is None:
                col_nombre = enc
            elif "email" in enc_lower and col_email is None:
                col_email = enc
            elif "estado de pago" in enc_lower and col_pago is None:
                col_pago = enc
            elif "plan" in enc_lower and col_plan is None:
                col_plan = enc
            elif "estado" in enc_lower and "pago" not in enc_lower and col_estado is None:
                col_estado = enc
            elif ("código" in enc_lower or "codigo" in enc_lower or "materias" in enc_lower) and col_materias is None:
                col_materias = enc
            elif "distrito" in enc_lower:
                cols_distritos.append(enc)

        # --- Agrupar filas por email de forma cronológica ---
        historial_usuarios = {}

        for reg in registros:
            email = str(reg.get(col_email, "")).strip().lower()
            if not email:
                continue

            nombre = str(reg.get(col_nombre, "")).strip() if col_nombre else ""
            estado_raw = str(reg.get(col_estado, "")).strip() if col_estado else ""
            pago_raw = str(reg.get(col_pago, "")).strip() if col_pago else ""
            plan_raw = str(reg.get(col_plan, "")).strip() if col_plan else "Premium" # Por defecto asumimos Premium si no existía la columna antes
            materias_str = str(reg.get(col_materias, "")).strip() if col_materias else ""

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

            historial_usuarios[email] = {
                "nombre": nombre if nombre else "Colega",
                "email": email,
                "estado_raw": estado_raw,
                "pago_raw": pago_raw,
                "plan_raw": plan_raw,
                "distritos": distritos,
                "materias": materias
            }

        # --- Filtros FREEMIUM ---
        usuarios = []
        usuarios_vencidos = []
        fecha_evaluacion = datetime.now()

        for email, datos in historial_usuarios.items():
            estado_val = datos["estado_raw"].lower()
            pago_val = datos["pago_raw"].upper()
            plan_val = datos["plan_raw"].title()

            # 1. Que el Estado NO sea 'baja'
            if estado_val == "baja":
                continue

            es_desarrollador = (pago_val == "DESARROLLADOR" or estado_val == "desarrollador")
            es_pagado = (pago_val == "PAGADO")
            
            # --- EVALUACIÓN DE VENCIMIENTO PREMIUM ---
            # Si pasaron más de 30 días del último pago en Pagos_MP, el estado de pago pasa a PENDIENTE
            ultimo_pago = ultimos_pagos.get(email)
            if plan_val == "Premium" and not es_desarrollador:
                if ultimo_pago and (fecha_evaluacion - ultimo_pago).days > 30:
                    es_pagado = False
                    pago_val = "PENDIENTE"
                    usuarios_vencidos.append(datos) # Notificaremos su caída a Gratis

            # Definir Acceso
            acceso_total = es_desarrollador or (plan_val == "Premium" and es_pagado)
            
            # Si NO tiene acceso total, recortamos a PLAN GRATIS (1 distrito, 1 materia)
            if not acceso_total:
                # Si dice PENDIENTE y su plan NO es Gratis, igual lo procesamos como Gratis (modo caída/vencido)
                datos["distritos"] = [datos["distritos"][0]] if datos["distritos"] else []
                datos["materias"]  = [datos["materias"][0]] if datos["materias"] else []
                
            # Validar que le quede algo
            if not datos["distritos"] or not datos["materias"]:
                continue

            usuarios.append({
                "nombre":   datos["nombre"],
                "email":    datos["email"],
                "distritos": datos["distritos"],
                "materias":  datos["materias"],
            })

        print(f"[GOOGLE SHEETS] Obtenidos {len(usuarios)} usuarios válidos tras procesar Freemium.")
        return usuarios, usuarios_vencidos

    except Exception as e:
        print(f"[GOOGLE SHEETS ERROR] Error al intentar leer DB_Lector_ABC: {e}")
        return [], []
