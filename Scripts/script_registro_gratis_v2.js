function doPost(e) {
  const sheetName = 'Respuestas de formulario 1';
  // ID estático garantizado
  const ss = SpreadsheetApp.openById('14UNkDXKDw3pWLeVBnElcU4GvEznO9g5G6qhkzwU78sI');
  const sheet = ss.getSheetByName(sheetName);
  
  if (!sheet) {
    return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': 'Hoja no encontrada' }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  try {
    // Lectura de texto plano (para esquivar CORS 401 de preflight)
    let payload;
    try {
      payload = JSON.parse(e.postData.contents);
    } catch(err) {
      return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': 'Formato no JSON recibido o paquete dañado.' }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // Función local para encontrar la PRIMERA fila realmente vacía analizando solo la Columna A (Fecha)
    const findFirstEmptyRow = () => {
      const columnAMax = sheet.getMaxRows();
      if (columnAMax === 0) return 1;
      
      const columnAData = sheet.getRange(1, 1, columnAMax, 1).getValues();
      for (let i = 0; i < columnAData.length; i++) {
        if (!columnAData[i][0] || columnAData[i][0] === "") {
           return i + 1;
        }
      }
      return columnAMax + 1;
    };

    const emptyRow = findFirstEmptyRow();

    const estrictoDistrito = payload.distrito || "";
    const estrictoMateria = payload.materia || "";

    // ARRAY ESTRICTO - Mapeo uno a uno con el Excel
    const strictArray = [
      new Date(),       
      payload.nombre || "", 
      payload.email  || "", 
      estrictoDistrito, 
      "", "", "", 
      estrictoMateria,  
      "", "", "Alta", "PENDIENTE", "Gratis"          
    ];

    sheet.getRange(emptyRow, 1, 1, 13).setValues([strictArray]);
    
    // --- LÓGICA DE BÚSQUEDA DE OFERTAS ACTIVAS ---
    const URL_DB = "https://raw.githubusercontent.com/brujuladocente/portal-docente/main/ofertas_db.json";
    let ofertasEncontradas = [];
    
    try {
      const res = UrlFetchApp.fetch(URL_DB, {muteHttpExceptions: true});
      if (res.getResponseCode() === 200) {
         const db = JSON.parse(res.getContentText());
         const ofertas = db.ofertas || {};
         
         // Helper: Remover tildes
         const removeAccents = (str) => {
           // En AppsScript no podemos usar `str.normalize("NFD")` de forma totalmente segura a veces, 
           // pero el V8 engine actual lo soporta bien. Forma manual de fallback si falla:
           return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
         };
         
         let d_buscado = removeAccents(estrictoDistrito.toUpperCase());
         if (d_buscado === 'LOMAS DE ZAMORA') d_buscado = 'L DE ZAMORA';
         if (d_buscado === 'ALMIRANTE BROWN') d_buscado = 'A BROWN';
         if (d_buscado === 'ESTEBAN ECHEVERRIA') d_buscado = 'E ECHEVERRIA';
         
         const m_buscado = estrictoMateria.toUpperCase().replace(/\./g, ' ').replace(/,/g, ' ').trim();

         // Iterar y cruzar IDs
         for (const id in ofertas) {
             const o = ofertas[id];
             if (o.estado === 'activa') {
                 const d_oferta = removeAccents((o.distrito || "").toUpperCase());
                 const m_oferta = (o.codigo_area || "").toUpperCase();
                 
                 const matchDistrito = d_oferta.includes(removeAccents(estrictoDistrito.toUpperCase())) || d_oferta.includes(d_buscado);
                 const matchMateria = m_oferta.includes(m_buscado);
                 
                 if (matchDistrito && matchMateria) {
                     ofertasEncontradas.push(o);
                 }
             }
         }
      } else {
         console.warn("Fetch a ofertas_db.json retornó un error: " + res.getResponseCode());
      }
    } catch(err) {
      console.warn("Error al intentar descargar la base de ofertas en Apps Script: " + err);
    }

    // --- LÓGICA DE ENVÍO DE CORREO ESTILO BRÚJULA DOCENTE ---
    const correoUsuario = payload.email;
    if (correoUsuario) {
      if (ofertasEncontradas.length > 0) {
        let cuerpoHtml = `<h3>¡Bienvenido/a a Brújula Docente!</h3>
        <p>Te confirmamos que ya estás registrado en el Plan Gratis para recibir alertas de <b>${estrictoMateria}</b> en <b>${estrictoDistrito}</b>.</p>
        <p>¡Tenemos buenas noticias! Encontramos estas ofertas actualmente vigentes para vos:</p>
        <hr style="border:1px solid #c0d4e8; margin-bottom:15px;">`;
        
        ofertasEncontradas.forEach(o => {
            let horarios = (o.horarios || 'Ver en portal').replace(/\n/g, '<br>').replace(/ \| /g, '<br>');
            cuerpoHtml += `
            <div style="margin-bottom: 20px; padding: 15px; border-left: 4px solid #1937b0; background-color: #f8fcff; border-radius: 4px;">
                <h4 style="margin:0 0 10px 0; color:#1937b0; font-size:16px;">${o.encabezado || 'N/A'}</h4>
                <p style="margin: 4px 0; font-size:14px; color:#333;"><b>Nivel:</b> ${o.nivel || '-'} | <b style="color:#1937b0;">Escuela:</b> ${o.escuela || '-'}</p>
                <p style="margin: 4px 0; font-size:14px; color:#333;"><b>Horarios:</b><br/>${horarios}</p>
                <p style="margin: 4px 0; font-size:14px; color:#333;"><b>Observaciones:</b> ${o.observaciones || '-'}</p>
                <p style="font-size:12px; color:#6f9ac8; margin-top:8px; margin-bottom:0;">Nro IGE: ${o.ige || '-'}</p>
            </div>`;
        });
        
        cuerpoHtml += `
        <br><p>Te seguiremos notificando si surge alguna nueva de lunes a viernes entre las 08:00 y las 21:00 hs.</p>
        <br><p>Saludos,<br>Equipo de Brújula Docente</p>`;
        
        MailApp.sendEmail({
            to: correoUsuario,
            subject: `¡Tenemos ${ofertasEncontradas.length} ofertas para vos hoy! 🚀 Búsqueda: ${estrictoMateria} en ${estrictoDistrito}`,
            htmlBody: cuerpoHtml
        });
      } else {
        const cuerpoHtml = `<h3>¡Bienvenido/a a Brújula Docente!</h3>
        <p>En este momento no hay cargos activos en el sistema para tu perfil de <b>${estrictoMateria}</b> en el distrito de <b>${estrictoDistrito}</b>.</p>
        <p>Te recordamos que <b>enviamos nuestras alertas de lunes a viernes entre las 08:00 y las 21:00 hs</b>. Si no recibís correos en esos horarios, es porque no se han detectado nuevas ofertas con el código que ingresaste en nuestro barrido.</p>
        <p>¡Quedate atento/a a tu bandeja de entrada!</p>
        <br><p>Saludos,<br>Equipo de Brújula Docente</p>`;
        
        MailApp.sendEmail({
            to: correoUsuario,
            subject: `¡Alta confirmada! Alertas Gratis 📚 Búsqueda: ${estrictoMateria} en ${estrictoDistrito}`,
            htmlBody: cuerpoHtml
        });
      }
    }

    return ContentService.createTextOutput(JSON.stringify({ 'result': 'success', 'row': emptyRow }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
