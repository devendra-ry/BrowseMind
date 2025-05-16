from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, BrowserConfig
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

browser = Browser(
    config=BrowserConfig(
        chrome_instance_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    )
)

async def main():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    agent = Agent(
        task="Navigate to WhatsApp Web (https://web.whatsapp.com/) and locate the chat named ' '. Scroll through the past messages in the conversation to understand the context. Summarize the key discussion points from the last 40 messages. Based on the conversation history, craft a relevant response that contributes meaningfully to the discussion. Send the reply in the chat. Maximum steps: 80.",
        llm=llm,
        browser=browser
    )

    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())