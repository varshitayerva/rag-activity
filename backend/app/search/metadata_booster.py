"""Dynamic Metadata Weighting for context-aware result boosting"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetadataBooster:
    """Boost search results based on metadata relevance"""

    # Boost multipliers
    DEPARTMENT_MATCH_BOOST = 1.2  # 20% boost for department match
    CATEGORY_MATCH_BOOST = 1.15  # 15% boost for category match
    RECENT_BOOST_DAYS = 7  # Boost docs < 7 days old
    RECENT_BOOST_FACTOR = 1.1  # 10% boost for recent docs

    def __init__(self):
        """Initialize metadata booster"""
        self.department_weights = {}  # Track popular departments
        self.category_weights = {}  # Track popular categories
        self.access_count = {}  # Track document popularity

    def boost_results(
        self,
        results: List[Dict[str, Any]],
        query_department: Optional[str] = None,
        query_category: Optional[str] = None,
        boost_recent: bool = True,
        boost_popular: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Apply dynamic boosts to search results.

        Args:
            results: Search results to boost
            query_department: Department to prioritize
            query_category: Category to prioritize
            boost_recent: Boost recently created documents
            boost_popular: Boost frequently accessed documents

        Returns:
            Results with updated scores and boost_factor field
        """
        if not results:
            return results

        boosted = []

        for result in results:
            boost_factor = 1.0

            # Department match boost
            if query_department and result.get('department') == query_department:
                boost_factor *= self.DEPARTMENT_MATCH_BOOST
                logger.debug(f"Department match boost: {result.get('chunk_id')}")

            # Category match boost
            if query_category and result.get('category') == query_category:
                boost_factor *= self.CATEGORY_MATCH_BOOST
                logger.debug(f"Category match boost: {result.get('chunk_id')}")

            # Recent document boost
            if boost_recent:
                boost_factor *= self._get_temporal_boost(result.get('created_at'))

            # Popular document boost
            if boost_popular:
                doc_id = result.get('doc_id')
                popularity_boost = self._get_popularity_boost(doc_id)
                boost_factor *= popularity_boost

            # Apply boost to score
            original_score = result.get('score', 0)
            result['original_score'] = original_score
            result['score'] = original_score * boost_factor
            result['boost_factor'] = boost_factor

            boosted.append(result)

        # Re-sort by boosted scores
        boosted.sort(key=lambda x: x['score'], reverse=True)

        # Update ranks
        for idx, result in enumerate(boosted):
            result['rank'] = idx

        logger.info(f"Applied dynamic boosts to {len(boosted)} results")
        return boosted

    def _get_temporal_boost(self, created_at: Optional[str]) -> float:
        """
        Calculate temporal boost for recent documents.

        Args:
            created_at: ISO datetime string

        Returns:
            Boost factor (1.0 or higher)
        """
        if not created_at:
            return 1.0

        try:
            # Parse ISO datetime
            if isinstance(created_at, str):
                # Try parsing ISO format
                if 'T' in created_at:
                    created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    return 1.0
            else:
                created = created_at

            # Calculate age
            now = datetime.now(created.tzinfo) if created.tzinfo else datetime.now()
            age = now - created
            days_old = age.days

            # Boost if recently created
            if days_old <= self.RECENT_BOOST_DAYS:
                logger.debug(f"Recent document (age={days_old} days)")
                return self.RECENT_BOOST_FACTOR

            return 1.0

        except Exception as e:
            logger.warning(f"Failed to calculate temporal boost: {e}")
            return 1.0

    def _get_popularity_boost(self, doc_id: Optional[str]) -> float:
        """
        Calculate popularity boost based on access count.

        Args:
            doc_id: Document ID

        Returns:
            Boost factor based on popularity
        """
        if not doc_id:
            return 1.0

        # Get access count (default 0)
        access_count = self.access_count.get(doc_id, 0)

        # Simple popularity boost: higher access = higher boost
        # Formula: 1.0 + (log(access_count) / 10)
        if access_count > 0:
            import math
            boost = 1.0 + (math.log(access_count + 1) / 10)
            logger.debug(f"Popularity boost for {doc_id}: {boost:.3f}")
            return boost

        return 1.0

    def track_access(self, doc_id: str):
        """Track document access for popularity scoring"""
        self.access_count[doc_id] = self.access_count.get(doc_id, 0) + 1

    def update_department_weight(self, department: str, weight: float = 1.0):
        """Update department weight"""
        self.department_weights[department] = weight

    def update_category_weight(self, category: str, weight: float = 1.0):
        """Update category weight"""
        self.category_weights[category] = weight

    def get_stats(self) -> Dict[str, Any]:
        """Get booster statistics"""
        return {
            "popular_docs": len(self.access_count),
            "tracked_departments": len(self.department_weights),
            "tracked_categories": len(self.category_weights),
            "department_match_boost": self.DEPARTMENT_MATCH_BOOST,
            "category_match_boost": self.CATEGORY_MATCH_BOOST,
            "recent_boost_days": self.RECENT_BOOST_DAYS,
            "recent_boost_factor": self.RECENT_BOOST_FACTOR
        }

    def reset(self):
        """Reset all tracking data"""
        self.department_weights.clear()
        self.category_weights.clear()
        self.access_count.clear()
        logger.info("Metadata booster reset")
