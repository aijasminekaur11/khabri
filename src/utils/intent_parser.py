"""
Smart Intent Parser
Converts vague natural language commands into structured actions
Designed for non-technical users (e.g., "add car companies like mahindra")
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedIntent:
    """Structured representation of user intent"""
    intent_type: str  # ADD_COMPANIES, REMOVE_ITEM, CHANGE_TIME, etc.
    category: Optional[str]  # automotive, bollywood, cricket, etc.
    entities: List[str]  # Extracted names/items
    target_file: Optional[str]  # config/celebrities.yaml, config/schedules.yaml, etc.
    confidence: float  # 0.0 to 1.0
    original_text: str
    suggested_changes: Optional[str] = None  # Human-readable description


class IntentParser:
    """
    Parses vague commands into structured intents using patterns + AI fallback
    """
    
    # Intent patterns - maps regex patterns to intent types
    INTENT_PATTERNS = [
        # ADD patterns
        (r'add\s+(?:(?:some|few|more|new)\s+)?(.+?)\s+(?:companies?|celebrities?|people|names?)', 'ADD_COMPANIES'),
        (r'include\s+(.+?)\s+(?:companies?|celebrities?|names?)', 'ADD_COMPANIES'),
        (r'put\s+(.+?)\s+(?:in|to)\s+(?:the\s+)?list', 'ADD_COMPANIES'),
        
        # REMOVE patterns
        (r'remove\s+(?:the\s+)?(.+)', 'REMOVE_ITEM'),
        (r'delete\s+(?:the\s+)?(.+)', 'REMOVE_ITEM'),
        (r'take\s+out\s+(?:the\s+)?(.+)', 'REMOVE_ITEM'),
        
        # TIME/Schedule patterns
        (r'change\s+(?:the\s+)?time', 'CHANGE_TIME'),
        (r'set\s+(?:the\s+)?schedule', 'CHANGE_TIME'),
        (r'update\s+(?:the\s+)?(?:morning|evening)?\s*time', 'CHANGE_TIME'),
        (r'move\s+(?:the\s+)?(?:morning|evening)?\s*(?:news|digest)?\s*to', 'CHANGE_TIME'),
        
        # LIST/Show patterns
        (r'(?:show|list|view)\s+(?:all\s+)?(.+?)\s+(?:companies?|celebrities?|names?)', 'LIST_ITEMS'),
        (r'what\s+(?:companies?|celebrities?|names?)\s+(?:do we|are we)\s+(?:have|tracking)', 'LIST_ITEMS'),
        
        # SOURCE patterns
        (r'add\s+(?:a\s+)?(?:new\s+)?(?:news\s+)?source', 'ADD_SOURCE'),
        (r'include\s+(?:a\s+)?(?:new\s+)?website', 'ADD_SOURCE'),
        
        # HELP
        (r'help|what\s+can\s+you\s+do|commands', 'HELP'),
    ]
    
    # Category keywords for entity extraction
    CATEGORY_KEYWORDS = {
        'automotive': ['car', 'automotive', 'vehicle', 'auto', 'mahindra', 'tata', 'maruti', 'hyundai', 'kia', 'toyota', 'honda', 'bike', 'motorcycle'],
        'bollywood': ['bollywood', 'actor', 'actress', 'movie', 'film', 'star', 'hero', 'heroine', 'shah rukh', 'salman', 'amitabh'],
        'cricket': ['cricket', 'player', 'batsman', 'bowler', 'ipl', 'bcci', 'virat', 'rohit', 'dhoni'],
        'business': ['company', 'business', 'industrialist', 'tycoon', 'mukesh ambani', 'gautam adani', 'ratan tata'],
        'real_estate': ['real estate', 'property', 'builder', 'developer', 'lodha', 'hiranandani'],
        'tech': ['tech', 'startup', 'entrepreneur', 'founder', 'byju', 'ola', 'paytm'],
    }
    
    # Common company/person name patterns
    NAME_PATTERNS = [
        r'(?:Mahindra(?:\s+&\s+Mahindra)?)',
        r'(?:Tata(?:\s+Motors)?)',
        r'(?:Sonalika(?:\s+Tractors?)?)',
        r'(?:TAFE)',
        r'(?:John\s+Deere)',
        r'(?:Ashok\s+Leyland)',
        r'(?:Eicher(?:\s+Motors?)?)',
        r'(?:Bajaj(?:\s+Auto)?)',
        r'(?:TVS(?:\s+Motor)?)',
        r'(?:Force\s+Motors)',
        r'(?:Maruti(?:\s+Suzuki)?)',
        r'(?:Hyundai)',
        r'(?:Kia)',
        r'(?:Toyota)',
        r'(?:Honda)',
        r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Generic capitalized names
    ]
    
    def __init__(self):
        self.compiled_patterns = [(re.compile(p, re.IGNORECASE), intent) for p, intent in self.INTENT_PATTERNS]
    
    def parse(self, message: str) -> Optional[ParsedIntent]:
        """
        Parse a user message into structured intent
        
        Args:
            message: Raw user message (e.g., "add automotive companies like mahindra tata")
            
        Returns:
            ParsedIntent object or None if no pattern matched
        """
        message_lower = message.lower().strip()
        
        # Try pattern matching first
        for pattern, intent_type in self.compiled_patterns:
            match = pattern.search(message)
            if match:
                return self._build_intent(intent_type, match, message)
        
        # No pattern matched - will fall back to generic /fix
        logger.info(f"No intent pattern matched for: {message}")
        return None
    
    def _build_intent(self, intent_type: str, match: re.Match, original_text: str) -> ParsedIntent:
        """Build ParsedIntent from regex match"""
        
        # Extract captured group
        captured = match.group(1).strip() if match.lastindex and match.lastindex >= 1 else ""
        
        # Detect category
        category = self._detect_category(original_text)
        
        # Extract entities (names/companies)
        entities = self._extract_entities(original_text, category)
        
        # Map to target file
        target_file = self._map_to_file(intent_type, category)
        
        # Calculate confidence
        confidence = self._calculate_confidence(intent_type, entities, category)
        
        # Generate suggested changes description
        suggested_changes = self._generate_description(intent_type, category, entities)
        
        return ParsedIntent(
            intent_type=intent_type,
            category=category,
            entities=entities,
            target_file=target_file,
            confidence=confidence,
            original_text=original_text,
            suggested_changes=suggested_changes
        )
    
    def _detect_category(self, text: str) -> Optional[str]:
        """Detect category from keywords in text"""
        text_lower = text.lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return category
        
        # Default based on context
        if any(word in text_lower for word in ['company', 'business', 'industry']):
            return 'business'
        
        return None
    
    def _extract_entities(self, text: str, category: Optional[str]) -> List[str]:
        """Extract company/person names from text"""
        entities = []
        
        # Try specific patterns first
        for pattern in self.NAME_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        # Remove duplicates and clean
        entities = list(set([e.strip() for e in entities if len(e.strip()) > 2]))
        
        # If no entities found, try to extract capitalized words after "like" or commas
        if not entities:
            # Pattern: "like X, Y, Z" or "such as X, Y, Z"
            like_pattern = r'(?:like|such as|including)\s+([A-Za-z\s&,]+?)(?:\s+(?:and|or)\s+|$|\s+for|\s+to)'
            like_match = re.search(like_pattern, text, re.IGNORECASE)
            if like_match:
                items = re.split(r',|\s+and\s+', like_match.group(1))
                entities = [item.strip() for item in items if len(item.strip()) > 2]
        
        return entities[:20]  # Limit to 20 entities
    
    def _map_to_file(self, intent_type: str, category: Optional[str]) -> Optional[str]:
        """Map intent to target configuration file"""
        
        file_mapping = {
            'ADD_COMPANIES': 'config/celebrities.yaml',
            'REMOVE_ITEM': 'config/celebrities.yaml',
            'LIST_ITEMS': 'config/celebrities.yaml',
            'CHANGE_TIME': 'config/schedules.yaml',
            'ADD_SOURCE': 'config/sources.yaml',
        }
        
        return file_mapping.get(intent_type)
    
    def _calculate_confidence(self, intent_type: str, entities: List[str], category: Optional[str]) -> float:
        """Calculate confidence score (0.0 to 1.0)"""
        confidence = 0.5  # Base confidence
        
        # Boost for having entities
        if entities:
            confidence += 0.2
            if len(entities) >= 2:
                confidence += 0.1
        
        # Boost for having category
        if category:
            confidence += 0.2
        
        # Cap at 0.95
        return min(confidence, 0.95)
    
    def _generate_description(self, intent_type: str, category: Optional[str], entities: List[str]) -> str:
        """Generate human-readable description of the action"""
        
        if intent_type == 'ADD_COMPANIES':
            cat_display = category.replace('_', ' ').title() if category else 'General'
            if entities:
                entity_list = ', '.join(entities[:5])
                if len(entities) > 5:
                    entity_list += f" and {len(entities) - 5} more"
                return f"Add {len(entities)} {cat_display} companies/people: {entity_list}"
            return f"Add companies to {cat_display} category"
        
        elif intent_type == 'REMOVE_ITEM':
            if entities:
                return f"Remove: {', '.join(entities[:3])}"
            return "Remove items from list"
        
        elif intent_type == 'CHANGE_TIME':
            return "Change digest schedule time"
        
        elif intent_type == 'LIST_ITEMS':
            cat_display = category.replace('_', ' ').title() if category else 'all'
            return f"Show {cat_display} tracked items"
        
        elif intent_type == 'ADD_SOURCE':
            return "Add new news source"
        
        elif intent_type == 'HELP':
            return "Show available commands"
        
        return "Unknown action"


def parse_intent(message: str) -> Optional[ParsedIntent]:
    """Convenience function"""
    parser = IntentParser()
    return parser.parse(message)
