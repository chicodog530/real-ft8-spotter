import queue
import threading

class BackgroundAlertService:
    def __init__(self):
        self.queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def _worker_loop(self):
        import pyttsx3
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
        print(f"[VOICE ALERT]: {message}")
        self.queue.put(message)

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
