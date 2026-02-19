# Import all models to ensure they're registered with SQLAlchemy
from .user import User
from .competitor import Competitor
from .data_source import DataSource
from .raw_content import RawContent
from .scraping_schedule import ScrapingSchedule
from .processed_insights import ProcessedInsights
from .alert import Alert, Notification
from .competitive_snapshot import CompetitiveSnapshot
from .change_detection import ChangeEvent
from .timeline import CompetitorTimeline
from .strategic_event import StrategicEvent
from .entity import Entity
from .entity_relationship import EntityRelationship
from .prediction import CompetitorPrediction

__all__ = [
    "User",
    "Competitor",
    "DataSource",
    "RawContent",
    "ScrapingSchedule",
    "ProcessedInsights",
    "Alert",
    "Notification",
    "CompetitiveSnapshot",
    "ChangeEvent",
    "CompetitorTimeline",
    "StrategicEvent",
    "Entity",
    "EntityRelationship",
    "CompetitorPrediction"
]