import json
import os
import time
import asyncio
from typing import Any, List, Dict

class AsyncRateLimiter:
    def __init__(self, max_calls: int, period: float = 1.0):
        self.max_calls = max_calls
        self.period = period
        self.timestamps = []

    async def acquire(self):
        now = time.time()
        # Remove timestamps older than the period
        self.timestamps = [t for t in self.timestamps if now - t <= self.period]
        
        if len(self.timestamps) >= self.max_calls:
            # Wait until the oldest call expires
            sleep_time = self.timestamps[0] + self.period - now
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            # Re-check/clean after sleep
            now = time.time()
            self.timestamps = [t for t in self.timestamps if now - t <= self.period]
        
        self.timestamps.append(now)

def save_json(data: Any, filepath: str):
    """Saves data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_dataset_output(model_alias: str, data: List[List[Dict]]) -> Dict:
    """Formats the collected data for the final dataset output."""
    return {
        "model": model_alias,
        "data": data
    }
