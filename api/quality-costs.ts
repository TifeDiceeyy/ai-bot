import type { VercelRequest, VercelResponse } from "@vercel/node";
import { WEB_QUALITY_COSTS } from "./_lib.js";

export default function handler(req: VercelRequest, res: VercelResponse): void {
  if (req.method !== "GET") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }
  res.status(200).json(WEB_QUALITY_COSTS);
}
