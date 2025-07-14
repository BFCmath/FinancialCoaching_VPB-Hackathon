"""
Confidence Service - Complete Implementation from Lab
=====================================================

This module implements the confidence handling service from the lab,
including all functions from utils.py and service.py related to confidence:
- format_confidence_response, request_clarification, determine_confidence_level
- should_ask_for_confirmation, generate_confidence_explanation, validate_user_intent, suggest_alternatives
No db operations, so all sync.
"""

from typing import Tuple, List, Dict, Any, Optional

class ConfidenceService:
    """
    Service for handling confidence levels, user confirmation, and clarification requests.
    """
    
    @staticmethod
    def format_confidence_response(result: str, confidence: int) -> str:
        """
        Format response based on confidence level.
        
        Args:
            result: The base response text
            confidence: Confidence score (0-100)
            
        Returns:
            Formatted response with confidence indicators
        """
        if confidence >= 90:
            return f"✅ {result} ({confidence}% confident)"
        elif confidence >= 70:
            return f"⚠️ {result} ({confidence}% confident - moderate certainty)"
        elif confidence >= 50:
            return f"❓ {result} ({confidence}% confident - please verify)"
        else:
            return f"🔍 {result} ({confidence}% confident - low certainty, please confirm)"
    
    @staticmethod
    def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
        """
        Request clarification from user with optional suggestions.
        
        Args:
            question: The clarification question to ask
            suggestions: Optional suggestions or examples
            
        Returns:
            Formatted clarification request
        """
        response = f"❓ {question}"
        if suggestions:
            response += f"\n💡 Suggestions: {suggestions}"
        return response
    
    @staticmethod
    def determine_confidence_level(confidence_score: int) -> str:
        """
        Convert numeric confidence to descriptive level.
        
        Args:
            confidence_score: Numeric confidence (0-100)
            
        Returns:
            Descriptive confidence level
        """
        if confidence_score >= 90:
            return "very_high"
        elif confidence_score >= 80:
            return "high"
        elif confidence_score >= 70:
            return "good"
        elif confidence_score >= 60:
            return "moderate"
        elif confidence_score >= 50:
            return "low"
        else:
            return "very_low"
    
    @staticmethod
    def should_ask_for_confirmation(confidence: int, threshold: int = 70) -> bool:
        """
        Determine if confirmation should be requested based on confidence level.
        
        Args:
            confidence: Confidence score (0-100)
            threshold: Minimum confidence to proceed without confirmation
            
        Returns:
            True if confirmation should be requested
        """
        return confidence < threshold
    
    @staticmethod
    def generate_confidence_explanation(confidence: int, factors: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate explanation for confidence level.
        
        Args:
            confidence: Confidence score (0-100)
            factors: Optional dict of factors affecting confidence
            
        Returns:
            Human-readable confidence explanation
        """
        level = ConfidenceService.determine_confidence_level(confidence)
        
        base_explanations = {
            "very_high": "I'm very confident about this action based on clear context and data.",
            "high": "I'm confident about this action with good supporting information.",
            "good": "I have good confidence in this action with reasonable certainty.",
            "moderate": "I have moderate confidence - the action seems appropriate but may need verification.",
            "low": "I have low confidence - this action may need manual review or clarification.",
            "very_low": "I have very low confidence - this action definitely needs clarification or review."
        }
        
        explanation = base_explanations.get(level, "Confidence level unclear.")
        
        if factors:
            factor_details = [f"{factor}: {value}" for factor, value in factors.items()]
            if factor_details:
                explanation += f" Contributing factors: {', '.join(factor_details)}"
        
        return explanation
    
    @staticmethod
    def validate_user_intent(user_input: str, expected_actions: List[str]) -> Tuple[bool, str, int]:
        """
        Validate if user input matches expected actions and return confidence.
        
        Args:
            user_input: User's input text
            expected_actions: List of expected action keywords
            
        Returns:
            Tuple of (is_valid, matched_action, confidence_score)
        """
        user_lower = user_input.lower().strip()
        
        # Direct matches get highest confidence
        for action in expected_actions:
            if action.lower() in user_lower:
                return True, action, 95
        
        # Partial matches get lower confidence
        for action in expected_actions:
            action_words = action.lower().split()
            matches = sum(1 for word in action_words if word in user_lower)
            if matches > 0:
                confidence = min(80, (matches / len(action_words)) * 100)
                return True, action, int(confidence)
        
        # No matches
        return False, "", 0
    
    @staticmethod
    def suggest_alternatives(failed_input: str, available_options: List[str]) -> str:
        """
        Suggest alternatives when user input doesn't match expected options.
        
        Args:
            failed_input: The input that didn't match
            available_options: List of valid options
            
        Returns:
            Formatted suggestion message
        """
        return f"❓ I didn't understand '{failed_input}'. Did you mean one of these? {', '.join(available_options)}"