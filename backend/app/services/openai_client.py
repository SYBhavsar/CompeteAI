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
        try:
            api_key = settings.openai_api_key
            if not api_key:
                logger.error("OPENAI_API_KEY not found in environment variables.")
                raise ValueError("OPENAI_API_KEY is required for OpenAIClient.")

            self.client = OpenAI(api_key=api_key)
            self.model = model or settings.openai_model
            self.temperature = settings.openai_temperature
            self.max_tokens = settings.openai_max_tokens
            logger.info(f"OpenAIClient initialized with model: {self.model}, temperature: {self.temperature}")
        except Exception as e:
            logger.critical(f"Failed to initialize OpenAIClient: {e}", exc_info=True)
            raise
    
    @retry_with_backoff(exceptions=(OpenAIError,))
    def summarize_content(self, content: str) -> Optional[str]:
        """Summarize content using OpenAI with retry logic"""
        logger.debug(f"Summarizing content with model {self.model}.")
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
            summary = response.choices[0].message.content
            logger.info("Successfully summarized content.")
            return summary
        except OpenAIError as e:
            logger.warning(f"OpenAI API error during summarization, will retry... Error: {e}")
            raise  # Re-raise to allow retry decorator to work
        except Exception as e:
            logger.error(f"Failed to summarize content after retries. Error: {e}", exc_info=True)
            return None
    
    @retry_with_backoff(exceptions=(OpenAIError,))
    def extract_insights(self, content: str) -> Optional[str]:
        """Extract key insights from content with retry logic"""
        logger.debug(f"Extracting insights with model {self.model}.")
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
            insights = response.choices[0].message.content
            logger.info("Successfully extracted insights.")
            return insights
        except OpenAIError as e:
            logger.warning(f"OpenAI API error during insight extraction, will retry... Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract insights after retries. Error: {e}", exc_info=True)
            return None
    
    @retry_with_backoff(exceptions=(OpenAIError,))
    def analyze_sentiment(self, content: str) -> Optional[str]:
        """Analyze sentiment of content with retry logic"""
        logger.debug(f"Analyzing sentiment with model {self.model}.")
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
            sentiment = response.choices[0].message.content.strip().lower()
            # Basic validation
            if sentiment not in ['positive', 'negative', 'neutral']:
                logger.warning(f"Sentiment analysis returned an unexpected value: '{sentiment}'")
                return 'neutral' # Fallback to neutral
            
            logger.info(f"Successfully analyzed sentiment: {sentiment}")
            return sentiment
        except OpenAIError as e:
            logger.warning(f"OpenAI API error during sentiment analysis, will retry... Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to analyze sentiment after retries. Error: {e}", exc_info=True)
            return None