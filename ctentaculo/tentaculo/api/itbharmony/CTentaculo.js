function menuTodolist() {
	sendMessage("menu_todolist");
}

function menuBrowser() {
	sendMessage("menu_browser");
}

function menuPublish() {
	sendMessage("menu_publish");
}

function menuReport() {
	sendMessage("menu_createreport");
}

function menuWorkdir() {
	sendMessage("menu_workdir");
}

function menuLogout() {
	sendMessage("menu_logout");
}

function menuStop() {
	sendMessage("stop");
}

function menuAbout() {
	sendMessage("menu_about");
}

function sa() {
	sendMessage("check");
}

function sendMessage(func, args) {
	if (!scene.Tentaculo.Sender.isRunning) {
		print("Sender error")
	} else {
		scene.Tentaculo.Sender.sendMessage(func, args);
	}
}

(function () {
	print("Run CTentaculo");
	if (!scene.Tentaculo) scene.Tentaculo = require("Tentaculo.js");
	if (!scene.Tentaculo.Receiver.isRunning) scene.Tentaculo.Receiver.run();
	if (!scene.Tentaculo.Sender.isRunning) scene.Tentaculo.Sender.run();
})()