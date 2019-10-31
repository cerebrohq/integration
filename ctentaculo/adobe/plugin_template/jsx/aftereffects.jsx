$._ext.evalFile(File($.fileName).path + '/json2.min.js')

getDocumentFilename = function() {
  try {
    if (!app.project.file) throw new Error('Project not saved')
    return $._ext.successResult(app.project.file.fsName)
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}

newDocument = function(filename) {
  try {
    app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES)
    var prj = app.newProject()
    if (prj) {
      prj.save(File(filename))
      return $._ext.successResult(true)
    }
    throw new Error('Project not created')
  } catch (error) {
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
    var activeItem = app.project.activeItem
    if (activeItem == null || !(activeItem instanceof CompItem)) {
      throw new Error('Please acivate a composition')
    } else {
      var res = [1, 1]
      if (activeItem.resolutionFactor != '1,1') {
        res = activeItem.resolutionFactor
        activeItem.resolutionFactor = [1, 1]
      }
      if (location != null) {
        location = decodeURIComponent(location)
        activeItem.saveFrameToPng(activeItem.time, File(location))
        app.activeViewer.setActive()
        activeItem.resolutionFactor = res
        app.project.save()
        return $._ext.successResult(true)
      } else {
        throw new Error('Location is undefined')
      }
    }
  } catch (error) {
    alert(error.message)
    return $._ext.errorResult(error.message)
  }
}
