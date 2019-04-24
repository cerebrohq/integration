(function () {
    exports["command"] = "open_file";
    exports["description"] = "Open specified file";
    exports["run"] = function (request) {
        scene.saveAll();
        var opened = scene.closeSceneAndOpen("", "", request.args[0], "");
        if (opened) {
            scene.Tentaculo.Receiver.sendResponse("open_file", [true]);
        } else {
            scene.Tentaculo.Receiver.sendResponse("open_file", [false]);
        }
    };
})();