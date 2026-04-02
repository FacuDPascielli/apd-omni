function doPost(e) {
  const sheetName = 'Respuestas de formulario 1';
  // El mismo ID de spreadsheet
  const ss = SpreadsheetApp.openById('14UNkDXKDw3pWLeVBnElcU4GvEznO9g5G6qhkzwU78sI');
  const sheet = ss.getSheetByName(sheetName);
  
  if (!sheet) {
    return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': 'Hoja no encontrada' }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  try {
    let payload;
    try {
      payload = JSON.parse(e.postData.contents);
    } catch(err) {
      return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': 'Formato no JSON recibido o paquete dañado.' }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    if (payload.accion !== "modificar") {
      return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': 'Acción no soportada.' }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    const emailViejo = (payload.email_viejo || "").toString().toLowerCase().trim();
    const emailNuevo = (payload.email_nuevo || "").toString().toLowerCase().trim();
    const nuevoDistrito = (payload.nuevo_distrito || "").toString().toUpperCase().trim();
    const nuevaMateria = (payload.nueva_materia || "").toString().toUpperCase().trim();

    if (!emailViejo) {
       return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': 'Falta email identificador.' }))
         .setMimeType(ContentService.MimeType.JSON);
    }

    // Buscar el email (Columna C)
    const ultimaFila = sheet.getLastRow();
    if (ultimaFila < 2) {
       return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': 'La sheet está vacía.' }))
         .setMimeType(ContentService.MimeType.JSON);
    }
    
    // Leemos toda la columna C desde la fila 1
    const emailsData = sheet.getRange(1, 3, ultimaFila, 1).getValues();
    let filaModificar = -1;
    
    // Buscar la última coincidencia de ese email (ya que algunos usuarios se registran varias veces, la última es su registro más reciente)
    for (let i = emailsData.length - 1; i >= 0; i--) {
       if (emailsData[i][0].toString().toLowerCase().trim() === emailViejo) {
          // Chequear que el estado final (Columna K) no sea "Baja"
          const estadoFila = sheet.getRange(i + 1, 11).getValue().toString().toLowerCase().trim();
          if (estadoFila !== "baja") {
             filaModificar = i + 1;
             break;
          }
       }
    }
    
    // Si no encontramos un usuario activo, tomamos cualquier coincidencia histórica para poder modificarla (tal vez el usuario se dio de baja y ahora quiere cambiar su mail)
    if (filaModificar === -1) {
       for (let i = emailsData.length - 1; i >= 0; i--) {
          if (emailsData[i][0].toString().toLowerCase().trim() === emailViejo) {
             filaModificar = i + 1;
             break;
          }
       }
    }

    if (filaModificar === -1) {
       return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': 'No se encontró un usuario con ese correo para modificar.' }))
         .setMimeType(ContentService.MimeType.JSON);
    }

    // Aplicar las modificaciones estrictamente en las celdas C, D, y H
    if (emailNuevo) {
       sheet.getRange(filaModificar, 3).setValue(emailNuevo);
    }
    if (nuevoDistrito) {
       sheet.getRange(filaModificar, 4).setValue(nuevoDistrito);
    }
    if (nuevaMateria) {
       sheet.getRange(filaModificar, 8).setValue(nuevaMateria);
    }

    return ContentService.createTextOutput(JSON.stringify({ 'result': 'success', 'row': filaModificar }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
