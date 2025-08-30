from Frontend.GUI import(
    grpahicaluserInterface,
    setassistanceStatus,
    ShowTextToScreen,
    TempDirectorPath,
    SetMicrphoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStauts,
    GetAssistantStatus
)
from Backened.Model import FirstLayerDMM
from Backened.RealtimeSearchEngine import RealtimeSearch
from Backened.Automation import Automation
from Backened.SpeechToText import SpeechRecognition
from Backened.Chatbot import Chatbot
from Backened.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os 
env_vars = dotenv_values(".env")
USername = env_vars.get("Username")
AssistantName = env_vars.get("AssistantName")
DefaultMessage =f ''' {Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}, I am doing well, How can I help you today?''' 
subprocesses= []
Functions = ["open","close","play","system","content","google search","youtube search"]
def ShowDefaultChatIfNochats():
    File = open(r'Data\ChatLog.json',"r",encoding='utf-8')
    if len(File.read())<5:
        with open(TempDirectoryPath('Database.data'),'w', encoding='utf-8') as file:
            file.write("")
        with open(TempDirectoryPath('Response.data'), 'w',encoding='utf-8') as file:
            file.write(DefaultMessage)   
def ReadChatLogJson():
    with open(r'Data\ChatLog.json',"r",encoding='utf-8') as file:
        chatlog_data = json.load(file)
    return chatlog_data
def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"]=="user":
             formatted_chatlog += f"User:{entry['content']}\n"
        elif entry["role"] =="assistant":
                formatted_chatlog += f"Assistant:{entry['content']}\n"
    formatted_chatlog =formatted_chatlog.replace("User:", Username + " ")
    formatted_chatlog =formatted_chatlog.replace("Assistant:", AssistantName + " ")
    with open(TempDirectoryPath('Database.data'),'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))
def ShowChatOnGUI():
    File = open(TempDirectoryPath('Database.data'),"r",encoding='utf-8')
    Data =File.read()
    if len(str(Data))>0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        File.close()
        File = open(TempDirectoryPath('Response.data'),"w",encoding='utf-8')
        File.write(result)
        File.close()
def InitialExecuton():
    SetMicrophonesStatus("False")
    ShowTextToScreen("")   
    ShowDefaultChatIfNochats()
    ChatLogIntegration()
    ShowChatOnGUI()
InitialExecution()
def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""
    SetAssistantStatus("Listening...")
    Query =SpeechRecognition()
    ShowTexttoScreen(f"{Username} : {Query}")
    SetAssistanceStatus("thinking...")
    Decision = FirstLayerDMM(Query)
    print("")
    print(f"Decision : {Decision}")
    print("")
    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])
    Mearged_query = " and ".join(
        [" ".join(i.split()[1:])for i in Decision if i.startswith("general") or i.startswith("realtime")]

    )
    for queries in Decision:
        if  TaskExecution == false:
            if any(queries.startswith(func) for func in Functions):
                run(Automation(list(Decision)))
                TaskExecution = True
    if ImageExecution == True:
        with open(r"Fronted\Files\ImageGeneratoion.data", "w") as file:
            file.write(f"{ImageGenerationQuery},True")
        try:
            p1=subprocess.Popen(['python',r'backend\Imagegeneration.py'],
                                stdout=subprocess.PIPE, stderr= subprocess.PIPE,
                                stdin= subprocess.PIPE, shell= False)
            
            subprocesses.append(p1)
        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")  
    if G and R or R:
        SetAssistantStatus(" Searchinf...") 
        Answer = RealtimeSearchEngine(QueryModifier(Mearged_query))
        ShowTextToScreen(f"{AssistantName} : {Answer}")
        SetAssistantStatus(" Answering...")
        TextToSpeech(Answer)
        return True
    else:
        for Queries in Decision:
           if "general" in Queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("general","")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowtexttoScreen(f"{AssistantName} : {Answer}" )
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)    
                return True
           elif "realtime" in Queries:
               SetAssistantStatus("Searching...")
               QueryFinal = Queries.replace("realtime","")
               Answer = RealtimeSearch(QueryModifier(QueryFinal))
               ShowTextToScreen(f"{AssistantName} : {Answer}    ")
               SetAssistantStatus("Answering...")
               TextToSpeech(Answer)
               return True
           elif "exit" in Queries:
               QueryFinal = "Okay, Bye!"
               Answer = ChatBot(QueryModifier(QueryFinal))  
               ShowTextToScreen(f"{Assistantname} : {Answer}")  
               SetAssistantStatus("Answering...")
               TextToSpeech(Answer)
               SetAssistantStatus("Answering...")
               os,_exit(1)
def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()
        if CurrentStatus == "True":
            MainExecution()
        else:
            AIStatus = GetAssistantStatus()
            if "Available..." in AIStatus:
                sleep(0.1)
            else:
                SetAssistantStatus("Available...")
def SeconfThread():
    GraphicalUserInterface()
if _name_ == "_main_":
    thread2 = threading.thread(target = FirstThread,daemon = True)
    thread2.start()
    secondThread()    


 
                
