import pyttsx3

class SpeechEngine:
    def __init__(self, rate=150, volume=1.0, voice_id=None):
        """Initialize the text-to-speech engine with customizable properties."""
        self.engine = pyttsx3.init()
        
        # Set speech rate (words per minute)
        self.set_rate(rate)

        # Set volume (0.0 to 1.0)
        self.set_volume(volume)

        # Set voice (Male/Female selection)
        self.set_voice(voice_id)

    def set_rate(self, rate):
        """Adjust speech speed (Default: 150 WPM)."""
        self.engine.setProperty('rate', rate)
        print(f"[INFO] Speech rate set to {rate} WPM")

    def set_volume(self, volume):
        """Adjust volume (0.0 to 1.0)."""
        self.engine.setProperty('volume', max(0.0, min(volume, 1.0)))  # Ensure within range
        print(f"[INFO] Volume set to {volume}")

    def set_voice(self, voice_id=None):
        """Change the voice (Male/Female) based on available system voices."""
        voices = self.engine.getProperty('voices')

        if voice_id is None:
            # Auto-select first available voice (default system voice)
            voice_id = voices[0].id if voices else None
        elif isinstance(voice_id, str):
            # Search for a voice containing the given keyword (e.g., "female" or "male")
            matching_voices = [v.id for v in voices if voice_id.lower() in v.name.lower()]
            if matching_voices:
                voice_id = matching_voices[0]  # Pick first match

        if voice_id:
            self.engine.setProperty('voice', voice_id)
            print(f"[INFO] Voice set to: {voice_id}")
        else:
            print("[WARNING] No matching voice found. Using default voice.")

    def list_voices(self):
        """Print available voices on the system."""
        voices = self.engine.getProperty('voices')
        for idx, voice in enumerate(voices):
            print(f"[{idx}] ID: {voice.id}, Name: {voice.name}, Lang: {voice.languages}")

    def speak(self, text):
        """Speak the given text."""
        print(f"[TTS] {text}")  # Print for debugging
        self.engine.say(text)
        self.engine.runAndWait()