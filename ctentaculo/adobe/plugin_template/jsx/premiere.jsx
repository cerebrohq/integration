$._ext.evalFile(File($.fileName).path + '/json2.min.js')

getDocumentFilename = function() {
  try {
    var documentPath = app.project.path
    if (documentPath.indexOf('\\?\\UNC') != -1) {
      documentPath = documentPath.replace('\\?\\UNC', '')
    } else if (documentPath.indexOf('\\\\?\\') != -1) {
      documentPath = documentPath.replace('\\\\?\\', '')
    }
    return $._ext.successResult(documentPath)
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}

newDocument = function(filename) {
  try {
    var directory = new File($.fileName).fsName
    var oldPath = directory + '/template.prproj'
    var newPath = filename
    new File(oldPath).copy(newPath)
    var result = app.openDocument(new File(newPath).fsName)
    if (result) return $._ext.successResult(true)
    else throw new Erorr('Failed create document')
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}

openDocument = function(filename) {
  try {
    var result = app.openDocument(filename)
    if (result) return $._ext.successResult(true)
    else throw new Error('Document not saved')
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}

takeSnapshot = function(location) {
  try {
    app.enableQE()
    var activeSequence = qe.project.getActiveSequence()
    if (activeSequence) {
      var time = activeSequence.CTI.timecode
      var outputPath = new File(location)
      var outputFileName = outputPath.fsName
      activeSequence.exportFramePNG(time, outputFileName)
      return $._ext.successResult(true)
    } else throw new Error('No active sequence')
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}
