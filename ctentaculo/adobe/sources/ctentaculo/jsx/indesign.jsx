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

newDocument = function(filename) {
  try {
    var doc = app.documents.add()
    doc.save(new File(filename), true)
    return $._ext.successResult(true)
  } catch (error) {
    app.activeDocument.close(SaveOptions.no)
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
    document.exportFile(ExportFormat.PNG_FORMAT, new File(location))
    document.save()
    return $._ext.successResult(true)
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}
