import pyaudio
import audioop
import speech_recognition as sr
import os
import time
import ctypes
import sys
import pyttsx3
import threading

# --- Text-to-Speech (Voice) Setup ---
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) # 0 = Male Voice, 1 = Female Voice
engine.setProperty('rate', 170) # Bolne ki speed

def speak(text):
    print(f"\n[JARVIS]: {text}")
    engine.say(text)
    engine.runAndWait()

# --- Admin Check Function ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# --- App Open Function ---
def open_jarvis_app():
    # Aapka exact Jarvis file path
    app_path = r"C:\Users\YASH\Desktop\J.A.R.V.I.S.lnk" 
    
    try:
        speak("Opening Jarvis App...")
        # Yeh Windows ka native 'Double-Click' command hai
        # Kyunki script pehle se Admin hai, yeh bina kisi error ke direct khulega
        result = ctypes.windll.shell32.ShellExecuteW(None, "open", app_path, None, None, 1)
        
        if result <= 32:
            print(f"Windows failed to open the file. Error code: {result}")
    except Exception as e:
        speak(f"Error opening file: {e}")

# ==========================================
# 1. TEXT DETECTION (Background Thread)
# ==========================================
def listen_for_text():
    while True:
        # Yeh line terminal me aapki typing ka wait karegi
        command = input().lower()
        
        # Exact command match check for text input
        if "hey jarvis wake up" in command:
            speak("Text Command Matched! Access Granted.")
            open_jarvis_app()
            os._exit(0) # App khulne ke baad poore program ko band kar dega

# ==========================================
# 2. VOICE & CLAP DETECTION (Main Thread)
# ==========================================
def listen_for_claps():
    chunk = 1024
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=chunk)
    
    clap_count = 0
    threshold = 15000 
    last_clap_time = time.time()
    
    while True:
        data = stream.read(chunk)
        rms = audioop.rms(data, 2)
        
        if rms > threshold:
            current_time = time.time()
            if current_time - last_clap_time > 0.5: 
                clap_count += 1
                print(f"\nClap {clap_count} detected!")
                last_clap_time = current_time
                
            if clap_count == 2:
                speak("2 Claps detected! Mic is active now.")
                stream.stop_stream()
                stream.close()
                p.terminate()
                return True
        
        if time.time() - last_clap_time > 3 and clap_count > 0:
            print("\nTime out. Resetting clap count.")
            clap_count = 0

def listen_for_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Say Hey Jarvis wake up...")
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            command = r.recognize_google(audio).lower()
            print(f"\nYou said via Voice: {command}")
            
            if "hey jarvis wake up" in command or "jarvis wake up" in command:
                return True
        except sr.WaitTimeoutError:
            speak("No voice detected.")
        except sr.UnknownValueError:
            speak("Could not understand audio.")
    return False

# --- Main Execution ---
if __name__ == "__main__":
    # Agar script admin nahi hai, toh auto-admin mode me restart karo
    if not is_admin():
        print("Requesting Admin rights...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    
    # Text listening ko background (Daemon Thread) me start karo
    text_thread = threading.Thread(target=listen_for_text, daemon=True)
    text_thread.start()
    
    # Admin banne ke baad program shuru hoga
    speak("System is ready. Type 'hey jarvis wake up' in terminal OR physically clap 2 times to use voice.")
    
    # Clap aur voice ka loop
    while True:
        if listen_for_claps():
            if listen_for_voice():
                speak("Voice Command Matched! Access Granted.")
                open_jarvis_app()
                os._exit(0) # App khulne ke baad script ko band kar dega
            else:
                speak("Voice command failed. Going back to sleep. You can still type the command.")
                time.sleep(1)