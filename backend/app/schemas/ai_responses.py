"""
AI Response Schemas

Pydantic models used as structured output targets for LLM calls.
LangChain's .with_structured_output() enforces these at the API level
so callers always receive typed objects instead of raw strings.
"""
from typing import Literal
from pydantic import BaseModel, Field


class SummaryResult(BaseModel):
    summary: str = Field(description="2-3 sentence summary focusing on key business insights")


class InsightsResult(BaseModel):
    insights: str = Field(
        description="Key business insights covering strategic information, product updates, "
                    "market positioning, and competitive advantages"
    )


class SentimentResult(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"] = Field(
        description="Overall sentiment of the content"
    )
