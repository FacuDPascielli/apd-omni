/* Archivo: script_modificar_premium.js */

function doPost(e) {
  // Asegurá que este ID sea el de tu BD de Producción
  const ss = SpreadsheetApp.openById('14UNkDXKDw3pWLeVBnElcU4GvEznO9g5G6qhkzwU78sI');
  const sheet = ss.getSheetByName('Respuestas de formulario 1');
  
  if (!sheet) {
    return _error("Hoja no encontrada");
  }

  try {
    let payload;
    try {
      payload = JSON.parse(e.postData.contents);
    } catch(err) {
      return _error('Formato no JSON recibido o paquete dañado.');
    }
    
    if (payload.accion !== "modificar_premium") {
      return _error('Acción no soportada.');
    }

    const emailViejo = (payload.email_viejo || "").toString().toLowerCase().trim();
    const emailNuevo = (payload.email_nuevo || "").toString().toLowerCase().trim();
    const nuevoDistrito = (payload.nuevo_distrito || "").toString().toUpperCase().trim();
    const nuevaMateria = (payload.nueva_materia || "").toString().toUpperCase().trim();

    if (!emailViejo) {
       return _error('Falta email identificador.');
    }

    // Buscar en la Columna C (índice 3)
    const ultimaFila = sheet.getLastRow();
    if (ultimaFila < 2) return _error('La sheet está vacía.');
    
    const emailsData = sheet.getRange(1, 3, ultimaFila, 1).getValues();
    let filaModificar = -1;
    
    // Buscar la última coincidencia activa
    for (let i = emailsData.length - 1; i >= 0; i--) {
       if (emailsData[i][0].toString().toLowerCase().trim() === emailViejo) {
          const estadoFila = sheet.getRange(i + 1, 11).getValue().toString().toLowerCase().trim(); // K = 11 (Baja)
          if (estadoFila !== "baja") {
             filaModificar = i + 1;
             break;
          }
       }
    }
    
    // Si no está activo pero existe, la modificamos igual
    if (filaModificar === -1) {
       for (let i = emailsData.length - 1; i >= 0; i--) {
          if (emailsData[i][0].toString().toLowerCase().trim() === emailViejo) {
             filaModificar = i + 1;
             break;
          }
       }
    }

    if (filaModificar === -1) {
       return _error('No se encontró un usuario con ese correo para modificar.');
    }

    // Realizar las actualizaciones de datos en el Excel
    if (emailNuevo) {
       sheet.getRange(filaModificar, 3).setValue(emailNuevo); // C = 3
    }
    if (nuevoDistrito) {
       sheet.getRange(filaModificar, 4).setValue(nuevoDistrito); // D = 4
    }
    if (nuevaMateria) {
       sheet.getRange(filaModificar, 8).setValue(nuevaMateria); // H = 8
    }

    // ENVIAR EL CORREO DE CONFIRMACIÓN AL CORREO DESTINO
    enviarMailConfirmacionModificacion(emailNuevo || emailViejo, nuevoDistrito, nuevaMateria);

    return ContentService.createTextOutput(JSON.stringify({ 'result': 'success', 'row': filaModificar }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return _error(error.toString());
  }
}

function _error(mensaje) {
    return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': mensaje }))
      .setMimeType(ContentService.MimeType.JSON);
}

// =====================================
// FUNCIÓN PARA ENVIAR CORREO
// =====================================
function enviarMailConfirmacionModificacion(emailDestino, nuevoDistrito, nuevaMateria) {
  try {
    const asunto = "¡Brújula Docente! Tus datos Premium se actualizaron correctamente ✅";
    const cuerpoHtml = `
      <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #d97706;">Tus alertas fueron actualizadas</h2>
        <p>¡Hola!</p>
        <p>Te confirmamos que hemos procesado la modificación de tu perfil Premium en <b>Brújula Docente</b> con los siguientes datos (aquellos no informados, se mantienen como estaban antes de solicitar el cambio):</p>
        <ul>
          ${nuevoDistrito ? "<li><b>Distritos declarados:</b> " + nuevoDistrito + "</li>" : ''}
          ${nuevaMateria ? "<li><b>Materias declaradas:</b> " + nuevaMateria + "</li>" : ''}
        </ul>
        <p>A partir del próximo envío, recibirás las ofertas filtradas con estos nuevos criterios en este correo.</p>
        <p>Cualquier consulta, no dudes en responder a este e-mail.</p>
        <br>
        <p>Saludos,<br><b>El equipo de Brújula Docente</b></p>
      </div>
    `;
    
    MailApp.sendEmail({
      to: emailDestino,
      subject: asunto,
      htmlBody: cuerpoHtml,
      name: "Brújula Docente"
    });
  } catch (e) {
    console.log("Error enviando mail de confirmación: " + e.toString());
  }
}
