import "dotenv/config";
import { readFile } from "node:fs/promises";
import { Bot, InlineKeyboard, InputFile } from "grammy";
import type { EditQuality, ImageEditor, PromptEngineer } from "./core/types.js";
import { EditorRegistry } from "./core/registry.js";
import { allEditors } from "./editors/index.js";
import { allEngineers } from "./engineers/index.js";

// Same hidden-identity philosophy as the web app (src/server.ts) — real
// model ids never reach the user, only confidential codenames. Kept in sync
// by hand with server.ts's EDITOR_CODENAMES; if a third codename is ever
// added there, add it here too.
const BOT_ENGINEER_ID = "natural-passthrough";

const registry = new EditorRegistry();
for (const editor of allEditors) {
  registry.register(editor);
}

const EDITOR_CODENAMES: Record<string, ImageEditor> = {
  banana: registry.select("nano-banana-pro"),
  dream: registry.select("seedream-5-pro"),
};

const EDITOR_LABELS: Record<string, string> = {
  banana: "Studio 1",
  dream: "Studio 2",
};

const engineers: Record<string, PromptEngineer> = Object.fromEntries(
  allEngineers.map((engineer) => [engineer.id, engineer]),
);

const token = process.env.BOT_TOKEN;
if (!token) {
  throw new Error(
    "BOT_TOKEN is not set. Copy .env.example to .env and fill it in.",
  );
}

const bot = new Bot(token);

bot.use(async (ctx, next) => {
  console.log(
    `[update ${ctx.update.update_id}] chat=${ctx.chat?.id} type=${
      ctx.message
        ? Object.keys(ctx.message)
            .filter((k) => !["message_id", "date", "chat", "from"].includes(k))
            .join(",")
        : ctx.callbackQuery
          ? "callback_query"
          : "other"
    }`,
  );
  await next();
});

interface PendingEdit {
  image: Buffer;
  instruction?: string;
  editorCodename?: string;
}

// Per-chat conversation state — a photo (and optionally its caption as the
// instruction) waits here until an instruction, an editor choice, and a
// quality choice are all in hand.
const pending = new Map<number, PendingEdit>();

function editorKeyboard(): InlineKeyboard {
  const keyboard = new InlineKeyboard();
  for (const [codename, label] of Object.entries(EDITOR_LABELS)) {
    keyboard.text(label, `editor:${codename}`);
  }
  return keyboard;
}

// Costs pulled live from each codenamed editor's own costForQuality() —
// never a static/duplicated number, same fix applied to WEB_QUALITY_COSTS
// in src/server.ts.
function qualityKeyboard(editor: ImageEditor): InlineKeyboard {
  const natural = editor.costForQuality?.("natural");
  const upscale = editor.costForQuality?.("upscale");
  return new InlineKeyboard()
    .text(
      natural === undefined ? "Natural" : `Natural — $${natural.toFixed(2)}`,
      "quality:natural",
    )
    .text(
      upscale === undefined ? "Upscale" : `Upscale — $${upscale.toFixed(2)}`,
      "quality:upscale",
    );
}

async function downloadTelegramFile(fileId: string): Promise<Buffer> {
  const file = await bot.api.getFile(fileId);
  const url = `https://api.telegram.org/file/bot${token}/${file.file_path}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(
      `Failed to download Telegram file: ${response.status} ${response.statusText}`,
    );
  }
  return Buffer.from(await response.arrayBuffer());
}

bot.command("start", async (ctx) => {
  await ctx.reply(
    'Send me a photo with a caption describing the edit (e.g. "change my shirt to blue"), ' +
      "or send the photo first and I'll ask what edit you want.",
  );
});

bot.on("message:photo", async (ctx) => {
  const photos = ctx.message.photo;
  const largest = photos[photos.length - 1];
  if (!largest) return;

  const image = await downloadTelegramFile(largest.file_id);
  const caption = ctx.message.caption?.trim();

  if (caption) {
    pending.set(ctx.chat.id, { image, instruction: caption });
    await ctx.reply("Pick a style:", { reply_markup: editorKeyboard() });
  } else {
    pending.set(ctx.chat.id, { image });
    await ctx.reply("Got the photo — now tell me what edit you'd like.");
  }
});

bot.on("message:text", async (ctx) => {
  const existing = pending.get(ctx.chat.id);
  if (!existing) {
    await ctx.reply("Send a photo first, then describe the edit.");
    return;
  }
  if (existing.instruction) {
    // Already have an instruction and are waiting on a style/quality tap — ignore stray text.
    return;
  }

  existing.instruction = ctx.message.text.trim();
  await ctx.reply("Pick a style:", { reply_markup: editorKeyboard() });
});

bot.on("callback_query:data", async (ctx) => {
  const data = ctx.callbackQuery.data;
  const chatId = ctx.callbackQuery.message?.chat.id;
  if (chatId === undefined) {
    await ctx.answerCallbackQuery();
    return;
  }

  if (data.startsWith("editor:")) {
    const codename = data.slice("editor:".length);
    const editor = EDITOR_CODENAMES[codename];
    const job = pending.get(chatId);
    if (!job || !job.instruction || !editor) {
      await ctx.answerCallbackQuery({
        text: "Nothing pending — send a photo first.",
      });
      return;
    }

    job.editorCodename = codename;
    await ctx.answerCallbackQuery();
    await ctx.editMessageText("Pick a quality:", {
      reply_markup: qualityKeyboard(editor),
    });
    return;
  }

  if (!data.startsWith("quality:")) return;

  const quality = data.slice("quality:".length) as EditQuality;
  const job = pending.get(chatId);
  const editor = job?.editorCodename
    ? EDITOR_CODENAMES[job.editorCodename]
    : undefined;
  if (!job || !job.instruction || !editor) {
    await ctx.answerCallbackQuery({
      text: "Nothing pending — send a photo and pick a style first.",
    });
    return;
  }

  pending.delete(chatId);
  await ctx.answerCallbackQuery();
  await ctx.editMessageText(`Editing (${quality})…`);

  const engineer = engineers[BOT_ENGINEER_ID];
  if (!engineer) {
    await ctx.reply("Internal error: engineer not configured.");
    return;
  }
  if (!editor.isAvailable()) {
    await ctx.reply("Image editor is not available (missing FAL_KEY?).");
    return;
  }

  try {
    const engineered = await engineer.engineer({
      image: job.image,
      userPrompt: job.instruction,
    });
    const result = await editor.edit({
      image: job.image,
      instruction: engineered.instruction,
      quality,
    });

    // Sent as a document, not sendPhoto — Telegram's photo pipeline always
    // re-encodes/compresses, which would undo the natural-passthrough
    // engineer's whole point (no oversharpening, no AI-glow, no re-compression).
    const resultBuffer = await readFile(result.imagePath);
    await ctx.replyWithDocument(new InputFile(resultBuffer, "edited.png"), {
      caption: `${result.width}x${result.height}`,
    });
  } catch (err) {
    await ctx.reply(`Edit failed: ${(err as Error).message}`);
  }
});

bot.catch((err) => {
  console.error("Bot error:", err);
});

async function main(): Promise<void> {
  const me = await bot.api.getMe();
  console.log(`Telegram bot @${me.username} starting...`);
  await bot.start({
    onStart: (info) => console.log(`Long polling active as @${info.username}`),
  });
}

main().catch((err) => {
  console.error("Fatal bot error:", err);
  process.exit(1);
});
