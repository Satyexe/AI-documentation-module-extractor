"""Description Summarizer Module

Generates concise descriptions from extracted content using extractive summarization.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class DescriptionSummarizer:
    """Generates descriptions from extracted content."""
    
    def __init__(self, max_sentences: int = 3, min_length: int = 20):
        """Initialize the summarizer.
        
        Args:
            max_sentences: Maximum sentences per description
            min_length: Minimum description length
        """
        self.max_sentences = max_sentences
        self.min_length = min_length
    
    def generate_description(self, content: str) -> str:
        """Generate a description from content.
        
        Args:
            content: Raw content text
            
        Returns:
            Generated description
        """
        if not content or len(content.strip()) < self.min_length:
            return ""
        
        # Clean and normalize content
        cleaned = self._clean_content(content)
        
        # Extract key sentences
        sentences = self._extract_sentences(cleaned)
        
        if not sentences:
            return ""
        
        # Select best sentences
        selected = self._select_sentences(sentences)
        
        # Join and format
        description = ' '.join(selected)
        description = self._finalize_description(description)
        
        return description
    
    def _clean_content(self, content: str) -> str:
        """Clean content by removing noise.
        
        Args:
            content: Raw content
            
        Returns:
            Cleaned content
        """
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # Remove common documentation noise
        patterns_to_remove = [
            r'See also:.*',
            r'Related:.*',
            r'Note:.*',
            r'Warning:.*',
            r'Example:.*',
            r'For more information.*',
            r'Click here.*',
            r'Learn more.*',
        ]
        
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Remove URLs
        content = re.sub(r'https?://\S+', '', content)
        
        # Remove email addresses
        content = re.sub(r'\S+@\S+', '', content)
        
        return content.strip()
    
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text.
        
        Args:
            text: Text content
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter sentences
        filtered = []
        for sent in sentences:
            sent = sent.strip()
            # Skip very short or very long sentences
            if 20 <= len(sent) <= 300:
                # Skip if it looks like navigation/UI text
                if not self._is_navigation_text(sent):
                    filtered.append(sent)
        
        return filtered
    
    def _is_navigation_text(self, text: str) -> bool:
        """Check if text looks like navigation/UI text.
        
        Args:
            text: Text to check
            
        Returns:
            True if appears to be navigation text
        """
        nav_patterns = [
            r'^[A-Z][a-z]+\s+→',
            r'^Click\s+',
            r'^Select\s+',
            r'^Navigate\s+to',
            r'^Go\s+to',
            r'^Menu\s*:',
            r'^Home\s*$',
            r'^Back\s*$',
        ]
        
        for pattern in nav_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _select_sentences(self, sentences: List[str]) -> List[str]:
        """Select best sentences for description.
        
        Args:
            sentences: List of candidate sentences
            
        Returns:
            Selected sentences (up to max_sentences)
        """
        if not sentences:
            return []
        
        # Score sentences (simple heuristic)
        scored = []
        for sent in sentences[:20]:  # Limit candidates
            score = self._score_sentence(sent)
            scored.append((score, sent))
        
        # Sort by score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Select top sentences
        selected = [sent for _, sent in scored[:self.max_sentences]]
        
        # Maintain original order if possible
        result = []
        for sent in sentences:
            if sent in selected:
                result.append(sent)
                if len(result) >= self.max_sentences:
                    break
        
        return result if result else sentences[:self.max_sentences]
    
    def _score_sentence(self, sentence: str) -> float:
        """Score a sentence for quality.
        
        Args:
            sentence: Sentence to score
            
        Returns:
            Score (higher is better)
        """
        score = 0.0
        
        # Prefer sentences with action verbs (functional descriptions)
        action_words = ['provides', 'enables', 'allows', 'supports', 'manages', 
                       'handles', 'processes', 'creates', 'generates', 'sends',
                       'receives', 'configures', 'sets', 'displays', 'shows']
        sentence_lower = sentence.lower()
        for word in action_words:
            if word in sentence_lower:
                score += 2.0
                break
        
        # Prefer sentences that are not questions
        if '?' in sentence:
            score -= 1.0
        
        # Prefer sentences with specific terms (not generic)
        if len(sentence.split()) >= 8:  # Prefer substantial sentences
            score += 1.0
        
        # Penalize sentences with too many capitals (likely headings)
        if sum(1 for c in sentence if c.isupper()) > len(sentence) * 0.3:
            score -= 2.0
        
        # Penalize very short sentences
        if len(sentence) < 40:
            score -= 0.5
        
        return score
    
    def _finalize_description(self, description: str) -> str:
        """Finalize description formatting.
        
        Args:
            description: Raw description
            
        Returns:
            Finalized description
        """
        # Clean up
        description = re.sub(r'\s+', ' ', description)
        description = description.strip()
        
        # Ensure it ends with proper punctuation
        if description and not description[-1] in '.!?':
            description += '.'
        
        # Ensure minimum length
        if len(description) < self.min_length:
            return ""
        
        # Limit maximum length
        if len(description) > 500:
            # Truncate at last sentence boundary
            sentences = re.split(r'(?<=[.!?])\s+', description)
            truncated = []
            length = 0
            for sent in sentences:
                if length + len(sent) <= 500:
                    truncated.append(sent)
                    length += len(sent) + 1
                else:
                    break
            description = ' '.join(truncated)
        
        return description.strip()

