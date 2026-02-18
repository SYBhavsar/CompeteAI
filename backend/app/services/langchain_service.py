from typing import Dict, Optional
from langchain_core.language_models.chat_models import BaseChatModel
import logging
from openai import OpenAIError

from app.core.llm_factory import LLMFactory
from app.core.prompt_loader import PromptLoader
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)



class LangChainService:
    """Service for advanced AI workflows using LangChain"""

    def __init__(self):
        """Initialize LangChain service with a per-service LLM cache."""
        self._llm_cache: Dict[str, BaseChatModel] = {}
        logger.info("LangChainService initialized.")

    def _get_llm(self, service_name: str) -> BaseChatModel:
        """Return a cached LLM for the given service, creating it if needed."""
        if service_name not in self._llm_cache:
            self._llm_cache[service_name] = LLMFactory.create(service_name)
        return self._llm_cache[service_name]

    def analyze_competitive_intelligence(self, content: str) -> Optional[str]:
        """
        Analyze content for competitive intelligence insights

        Args:
            content: Raw content to analyze

        Returns:
            Strategic analysis or None on error
        """
        logger.debug("Starting competitive intelligence analysis.")
        try:
            result = self._analyze_with_retry(content)
            logger.info("Successfully completed competitive intelligence analysis.")
            return result
        except Exception as e:
            logger.error(f"Failed to analyze competitive intelligence after retries. Error: {e}", exc_info=True)
            return None

    @retry_with_backoff(exceptions=(OpenAIError, Exception))
    def _analyze_with_retry(self, content: str) -> str:
        """Internal method with retry logic"""
        prompt = self._create_competitive_analysis_prompt(content)
        response = self._get_llm("competitive_analysis").invoke(prompt)
        return response.content

    def generate_summary(self, content: str) -> Optional[str]:
        """
        Generate concise summary of content

        Args:
            content: Content to summarize

        Returns:
            Summary text or None
        """
        logger.debug("Generating summary.")
        try:
            prompt_config = PromptLoader.load("summarization")
            user_msg = prompt_config.user_prompt.format(content=content)
            response = self._get_llm("summarization").invoke(user_msg)
            summary = response.content.strip()
            logger.info("Successfully generated summary.")
            return summary
        except Exception as e:
            logger.error(f"Failed to generate summary. Error: {e}", exc_info=True)
            return None

    def extract_strategic_insights(self, content: str) -> Optional[str]:
        """
        Extract strategic insights from content

        Args:
            content: Content to analyze

        Returns:
            Strategic insights or None
        """
        logger.debug("Extracting strategic insights.")
        try:
            prompt_config = PromptLoader.load("insight_extraction")
            user_msg = prompt_config.user_prompt.format(content=content)
            response = self._get_llm("insight_extraction").invoke(user_msg)
            insights = response.content.strip()
            logger.info("Successfully extracted strategic insights.")
            return insights
        except Exception as e:
            logger.error(f"Failed to extract strategic insights. Error: {e}", exc_info=True)
            return None

    def analyze_sentiment_with_reasoning(self, content: str) -> Optional[Dict[str, str]]:
        """
        Analyze sentiment with detailed reasoning

        Args:
            content: Content to analyze

        Returns:
            Dictionary with sentiment and reasoning
        """
        logger.debug("Analyzing sentiment with reasoning.")
        try:
            user_msg = (
                f"Analyze the sentiment of the following content.\n"
                f"Provide your response in the format: sentiment|reasoning\n"
                f"Where sentiment is one of: positive, negative, neutral\n\n"
                f"Content: {content}\n\nResponse:"
            )
            response = self._get_llm("sentiment_analysis").invoke(user_msg)
            result = response.content.strip()

            # Parse response
            if "|" in result:
                parts = result.split("|", 1)
                sentiment_data = {
                    "sentiment": parts[0].strip().lower(),
                    "reasoning": parts[1].strip()
                }
            else:
                sentiment_data = {
                    "sentiment": result.strip().lower(),
                    "reasoning": ""
                }
            
            logger.info(f"Successfully analyzed sentiment: {sentiment_data['sentiment']}")
            return sentiment_data
        except Exception as e:
            logger.error(f"Failed to analyze sentiment. Error: {e}", exc_info=True)
            return None

    def full_content_analysis(self, content: str) -> Optional[Dict[str, str]]:
        """
        Perform full analysis chain: summary, insights, and sentiment

        Args:
            content: Content to analyze

        Returns:
            Dictionary with summary, insights, and sentiment
        """
        logger.info("Starting full content analysis.")
        try:
            # Chain 1: Generate summary
            summary = self.generate_summary(content)

            # Chain 2: Extract strategic insights
            insights = self.extract_strategic_insights(content)

            # Chain 3: Analyze sentiment
            sentiment_result = self.analyze_sentiment_with_reasoning(content)
            sentiment = sentiment_result.get("sentiment", "neutral") if sentiment_result else "neutral"

            analysis_result = {
                "summary": summary or "",
                "insights": insights or "",
                "sentiment": sentiment
            }
            
            logger.info("Full content analysis completed successfully.")
            return analysis_result
        except Exception as e:
            logger.error(f"Full content analysis failed. Error: {e}", exc_info=True)
            return None

    def _create_competitive_analysis_prompt(self, content: str) -> str:
        """
        Create formatted prompt for competitive intelligence analysis.

        Args:
            content: Content to analyze

        Returns:
            Formatted prompt string
        """
        prompt_config = PromptLoader.load("competitive_analysis")
        return prompt_config.user_prompt.format(content=content)