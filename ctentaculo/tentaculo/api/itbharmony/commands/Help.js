(function () {
    if (specialFolders.userConfig.indexOf("USA_DB") != -1) {
        localPath = fileMapper.toNativePath(specialFolders.userConfig);
        var idxOf = localPath.indexOf("users");
        localPathScripts = localPath.slice(0, idxOf) + "scripts/commands";
    }
    else {
        localPath = specialFolders.userConfig;
        var idxOf_full = localPath.indexOf("full-");
        var version = localPath.slice(idxOf_full + 5, -5);
        localPathScripts = localPath.replace("/full-" + version + "-pref", "/" + version + "-scripts/commands");
    }
    var currentDir = new Dir(localPathScripts);
    exports["command"] = "Help";
    exports["description"] = "Display help for all commands";
    exports["run"] = function (request) {
        var data = "";
        var files = currentDir.entryList("*.js");
        for (var i = 0; i < files.length; i++) {
            try {
                var module = require(files[i]);
                data += module.command + " - " + module.description + "\n";
            } catch (e) { }
        }
        var responseObj = {
            data: data
        }
        scene.TentaculoServer.sendResponse(responseObj);
    };
})();