from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os
import re
import datetime
import pyautogui
import pyttsx3

# Load environment variables
enc_vars = dotenv_values(".env")
GroqAPIKey = enc_vars.get("GroqAPIKey")

# Initialize Groq client
Client = Groq(api_key=GroqAPIKey)
professional_responses = [
    "Your satisfaction is my priority; feel free to reach out if there's anything else Ican help you with"
    "I'm at your service; please let me know if you need any further assistance",
]

messages = []
username = os.environ.get('USERNAME', 'User')
SystemChatBot = [{"role": "system", "content": f"Hello, I am {username}. You're a content writer. You have to write engaging and informative content based on the given topics."}]

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

# Text-to-speech

def tell_time():
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"⏰ Time: {now}")

def take_screenshot():
    path = os.path.join(os.getcwd(), f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    pyautogui.screenshot(path)
    print(f"📸 Screenshot saved to {path}")

def GoogleSearch(Topic):
    try:
        search(Topic)
        return True
    except Exception as e:
        print(f"Google search failed: {e}")
        return False

def Content(Topic):
    def OpenNotepad(File):
        try:
            subprocess.Popen(["notepad.exe", File])
        except Exception as e:
            print(f"Failed to open notepad: {e}")

    def ContentWriterAI(prompt):
        try:
            messages.append({"role": "user", "content": prompt})
            completion = Client.chat.completions.create(
                model="llama3-70b-8192",
                messages=SystemChatBot + messages,
                max_tokens=2048,
                temperature=0.7,
                top_p=1,
                stream=False
            )
            Answer = completion.choices[0].message.content
            messages.append({"role": "assistant", "content": Answer})
            return Answer
        except Exception as e:
            print(f"AI content generation failed: {e}")
            return "Failed to generate content."

    Topic = Topic.replace("Content ", "").replace("content ", "")
    ContentByAI = ContentWriterAI(Topic)

    os.makedirs("Data", exist_ok=True)
    filename = f"Data/{Topic.lower().replace(' ', '').replace('?', '').replace('!', '')}.txt"

    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(ContentByAI)
        OpenNotepad(filename)
        return True
    except Exception as e:
        print(f"Failed to save content: {e}")
        return False

def YoutubeSearch(Topic):
    try:
        Url4Search = f"https://www.youtube.com/results?search_query={Topic.replace(' ', '+')}"
        webbrowser.open(Url4Search)
        return True
    except Exception as e:
        print(f"YouTube search failed: {e}")
        return False

def OpenApp(app):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception as e:
        print(f"Failed to open app: {e}")
        try:
            html = search_google(f"{app} download")
            if html:
                links = extract_links(html)
                if links:
                    webopen(links[0])
                    return True
            return False
        except Exception as e:
            print(f"Fallback search failed: {e}")
            return False

def CloseApp(app):
    if "chrome" in app.lower():
        try:
            os.system("taskkill /f /im chrome.exe")
            return True
        except:
            return False
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)
            return True
        except Exception as e:
            print(f"Failed to close app: {e}")
            return False

def System(command):
    try:
        if command in ["mute", "mute system"]:
            keyboard.press_and_release("volume mute")
        elif command in ["unmute", "unmute system"]:
            keyboard.press_and_release("volume mute")
        elif command in ["volume up", "increase volume"]:
            keyboard.press_and_release("volume up")
        elif command in ["volume down", "decrease volume"]:
            keyboard.press_and_release("volume down")
        return True
    except Exception as e:
        print(f"System command failed: {e}")
        return False

def extract_links(html):
    if html is None:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', {'jsname': 'UWckNb'})
    return [link.get('href') for link in links if link.get('href')]

def search_google(query):
    url = f"https://www.google.com/search?q={query}"
    headers = {'User-Agent': useragent}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"Search request failed: {e}")
        return None
def split_multiple_commands(command):
    # Split using ' and ' or ',' as separator
    return [c.strip() for c in re.split(r'\s+and\s+|,', command) if c.strip()]
    
