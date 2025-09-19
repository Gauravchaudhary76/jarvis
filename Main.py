from Frontend.GUI import (
    AnswerModifier,
    QueryModifier,
    GetassistantStatus,
    SetassistantStatus,
    ShowtextToScreen,
    TempDirectorypath,
    GetMicrophoneStatus,
    GraphicalUserInterface,
    SetMicrophoneStatus
)
from Backened.Model import FirstLayerDMW
from Backened.RealtimeSearchEngine import RealtimeSearchEngine
from Backened.Automation import Automation
from Backened.SpeechToText import JarvisSpeechRecognition
import asyncio
from Backened.Chatbot import ChatBot
from Backened.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
AssistantName = env_vars.get("AssistantName")
DefaultMessage = f'''{Username}: Hello {AssistantName}, How are you?\n{AssistantName}: Welcome {Username}, I am doing well, How can I help you today?'''
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]


def ShowDefaultChatIfNochats():
    File = open(r'Data\ChatLog.json', "r", encoding='utf-8')
    if len(File.read()) < 5:
        with open(TempDirectorypath('Database.data'), 'w', encoding='utf-8') as file:
            file.write("")
        with open(TempDirectorypath('Response.data'), 'w', encoding='utf-8') as file:
            file.write(DefaultMessage)


def ReadChatLogJson():
    with open(r'Data\ChatLog.json', "r", encoding='utf-8') as file:
        chatlog_data = json.load(file)
    return chatlog_data


def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User:{entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant:{entry['content']}\n"
    formatted_chatlog = formatted_chatlog.replace("User:", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant:", AssistantName + " ")
    with open(TempDirectorypath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))


def ShowChatOnGUI():
    File = open(TempDirectorypath('Database.data'), "r", encoding='utf-8')
    Data = File.read()
    if len(str(Data)) > 0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        File.close()
    File = open(TempDirectorypath('Response.data'), "w", encoding='utf-8')
    File.write(result)
    File.close()


def InitialExecuton():
    SetassistantStatus("False")
    ShowtextToScreen("")
    ShowDefaultChatIfNochats()
    ChatLogIntegration()
    ShowChatOnGUI()



# --- Speech recognizer instance setup ---
try:
    print("Initializing Speech Recognition Engine...")
    speech_recognizer = JarvisSpeechRecognition()
    speech_recognizer.create_html_file()
    speech_recognizer.start_server()
    if not speech_recognizer.setup_driver():
        raise RuntimeError("Failed to setup Selenium driver for speech recognition.")
    print("Speech Recognition Engine Ready.")
except Exception as e:
    print(f"FATAL ERROR during STT setup: {e}")
    speech_recognizer = None

def MainExecution():
    if not speech_recognizer:
        print("Speech recognizer is not available.")
        sleep(2)
        return

    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""
    SetassistantStatus("Listening...")
    Query = speech_recognizer.recognize()
    if not Query:
        return
    ShowtextToScreen(f"{Username} : {Query}")
    SetassistantStatus("thinking...")
    Decision = FirstLayerDMW(Query)
    print("")
    print(f"Decision : {Decision}")
    print("")

    # Image generation logic
    image_tasks = [d for d in Decision if d.startswith("generate image")]
    if image_tasks:
        ImageGenerationQuery = image_tasks[0].replace("generate image", "").strip()
        ImageExecution = True

    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])
    Mearged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )
    for queries in Decision:
        if not TaskExecution:
            if any(queries.startswith(func) for func in Functions):
                asyncio.run(Automation(list(Decision)))
                TaskExecution = True
    if ImageExecution:
        with open(r"Frontend\Files\ImageGeneration.data", "w") as file:
            file.write(f"{ImageGenerationQuery},True")
        try:
            p1 = subprocess.Popen(['python', r'Backened\ImageGeneration.py'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE, shell=False)
            subprocesses.append(p1)
        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")
    if (G and R) or R:
        SetassistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Mearged_query))
        ShowtextToScreen(f"{AssistantName} : {Answer}")
        SetassistantStatus("Answering...")
        TextToSpeech(Answer)
        return True
    else:
        for Queries in Decision:
            if "general" in Queries:
                SetassistantStatus("Thinking...")
                QueryFinal = Queries.replace("general", "")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowtextToScreen(f"{AssistantName} : {Answer}")
                SetassistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            elif "realtime" in Queries:
                SetassistantStatus("Searching...")
                QueryFinal = Queries.replace("realtime", "")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                ShowtextToScreen(f"{AssistantName} : {Answer}    ")
                SetassistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowtextToScreen(f"{AssistantName} : {Answer}")
                SetassistantStatus("Answering...")
                TextToSpeech(Answer)
                SetassistantStatus("Answering...")
                os._exit(1)


def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()
        if CurrentStatus == "True":
            MainExecution()
        else:
            AIStatus = GetassistantStatus()
            if "Available..." in AIStatus:
                sleep(0.1)
            else:
                SetassistantStatus("Available...")


def SecondThread():
    GraphicalUserInterface()


if __name__ == "__main__":
    InitialExecuton()
    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread1.start()
    SecondThread()