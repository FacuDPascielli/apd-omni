# -*- coding: utf-8 -*-
"""
Formateo y envío de correos electrónicos vía Gmail (smtplib y email.mime).
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

LINK_BAJA = "https://docs.google.com/forms/d/e/1FAIpQLSdn6pJoHFKmBdUKqyyLGYsbf7MBx5lqP-Q6EMXWMZSUiEhH8w/viewform?usp=sharing&ouid=106040616818185769622"

def enviar_correo(ofertas, destinatario, nombre="Colega"):
    """
    Envía un resumen de las ofertas filtradas por correo usando HTML simple al destinatario especificado.
    """
    if not ofertas:
        return

    remitente = os.environ.get("EMAIL_REMITENTE")
    password = os.environ.get("EMAIL_PASSWORD")

    if not remitente or not password:
        print("INFO: No configuró credenciales de correo (EMAIL_REMITENTE / EMAIL_PASSWORD). Saltando envío de email.")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Alerta Lector ABC: {len(ofertas)} nuevas ofertas docentes en tus distritos"
    msg['From'] = remitente
    msg['To'] = destinatario

    html = f"""
    <div style="font-family: Arial, sans-serif; color: #222;">
      <p>Hola, <strong>{nombre}</strong>! Encontramos estas ofertas para vos:</p>
    </div>
    """
    
    for o in ofertas:
        html += f"""
        <div style="font-family: Arial, sans-serif; border-left: 4px solid #800080; padding: 12px 16px; margin-bottom: 14px; background: #f9f9f9;">
          <h3 style="color: #800080; margin: 0 0 6px 0;">{o.get('encabezado', 'N/A').strip()}</h3>
          <p style="margin: 3px 0; color: #333;">
            <b>Nivel:</b> {o.get('nivel', 'Desconocido').strip()} &nbsp;|&nbsp;
            <b>Escuela:</b> {o.get('escuela', 'Desconocido').strip()}
          </p>
          <p style="margin: 3px 0; color: #333;"><b>Horarios:</b> {o.get('horarios', 'Ver en Portal').strip()}</p>
          <p style="margin: 3px 0; color: #555;"><b>Observaciones:</b> {o.get('observaciones', '-').strip()}</p>
          <p style="margin: 3px 0; color: #333;"><b>Nro. IGE:</b> {o.get('ige', 'Desconocido').strip()}</p>
        </div>
        """
    
    html += "<p>Ingresa a <a href='https://misservicios.abc.gob.ar/actos.publicos.digitales/'>Actos Públicos Digitales</a> para ver detalles completos y postularte.</p>"
    html += f"""
    <hr style="border: none; border-top: 1px solid #ddd; margin: 24px 0;">
    <p style="font-size: 13px; color: #555;">
      ¿Ya conseguiste tus horas? Si no querés recibir más alertas, podés darte de baja acá: 
      <a href="{LINK_BAJA}" style="color: #6c3483; text-decoration: underline;">Solicitar baja</a>
    </p>
    <p style="font-size: 11px; color: #999; margin-top: 10px;">
      <b>Bot Automático Lector ABC</b> | Automate & Professionalize
    </p>
    """

    parte_html = MIMEText(html, 'html')
    msg.attach(parte_html)

    try:
        # Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        print(f"Correo de notificación enviado con éxito a {destinatario}: {len(ofertas)} ofertas notificadas.")
    except Exception as e:
        print(f"Error crítico al enviar el correo a {destinatario}: {e}")

def enviar_correo_vencimiento(destinatario, nombre="Colega"):
    """
    Envía un mail de cortesía informando que la suscripción pasó al Plan Gratis.
    """
    remitente = os.environ.get("EMAIL_REMITENTE")
    password = os.environ.get("EMAIL_PASSWORD")

    if not remitente or not password:
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Aviso importante: Pasaste al Plan Gratis de Lector ABC"
    msg['From'] = remitente
    msg['To'] = destinatario

    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333;">
      <h2 style="color: #ffaa00;">Aviso de suscripción vencida</h2>
      <p>Hola, <strong>{nombre}</strong>.</p>
      <p>Nos comunicamos para avisarte que han pasado más de 30 días desde tu último pago, por lo que <b>tu suscripción Premium ha finalizado</b>.</p>
      <p>Para que no te pierdas todas las alertas, te hemos mantenido en el sistema pero te hemos pasado automáticamente al <b>Plan Gratis</b> (limitado a tu primer distrito y primera materia registrada).</p>
      <p>Si deseas recuperar el acceso <b>Premium</b> (con todos tus distritos y materias), por favor renueva tu suscripción a la brevedad.</p>
      <br>
      <p style="font-size: 13px; color: #555;">Si ya pagaste, por favor desestima este mensaje; el sistema puede demorar unos minutos en procesarlo.</p>
      <p style="font-size: 11px; color: #999;"><b>Bot Automático Lector ABC</b> | Automate & Professionalize</p>
    </div>
    """

    parte_html = MIMEText(html, 'html')
    msg.attach(parte_html)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        print(f"Correo de vencimiento enviado a {destinatario}.")
        return True
    except Exception as e:
        print(f"Error al enviar correo de vencimiento a {destinatario}: {e}")
        return False

