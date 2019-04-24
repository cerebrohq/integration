(function () {
	exports["command"] = "screenshot";
	exports["description"] = "Create screenshot for current file";
	exports["run"] = function (request) {
		var outputFile = new File(request.args[0]);
		var layoutExport = new LayoutExport();
		var exportParams = new LayoutExportParams;
		exportParams.fileDirectory = outputFile.path;
		exportParams.filePattern = outputFile.baseName;
		exportParams.fileFormat = "PNG"
		exportParams.exportCameraFrame = false
		var isRendered = layoutExport.addRender(exportParams);
		var isSaved = layoutExport.save(exportParams);
		if (!isSaved) {
			scene.Tentaculo.Receiver.sendResponse("screenshot", [false]);
		} else {
			scene.Tentaculo.Receiver.sendResponse("screenshot", [true]);
		}
	};
})();