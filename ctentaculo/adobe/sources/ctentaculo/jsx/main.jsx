try {
  if (fl) {
    $ = {}
  }
} catch (e) {
  if (!$._ext) {
    $._ext = { fl: false }
  }
}

$._ext.evalFile = function(path) {
  try {
    if ($._ext.fl) {
      fl.runScript('file:///' + path)
    } else {
      $.evalFile(path)
    }
  } catch (e) {
    alert('Exception:' + e)
  }
}

$._ext.evalFiles = function(jsxFolderPath) {
  var folder = new Folder(jsxFolderPath)
  if (folder.exists) {
    var jsxFiles = folder.getFiles('*.jsx')
    for (var i = 0; i < jsxFiles.length; i++) {
      var jsxFile = jsxFiles[i]
      $._ext.evalFile(jsxFile)
    }
  }
}

$._ext.errorResult = function(message, code) {
  return JSON.stringify({
    error: message,
    code: code !== undefined ? code : -1,
  })
}

$._ext.successResult = function(data) {
  return JSON.stringify({
    data: data,
  })
}
