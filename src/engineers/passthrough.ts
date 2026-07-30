import type { EngineerInput, EngineerOutput, PromptEngineer } from "../core/types.js";

/**
 * Baseline engineer: raw prompt straight to the model, unmodified. Per
 * CLAUDE.md §6, this must exist first so any real engineer can be measured
 * against it before it's trusted.
 */
export const passthrough: PromptEngineer = {
  id: "passthrough",

  async engineer(input: EngineerInput): Promise<EngineerOutput> {
    return { instruction: input.userPrompt };
  },
};
