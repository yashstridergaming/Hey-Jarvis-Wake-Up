import pyaudio
import speech_recognition as sr
import os
import time
import ctypes
import sys
import pyttsx3
import threading
import queue
import math
import struct

# ==========================================
# TEXT-TO-SPEECH (QUEUE SYSTEM)
# ==========================================
speech_queue = queue.Queue()

def speech_worker():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 170)
    
    while True:
        text = speech_queue.get()
        if text is None:
            break
        engine.say(text)
        engine.runAndWait()
        speech_queue.task_done()

threading.Thread(target=speech_worker, daemon=True).start()

def speak(text):
    print(f"\n[JARVIS]: {text}")
    speech_queue.put(text)

# --- Admin Check ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# --- App Open Function ---
def open_jarvis_app():
    app_path = r"C:\Users\YASH\Desktop\J.A.R.V.I.S.lnk" 
    try:
        speak("Opening Jarvis App...")
        result = ctypes.windll.shell32.ShellExecuteW(None, "open", app_path, None, None, 1)
        if result <= 32:
            print(f"Windows failed to open the file. Error code: {result}")
    except Exception as e:
        speak(f"Error opening file: {e}")

# ==========================================
# 1. TEXT COMMAND (Fallback Background)
# ==========================================
def listen_for_text():
    while True:
        command = input().lower()
        if "hey jarvis wake up" in command:
            speak("Text Command Matched! Access Granted.")
            open_jarvis_app()
            speech_queue.join()
            os._exit(0)

# ==========================================
# 2. STEP 1: CLAP DETECTION (2 Claps)
# ==========================================
def get_rms(data):
    count = len(data) // 2
    if count == 0:
        return 0
    shorts = struct.unpack(f"{count}h", data)
    sum_squares = sum(s * s for s in shorts)
    return int(math.sqrt(sum_squares / count))

def wait_for_two_claps():
    chunk = 1024
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=chunk)
    
    clap_count = 0
    threshold = 15000 
    last_clap_time = time.time()
    
    print("\n[STEP 1] Waiting for 2 Claps to arm the system...")
    
    while True:
        try:
            data = stream.read(chunk, exception_on_overflow=False)
            rms = get_rms(data) 
            
            if rms > threshold:
                current_time = time.time()
                if current_time - last_clap_time > 0.35: 
                    clap_count += 1
                    print(f"Clap {clap_count} detected!")
                    last_clap_time = current_time
                    
                if clap_count == 2:
                    # Stream close karo taaki speech_recognition microphone access le sake
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    return True
            
            # Agar doosri clap 3 second ke andar nahi aayi to reset
            if time.time() - last_clap_time > 3 and clap_count > 0:
                print("Clap timeout. Resetting count.")
                clap_count = 0
        except Exception:
            pass

# ==========================================
# 3. STEP 2: VOICE WAKE-UP
# ==========================================
def verify_voice_wake_up():
    r = sr.Recognizer()
    
    with sr.Microphone() as source:
        speak("2 Claps confirmed. Say: Hey Jarvis wake up.")
        r.adjust_for_ambient_noise(source, duration=0.8)
        
        print("\n[STEP 2] Listening for 'Hey Jarvis wake up' (5 seconds window)...")
        try:
            audio = r.listen(source, timeout=6, phrase_time_limit=4)
            command = r.recognize_google(audio).lower()
            print(f"Heard: '{command}'")
            
            if "jarvis" in command and "wake" in command:
                return True
            else:
                speak("Voice phrase did not match. Returning to standby.")
                return False
                
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            speak("No clear command heard. Standby mode active.")
            return False
        except sr.RequestError:
            print("[ERROR] Google API connection failed.")
            return False

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    if not is_admin():
        print("Requesting Admin rights...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    
    threading.Thread(target=listen_for_text, daemon=True).start()
    speak("Jarvis armed. Clap twice, then give wake up command.")
    
    while True:
        # Step 1: 2 Taali bajne ka wait karo
        if wait_for_two_claps():
            # Step 2: Taali bajte hi bolo 'Hey Jarvis wake up'
            if verify_voice_wake_up():
                speak("Access Granted. Welcome back, Sir.")
                open_jarvis_app()
                speech_queue.join()
                time.sleep(2)
                os._exit(0)
            else:
                # Agar voice match nahi hui, wapas 2 clap ka wait karega
                time.sleep(1)