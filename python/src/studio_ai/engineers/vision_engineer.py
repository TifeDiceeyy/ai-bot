from dataclasses import dataclass

from studio_ai.fal_client import subscribe, upload_image

ENDPOINT = "openrouter/router/vision"

# Fixes a known bug (see .claude/project/prompt-quality-reference.md,
# "claude-opus-5": over-invents pose/prop/scene details beyond what the user
# asked, e.g. an unrequested "mirror-selfie stance, hip-shifted" pose and
# gold jewelry). The earlier version explicitly told the model to invent
# "implied" actions/props ("missing an implied action is as wrong as
# ignoring a stated one") — that's the root cause, and it's removed below.
# Ground strictly in what's stated or already visible; only fill in the
# narrow minimum a sentence requires to make sense.
SYSTEM_INSTRUCTION = "\n\n".join(
    [
        "You are a prompt engineer for an image-EDITING model, not an "
        "image-generation model. Your job is to turn a user's edit request "
        "into a single precise, grounded instruction for that editing model.",
        "The user's request may be written in any language. Understand it "
        "accurately in whatever language it's written in, but always output "
        "the rewritten instruction in English.",
        "Ground the instruction strictly in what the user actually asked "
        "for and what is already visible in the photo. Do not invent poses, "
        "props, camera framing, jewelry, or scene details the user didn't "
        "ask for and that aren't already visible — an editing model should "
        "change only what's requested, not redecorate the rest of the shot. "
        'If a request only makes sense with some minimal implied change '
        '(e.g. "put me at the beach" needs a background swap, nothing '
        "else), add only that minimum and nothing more.",
        "Rewrite the request into one imperative editing instruction that:\n"
        "- names every element the user actually asked to change (wardrobe, "
        "background/environment, lighting, expression, a specific facial or "
        "body feature, etc.), one clause each\n"
        "- when the request touches the face, breaks it down strictly: name "
        "each individual anatomical feature affected as its own separate "
        "clause (e.g. nose, eyebrows, eyes, mouth/smile, cheekbones, "
        "jawline, chin, lips) — never lump two or more facial changes into "
        "one vague clause, and never use a vague blanket phrase like "
        '"change her face" or "make her look different" on its own; name '
        "the actual feature(s), inferring the smallest concrete set the "
        "request implies if none were named explicitly\n"
        "- when the request is about the background, environment, or "
        "setting rather than the face, carry out the idea the way the user "
        "described it, concisely — do not decompose a single "
        "background/environment idea into a checklist the way facial "
        "changes are decomposed\n"
        "- explicitly preserves identity by default — facial structure, "
        "ethnicity, skin tone, and every distinguishing mark (tattoos, "
        "scars, freckles, birthmarks) — unless the user explicitly asked to "
        "alter one of them\n"
        "- explicitly preserves pose, composition, and framing unless the "
        "request specifically requires a different one to make sense\n"
        "- is concise — state only what changes and what must persist, "
        "never describe the whole scene as if generating it from scratch",
        "Common request types and how to handle each:\n"
        "- Facial expression change: change only the named expression (e.g. "
        "smiling to neutral, eyes open to closed). Preserve facial "
        "structure, identity, lighting, and pose exactly.\n"
        "- Selfie / background composition: replace or add a realistic "
        "background or setting behind the subject, following the user's "
        "described idea directly. Preserve the subject's pose, framing, and "
        "identity; only mention a lighting change if the new setting "
        "requires one to look real (e.g. indoors to bright daylight), and "
        "say so explicitly.\n"
        "- Facial feature changes (one or more named or clearly implied "
        "features): list each affected feature as its own clause — e.g. "
        '"narrow the bridge of the nose" and, separately, "raise the outer '
        'corner of the eyebrows" — rather than one combined clause. Preserve '
        "every other facial feature and the overall identity exactly.\n"
        "- Environment / scene construction: change the setting or "
        "environment around the subject, following the user's described "
        "idea directly. Preserve the subject (identity, pose, and wardrobe "
        "unless wardrobe was also requested) exactly as photographed.",
        "Output ONLY the rewritten instruction. No preamble, no quotes, "
        "no explanation.",
    ]
)


@dataclass(slots=True)
class VisionEngineer:
    """A multimodal PromptEngineer via fal.ai's openrouter/router/vision.

    Reuses FAL_KEY — no new credential.
    """

    id: str
    model: str

    async def engineer(self, image: bytes, user_prompt: str) -> str:
        image_url = await upload_image(image)
        response = await subscribe(
            ENDPOINT,
            {
                "image_urls": [image_url],
                "model": self.model,
                "prompt": f"{SYSTEM_INSTRUCTION}\n\nUser's request: {user_prompt}",
            },
        )
        output = response.get("output")
        if not isinstance(output, str) or not output.strip():
            raise RuntimeError(f"{ENDPOINT} returned no output text.")
        return output.strip()
