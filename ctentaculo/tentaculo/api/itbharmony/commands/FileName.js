(function () {
    exports["command"] = "file_name";
    exports["description"] = "Get current filename";
    exports["run"] = function (request) {
        var sceneFilePath = scene.currentProjectPath() + "/" + scene.currentVersionName() + ".xstage";
        var sceneFile = new File(sceneFilePath);
        if (sceneFile.exists) {
            scene.Tentaculo.Receiver.sendResponse("file_name", [sceneFilePath]);
        } else {
            scene.Tentaculo.Receiver.sendResponse("file_name", [""]);
        }
    };
})();