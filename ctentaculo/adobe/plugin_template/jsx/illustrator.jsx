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
    var doc = documents.add(DocumentColorSpace.RGB, width, height)
    doc.saveAs(File(filename), new IllustratorSaveOptions())
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

takeSnapshot = function(location) {
  try {
    var document = app.activeDocument
    var options = ExportOptionsPNG24
    options.transparency = false
    document.exportFile(File(location), ExportType.PNG24, options)
    document.save()
    return $._ext.successResult(true)
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}
