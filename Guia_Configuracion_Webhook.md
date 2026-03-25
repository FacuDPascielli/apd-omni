# Guía de Configuración Webhook Mercado Pago 🚀

Esta guía detalla los pasos exactos para conectar tu frontend ('Alertas Premium' de ProfePortal) con tu Google Sheet usando los Webhooks (IPN) de Mercado Pago.

---

## PASO 1: Desplegar el Webhook en Google Apps Script
1. Abre tu Google Sheet de Respuestas (el que guarda los usuarios).
2. Ve al menú **Extensiones > Apps Script**.
3. Haz clic en el signo `+` (Añadir un archivo) > **Secuencia de comandos** y nómbralo `webhook_mercado_pago`.
4. Abre el archivo `webhook_mercado_pago.gs` que generamos en tu carpeta local del proyecto (`e:\IA\APD-Omni\webhook_mercado_pago.gs`), copia absolutamente todo el código y pégalo allí.
5. Arriba en el script, completa:
   - `MP_ACCESS_TOKEN`: (Lo obtendrás en el Paso 2).
   - `URL_FORMULARIO_INGRESO`: El link a donde quieres mandar a los que pagan sin llenar el form (ej: `https://tu-dominio.com/#modalFree`).
6. En la parte superior derecha, haz clic en el botón azul **Implementar (Deploy) > Nueva Implementación**.
7. Configura:
   - **Tipo:** Aplicación Web (Web App).
   - **Descripción:** *Webhook Mercado Pago*
   - **Ejecutar como:** *Tú (tu correo)*
   - **Quién tiene acceso:** *Cualquier persona (Everyone)* **(¡ESTO ES CLAVE para que MercadoPago pueda entrar!)**
8. Haz clic en **Implementar**. Copia la **URL de la Aplicación Web** obtenida. (Ej: `https://script.google.com/macros/s/AKfy.../exec`).

---

## PASO 2: Obtener Access Token y Configurar Webhook en Mercado Pago
1. Ingresa a **[Mercado Pago Developers (Tus Integraciones)](https://open.mercadopago.com.ar/panel/applications)** e inicia sesión con la cuenta de 'BRUJULA DOCENTE'.
2. Si no tienes una aplicación creada, haz clic en **"Crear aplicación"** y llénala con datos básicos (Nombre: ProfePortal pagos, Producto: Checkout Pro).
3. Entra a tu Aplicación.
4. En el menú izquierdo, ve a **Credenciales de Producción**. (No uses las de prueba).
5. Copia el **Access Token** (`APP_USR-...`) y pégalo en el script del PASO 1, reemplazando `'APP_USR-ACA_VA_TU_ACCESS_TOKEN_REAL_DE_PRODUCCION'`. (Guarda el script y vuelve a darle **Implementar > Gestionar Implementaciones > Editar (Lapiz) > Nueva versión**).

**Configurar el Webhook:**
6. En el menú izquierdo de tu aplicación en Mercado Pago, ve a **Notificaciones > Webhooks**.
7. En el campo **URL de Producción**, pega la URL de tu Google Apps Script obtenida en el PASO 1.
8. En la sección de "Eventos (Events)", marca únicamente la casilla que diga:
   - **Pagos (Payments)**
   - **Suscripciones (Subscriptions)** *(Si está disponible)*
9. Presiona **Guardar**. Listo, MP ya está enviando avisos a tu script por detrás.

---

## PASO 3: Configurar Back URLs (Página de Retorno)
Para que el usuario regrese a tu sitio apenas paga:

*   **Si usaste Checkout Pro (Smart Links):** 
    En la configuración de tu botón de MercadoPago, busca la opción "URL de retorno" (Back URLs) y pon el link de tu página principal o del formulario. (MercadoPago los redirige automáticamente tras 5 segundos del "Pago aprobado").
    
*   **Si es una Suscripción:**
    Al configurar el "Plan Preapproval" de suscripción, debés enviar el parámetro `back_url` en el JSON de creación del plan en MercadoPago, de modo que vuelvan a `https://tu-dominio.com`.

---

## PASO 4: ¡Prueba Final!
1. Ingresa a tu web (index.html).
2. Abre "Alertas Ilimitadas" (Modal Premium), ingresa un correo (ej: `premium_test@gmail.com`).
3. Toca Continuar y elige "Abonar Manualmente" enviándote 1 peso a tu propia cuenta o haciendo un pago real.
4. Revisa tu Google Sheet: A los segundos de que se apruebe el pago, debería aparecer una fila nueva o modificada (si el correo ya existía) con el Estado en `PAGADO` y Plan `Premium`! 
5. Revisa la bandeja de entrada de `premium_test@gmail.com` para ver si llegó el mail de bienvenida.
