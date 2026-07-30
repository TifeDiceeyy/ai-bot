const { app, BrowserWindow, ipcMain, safeStorage, dialog } = require("electron");
const path = require("node:path");
const fs = require("node:fs/promises");
const { fal } = require("@fal-ai/client");

const CONFIG_PATH = () => path.join(app.getPath("userData"), "config.bin");

const MODELS = {
  "nano-banana-pro": {
    label: "Nano Banana Pro (Google) — highest overall quality",
    endpoint: "fal-ai/nano-banana-pro/edit",
    buildInput: (prompt, imageUrls) => ({ prompt, image_urls: imageUrls }),
  },
  "flux-2-pro-edit": {
    label: "FLUX.2 [pro] Edit — style transfer & sequential edits",
    endpoint: "fal-ai/flux-pro/v2/edit",
    buildInput: (prompt, imageUrls) => ({ prompt, image_urls: imageUrls }),
  },
  "flux-kontext-pro": {
    label: "FLUX.1 Kontext [pro] — targeted local edits",
    endpoint: "fal-ai/flux-pro/kontext",
    buildInput: (prompt, imageUrls) => ({ prompt, image_url: imageUrls[0] }),
  },
};

async function getApiKey() {
  try {
    const encrypted = await fs.readFile(CONFIG_PATH());
    if (!safeStorage.isEncryptionAvailable()) return null;
    return safeStorage.decryptString(encrypted);
  } catch {
    return null;
  }
}

async function setApiKey(key) {
  const encrypted = safeStorage.encryptString(key);
  await fs.writeFile(CONFIG_PATH(), encrypted);
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 760,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.loadFile(path.join(__dirname, "renderer", "index.html"));
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

ipcMain.handle("models:list", () =>
  Object.entries(MODELS).map(([id, m]) => ({ id, label: m.label }))
);

ipcMain.handle("apikey:get-status", async () => {
  const key = await getApiKey();
  return { hasKey: Boolean(key) };
});

ipcMain.handle("apikey:set", async (_event, key) => {
  if (!key || typeof key !== "string" || key.trim().length === 0) {
    throw new Error("API key cannot be empty");
  }
  await setApiKey(key.trim());
  return { ok: true };
});

ipcMain.handle("dialog:pick-image", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openFile"],
    filters: [{ name: "Images", extensions: ["png", "jpg", "jpeg", "webp"] }],
  });
  if (result.canceled || result.filePaths.length === 0) return null;
  const filePath = result.filePaths[0];
  const buffer = await fs.readFile(filePath);
  const ext = path.extname(filePath).slice(1).toLowerCase();
  const mime = ext === "jpg" ? "jpeg" : ext;
  return {
    filePath,
    dataUrl: `data:image/${mime};base64,${buffer.toString("base64")}`,
  };
});

ipcMain.handle("dialog:save-image", async (_event, dataUrl) => {
  const result = await dialog.showSaveDialog({
    defaultPath: `edited-${Date.now()}.png`,
    filters: [{ name: "PNG Image", extensions: ["png"] }],
  });
  if (result.canceled || !result.filePath) return null;
  const base64 = dataUrl.split(",")[1];
  await fs.writeFile(result.filePath, Buffer.from(base64, "base64"));
  return result.filePath;
});

ipcMain.handle("image:edit", async (_event, { modelId, prompt, imageDataUrl }) => {
  const model = MODELS[modelId];
  if (!model) throw new Error(`Unknown model: ${modelId}`);

  const key = await getApiKey();
  if (!key) throw new Error("No fal.ai API key configured. Open Settings to add one.");

  fal.config({ credentials: key });

  const blob = await (await fetch(imageDataUrl)).blob();
  const uploadedUrl = await fal.storage.upload(blob);

  const result = await fal.subscribe(model.endpoint, {
    input: model.buildInput(prompt, [uploadedUrl]),
    logs: false,
  });

  const images = result.data?.images;
  if (!images || images.length === 0) {
    throw new Error("Model returned no images.");
  }
  return { imageUrl: images[0].url };
});
