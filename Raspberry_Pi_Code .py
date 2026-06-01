import os
import threading
import tkinter as tk
from time import sleep
from openai import OpenAI
import speech_recognition as sr
from gpiozero import Robot, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Hardware Setup
Device.pin_factory = LGPIOFactory()
bob_motors = Robot(left=(17, 18), right=(22, 23))

# OpenAI Setup - REVEALED KEY EXPIRED? Use a new one here.
client = OpenAI(api_key="YOUR_NEW_OPENAI_API_KEY_HERE")

class BobFace:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(background='black')
        self.canvas = tk.Canvas(
            self.root, 
            width=self.root.winfo_screenwidth(),
            height=self.root.winfo_screenheight(),
            bg='black', 
            highlightthickness=0
        )
        self.canvas.pack()
        self.active = False

    def wake_up(self):
        self.active = True
        self.canvas.configure(bg='#ADD8E6') # Light blue wake color
        self.draw_eyes()
        self.blink_loop()

    def go_to_sleep(self):
        self.active = False
        self.canvas.delete("all")
        self.canvas.configure(bg='black')

    def draw_eyes(self, open=True):
        self.canvas.delete("eye")
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        ew, eh = (100, 150) if open else (100, 10)
        
        # Left Eye
        self.canvas.create_oval(w/3-ew, h/2-eh, w/3+ew, h/2+eh, fill="white", tags="eye")
        # Right Eye
        self.canvas.create_oval(2*w/3-ew, h/2-eh, 2*w/3+ew, h/2+eh, fill="white", tags="eye")

    def blink_loop(self):
        if self.active:
            self.draw_eyes(open=False)
            self.root.after(200, lambda: self.draw_eyes(open=True))
            self.root.after(3000, self.blink_loop)

face = BobFace()

def speak(text):
    print(f"Bob says: {text}")
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        response.stream_to_file("output.mp3")
        os.system("mpg123 output.mp3 > /dev/null 2>&1")
    except Exception as e:
        print(f"Speech Error: {e}")

def robot_brain():
    recognizer = sr.Recognizer()
    # Adjust device_index based on your 'arecord -l' output
    mic = sr.Microphone(device_index=1)

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("System Initialized. Bob is listening...")

    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio).lower()
            print(f"You said: {text}")

            if "move forward" in text:
                speak("Moving Forward")
                face.wake_up()
                bob_motors.forward(speed=1.0)
            
            elif "move backward" in text or "go back" in text:
                speak("Moving Backward")
                face.wake_up()
                bob_motors.backward(speed=1.0)

            elif "stop" in text:
                speak("Stopping")
                bob_motors.stop()
                sleep(2)
                face.go_to_sleep()

            elif "how are you" in text:
                speak("I am doing great! My motors are a bit slow, but I am learning.")

            else:
                bob_motors.stop()

        except sr.UnknownValueError:
            print("Error: Could not understand audio")
        except sr.RequestError as e:
            print(f"Error: Could not request results; {e}")
        except Exception as e:
            print(f"General Error: {e}")
            continue

# Run the brain in a separate thread so the GUI doesn't freeze
threading.Thread(target=robot_brain, daemon=True).start()

# Start the Tkinter GUI loop
face.root.mainloop()
