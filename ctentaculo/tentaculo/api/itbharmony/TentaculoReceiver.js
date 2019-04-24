(function () {
    var TentaculoUtils = require("TentaculoUtils.js");
    var TentaculoCommands = require("TentaculoCommands.js")
    TentaculoUtils.setPrompt("Tentaculo Receiver: ");
    var TentaculoReceiver = {
        isRunning: false,
        tcpServer: null,
        tcpSocket: null,
        listenPort: function (startPort, count) {
            if (this.tcpServer.isListening()) return this.tcpServer.serverPort();
            if (startPort == undefined) startPort = 11001;
            if (count == undefined) count = 10;
            var listeningPort = startPort;
            for (var i = 0; i < count; i++) {
                if (this.tcpServer.listen(QHostAddress.LocalHost, listeningPort)) break;
                listeningPort++;
            }
            if (this.tcpServer.isListening()) return listeningPort;
            return false;
        },
        run: function () {
            this.tcpServer = new QTcpServer(undefined);
            TentaculoUtils.TentaculoLog("Begin start server");
            var listeningPort = this.listenPort();
            if (listeningPort === false) {
                TentaculoUtils.TentaculoLog("Unable to start the server (" + this.tcpServer.errorString() + ")");
                return;
            }
            ipAddress = this.tcpServer.serverAddress().toString();
            TentaculoUtils.TentaculoLog("The server is running on " + ipAddress + ":" + this.tcpServer.serverPort());
            this.isRunning = true;
            this.tcpServer.newConnection.connect(this, this.newConnection);
        },
        stop: function () {
            TentaculoUtils.TentaculoLog("Stopped server");
            this.tcpServer.close();
        },
        newConnection: function () {
            TentaculoUtils.TentaculoLog("New connection")
            this.tcpSocket = this.tcpServer.nextPendingConnection();
            this.tcpSocket.readyRead.connect(this, this.readyRead);
        },
        readyRead: function () {
            var data = (new QTextStream(this.tcpSocket.readAll(), QIODevice.ReadOnly)).readAll();
            TentaculoUtils.TentaculoLog("Receive: " + data);
            try {
                var result = JSON.parse(data);
                if (result.versionMajor === undefined || result.versionMinor === undefined) {
                    this.sendError("Unknown version");
                    TentaculoUtils.TentaculoLog("Unknown version");
                } else if (result.versionMajor != TentaculoUtils.MAJOR_VERSION) {
                    this.sendError("The specified version does not match the version of the protocol");
                    TentaculoUtils.TentaculoLog("The specified version does not match the version of the protocol");
                } else if (result["function"] === undefined) {
                    this.sendError("Function name not specified");
                    TentaculoUtils.TentaculoLog("Command not specified");
                } else if (TentaculoCommands[result["function"]] === undefined) {
                    this.sendError("Unknown command");
                    TentaculoUtils.TentaculoLog("Unknown command");
                } else {
                    TentaculoUtils.TentaculoLog("Function: " + result["function"]);
                    TentaculoUtils.TentaculoLog("Version: " + result.versionMajor + "." + result.versionMinor);
                    TentaculoCommands[result["function"]].run(result);
                }
            } catch (e) {
                TentaculoUtils.TentaculoLog(e.message);
                this.sendError(e.message);
            }
        },
        sendResponse: function (func, args) {
            var response = {
                "function": func,
                versionMajor: TentaculoUtils.MAJOR_VERSION,
                versionMinor: TentaculoUtils.MINOR_VERSION,
                args: args
            }
            var bytes = new QByteArray();
            bytes.append(String(JSON.stringify(response) + "\n"));
            TentaculoUtils.TentaculoLog("Send: " + String(JSON.stringify(response) + "\n"))
            this.tcpSocket.write(bytes);
        },
        sendError: function (errorMsg) {
            var response = {
                error: errorMsg
            }
            this.sendResponse(response);
        }
    }
    for (var i in TentaculoReceiver)
        exports[i] = TentaculoReceiver[i];
})();