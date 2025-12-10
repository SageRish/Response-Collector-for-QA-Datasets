from dataclasses import dataclass
import time

@dataclass
class ProgressState:
    model_alias: str
    completed: int
    total: int
    start_time: float
    status: str = "Pending"

    @property
    def progress_pct(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100

    @property
    def eta_seconds(self) -> float:
        if self.completed == 0:
            return 0.0
        elapsed = time.time() - self.start_time
        avg_time_per_item = elapsed / self.completed
        remaining = self.total - self.completed
        return avg_time_per_item * remaining

    def to_list(self):
        eta_str = f"{int(self.eta_seconds)}s" if self.status == "Running" else "-"
        return [
            self.model_alias,
            f"{self.progress_pct:.1f}%",
            f"{self.completed}/{self.total}",
            eta_str,
            self.status
        ]
