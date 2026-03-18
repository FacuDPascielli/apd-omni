"""
Lógica para buscar ofertas en el portal ABC, extraer la tabla y aplicar los filtros comerciales.
"""
from playwright.sync_api import Page
import re
from auth import login_abc
from database_google import coincide_distrito, limpiar_texto_abc

APD_URL = "https://misservicios.abc.gob.ar/actos.publicos.digitales/"

def limpiar_modales(page: Page):
    print("\n[MODAL] Revisando / Limpiando pop-ups modales activos...")
    try:
        # 1. Pulsación de Tecla (Escape)
        print("[MODAL] Intentando cerrar modales con la tecla Escape...")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        
        # 2. Clic fuera del modal (coordenada 0,0)
        print("[MODAL] Simulando clic en el fondo de la pantalla (0,0)...")
        page.mouse.click(0, 0)
        page.wait_for_timeout(500)

        # 3. Búsqueda flexible de la 'X'
        for iteracion in range(2):
            try:
                boton_cerrar = page.locator("button.close, [aria-label='Close'], button:has-text('×'), button.btn-close").locator("visible=true").first
                boton_cerrar.wait_for(timeout=2000)
                boton_cerrar.click(force=True)
                print(f"[MODAL] Pop-up modal (iter {iteracion+1}) cerrado con botón X.")
                page.wait_for_timeout(1000)
            except Exception:
                break
    except Exception as e:
        print(f"[MODAL] Error ignorado limpiando modales: {e}")
        
    print("[MODAL] Limpieza de modales completada u omitida.")

