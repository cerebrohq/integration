(function () {
    exports["command"] = "save_file";
    exports["description"] = "Save current file";
    exports["run"] = function (request) {
        var file = new File(request.args[0]);
        var saved = false;
        try {
            print("file exists " + file.exists);
            if (file.exists) saved = scene.saveAll();
            else saved = scene.saveAs(request.args[0])
        } catch (e) {
            print(e);
        }
        if (saved) {
            scene.Tentaculo.Receiver.sendResponse("save_file", [true]);
        } else {
            scene.Tentaculo.Receiver.sendResponse("save_file", [false]);
        }
    };
})();