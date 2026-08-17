from studio_ai.editors.fal_editor import FalEditor, QualityTier


def create_editors() -> list[FalEditor]:
    return [
        FalEditor(
            id="nano-banana-pro",
            endpoint="fal-ai/nano-banana-pro/edit",
            quality={
                "natural": QualityTier({"resolution": "1K"}, 0.15),
                "upscale": QualityTier({"resolution": "4K"}, 0.30),
            },
        ),
        FalEditor(
            id="flux-2-klein-4b",
            endpoint="fal-ai/flux-2/klein/4b/edit",
        ),
        FalEditor(
            id="qwen-image-edit-2511",
            endpoint="fal-ai/qwen-image-edit-2511",
        ),
        FalEditor(
            id="flux-kontext-pro",
            endpoint="fal-ai/flux-pro/kontext",
            image_input_mode="url",
        ),
        FalEditor(
            id="gpt-image-1-edit",
            endpoint="fal-ai/gpt-image-1/edit-image",
        ),
        FalEditor(
            id="seedream-5-pro",
            endpoint="bytedance/seedream/v5/pro/edit",
            quality={
                "natural": QualityTier(
                    {"image_size": {"width": 1024, "height": 1024}}, 0.0675
                ),
                "upscale": QualityTier(
                    {"image_size": {"width": 2048, "height": 2048}}, 0.135
                ),
            },
        ),
    ]


__all__ = ["FalEditor", "QualityTier", "create_editors"]
