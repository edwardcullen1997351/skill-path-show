"""
Adaptive recommendation service for personalized learning paths.

This module provides adaptive recommendations using:
- Collaborative filtering (find similar users)
- Q-learning (reinforcement learning for recommendations)
- Integration with existing MECE algorithm
"""

from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict
import random
from supabase import Client

from app.utils.supabase_client import get_supabase_client
from app.utils.mece_algorithm import get_mece_engine


class AdaptiveRecommendationService:
    """Service for adaptive recommendations using ML techniques."""
    
    def __init__(self, client: Optional[Client] = None):
        """Initialize adaptive recommendation service."""
        self._client = client or get_supabase_client()
        self._q_table: Dict[Tuple[str, str], float] = defaultdict(float)
        self._learning_rate = 0.1
        self._discount_factor = 0.9
        self._exploration_rate = 0.3
    
    def get_adaptive_recommendations(
        self,
        user_id: str,
        target_role: str,
        missing_skills: List[str],
        use_collaborative: bool = True,
        use_rl: bool = False,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Get adaptive recommendations based on user history and preferences.
        
        Args:
            user_id: User ID
            target_role: Target job role
            missing_skills: Skills the user needs to learn
            use_collaborative: Use collaborative filtering
            use_rl: Use Q-learning
            top_k: Number of recommendations
            
        Returns:
            Dict with recommendations and metadata
        """
        # Get base recommendations from MECE algorithm
        mece_engine = get_mece_engine()
        mece_result = mece_engine.generate_recommendations(missing_skills)
        mece_recommendations = mece_result.get("selected_subjects", [])
        
        if not use_collaborative and not use_rl:
            return {
                "recommendations": mece_recommendations[:top_k],
                "algorithm": "MECE",
                "user_id": user_id,
            }
        
        # Apply collaborative filtering
        if use_collaborative:
            collaborative_recs = self._collaborative_filtering(
                user_id, target_role, mece_recommendations
            )
            # Merge with MECE recommendations
            combined = self._merge_recommendations(mece_recommendations, collaborative_recs)
        else:
            combined = mece_recommendations
        
        # Apply Q-learning
        if use_rl:
            combined = self._apply_q_learning(
                user_id, target_role, combined, missing_skills
            )
        
        return {
            "recommendations": combined[:top_k],
            "algorithm": "Adaptive",
            "uses_collaborative": use_collaborative,
            "uses_rl": use_rl,
            "user_id": user_id,
        }
    
    def _collaborative_filtering(
        self,
        user_id: str,
        target_role: str,
        base_recommendations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Find similar users and recommend what they completed.
        
        Collaborative filtering approach:
        1. Find users with similar skill profiles
        2. Look at what subjects they completed
        3. Recommend highly-rated subjects from similar users
        """
        # Get user's completed subjects
        completed_response = (
            self._client.table("completed_subjects")
            .select("subject_code, grade")
            .eq("user_id", user_id)
            .execute()
        )
        user_completed = set(s["subject_code"] for s in completed_response.data)
        
        # Get users with same role goal who completed subjects
        similar_users_response = (
            self._client.table("user_profiles")
            .select("id, role_goal")
            .eq("role_goal", target_role)
            .neq("id", user_id)
            .execute()
        )
        
        if not similar_users_response.data:
            return base_recommendations
        
        # Get subject completions for similar users
        similar_user_ids = [u["id"] for u in similar_users_response.data]
        completions_response = (
            self._client.table("completed_subjects")
            .select("user_id, subject_code, grade")
            .in_("user_id", similar_user_ids)
            .execute()
        )
        
        # Score subjects by popularity among similar users
        subject_scores: Dict[str, Tuple[int, float]] = {}
        for completion in completions_response.data:
            subject_code = completion["subject_code"]
            if subject_code not in user_completed:  # Don't recommend already completed
                if subject_code not in subject_scores:
                    subject_scores[subject_code] = (0, 0.0)
                count, total_grade = subject_scores[subject_code]
                grade = completion.get("grade", 0) or 0
                subject_scores[subject_code] = (count + 1, total_grade + grade)
        
        # Sort by score (count * average grade)
        scored_subjects = [
            (code, count * (total_grade / count if count > 0 else 0))
            for code, (count, total_grade) in subject_scores.items()
        ]
        scored_subjects.sort(key=lambda x: x[1], reverse=True)
        
        # Convert to recommendation format
        recommended = []
        for subject_code, score in scored_subjects[:len(base_recommendations)]:
            recommended.append({
                "subject_code": subject_code,
                "score": score,
                "source": "collaborative",
            })
        
        return recommended
    
    def _merge_recommendations(
        self,
        mece_recs: List[Dict[str, Any]],
        collaborative_recs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge MECE and collaborative filtering recommendations.
        
        Uses a weighted combination:
        - 60% MECE (quality, non-overlapping)
        - 40% Collaborative (proven popular)
        """
        merged = []
        seen = set()
        
        # Interleave recommendations
        mece_index = 0
        collab_index = 0
        
        while len(merged) < len(mece_recs):
            # Add MECE recommendation (60% weight)
            if mece_index < len(mece_recs):
                rec = mece_recs[mece_index]
                code = rec.get("subject_code", rec.get("subject_name", ""))
                if code not in seen:
                    merged.append({
                        **rec,
                        "source": "MECE",
                        "combined_score": rec.get("marginal_contribution", 0) * 0.6,
                    })
                    seen.add(code)
                mece_index += 1
            
            # Add collaborative recommendation (40% weight)
            if len(merged) < len(mece_recs) and collab_index < len(collaborative_recs):
                rec = collaborative_recs[collab_index]
                code = rec.get("subject_code", "")
                if code not in seen:
                    merged.append({
                        "subject_code": rec.get("subject_code", ""),
                        "subject_name": rec.get("subject_code", ""),
                        "covered_skills": [],
                        "marginal_contribution": rec.get("score", 0) / 100 if rec.get("score") else 0,
                        "source": "collaborative",
                        "combined_score": rec.get("score", 0) / 100 * 0.4 if rec.get("score") else 0,
                    })
                    seen.add(code)
                collab_index += 1
            
            # If we've exhausted both, break
            if mece_index >= len(mece_recs) and collab_index >= len(collaborative_recs):
                break
        
        # Re-sort by combined score
        merged.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        
        return merged
    
    def _apply_q_learning(
        self,
        user_id: str,
        target_role: str,
        recommendations: List[Dict[str, Any]],
        missing_skills: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Apply Q-learning to optimize recommendations.
        
        Q-learning approach:
        - States: Missing skills
        - Actions: Recommend subjects
        - Rewards: Based on skill coverage and user feedback
        """
        # Get user feedback history
        feedback_response = (
            self._client.table("recommendation_feedback")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        
        # Update Q-table based on feedback
        for feedback in feedback_response.data:
            subject_code = feedback["subject_code"]
            user_action = feedback["user_action"]
            
            # Calculate reward
            reward = 0
            if user_action == "accepted":
                reward = 1.0
            elif user_action == "rejected":
                reward = -0.5
            elif user_action == "ignored":
                reward = -0.1
            
            # Update Q-value
            for skill in missing_skills:
                key = (skill, subject_code)
                self._q_table[key] = (1 - self._learning_rate) * self._q_table[key] + \
                                    self._learning_rate * reward
        
        # Re-rank recommendations based on Q-values
        for i, rec in enumerate(recommendations):
            subject_code = rec.get("subject_code", "")
            q_value = sum(
                self._q_table[(skill, subject_code)]
                for skill in missing_skills
            ) / max(len(missing_skills), 1)
            
            # Exploration vs exploitation
            if random.random() < self._exploration_rate:
                # Explore: add some randomization
                rec["q_value"] = q_value + random.uniform(0, 0.2)
            else:
                # Exploit: use Q-value directly
                rec["q_value"] = q_value
        
        # Re-sort by Q-value
        recommendations.sort(key=lambda x: x.get("q_value", 0), reverse=True)
        
        return recommendations
    
    def record_feedback(
        self,
        user_id: str,
        subject_code: str,
        user_action: str,
    ) -> None:
        """
        Record user feedback for learning.
        
        Args:
            user_id: User ID
            subject_code: Subject that was recommended
            user_action: User's action (accepted/rejected/ignored)
        """
        data = {
            "user_id": user_id,
            "subject_code": subject_code,
            "was_recommended": True,
            "user_action": user_action,
        }
        
        self._client.table("recommendation_feedback").insert(data).execute()
    
    def update_q_value(
        self,
        skill: str,
        subject_code: str,
        reward: float,
    ) -> None:
        """
        Manually update Q-value for a skill-subject pair.
        
        Args:
            skill: Skill name
            subject_code: Subject code
            reward: Reward value
        """
        key = (skill, subject_code)
        self._q_table[key] = (1 - self._learning_rate) * self._q_table[key] + \
                            self._learning_rate * reward


# Global instance
_adaptive_service: Optional[AdaptiveRecommendationService] = None


def get_adaptive_service(client: Optional[Client] = None) -> AdaptiveRecommendationService:
    """Get the global adaptive recommendation service instance."""
    global _adaptive_service
    if _adaptive_service is None:
        _adaptive_service = AdaptiveRecommendationService(client)
    return _adaptive_service
