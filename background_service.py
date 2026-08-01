import queue
import threading

class BackgroundAlertService:
    def __init__(self):
        self.queue = queue.Queue(maxsize=15) # Protect against TTS freezing
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def _worker_loop(self):
        import pyttsx3
        import platform
        if platform.system() == "Windows":
            try:
                import pythoncom
                pythoncom.CoInitialize() # Explicit COM initialization for Windows threads
            except ImportError:
                pass
                
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
        except Exception as e:
            print(f"Error initializing TTS: {e}")
            self.engine = None
            return

        while True:
            message = self.queue.get()
            if message == "__STOP__":
                break
            if message and self.engine:
                try:
                    self.engine.say(message)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"TTS Error: {e}")
            self.queue.task_done()

    def announce(self, message):
        """Adds a message to the voice queue."""
        try:
            self.queue.put(message, block=False)
            print(f"[VOICE ALERT]: {message}")
        except queue.Full:
            print(f"[VOICE ALERT DROPPED - QUEUE FULL]: {message}")

    def clear(self):
        """Clears the queue of any pending announcements."""
        # Empty the queue
        with self.queue.mutex:
            self.queue.queue.clear()
        
        # We can't interrupt runAndWait() safely cross-thread in pyttsx3, 
        # but clearing the queue ensures no subsequent alerts will play.

# Example usage
if __name__ == "__main__":
    service = BackgroundAlertService()
    service.announce("DX Alert. Twenty meters is opening to Europe.")
    import time
    time.sleep(3) # Wait for thread to finish in test
