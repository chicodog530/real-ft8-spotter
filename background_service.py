import pyttsx3
import threading

class BackgroundAlertService:
    def __init__(self):
        self.engine = None
        self.initialize_tts()
        
    def initialize_tts(self):
        try:
            self.engine = pyttsx3.init()
            # Set a slightly slower rate for clarity
            rate = self.engine.getProperty('rate')
            self.engine.setProperty('rate', max(100, rate - 20))
        except Exception as e:
            print(f"Error initializing TTS: {e}")
            self.engine = None

    def _speak_thread(self, message):
        try:
            # pyttsx3 must be instantiated per-thread to avoid loop errors
            import pyttsx3
            engine = pyttsx3.init()
            # Set a static comfortable reading rate (default is usually 200)
            engine.setProperty('rate', 150)
            engine.say(message)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

    def announce(self, message):
        """Speaks the message in a non-blocking background thread."""
        print(f"[VOICE ALERT]: {message}")
        t = threading.Thread(target=self._speak_thread, args=(message,))
        t.daemon = True
        t.start()

# Example usage
if __name__ == "__main__":
    service = BackgroundAlertService()
    service.announce("DX Alert. Twenty meters is opening to Europe.")
    import time
    time.sleep(3) # Wait for thread to finish in test