def gestionar_estado_sesion(page: Page):
    """
    State Machine dinámica para manejar las redirecciones del portal ABC.
    Retorna la Page activa (nueva pestaña si aplica) o None si falló críticamente.
    """
    print("\n[ESTADOS] Navegando a Actos Públicos Digitales (APD)...")
    page.goto("https://misservicios.abc.gob.ar/actos.publicos.digitales/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(4000)
    
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        print(f"\n[ESTADOS] Evaluando Estado Actual del DOM (Intento {intentos + 1}/{max_intentos})...")
        
        # 1. ESTADO A: Pantalla de Login (mis.abc.gob.ar)
        es_login = page.locator("input[type='password'], input[type='email'], input[placeholder*='CUIL'], #Ecom_Password").locator("visible=true").count() > 0 or page.locator("text='CUIL o cuenta'").locator("visible=true").count() > 0
        
        # 2. ESTADO B/C: Pantalla APD Pública o Logueada
        es_apd_publico = page.locator("a, button", has_text=re.compile(r"Iniciar sesi.n", re.IGNORECASE)).locator("visible=true").count() > 0
        es_apd_logueado = page.locator("a, button", has_text=re.compile(r"Postularse", re.IGNORECASE)).locator("visible=true").count() > 0
        
        if es_login:
            print("[ESTADOS] -> Detectado ESTADO A (Pantalla de Login Centralizado).")
            print("[ESTADOS] Omitiendo limpieza de modales. Procediendo a inyectar credenciales...")
            login_abc(page)
            print("[ESTADOS] Credenciales inyectadas, esperando volver a APD...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(4000)
            intentos += 1
            continue
            
        elif es_apd_publico:
            print("[ESTADOS] -> Detectado ESTADO B (APD Vista Pública).")
            limpiar_modales(page)
            print("[ESTADOS] Clickeando en 'Iniciar Sesión ABC'...")
            btn_iniciar_sesion = page.locator("a, button", has_text=re.compile(r"Iniciar sesi.n", re.IGNORECASE)).locator("visible=true").first
            btn_iniciar_sesion.click(force=True)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            intentos += 1
            continue
            
        elif es_apd_logueado:
            print("[ESTADOS] -> Detectado ESTADO C (APD Logueado).")
            limpiar_modales(page)
            
            print("[ESTADOS] Clickeando 'Postularse' (target=_blank → esperando nueva pestaña)...")
            try:
                btn_postularse = page.locator("a, button", has_text=re.compile(r"Postularse", re.IGNORECASE)).locator("visible=true").first
                
                with page.context.expect_page(timeout=10000) as nueva_pagina_info:
                    btn_postularse.click(force=True)
                
                nueva_pagina = nueva_pagina_info.value
                nueva_pagina.wait_for_load_state("networkidle")
                nueva_pagina.wait_for_timeout(5000)
                
                url_nueva = nueva_pagina.url
                print(f"[ESTADOS] URL de la nueva pestaña: {url_nueva}")
                
                print("[ESTADOS] Cerrando pestaña original (dashboard)...")
                page.close()
                
                if "postulacionAPD" in url_nueva or "ofertas" in url_nueva:
                    print("[ESTADOS] ✓ Nueva pestaña es la vista de postulaciones. Continuando en ella.")
                    return nueva_pagina
                else:
                    print(f"[ESTADOS] ⚠ URL inesperada en nueva pestaña: {url_nueva}")
                    intentos += 1
                    page = nueva_pagina
                    continue
                    
            except Exception as e:
                print(f"[ESTADOS] No se abrió nueva pestaña (quizás misma pestaña): {type(e).__name__}. Verificando URL actual...")
                try:
                    btn_postularse = page.locator("a, button", has_text=re.compile(r"Postularse", re.IGNORECASE)).locator("visible=true").first
                    btn_postularse.click(force=True)
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(3000)
                    url_actual = page.url
                    print(f"[ESTADOS] URL tras clic simple: {url_actual}")
                    if "postulacionAPD" in url_actual or "ofertas" in url_actual:
                        print("[ESTADOS] ✓ Misma pestaña redirigida a postulaciones.")
                        return page
                except Exception as e2:
                    print(f"[ERROR] Fallo total al navegar a Postularse: {e2}")
                return None
                
        else:
            print("[ESTADOS] -> ESTADO DESCONOCIDO. Forzando recarga...")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            intentos += 1
            
    print("[ERROR CRÍTICO] No se logró llegar al ESTADO C tras múltiples intentos.")
    return None

def _navegar_a_ofertas(page: Page) -> Page:
    """
    Reseteo seguro entre distritos: vuelve al dashboard y reabre la sección
    de Postularse, manejando la nueva pestaña y cerrando la vieja.
    Retorna la Page activa (la de ofertas).
    """
    print("[NAV] Reseteando: volviendo al Dashboard APD...")
    try:
        page.goto(APD_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        limpiar_modales(page)
        
        btn = page.locator("a, button", has_text=re.compile(r"Postularse", re.IGNORECASE)).locator("visible=true").first
        
        try:
            with page.context.expect_page(timeout=8000) as nueva_pagina_info:
                btn.click(force=True)
            nueva_pagina = nueva_pagina_info.value
            nueva_pagina.wait_for_load_state("networkidle")
            nueva_pagina.wait_for_timeout(4000)
            print(f"[NAV] Nueva pestaña de ofertas: {nueva_pagina.url}")
            page.close()
            return nueva_pagina
        except Exception:
            btn.click(force=True)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            print(f"[NAV] Misma pestaña redirigida a: {page.url}")
            return page
    except Exception as e:
        print(f"[NAV] Error en reseteo seguro: {e}")
        return page

def extraer_todas_paginas(page: Page) -> list:
    ofertas_extraidas = []
    pagina_actual = 1
    intentos_sin_avance = 0
    MAX_INTENTOS_SIN_AVANCE = 3

    while True:
        print(f"\n[SCRAPER] --- Extrayendo Página {pagina_actual} ---")
        try:
            snapshot_antes = page.locator(".card").first.evaluate("node => node.innerText") if page.locator(".card").count() > 0 else ""
        except Exception:
            snapshot_antes = ""

        tarjetas = page.locator(".card").all()
        print(f"[SCRAPER] Total bruto de tarjetas extraídas en página {pagina_actual}: {len(tarjetas)}")

        for i, t in enumerate(tarjetas):
            try:
                # Usamos evaluate en vez de text_content para conservar los saltos de línea vitales (\n)
                # sin sufrir el Timeout de 30s que tenía inner_text() en Playwright
                texto_tarjeta = t.evaluate("node => node.innerText")
                if not texto_tarjeta:
                    continue
                    
                texto_upper = texto_tarjeta.upper()

                # Buscar código en paréntesis ej (FIA)
                match_codigo = re.search(r'\(([A-Z0-9\/\+\-]+)\)', texto_upper)
                codigo_area = match_codigo.group(1).strip() if match_codigo else "DESCONOCIDO"
                if codigo_area != "DESCONOCIDO":
                    codigo_area = limpiar_texto_abc(codigo_area)

                # IGE
                match_ige = re.search(r'#(?:IGE)?\s*(\d+)', texto_upper)
                if not match_ige:
                    match_ige = re.search(r'IGE\s*:\s*(\d+)', texto_upper)
                ige = match_ige.group(1) if match_ige else "SinIGE"

                # Distrito: Extraer de "DISTRITO: <valor>" para evitar domicilios
                match_distrito = re.search(r'DISTRITO\s*:\s*([^\n]+)', texto_upper)
                distrito_tarjeta = match_distrito.group(1).strip() if match_distrito else "DESCONOCIDO"
                if distrito_tarjeta != "DESCONOCIDO":
                    distrito_tarjeta = limpiar_texto_abc(distrito_tarjeta)

                # Limpieza de líneas
                lineas = [line.strip() for line in texto_tarjeta.split('\n') if line.strip()]
                
                # --- EXTRACCIÓN QUIRÚRGICA ---
                
                # Encabezado Garantizado: Únicamente Sigla Limpia — Distrito Limpio (Ej: CCD — AVELLANEDA)
                encabezado_estricto = f"{codigo_area} — {distrito_tarjeta}"

                escuela_linea = next((l for l in lineas if 'ESCUELA' in l.upper()), "")
                escuela = escuela_linea.split(':', 1)[-1].strip() if escuela_linea else "Ver en Portal"

                nivel_linea = next((l for l in lineas if 'NIVEL' in l.upper()), "")
                nivel = nivel_linea.split(':', 1)[-1].strip() if nivel_linea else "Ver en Portal"

                # Horarios
                DIAS = ['LUNES', 'MARTES', 'MIÉRCOLES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'SABADO']
                lineas_horario = [
                    l for l in lineas
                    if any(dia in l.upper() for dia in DIAS)
                ]
                horarios = " | ".join(lineas_horario) if lineas_horario else "Ver en Portal"

                # Observaciones
                match_obs = re.search(r'observaciones\s*:?\s*([^\n]+)', texto_tarjeta, re.IGNORECASE)
                observaciones = match_obs.group(1).strip() if match_obs and match_obs.group(1).strip() else "-"

                if not observaciones or "POSTULARSE" in observaciones.upper():
                    observaciones = "-"

                print(f"  -> [EXTRACCIÓN] {encabezado_estricto} | IGE: {ige} | Nivel: {nivel} (Pág: {pagina_actual})")

                ofertas_extraidas.append({
                    "id": f"IGE_{ige}_{distrito_tarjeta.replace(' ', '_')}",
                    "encabezado": encabezado_estricto,
                    "ige": ige,
                    "codigo_area": codigo_area,
                    "distrito": distrito_tarjeta,
                    "nivel": nivel,
                    "escuela": escuela,
                    "horarios": horarios,
                    "observaciones": observaciones,
                    "texto_completo": texto_tarjeta,
                    "pagina_actual": pagina_actual
                })
            except Exception as loop_e:
                print(f"  -> [ERROR] Fallo al procesar la tarjeta índice {i} ({loop_e}). Saltando...")
                continue

        # PAGINACIÓN
        try:
            contenedor_siguiente = page.locator('li.page-item.der').first
            btn_siguiente = page.locator('li.page-item.der a[aria-label="Next"]').first

            if not contenedor_siguiente.is_visible() or not btn_siguiente.is_visible():
                print(f"[SCRAPER] No se detectó paginación o botón Siguiente en la página {pagina_actual}. Fin de extracciones.")
                break

            class_attribute = contenedor_siguiente.get_attribute("class") or ""
            if "disabled" in class_attribute:
                print(f"[SCRAPER] Botón 'Siguiente' está deshabilitado en página {pagina_actual}. Llegamos al final.")
                break

            print(f"[SCRAPER] Botón 'Siguiente' habilitado. Navegando a la página {pagina_actual + 1}...")
            btn_siguiente.click(force=True)
            pagina_actual += 1

            page.wait_for_timeout(3000)
            try:
                page.wait_for_selector(".card", timeout=10000)
            except Exception:
                pass

            # Guardia de movimiento
            try:
                snapshot_despues = page.locator(".card").first.evaluate("node => node.innerText") if page.locator(".card").count() > 0 else ""
            except Exception:
                snapshot_despues = ""

            if snapshot_despues and snapshot_despues == snapshot_antes:
                intentos_sin_avance += 1
                print(f"[SCRAPER] ⚠ La página NO cambió tras clic en Siguiente (intento {intentos_sin_avance}/{MAX_INTENTOS_SIN_AVANCE}).")
                if intentos_sin_avance >= MAX_INTENTOS_SIN_AVANCE:
                    print(f"[SCRAPER] ✋ {MAX_INTENTOS_SIN_AVANCE} intentos sin avance. Forzando salida.")
                    break
            else:
                intentos_sin_avance = 0

        except Exception as eval_err:
            print(f"[SCRAPER] Error evaluando botón 'Siguiente': {eval_err}. Asumiendo fin del escaneo por esta tanda.")
            break

    return ofertas_extraidas


def scrape_ofertas(page: Page):
    """
    Inicia el Cosechador Masivo: extrae absolutamente todas las ofertas listadas en el portal publicamente.
    Itera automáticamente a través de todas las páginas de paginación disponibles.
    No aplica filtros previos por UI. La purga y el filtrado se hace en Base de Datos.
    """
    page_activa = gestionar_estado_sesion(page)
    if page_activa is None:
        print("Abortando extracción de ofertas por fallo en la sesión/navegación.")
        return []
    
    page = page_activa
    print(f"[SCRAPER] URL activa para scraping: {page.url}")

    try:
        page.wait_for_selector("text='Para Desempe'", timeout=5000)
        print("[SCRAPER] ✓ Título de la sección de postulaciones confirmado.")
    except Exception:
        print("[SCRAPER] Advertencia: título de la sección no detectado (continuando de todas formas).")

    print("\n[BARRIDO TOTAL] Extrayendo TODAS las ofertas de la provincia...")
    ofertas_provinciales = extraer_todas_paginas(page)

    print(f"[SCRAPER] Fin total de barrido. Extracciones enviadas a orquestador: {len(ofertas_provinciales)}")
    return ofertas_provinciales

