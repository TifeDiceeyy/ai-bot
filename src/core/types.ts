export type EditQuality = "natural" | "upscale";

export interface EditInput {
  image: Buffer;
  instruction: string;
  /** Optional — editors that don't support a resolution knob ignore this. */
  quality?: EditQuality;
}

export interface EditResult {
  imagePath: string;
  width: number;
  height: number;
  costUsd?: number;
}

export type License = "commercial-ok" | "non-commercial";

export interface ImageEditor {
  id: string;
  license: License;
  isAvailable(): boolean;
  edit(input: EditInput): Promise<EditResult>;
  /** Real cost at a given quality tier, if this editor supports one — lets
   * callers show accurate pricing upfront without duplicating a cost table. */
  costForQuality?(quality: EditQuality): number | undefined;
}

export interface EngineerInput {
  image: Buffer;
  userPrompt: string;
}

export interface EngineerOutput {
  instruction: string;
}

export interface PromptEngineer {
  id: string;
  engineer(input: EngineerInput): Promise<EngineerOutput>;
}
