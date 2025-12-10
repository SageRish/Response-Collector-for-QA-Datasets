from datetime import datetime

class Logger:
    def __init__(self):
        self.logs = []

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.logs.append(formatted_message)
        return self.get_logs()

    def get_logs(self) -> str:
        return "\n".join(self.logs)

    def clear(self):
        self.logs = []
