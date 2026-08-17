class Passthrough:
    id = "passthrough"

    async def engineer(self, image: bytes, user_prompt: str) -> str:
        del image
        return user_prompt
