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
    // Esto evita el problema de las 1000 filas pre-creadas por Google Forms y su borde.
    const findFirstEmptyRow = () => {
      const columnAMax = sheet.getMaxRows();
      if (columnAMax === 0) return 1;
      
      const columnAData = sheet.getRange(1, 1, columnAMax, 1).getValues();
      for (let i = 0; i < columnAData.length; i++) {
        if (!columnAData[i][0] || columnAData[i][0] === "") {
           // Las filas en Sheets son 1-indexed
           return i + 1;
        }
      }
      // Si todo estaba lleno, añadirla al final de la max capacity
      return columnAMax + 1;
    };

    const emptyRow = findFirstEmptyRow();

    // ARRAY ESTRICTO - Mapeo uno a uno con el Excel según instrucción
    // [A, B, C, D, E, F, G, H, I, J, K, L, M]
    const strictArray = [
      new Date(),       // A: Fecha
      payload.nombre || "", // B: Nombre
      payload.email  || "", // C: Email
      payload.distrito || "", // D: 1° distrito
      "",               // E: 2° distrito
      "",               // F: 3° distrito
      "",               // G: Nivel/Modalidad
      payload.materia || "",  // H: Códigos materias
      "",               // I: Pregunta
      "",               // J: Email MP
      "Alta",           // K: Estado (Siempre para este plan)
      "PENDIENTE",      // L: Estado de pago (Siempre para gratis o MP nuevo)
      "Gratis"          // M: Plan
    ];

    // Inyectar el arreglo duro (1 fila, 13 columnas [A hasta M])
    sheet.getRange(emptyRow, 1, 1, 13).setValues([strictArray]);
    
    return ContentService.createTextOutput(JSON.stringify({ 'result': 'success', 'row': emptyRow }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ 'result': 'error', 'message': error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
