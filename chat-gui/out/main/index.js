import { app, ipcMain, BrowserWindow, shell } from "electron";
import { join } from "path";
import { exec } from "child_process";
import __cjs_mod__ from "node:module";
const __filename = import.meta.filename;
const __dirname = import.meta.dirname;
const require2 = __cjs_mod__.createRequire(import.meta.url);
app.commandLine.appendSwitch("enable-touch-events");
app.commandLine.appendSwitch("enable-webview-tag");
function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 480,
    height: 800,
    fullscreen: true,
    frame: false,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, "../preload/index.mjs"),
      sandbox: false
    }
  });
  mainWindow.on("ready-to-show", () => {
    mainWindow.show();
  });
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url);
    return { action: "deny" };
  });
  if (process.env["ELECTRON_RENDERER_URL"]) {
    mainWindow.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    mainWindow.loadFile(join(__dirname, "../renderer/index.html"));
  }
}
app.whenReady().then(() => {
  ipcMain.on("app-quit", () => app.quit());
  ipcMain.handle("start-surveillance", async () => {
    return new Promise((resolve, reject) => {
      exec("cd /home/admin/Mr-A-Hacker-pocket-Ai-version-2 && /home/admin/Mr-A-Hacker-pocket-Ai-version-2/venv/bin/python lan_surveillance.py &", (error) => {
        if (error) {
          console.error("Failed to start surveillance:", error);
          reject(error);
        } else {
          resolve("Surveillance started");
        }
      });
    });
  });
  ipcMain.handle("run-organic-maps", async () => {
    return new Promise((resolve, reject) => {
      exec("flatpak run app.organicmaps.desktop", (error, stdout, stderr) => {
        if (error) {
          console.error("Failed to start Organic Maps:", error);
          reject(error);
        } else {
          resolve(stdout);
        }
      });
    });
  });
  createWindow();
  app.on("activate", function() {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
