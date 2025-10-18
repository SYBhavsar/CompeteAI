import os
from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


class LangChainService:
    """Service for advanced AI workflows using LangChain"""

    def __init__(self):
        """Initialize LangChain service with OpenAI LLM"""
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def analyze_competitive_intelligence(self, content: str) -> Optional[str]:
        """
        Analyze content for competitive intelligence insights

        Args:
            content: Raw content to analyze

        Returns:
            Strategic analysis or None on error
        """
        try:
            prompt = self._create_competitive_analysis_prompt(content)
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            # Retry once on failure
            try:
                prompt = self._create_competitive_analysis_prompt(content)
                response = self.llm.invoke(prompt)
                return response.content
            except Exception:
                return None

    def generate_summary(self, content: str) -> Optional[str]:
        """
        Generate concise summary of content

        Args:
            content: Content to summarize

        Returns:
            Summary text or None
        """
        try:
            template = """You are a competitive intelligence analyst.
            Summarize the following content in 2-3 concise sentences, focusing on key business insights:

            Content: {content}

            Summary:"""

            prompt = PromptTemplate(template=template, input_variables=["content"])
            formatted_prompt = prompt.format(content=content)

            response = self.llm.invoke(formatted_prompt)
            return response.content
        except Exception:
            return None

    def extract_strategic_insights(self, content: str) -> Optional[str]:
        """
        Extract strategic insights from content

        Args:
            content: Content to analyze

        Returns:
            Strategic insights or None
        """
        try:
            template = """As a competitive intelligence expert, analyze this content and extract strategic insights:
            Focus on: market positioning, competitive advantages, strategic moves, and business implications.

            Content: {content}

            Strategic Insights:"""

            prompt = PromptTemplate(template=template, input_variables=["content"])
            formatted_prompt = prompt.format(content=content)

            response = self.llm.invoke(formatted_prompt)
            return response.content
        except Exception:
            return None

    def analyze_sentiment_with_reasoning(self, content: str) -> Optional[Dict[str, str]]:
        """
        Analyze sentiment with detailed reasoning

        Args:
            content: Content to analyze

        Returns:
            Dictionary with sentiment and reasoning
        """
        try:
            template = """Analyze the sentiment of the following content.
            Provide your response in the format: sentiment|reasoning
            Where sentiment is one of: positive, negative, neutral

            Content: {content}

            Response:"""

            prompt = PromptTemplate(template=template, input_variables=["content"])
            formatted_prompt = prompt.format(content=content)

            response = self.llm.invoke(formatted_prompt)
            result = response.content

            # Parse response
            if "|" in result:
                parts = result.split("|", 1)
                return {
                    "sentiment": parts[0].strip(),
                    "reasoning": parts[1].strip()
                }
            else:
                return {
                    "sentiment": result.strip(),
                    "reasoning": ""
                }
        except Exception:
            return None

    def full_content_analysis(self, content: str) -> Optional[Dict[str, str]]:
        """
        Perform full analysis chain: summary, insights, and sentiment

        Args:
            content: Content to analyze

        Returns:
            Dictionary with summary, insights, and sentiment
        """
        try:
            # Chain 1: Generate summary
            summary = self.generate_summary(content)

            # Chain 2: Extract strategic insights
            insights = self.extract_strategic_insights(content)

            # Chain 3: Analyze sentiment
            sentiment_result = self.analyze_sentiment_with_reasoning(content)
            sentiment = sentiment_result.get("sentiment", "neutral") if sentiment_result else "neutral"

            return {
                "summary": summary or "",
                "insights": insights or "",
                "sentiment": sentiment
            }
        except Exception:
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