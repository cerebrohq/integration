if (fl) {
  var scriptPath = FLfile.uriToPlatformPath(fl.scriptURI)
  var parts = scriptPath.split('\\')
  if (parts.length === undefined || parts.length === 0) {
    parts = scriptPath.split('/')
  }
  var newScriptPath = parts.slice(0, -1).join('/') + '/json2.min.js'
  $._ext.evalFile(newScriptPath)
} else {
  $._ext.evalFile(File($.fileName).path + '/json2.min.js')
}

getDocumentFilename = function() {
  try {
    if (document && document.path) return $._ext.successResult(document.path)
    else throw new Error('No active document')
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}

newDocument = function(filename) {
  try {
    fl.createDocument()
    fl.saveDocument(document, 'file:///' + filename)
    return $._ext.successResult(true)
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}

openDocument = function(filename) {
  try {
    fl.openDocument('file:///' + filename)
    return $._ext.successResult(true)
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}

takeSnapshot = function(location) {
  try {
    document.exportPNG('file:///' + location, true, true)
    document.save()
    return $._ext.successResult(true)
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}
