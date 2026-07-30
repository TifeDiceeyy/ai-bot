interface EditResponse {
  imageBase64: string;
  width: number;
  height: number;
}

interface ErrorResponse {
  error: string;
}

type QualityCosts = Record<string, { natural?: number; upscale?: number }>;

function requireElement<T extends HTMLElement>(id: string): T {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing element #${id}`);
  return el as T;
}

const fileInput = requireElement<HTMLInputElement>("fileInput");
const instructionInput =
  requireElement<HTMLTextAreaElement>("instructionInput");
const editorSelect = requireElement<HTMLSelectElement>("editorSelect");
const qualitySelect = requireElement<HTMLSelectElement>("qualitySelect");
const runButton = requireElement<HTMLButtonElement>("runButton");
const statusEl = requireElement<HTMLParagraphElement>("status");
const beforeImage = requireElement<HTMLImageElement>("beforeImage");
const afterImage = requireElement<HTMLImageElement>("afterImage");
const downloadLink = requireElement<HTMLAnchorElement>("downloadLink");

let currentImageBase64: string | null = null;
let running = false;
let qualityCosts: QualityCosts | null = null;

function setStatus(message: string): void {
  statusEl.textContent = message;
}

function updateRunButtonEnabled(): void {
  runButton.disabled =
    running || !currentImageBase64 || instructionInput.value.trim() === "";
}

function updateQualityLabels(): void {
  const costs = qualityCosts?.[editorSelect.value];
  for (const option of Array.from(qualitySelect.options)) {
    const label = option.value === "natural" ? "Natural" : "Upscale";
    const cost = costs?.[option.value as "natural" | "upscale"];
    option.textContent =
      cost === undefined ? label : `${label} — $${cost.toFixed(2)}`;
  }
}

async function loadQualityCosts(): Promise<void> {
  const response = await fetch("/api/quality-costs");
  if (!response.ok) return;
  qualityCosts = (await response.json()) as QualityCosts;
  updateQualityLabels();
}

loadQualityCosts().catch(() => {
  /* Non-critical — options just keep their static labels without a price. */
});

editorSelect.addEventListener("change", updateQualityLabels);

fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    currentImageBase64 = reader.result as string;
    beforeImage.src = currentImageBase64;
    afterImage.src = "";
    downloadLink.hidden = true;
    updateRunButtonEnabled();
  };
  reader.readAsDataURL(file);
});

instructionInput.addEventListener("input", updateRunButtonEnabled);

runButton.addEventListener("click", async () => {
  if (!currentImageBase64) return;

  running = true;
  updateRunButtonEnabled();
  setStatus("Editing...");

  try {
    const response = await fetch("/api/edit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        imageBase64: currentImageBase64,
        instruction: instructionInput.value.trim(),
        quality: qualitySelect.value,
        editor: editorSelect.value,
      }),
    });

    if (!response.ok) {
      const err = (await response.json()) as ErrorResponse;
      throw new Error(err.error ?? `Request failed with ${response.status}`);
    }

    const result = (await response.json()) as EditResponse;
    afterImage.src = result.imageBase64;
    downloadLink.href = result.imageBase64;
    downloadLink.download = "edited.png";
    downloadLink.hidden = false;
    setStatus(`Done — ${result.width}x${result.height}`);
  } catch (err) {
    setStatus(`Error: ${(err as Error).message}`);
  } finally {
    running = false;
    updateRunButtonEnabled();
  }
});
