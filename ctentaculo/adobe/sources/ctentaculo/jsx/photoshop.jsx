$._ext.evalFile(File($.fileName).path + '/json2.min.js')

getDocumentFilename = function() {
  try {
    if (app.activeDocument)
      return $._ext.successResult(app.activeDocument.fullName.fsName)
    else throw new Error('No active document')
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}

newDocument = function(filename, width, height) {
  if (width === undefined) width = 800
  if (height === undefined) height = 600
  try {
    var doc = documents.add(width + 'px', height + 'px')
    doc.saveAs(File(filename), new PhotoshopSaveOptions(), false)
    return $._ext.successResult(true)
  } catch (error) {
    activeDocument.close(SaveOptions.DONOTSAVECHANGES)
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}

openDocument = function(filename) {
  try {
    app.open(File(filename))
    return $._ext.successResult(true)
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}

takeSnapshot = function(filename, size) {
  try {
    var document = app.activeDocument
    var webOptions = new ExportOptionsSaveForWeb()
    webOptions.format = SaveDocumentType.PNG
    webOptions.PNG8 = true
    webOptions.transparency = false
    webOptions.interlaced = 0
    webOptions.includeProfile = true
    webOptions.optimized = true
    var rulerUnits = app.preferences.rulerUnits
    var typeUnits = app.preferences.typeUnits
    var savedState = document.activeHistoryState
    app.preferences.rulerUnits = Units.PIXELS
    app.preferences.typeUnits = TypeUnits.PIXELS
    if (document.width.value > document.height.value)
      document.resizeImage(size + 'px', undefined)
    else document.resizeImage(undefined, size + 'px')
    document.exportDocument(
      new File(filename),
      ExportType.SAVEFORWEB,
      webOptions,
    )
    app.preferences.rulerUnits = rulerUnits
    app.preferences.typeUnits = typeUnits
    document.activeHistoryState = savedState
    document.save()
    return $._ext.successResult(true)
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}
