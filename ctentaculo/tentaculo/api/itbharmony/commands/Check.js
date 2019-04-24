(function () {
    exports["command"] = "check";
    exports["description"] = "Check command";
    exports["run"] = function (request) {
        var response = ["OK"]
        scene.Tentaculo.Receiver.sendResponse("check", response);
    };
})();