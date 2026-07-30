const modelSelect = document.getElementById("modelSelect");
const promptInput = document.getElementById("promptInput");
const pickBtn = document.getElementById("pickBtn");
const editBtn = document.getElementById("editBtn");
const saveBtn = document.getElementById("saveBtn");
const statusEl = document.getElementById("status");
const originalImg = document.getElementById("originalImg");
const editedImg = document.getElementById("editedImg");

const settingsBtn = document.getElementById("settingsBtn");
const settingsDialog = document.getElementById("settingsDialog");
const apiKeyInput = document.getElementById("apiKeyInput");
const saveKeyBtn = document.getElementById("saveKeyBtn");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const settingsStatus = document.getElementById("settingsStatus");

let currentImageDataUrl = null;

function setStatus(text) {
  statusEl.textContent = text;
}

async function init() {
  const models = await window.api.listModels();
  modelSelect.innerHTML = models
    .map((m) => `<option value="${m.id}">${m.label}</option>`)
    .join("");

  const { hasKey } = await window.api.getKeyStatus();
  if (!hasKey) {
    setStatus("No fal.ai API key set — open Settings (⚙) to add one.");
    settingsDialog.showModal();
  }
}

pickBtn.addEventListener("click", async () => {
  const picked = await window.api.pickImage();
  if (!picked) return;
  currentImageDataUrl = picked.dataUrl;
  originalImg.src = picked.dataUrl;
  editedImg.src = "";
  editBtn.disabled = false;
  saveBtn.disabled = true;
  setStatus("Image loaded.");
});

editBtn.addEventListener("click", async () => {
  const prompt = promptInput.value.trim();
  if (!currentImageDataUrl) {
    setStatus("Choose an image first.");
    return;
  }
  if (!prompt) {
    setStatus("Enter edit instructions first.");
    return;
  }

  editBtn.disabled = true;
  saveBtn.disabled = true;
  setStatus("Editing… this can take 10-30s depending on the model.");

  try {
    const { imageUrl } = await window.api.editImage({
      modelId: modelSelect.value,
      prompt,
      imageDataUrl: currentImageDataUrl,
    });
    editedImg.src = imageUrl;
    saveBtn.disabled = false;
    setStatus("Done.");
  } catch (err) {
    setStatus(`Error: ${err.message}`);
  } finally {
    editBtn.disabled = false;
  }
});

saveBtn.addEventListener("click", async () => {
  if (!editedImg.src) return;
  setStatus("Saving…");
  try {
    const response = await fetch(editedImg.src);
    const blob = await response.blob();
    const buffer = await blob.arrayBuffer();
    const base64 = btoa(
      new Uint8Array(buffer).reduce((data, byte) => data + String.fromCharCode(byte), "")
    );
    const savedPath = await window.api.saveImage(`data:image/png;base64,${base64}`);
    setStatus(savedPath ? `Saved to ${savedPath}` : "Save cancelled.");
  } catch (err) {
    setStatus(`Save failed: ${err.message}`);
  }
});

settingsBtn.addEventListener("click", () => {
  settingsStatus.textContent = "";
  settingsDialog.showModal();
});

closeSettingsBtn.addEventListener("click", () => settingsDialog.close());

saveKeyBtn.addEventListener("click", async () => {
  try {
    await window.api.setApiKey(apiKeyInput.value);
    settingsStatus.textContent = "Saved.";
    apiKeyInput.value = "";
    setTimeout(() => settingsDialog.close(), 600);
    setStatus("");
  } catch (err) {
    settingsStatus.textContent = `Error: ${err.message}`;
  }
});

init();