def parse_natural_command(command):
    command = command.strip().lower()

    if "time" in command:
        return "tell time"
    if "screenshot" in command:
        return "take screenshot"

    youtube_patterns = [r"search (.+) on youtube", r"youtube search (.+)", r"find (.+) on youtube", r"play (.+) on youtube"]
    google_patterns = [r"search (.+) on google", r"google search (.+)", r"search for (.+)", r"find (.+) on google", r"look up (.+)"]
    content_patterns = [r"write (.+) on notepad", r"write a (.+) on notepad", r"create (.+) content", r"generate content about (.+)", r"write about (.+)", r"content (.+)"]
    open_patterns = [r"open (.+)", r"launch (.+)", r"start (.+)"]
    close_patterns = [r"close (.+)", r"quit (.+)", r"exit (.+)"]
    system_patterns = ["mute system", "unmute system", "volume up", "volume down", "increase volume", "decrease volume", "turn up volume", "turn down volume"]

    for pattern in youtube_patterns:
        match = re.search(pattern, command)
        if match:
            return f"play {match.group(1)}"

    for pattern in google_patterns:
        match = re.search(pattern, command)
        if match:
            return f"google search {match.group(1)}"

    for pattern in content_patterns:
        match = re.search(pattern, command)
        if match:
            return f"content {match.group(1)}"

    for pattern in open_patterns:
        match = re.search(pattern, command)
        if match:
            return f"open {match.group(1)}"

    for pattern in close_patterns:
        match = re.search(pattern, command)
        if match:
            return f"close {match.group(1)}"

    for pattern in system_patterns:
        if pattern in command:
            if "mute" in command and "unmute" not in command:
                return "system mute"
            elif "unmute" in command:
                return "system unmute"
            elif "up" in command:
                return "system volume up"
            elif "down" in command:
                return "system volume down"

    return command

async def TranslateAndExecute(commands):
    funcs = []
    for original_command in commands:
        command = parse_natural_command(original_command)
        print(f"Parsed: '{original_command}' -> '{command}'")

        if command.startswith("open "):
            funcs.append(asyncio.to_thread(OpenApp, command.replace("open ", "")))
        elif command.startswith("close "):
            funcs.append(asyncio.to_thread(CloseApp, command.replace("close ", "")))
        elif command.startswith("play "):
            funcs.append(asyncio.to_thread(playonyt, command.replace("play ", "")))
        elif command.startswith("content "):
            funcs.append(asyncio.to_thread(Content, command.replace("content ", "")))
        elif command.startswith("google search "):
            funcs.append(asyncio.to_thread(GoogleSearch, command.replace("google search ", "")))
        elif command.startswith("youtube search "):
            funcs.append(asyncio.to_thread(YoutubeSearch, command.replace("youtube search ", "")))
        elif command.startswith("system "):
            funcs.append(asyncio.to_thread(System, command.replace("system ", "")))
        elif command == "tell time":
            funcs.append(asyncio.to_thread(tell_time))
        elif command == "take screenshot":
            funcs.append(asyncio.to_thread(take_screenshot))
        else:
            print(f"Could not parse command: {original_command}")

    if funcs:
        results = await asyncio.gather(*funcs, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Function {i} failed: {result}")
            elif result:
                yield result
    else:
        print("No valid commands to execute.")

async def Automation(user_inputs):
    all_commands = []
    for input_text in user_inputs:
        split_cmds = split_multiple_commands(input_text)
        all_commands.extend(split_cmds)

    print(f"Executing {len(all_commands)} command(s)...")
    success_count = 0
    async for result in TranslateAndExecute(all_commands):
        if result:
            success_count += 1
    print(f"✅ Completed {success_count} command(s) successfully.")

def get_user_commands():
    print("\n=== Personal Automation Assistant ===")
    print("Use natural commands like:")
    print("• 'play despacito on youtube'")
    print("• 'write an application for sick leave on notepad'")
    print("• 'google search python tutorial'")
    print("• 'open calculator'")
    print("• 'volume up'")
    print("• 'what is the time'")
    print("• 'take screenshot'")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n👤 Enter command: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Exiting...")
                break
            elif user_input == '':
                continue
            asyncio.run(Automation([user_input]))
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

# Run the assistant
if __name__ == "__main__":
    get_user_commands()
