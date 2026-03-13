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

def normalizar_texto(texto):
    if not texto:
        return ""
    texto = str(texto).strip()
    # Descompone los caracteres especiales (ej: á -> a + ´)
    texto = unicodedata.normalize('NFD', texto)
    # Codifica a ASCII ignorando los caracteres extraños (las tildes sueltas)
    texto = texto.encode('ascii', 'ignore').decode("utf-8")
    texto = texto.upper()

    # === Excepciones Estrictas del ABC ===
    if texto == "9 DE JULIO":
        return "N DE JULIO"

    if "JOSE C" in texto and "PAZ" in texto:
        return "JOSE C PAZ"

    # Limpieza general de puntos y caracteres especiales que puedan fallar
    texto = texto.replace(".", " ").replace(",", " ")
    
    # Remover múltiples espacios
    texto = re.sub(r'\s+', ' ', texto).strip()

    return texto

def coincide_distrito(buscado, leido):
    if not buscado or not leido:
        return False
        
    buscado_norm = normalizar_texto(buscado)
    leido_norm = normalizar_texto(leido)
    
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


def obtener_usuarios_desde_sheets():
    """
    Se conecta a la planilla 'DB_Lector_ABC' y lee la hoja 'Respuestas de formulario 1'.
    Usa mapeo flexible: recorre los encabezados buscando palabras clave en lugar de
    nombres exactos, para tolerar los encabezados largos generados por Google Forms.
    """
    try:
        # Lógica de Seguridad: Primero la Nube, luego el archivo Local
        google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        
        if google_creds_json:
            print("[GOOGLE SHEETS] Leyendo credenciales desde variable de entorno (Nube).")
            creds_dict = json.loads(google_creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
        else:
            print("[GOOGLE SHEETS] Variable GOOGLE_CREDENTIALS no encontrada, buscando archivo credentials.json (Local).")
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPES)

        client = gspread.authorize(creds)
        sheet = client.open("DB_Lector_ABC").worksheet("Respuestas de formulario 1")

        # get_all_records() asume que la primera fila tiene los encabezados
        registros = sheet.get_all_records()

        if not registros:
            print("[GOOGLE SHEETS] La hoja está vacía o no tiene registros.")
            return []

        # --- Mapeo flexible de encabezados ---
        # Tomamos las claves del primer registro para identificar qué columnas existen.
        encabezados = list(registros[0].keys())
        print(f"[GOOGLE SHEETS] Encabezados detectados: {encabezados}")

        # Para cada categoría, guardamos la(s) clave(s) reales del dict que le corresponden.
        col_nombre    = None
        col_email     = None
        col_estado    = None
        col_materias  = None
        cols_distritos = []  # puede haber varias columnas de distrito

        for enc in encabezados:
            enc_lower = enc.lower()
            if "nombre" in enc_lower and col_nombre is None:
                col_nombre = enc
            elif "email" in enc_lower and col_email is None:
                col_email = enc
            elif "estado" in enc_lower and col_estado is None:
                col_estado = enc
            elif ("código" in enc_lower or "codigo" in enc_lower) and col_materias is None:
                col_materias = enc
            elif "distrito" in enc_lower:
                cols_distritos.append(enc)

        print(f"[GOOGLE SHEETS] Mapa de columnas:")
        print(f"  Nombre   -> '{col_nombre}'")
        print(f"  Email    -> '{col_email}'")
        print(f"  Estado   -> '{col_estado}'")
        print(f"  Materias -> '{col_materias}'")
        print(f"  Distritos -> {cols_distritos}")

        usuarios = []

        for reg in registros:
            # --- Extraer valores usando las claves mapeadas ---
            nombre = str(reg.get(col_nombre, "")).strip() if col_nombre else ""
            nombre = nombre if nombre else "Colega"

            email = str(reg.get(col_email, "")).strip() if col_email else ""

            estado_raw = str(reg.get(col_estado, "")).strip() if col_estado else ""

            materias_str = str(reg.get(col_materias, "")).strip() if col_materias else ""

            # Reunir todos los valores de columnas de distrito
            distritos_crudos = []
            for col_d in cols_distritos:
                val = str(reg.get(col_d, "")).strip()
                if val:
                    distritos_crudos.append(val)

            # --- Filtros de seguridad ---

            # 1. Saltamos si no hay email
            if not email:
                continue

            # 2. Solo procesamos usuarios ACTIVOS
            if estado_raw.strip().upper() != "ACTIVO":
                continue

            # --- Normalización ---
            distritos = [normalizar_texto(d) for d in distritos_crudos if d.strip()]
            materias  = [normalizar_texto(m) for m in materias_str.split(",") if m.strip()]

            # 3. Necesitamos al menos un distrito y una materia
            if not distritos or not materias:
                continue

            usuarios.append({
                "nombre":   nombre,
                "email":    email,
                "distritos": distritos,
                "materias":  materias,
            })

        print(f"[GOOGLE SHEETS] Se obtuvieron {len(usuarios)} usuarios con estado ACTIVO correctamente.")
        return usuarios

    except Exception as e:
        print(f"[GOOGLE SHEETS ERROR] Ocurrió un error al intentar leer DB_Lector_ABC: {e}")
        return []
