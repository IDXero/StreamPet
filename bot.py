import time
import twitchio
from twitchio.ext import commands

from config import cfg
import llm
import tts
from server import broadcast_event


class StreamPetBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=cfg.TWITCH_TOKEN,
            prefix="!",
            initial_channels=[cfg.TWITCH_CHANNEL],
        )
        self._cooldowns: dict[str, float] = {}

    async def event_ready(self):
        print(f"[Bot] Connected as {self.nick} | Channel: #{cfg.TWITCH_CHANNEL}")

    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        await self.handle_commands(message)

    @commands.command(name="ask")
    async def ask_command(self, ctx: commands.Context):
        username = ctx.author.name
        question = ctx.message.content[len("!ask"):].strip()

        if not question:
            await ctx.send(f"@{username} Ask me something! Usage: !ask <your question>")
            return

        # Per-user cooldown
        now = time.time()
        last = self._cooldowns.get(username, 0)
        remaining = cfg.COOLDOWN_SECONDS - (now - last)
        if remaining > 0:
            await ctx.send(f"@{username} Slow down! Try again in {int(remaining)+1}s.")
            return
        self._cooldowns[username] = now

        # Signal pet is thinking
        await broadcast_event({"type": "thinking", "username": username, "question": question})
        await ctx.send(f"@{username} Let me think... 🐾")

        # Ask the LLM
        answer = await llm.ask(question, username)
        if not answer:
            await broadcast_event({"type": "error", "username": username})
            await ctx.send(f"@{username} My brain is offline right now! Try again later.")
            return

        # Generate TTS audio
        audio_url = await tts.synthesize(answer)

        # Broadcast to browser source
        await broadcast_event({
            "type": "speak",
            "username": username,
            "question": question,
            "answer": answer,
            "audioUrl": audio_url,
        })

        # Post answer in chat (truncated for readability)
        chat_answer = answer if len(answer) <= 200 else answer[:197] + "..."
        await ctx.send(f"@{username} {chat_answer}")
