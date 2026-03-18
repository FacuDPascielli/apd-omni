"""
Administrador de la base de datos local (JSON) para las ofertas de APD.
Implementa índices invertidos para búsquedas instantáneas por distrito y materia.
"""
import json
import os
from datetime import datetime

DB_FILE = "ofertas_db.json"

def cargar_db():
    if not os.path.exists(DB_FILE):
        return {
            "metadata": {"ultima_actualizacion_barrido": ""},
            "ofertas": {},
            "indices": {
                "distrito": {},
                "materia": {}
            }
        }
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Asegurar estructura básica
            if "ofertas" not in data: data["ofertas"] = {}
            if "indices" not in data: data["indices"] = {"distrito": {}, "materia": {}}
            if "distrito" not in data["indices"]: data["indices"]["distrito"] = {}
            if "materia" not in data["indices"]: data["indices"]["materia"] = {}
            return data
    except Exception as e:
        print(f"[DB] Error cargando {DB_FILE}: {e}. Retornando DB vacía.")
        return {
            "metadata": {"ultima_actualizacion_barrido": ""},
            "ofertas": {},
            "indices": {"distrito": {}, "materia": {}}
        }

def guardar_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[DB] Error guardando {DB_FILE}: {e}")

def regenerar_indices(db):
    """
    Reconstruye los índices desde cero basándose en las ofertas actuales.
    Útil para mantener la consistencia si hay modificaciones manuales o errores.
    """
    indices = {"distrito": {}, "materia": {}}
    
    for oferta_id, datos in db["ofertas"].items():
        if datos.get("estado") != "activa":
            continue
            
        distrito = datos.get("distrito", "").upper()
        materia = datos.get("codigo_area", "").upper()
        
        if distrito:
            if distrito not in indices["distrito"]:
                indices["distrito"][distrito] = []
            indices["distrito"][distrito].append(oferta_id)
            
        if materia:
            if materia not in indices["materia"]:
                indices["materia"][materia] = []
            indices["materia"][materia].append(oferta_id)
            
    db["indices"] = indices

def sincronizar_ofertas(ofertas_scraper):
    """
    Recibe la lista completa del barrido actual.
    Inserta ofertas nuevas, actualiza las existentes, y marca como 'vencidas' las que ya no están.
    """
    db = cargar_db()
    ahora = datetime.now().isoformat()
    db["metadata"]["ultima_actualizacion_barrido"] = ahora
    
    ids_en_barrido_actual = set()
    nuevas = 0
    actualizadas = 0
    
    # Procesar ofertas entrantes
    for o in ofertas_scraper:
        oid = o["id"]
        ids_en_barrido_actual.add(oid)
        
        if oid not in db["ofertas"]:
            # Nueva oferta
            o["estado"] = "activa"
            o["primera_aparicion_pag"] = o.get("pagina_actual", -1)
            o["primera_vez_visto"] = ahora
            o["ultima_vez_visto"] = ahora
            db["ofertas"][oid] = o
            nuevas += 1
        else:
            # Actualizar existente
            db["ofertas"][oid]["ultima_vez_visto"] = ahora
            # Si estaba vencida y volvió a aparecer, reactivarla
            if db["ofertas"][oid].get("estado") == "vencida":
                db["ofertas"][oid]["estado"] = "activa"
                db["ofertas"][oid]["primera_aparicion_pag"] = o.get("pagina_actual", -1)
            actualizadas += 1
            
    # Marcar vencidas
    vencidas = 0
    for oid, datos in db["ofertas"].items():
        if datos.get("estado") == "activa" and oid not in ids_en_barrido_actual:
            db["ofertas"][oid]["estado"] = "vencida"
            vencidas += 1
            
    # Reconstruir índices
    regenerar_indices(db)
    guardar_db(db)
    
    print(f"[DB] Sincronización completada. Nuevas: {nuevas} | Actualizadas: {actualizadas} | Vencidas marcadas: {vencidas}")

def obtener_ofertas_por_filtros(distritos, materias):
    """
    Usa los índices invertidos en memoria para retornar ofertas 'activas'
    que crucen la intersección de Distritos y Materias solicitadas de forma instántanea.
    """
    db = cargar_db()
    
    # 1. Obtener todos los IDs de los distritos
    ids_distritos = set()
    for d in distritos:
        d_upper = d.upper()
        # Buscamos coincidencias flexibles dentro de las claves del índice de distritos
        for dist_key, ids in db["indices"]["distrito"].items():
            from database_google import coincide_distrito
            if coincide_distrito(d_upper, dist_key):
                ids_distritos.update(ids)
                
    if not ids_distritos:
        return []
        
    # 2. Obtener todos los IDs de las materias
    ids_materias = set()
    for m in materias:
        m_upper = m.upper()
        if m_upper in db["indices"]["materia"]:
            ids_materias.update(db["indices"]["materia"][m_upper])
            
    if not ids_materias:
        return []
        
    # 3. Intersección O(1)
    ids_coincidentes = ids_distritos.intersection(ids_materias)
    
    # 4. Recuperar los diccionarios completos
    resultados = []
    for oid in ids_coincidentes:
        oferta = db["ofertas"].get(oid)
        if oferta and oferta.get("estado") == "activa":
            resultados.append(oferta)
            
    return resultados
