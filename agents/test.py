import os

from dotenv import load_dotenv

from dedalus_labs import Dedalus, DedalusRunner
from dedalus_labs.utils.streaming import stream_sync

load_dotenv()

def main():
    client = Dedalus()
    runner = DedalusRunner(client)

    result = runner.run(
        input="""Find the top five startup ideas in 2025, and handoff to Claude
        to write a single creative pitch that merges all 5 ideas. Output this pitch.
        Use your tools.""",
        model=[ "openai/gpt-4.1", "anthropic/claude-sonnet-4-20250514"],
        mcp_servers=["windsor/brave-search-mcp"],
        stream=True,

    )
    stream_sync(result)
    print()

if __name__ == "__main__":
    main()