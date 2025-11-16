import os
from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
from openai import OpenAIError

from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)



class LangChainService:
    """Service for advanced AI workflows using LangChain"""

    def __init__(self):
        """Initialize LangChain service with OpenAI LLM"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY not found in environment variables.")
                raise ValueError("OPENAI_API_KEY is required for LangChainService.")

            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.3,
                openai_api_key=api_key
            )
            logger.info("LangChainService initialized successfully with gpt-3.5-turbo.")
        except Exception as e:
            logger.critical(f"Failed to initialize LangChainService: {e}", exc_info=True)
            raise

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
        response = self.llm.invoke(prompt)
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
            template = """You are a competitive intelligence analyst.
            Summarize the following content in 2-3 concise sentences, focusing on key business insights:

            Content: {content}

            Summary:"""

            prompt = PromptTemplate(template=template, input_variables=["content"])
            formatted_prompt = prompt.format(content=content)
            
            response = self.llm.invoke(formatted_prompt)
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
            template = """As a competitive intelligence expert, analyze this content and extract strategic insights:
            Focus on: market positioning, competitive advantages, strategic moves, and business implications.

            Content: {content}

            Strategic Insights:"""

            prompt = PromptTemplate(template=template, input_variables=["content"])
            formatted_prompt = prompt.format(content=content)

            response = self.llm.invoke(formatted_prompt)
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
            template = """Analyze the sentiment of the following content.
            Provide your response in the format: sentiment|reasoning
            Where sentiment is one of: positive, negative, neutral

            Content: {content}

            Response:"""

            prompt = PromptTemplate(template=template, input_variables=["content"])
            formatted_prompt = prompt.format(content=content)

            response = self.llm.invoke(formatted_prompt)
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
        Create formatted prompt for competitive intelligence analysis

        Args:
            content: Content to analyze

        Returns:
            Formatted prompt string
        """
        return f"""You are an expert competitive intelligence analyst.
        Analyze the following content and provide strategic insights about the competitor's activities,
        market positioning, and business implications.

        Focus on:
        - Strategic moves and intent
        - Competitive advantages or weaknesses
        - Market positioning changes
        - Business impact and implications

        Content to analyze:
        {content}

        Competitive Intelligence Analysis:"""