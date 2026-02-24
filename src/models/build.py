"""Build models for MES data."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class BuildStatus(Enum):
    """Build status values."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


@dataclass
class Build:
    """Represents a build/work order from the MES system."""
    build_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: BuildStatus

    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate build duration in minutes."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() / 60

    @classmethod
    def from_dict(cls, data: dict) -> "Build":
        """Create Build from dictionary."""
        status_str = data.get("status", "NOT_STARTED")
        try:
            status = BuildStatus(status_str)
        except ValueError:
            status = BuildStatus.NOT_STARTED

        start_time_str = data.get("start_time", "")
        end_time_str = data.get("end_time")

        start_time = datetime.fromisoformat(start_time_str) if start_time_str else datetime.min

        end_time = None
        if end_time_str:
            try:
                end_time = datetime.fromisoformat(end_time_str)
            except (ValueError, TypeError):
                end_time = None

        return cls(
            build_id=data.get("build_id", ""),
            start_time=start_time,
            end_time=end_time,
            status=status
        )
