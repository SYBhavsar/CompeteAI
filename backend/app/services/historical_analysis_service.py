"""
Historical Analysis Service

Purpose: Detect and analyze changes between competitor snapshots using AI
Architecture: Uses LangChain for semantic analysis (not just text diffs)
Follows: Single Responsibility Principle - focused on change detection only
"""

import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.llm_factory import LLMFactory
from app.core.prompt_loader import PromptLoader
from app.models.competitive_snapshot import CompetitiveSnapshot
from app.models.change_detection import ChangeEvent

logger = logging.getLogger(__name__)


class HistoricalAnalysisService:
    """
    Service for detecting and analyzing changes between competitor snapshots.

    Uses LangChain with GPT to perform semantic analysis of changes,
    not just text diffs. This provides strategic context and impact assessment.
    """

    def __init__(self):
        """Initialize with LLM from LLMFactory (provider/model configurable)."""
        self.llm = LLMFactory.create("historical_analysis")
        logger.info("HistoricalAnalysisService initialized successfully")

    def detect_changes(
        self,
        competitor_id: int,
        before_snapshot: Optional[CompetitiveSnapshot],
        after_snapshot: Optional[CompetitiveSnapshot],
        db: Session
    ) -> List[ChangeEvent]:
        """
        Detect changes between two snapshots using AI semantic analysis.

        Args:
            competitor_id: ID of the competitor
            before_snapshot: Earlier snapshot
            after_snapshot: Later snapshot
            db: Database session

        Returns:
            List of ChangeEvent objects (not yet committed to DB)

        Follows: Dependency Inversion Principle - depends on abstractions (Session)
        """
        # Input validation
        if not before_snapshot or not after_snapshot:
            logger.warning("One or both snapshots are None - cannot detect changes")
            return []

        # Quick check: identical hashes mean no changes
        if before_snapshot.data_hash == after_snapshot.data_hash:
            logger.debug(f"Identical hashes for competitor {competitor_id} - skipping analysis")
            return []

        try:
            # Use LangChain to analyze changes semantically
            analysis_result = self._analyze_with_langchain(
                before_data=before_snapshot.snapshot_data,
                after_data=after_snapshot.snapshot_data
            )

            # Parse and create ChangeEvent records
            changes = self._create_change_events(
                competitor_id=competitor_id,
                before_snapshot_id=before_snapshot.id,
                after_snapshot_id=after_snapshot.id,
                analysis_result=analysis_result,
                db=db
            )

            logger.info(f"Detected {len(changes)} changes for competitor {competitor_id}")
            return changes

        except Exception as e:
            logger.error(f"Error detecting changes for competitor {competitor_id}: {e}", exc_info=True)
            return []

    def analyze_latest_snapshots(
        self,
        competitor_id: int,
        db: Session
    ) -> Optional[List[ChangeEvent]]:
        """
        Analyze the two most recent snapshots for a competitor.

        Args:
            competitor_id: ID of the competitor
            db: Database session

        Returns:
            List of detected changes, or None if insufficient snapshots

        Follows: Open/Closed Principle - can extend without modifying
        """
        try:
            # Get the 2 most recent snapshots
            snapshots = db.query(CompetitiveSnapshot)\
                .filter(CompetitiveSnapshot.competitor_id == competitor_id)\
                .order_by(CompetitiveSnapshot.snapshot_date.desc())\
                .limit(2)\
                .all()

            if len(snapshots) < 2:
                logger.info(f"Insufficient snapshots for competitor {competitor_id} (found {len(snapshots)}, need 2)")
                return None

            # Most recent is index 0, previous is index 1
            after_snapshot = snapshots[0]
            before_snapshot = snapshots[1]

            return self.detect_changes(
                competitor_id=competitor_id,
                before_snapshot=before_snapshot,
                after_snapshot=after_snapshot,
                db=db
            )

        except Exception as e:
            logger.error(f"Error analyzing latest snapshots for competitor {competitor_id}: {e}", exc_info=True)
            return None

    def _analyze_with_langchain(
        self,
        before_data: Dict[str, Any],
        after_data: Dict[str, Any]
    ) -> str:
        """
        Use LLM to perform semantic analysis of changes.

        Args:
            before_data: Snapshot data before changes
            after_data: Snapshot data after changes

        Returns:
            JSON string with analysis results
        """
        try:
            prompt_config = PromptLoader.load("historical_analysis")
            user_msg = prompt_config.user_prompt.format(
                before_data=json.dumps(before_data, indent=2),
                after_data=json.dumps(after_data, indent=2),
            )
            from langchain.schema import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=prompt_config.system_prompt),
                HumanMessage(content=user_msg),
            ]
            response = self.llm.invoke(messages)
            return response.content or "{}"
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}", exc_info=True)
            return "{}"

    def _create_change_events(
        self,
        competitor_id: int,
        before_snapshot_id: int,
        after_snapshot_id: int,
        analysis_result: str,
        db: Session
    ) -> List[ChangeEvent]:
        """
        Parse LangChain analysis and create ChangeEvent records.

        Args:
            competitor_id: ID of competitor
            before_snapshot_id: ID of before snapshot
            after_snapshot_id: ID of after snapshot
            analysis_result: JSON string from LangChain
            db: Database session

        Returns:
            List of ChangeEvent objects (added to session but not committed)

        Follows: Clean Code - clear, single-purpose function
        """
        try:
            # Parse JSON response
            parsed = json.loads(analysis_result)

            changes = []

            # Handle single change format
            if "change_type" in parsed:
                if parsed["change_type"] != "none":
                    change_event = self._build_change_event(
                        competitor_id=competitor_id,
                        before_snapshot_id=before_snapshot_id,
                        after_snapshot_id=after_snapshot_id,
                        change_data=parsed
                    )
                    db.add(change_event)
                    changes.append(change_event)

            # Handle multiple changes format
            elif "changes" in parsed:
                for change_data in parsed["changes"]:
                    if change_data.get("change_type") != "none":
                        change_event = self._build_change_event(
                            competitor_id=competitor_id,
                            before_snapshot_id=before_snapshot_id,
                            after_snapshot_id=after_snapshot_id,
                            change_data=change_data
                        )
                        db.add(change_event)
                        changes.append(change_event)

            db.commit()
            return changes

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LangChain response as JSON: {e}")
            logger.debug(f"Response was: {analysis_result}")
            return []
        except Exception as e:
            logger.error(f"Error creating ChangeEvent records: {e}", exc_info=True)
            return []

    def _build_change_event(
        self,
        competitor_id: int,
        before_snapshot_id: int,
        after_snapshot_id: int,
        change_data: Dict[str, Any]
    ) -> ChangeEvent:
        """
        Build a ChangeEvent object from parsed data.

        Args:
            competitor_id: ID of competitor
            before_snapshot_id: ID of before snapshot
            after_snapshot_id: ID of after snapshot
            change_data: Parsed change data from LangChain

        Returns:
            ChangeEvent object

        Follows: Builder pattern for clean object construction
        """
        return ChangeEvent(
            competitor_id=competitor_id,
            change_type=change_data.get("change_type", "unknown"),
            severity=change_data.get("severity", "minor"),
            before_snapshot_id=before_snapshot_id,
            after_snapshot_id=after_snapshot_id,
            change_summary=change_data.get("change_summary", ""),
            strategic_impact=change_data.get("strategic_impact", ""),
            confidence_score=float(change_data.get("confidence_score", 0.5))
        )