def enviar_correo_bienvenida(destinatario, nombre="Colega"):
    remitente = os.environ.get("EMAIL_REMITENTE")
    password = os.environ.get("EMAIL_PASSWORD")
    if not remitente or not password:
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "¡Bienvenido/a a Brújula Docente! 🚀"
    msg['From'] = remitente
    msg['To'] = destinatario
    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
      <h2 style="color: #1937b0;">¡Alta exitosa en nuestras Alertas!</h2>
      <p>Hola, <strong>{nombre}</strong>.</p>
      <p>Queríamos darte la bienvenida a Brújula Docente. Tu cuenta ya está validada y lista para recibir ofertas.</p>
      <p>A partir de este momento, nuestro sistema buscará coincidencias con tus materias y distritos. Te enviaremos un correo apenas haya novedades compatibles (suele ser de lunes a viernes entre las 8:00 y las 19:00 hs).</p>
      <p>¡Esperamos que pronto consigas tus horas!</p>
      <br>
      <p style="font-size: 13px; color: #555;">Si deseás dejar de recibir estos mensajes, podés <a href="{LINK_BAJA}" style="color: #6c3483; text-decoration: underline;">darte de baja acá</a>.</p>
      <p style="font-size: 11px; color: #999;"><b>Bot Automático Lector ABC</b></p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo de bienvenida a {destinatario}: {e}")
        return False

def enviar_correo_espera(destinatario, nombre="Colega"):
    remitente = os.environ.get("EMAIL_REMITENTE")
    password = os.environ.get("EMAIL_PASSWORD")
    if not remitente or not password:
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Aviso: Seguimos buscando ofertas para vos 🕵️‍♀️"
    msg['From'] = remitente
    msg['To'] = destinatario
    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
      <h2 style="color: #1937b0;">Seguimos buscando coincidencias...</h2>
      <p>Hola, <strong>{nombre}</strong>.</p>
      <p>Ha pasado tu primer día en el sistema y queríamos contarte que <b>aún no han salido ofertas públicas en el ABC</b> que coincidan con tu distrito y materia.</p>
      <p>No te preocupes, esto es normal. Algunas materias específicas demoran unos días en salir a la luz, o puede ser un período de baja publicación en tu distrito. Nosotros seguimos trabajando en segundo plano y te avisaremos inmediatamente cuando encontremos una opción para vos.</p>
      <br>
      <p style="font-size: 13px; color: #555;">Si deseás dejar de recibir estos mensajes o modificar tus filtros, podés <a href="{LINK_BAJA}" style="color: #6c3483; text-decoration: underline;">darte de baja acá</a> e inscribirte nuevamente.</p>
      <p style="font-size: 11px; color: #999;"><b>Bot Automático Lector ABC</b></p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo de espera a {destinatario}: {e}")
        return False

def enviar_correo_sin_ofertas_hoy(destinatario, nombre, distritos, materias):
    remitente = os.environ.get("EMAIL_REMITENTE")
    password = os.environ.get("EMAIL_PASSWORD")
    if not remitente or not password:
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Reporte Diario Brújula Docente: Sin ofertas nuevas hoy"
    msg['From'] = remitente
    msg['To'] = destinatario
    
    dist_str = ", ".join(distritos)
    mat_str = ", ".join(materias)
    
    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
      <h2 style="color: #6f9ac8;">Resumen del día</h2>
      <p>Hola, <strong>{nombre}</strong>.</p>
      <p>Terminaron las tandas de publicación oficiales de la Provincia por el día de hoy.</p>
      <p>Te escribíamos para confirmarte que <b>hoy no se publicaron nuevas ofertas</b> para tus filtros actuales:</p>
      <ul>
         <li><b>Distritos:</b> {dist_str}</li>
         <li><b>Materias:</b> {mat_str}</li>
      </ul>
      <p>Nos parecía importante avisarte para que te quedes tranquilo/a sabiendo que el sistema sí te leyó, pero simplemente no hubo actos públicos para tu perfil hoy. Mañana a la mañana retomaremos la búsqueda automática.</p>
      <p>¡Que descanses!</p>
      <br>
      <p style="font-size: 13px; color: #555;">Si deseás dejar de recibir estos mensajes, podés <a href="{LINK_BAJA}" style="color: #6c3483; text-decoration: underline;">darte de baja acá</a>.</p>
      <p style="font-size: 11px; color: #999;"><b>Bot Automático Lector ABC</b></p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar resumen sin ofertas a {destinatario}: {e}")
        return False
