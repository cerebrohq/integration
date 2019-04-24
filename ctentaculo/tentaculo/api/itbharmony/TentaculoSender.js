(function () {
    var TentaculoUtils = require("TentaculoUtils.js");
    TentaculoUtils.setPrompt("Tentaculo Sender: ");
    var TentaculoSender = {
        isRunning: false,
        pythonProcess: null,
        tcpSocket: null,
        readError: function () {
            TentaculoUtils.TentaculoLog("Python process exited with error");
            var data = this.pythonProcess.readAllStandardError();
            var stream = new QTextStream(data);
            TentaculoUtils.TentaculoLog(stream.readAll());
        },
        readOutput: function () {
            TentaculoUtils.TentaculoLog("Python process exited successful");
        },
        pythonStarted: function () {
            TentaculoUtils.TentaculoLog("Python process started");
            this.isRunning = true;
            this.tcpSocket = new QTcpSocket;
            this.tcpSocket.readyRead.connect(this, this.readyRead);
        },
        pythonFinished: function () {
            TentaculoUtils.TentaculoLog("Python process finished");
            this.isRunning = false;
        },
        run: function () {
            var tentaculoPath = QProcessEnvironment.systemEnvironment().value("CTENTACULO_LOCATION", undefined);
            if (!tentaculoPath) {
                TentaculoUtils.TentaculoLog("Unknown system variable \"CTENTACULO_LOCATION\"");
            } else {
                this.pythonProcess = new QProcess;
                this.pythonProcess.readyReadStandardError.connect(this, this.readError);
                this.pythonProcess.readyReadStandardOutput.connect(this, this.readOutput);
                this.pythonProcess.started.connect(this, this.pythonStarted);
                this.pythonProcess["finished(int,QProcess::ExitStatus)"].connect(this, this.pythonFinished);
                this.pythonProcess.start("python \"" + tentaculoPath + "\\tentaculo\\server.py\" 11000 tbharmony");
                //this.pythonProcess.start("\"C:\\Users\\Tiberius\\AppData\\Roaming\\Toon Boom Animation\\Toon Boom Harmony Essentials\\1500-scripts\\start.bat\" \"" + tentaculoPath + "\\tentaculo\\server.py\" 11000 tbharmony");
            }
        },
        sendMessage: function (func, args) {
            if (args === undefined) args = "";
            var payload = {
                "function": func,
                "args": args,
                "versionMajor": TentaculoUtils.MAJOR_VERSION,
                "versionMonir": TentaculoUtils.MINOR_VERSION
            }
            var bytes = new QByteArray();
            bytes.append(String(JSON.stringify(payload) + "\n"));
            this.tcpSocket.connectToHost("localhost", 11000);
            if (!this.tcpSocket.waitForConnected(10000)) {
                TentaculoUtils.TentaculoLog("Could not connect to python server");
            } else {
                TentaculoUtils.TentaculoLog("Connected to python server");
                TentaculoUtils.TentaculoLog("Send: " + String(JSON.stringify(payload) + "\n"))
                this.tcpSocket.write(bytes);
            }
        },
        readyRead: function () {
            var chunk = (new QTextStream(this.tcpSocket.readAll(), QIODevice.ReadOnly)).readAll();
            TentaculoUtils.TentaculoLog("Read chunk: " + chunk);
        }
    }
    /*
        var TentaculoCommands = require("TentaculoCommands.js")
        function printMsg(msg) {
            print("Tentaculo Server: " + msg);
        }
        printMsg("Module loaded");
        var tcpServer = new QTcpServer(undefined);
        tcpServer.protocolVersion = "1.0";
        function listenPort(startPort, count) {
            if (tcpServer.isListening()) return tcpServer.serverPort();
            if (startPort == undefined) startPort = 100;
            if (count == undefined) count = 10;
            var listeningPort = startPort;
            for (var i = 0; i < count; i++) {
                if (tcpServer.listen(QHostAddress.LocalHost, listeningPort)) break;
                listeningPort++;
            }
            if (tcpServer.isListening()) return listeningPort;
            return false;
        }
    
        function startServer() {
            printMsg("Begin start server");
            var listeningPort = listenPort();
            if (listeningPort === false) {
                printMsg("Unable to start the server (" + tcpServer.errorString() + ")");
                return;
            }
            ipAddress = tcpServer.serverAddress().toString();
            printMsg("The server is running on " + ipAddress + ":" + tcpServer.serverPort());
            printMsg("Run the Client now");
            tcpServer.newConnection.connect(undefined, newConnection);
        }
    
        function stopServer() {
            printMsg("Stopped server");
            tcpServer.close();
        }
    
        function newConnection() {
            printMsg("New connection")
            var client = tcpServer.nextPendingConnection();
            client.readyRead.connect(undefined, readyRead);
            tcpServer.client = client;
            var data = "";
            function readyRead() {
                var chunk = (new QTextStream(client.readAll(), QIODevice.ReadOnly)).readAll();
                printMsg("Read chunk: " + chunk);
                data += chunk;
                if (data.indexOf("\n") != -1) {
                    data = data.replace(/\\n/g, "");
                    printMsg("Data: " + data);
                    try {
                        var result = JSON.parse(data);
                        if (result.version === undefined || result.version.indexOf('.') == -1) {
                            sendError("Unknown version");
                            printMsg("Unknown version");
                        } else if (result.command === undefined) {
                            sendError("Command not specified");
                            printMsg("Command not specified");
                        } else if (TentaculoCommands[result.command] === undefined) {
                            sendError("Unknown command")
                            printMsg("Unknown command");
                        } else {
                            printMsg("Command: " + result.command);
                            printMsg("Version: " + result.version);
                            var version = result.version;
                            var majorVersion = +version.substr(0, version.indexOf('.'))
                            var protocolMajorVersion = +tcpServer.protocolVersion.substr(0, tcpServer.protocolVersion.indexOf('.'))
                            if (majorVersion != protocolMajorVersion) {
                                sendError("The specified version does not match the version of the protocol");
                            } else {
                                TentaculoCommands[result.command].run(result);
                            }
                        }
                    } catch (e) {
                        printMsg(e.message);
                        sendError(e.message);
                    }
                    data = "";
                }
            }
        }
    
        function sendError(errorMsg) {
            var response = {
                error: errorMsg
            }
            sendResponse(response);
        }
    
        function sendResponse(payload) {
            var response = {
                version: tcpServer.protocolVersion,
            }
            Object.assign(response, payload);
            var bytes = new QByteArray();
            bytes.append(String(JSON.stringify(response) + "\n"));
            printMsg("Send: " + String(JSON.stringify(response) + "\n"))
            tcpServer.client.write(bytes);
        }*/
    //exports["startServer"] = startServer;
    //exports["stopServer"] = stopServer;
    //exports["sendResponse"] = sendResponse;
    //exports["sendError"] = sendError;
    for (var i in TentaculoSender)
        exports[i] = TentaculoSender[i];
})();