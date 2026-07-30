const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  listModels: () => ipcRenderer.invoke("models:list"),
  getKeyStatus: () => ipcRenderer.invoke("apikey:get-status"),
  setApiKey: (key) => ipcRenderer.invoke("apikey:set", key),
  pickImage: () => ipcRenderer.invoke("dialog:pick-image"),
  saveImage: (dataUrl) => ipcRenderer.invoke("dialog:save-image", dataUrl),
  editImage: (payload) => ipcRenderer.invoke("image:edit", payload),
});
