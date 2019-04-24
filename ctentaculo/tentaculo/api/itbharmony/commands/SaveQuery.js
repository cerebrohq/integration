(function () {
    exports["command"] = "save_query";
    exports["description"] = "Prompt user to save file";
    exports["run"] = function (request) {
        var messageBox = new QMessageBox();
        messageBox.addButton(QMessageBox.Ok);
        messageBox.addButton(QMessageBox.Cancel);
        messageBox.setWindowTitle("Save changes");
        messageBox.text = "Do you want to save your changes?";
        var saved = false;
        if (messageBox.exec() == QMessageBox.Ok) {
            scene.saveAll();
            saved = true;
        }
        if (saved) {
            scene.Tentaculo.Receiver.sendResponse("save_query", [false]);
        } else {
            scene.Tentaculo.Receiver.sendResponse("save_query", [true]);
        }
    };
})();