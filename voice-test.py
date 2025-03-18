import pyttsx3
def test_tts():
    try:
        engine = pyttsx3.init()
        engine.say("Hello, testing speech synthesis")
        engine.runAndWait()
        print("TTS executed successfully.")
    except Exception as e:
        print(f"TTS Error: {e}")

test_tts()