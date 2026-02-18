import pytest
from pydantic import ValidationError

from app.schemas.ai_responses import InsightsResult, SentimentResult, SummaryResult


def test_all_schemas_accept_valid_data():
    assert SummaryResult(summary="A brief summary.").summary == "A brief summary."
    assert InsightsResult(insights="Key competitive insight.").insights == "Key competitive insight."
    assert SentimentResult(sentiment="positive").sentiment == "positive"
    assert SentimentResult(sentiment="negative").sentiment == "negative"
    assert SentimentResult(sentiment="neutral").sentiment == "neutral"


def test_sentiment_rejects_invalid_value():
    with pytest.raises(ValidationError):
        SentimentResult(sentiment="happy")
