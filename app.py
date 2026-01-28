import os
from dotenv import load_dotenv
from modules.discord.bot import start_bot

load_dotenv()

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("MISSING DISCORD_TOKEN")
        return

    print("Starting Bot...")
    start_bot(token)

if __name__ == "__main__":
    main()
