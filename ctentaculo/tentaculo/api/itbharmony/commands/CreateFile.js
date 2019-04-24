(function () {
    exports["command"] = "create_file";
    exports["description"] = "Get current filename";
    exports["run"] = function (request) {
        var scenePath = request.args[0];
        var f = new QFile(scenePath);
        f.open(QIODevice.WriteOnly);
        f.close();
        var created = scene.closeSceneAndOpen("", "", scenePath, "");
        if (created) {
            scene.Tentaculo.Receiver.sendResponse("create_file", [true]);
        } else {
            scene.Tentaculo.Receiver.sendResponse("create_file", [false]);
        }
    };
})();