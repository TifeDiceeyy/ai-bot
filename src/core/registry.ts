import type { ImageEditor } from "./types.js";

export class EditorRegistry {
  private editors = new Map<string, ImageEditor>();

  register(editor: ImageEditor): void {
    this.editors.set(editor.id, editor);
  }

  list(): ImageEditor[] {
    return [...this.editors.values()];
  }

  select(id: string): ImageEditor {
    const editor = this.editors.get(id);
    if (!editor) {
      throw new Error(`Unknown editor id: ${id}. Available: ${[...this.editors.keys()].join(", ")}`);
    }
    return editor;
  }

  filterByAvailable(): ImageEditor[] {
    return this.list().filter((editor) => editor.isAvailable());
  }
}
