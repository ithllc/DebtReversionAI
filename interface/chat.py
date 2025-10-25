import asyncio


class ChatInterface:
    def __init__(self, agent):
        self.agent = agent

    async def start(self):
        while True:
            try:
                user_input = await asyncio.to_thread(input, "You: ")
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break

                if not user_input:
                    continue

                print("\n🤔 Analyzing with Dedalus + Manus AI...")
                response = await self.agent.chat(user_input)
                print(f"\n🤖 DebtReversionAI: {response}\n")

            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
