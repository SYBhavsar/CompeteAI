import os
import logging
from typing import Optional
from openai import OpenAI, OpenAIError

from app.core.config import settings
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API client for content processing"""

    def __init__(self, model: Optional[str] = None):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = model or settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens
    
    @retry_with_backoff(exceptions=(OpenAIError,))
    def summarize_content(self, content: str) -> Optional[str]:
        """Summarize content using OpenAI with retry logic"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a competitive intelligence analyst. Summarize the following content in 2-3 sentences, focusing on key business insights."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=min(150, self.max_tokens),
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to summarize content: {str(e)}")
            return None
    
    @retry_with_backoff(exceptions=(OpenAIError,))
    def extract_insights(self, content: str) -> Optional[str]:
        """Extract key insights from content with retry logic"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a competitive intelligence analyst. Extract the most important business insights from the following content. Focus on strategic information, product updates, market positioning, or competitive advantages."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=min(200, self.max_tokens),
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to extract insights: {str(e)}")
            return None
    
    @retry_with_backoff(exceptions=(OpenAIError,))
    def analyze_sentiment(self, content: str) -> Optional[str]:
        """Analyze sentiment of content with retry logic"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the sentiment of the following content. Respond with only one word: 'positive', 'negative', or 'neutral'."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=10,
                temperature=0.1
            )
            return response.choices[0].message.content.strip().lower()
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {str(e)}")
            return None