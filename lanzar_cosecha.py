import os
import sys
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    if not os.environ.get("ABC_USUARIO") or not os.environ.get("ABC_CLAVE"):
        print("ERROR: Faltan credenciales ABC_USUARIO y ABC_CLAVE en el .env")
        sys.exit(1)
        
    print("\n" + "="*50)
    print("🚀 LANZADOR DE COSECHA MANUAL (Barrido Total)")
    print("="*50)
    print("Iniciando la extracción inicial masiva para poblar ofertas_db.json...")
    
    from main import tarea_cosecha
    tarea_cosecha()
    
    print("\n✅ Cosecha finalizada. Ya puedes probar el buscador local (app.py) con datos reales.")
