"""
Smart Intent Parser
Converts vague natural language commands into structured actions
Designed for non-technical users (e.g., "add car companies like mahindra")
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Try to import rapidfuzz for fuzzy matching
try:
    from rapidfuzz import fuzz, process
    FUZZY_MATCHING_AVAILABLE = True
except ImportError:
    FUZZY_MATCHING_AVAILABLE = False
    # Fallback to built-in difflib
    import difflib

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
    # EXPANDED: Many variations for natural language flexibility
    INTENT_PATTERNS = [
        # ==========================================
        # ADD patterns (EXPANDED)
        # ==========================================
        # Basic add patterns
        (r'add\s+(?:(?:some|few|more|new|other)\s+)?(.+?)\s+(?:companies?|celebrities?|people|names?|actors?|players?)', 'ADD_COMPANIES'),
        (r'include\s+(.+?)\s+(?:companies?|celebrities?|names?|actors?|players?)', 'ADD_COMPANIES'),
        (r'put\s+(.+?)\s+(?:in|to|on)\s+(?:the\s+)?(?:list|tracking)', 'ADD_COMPANIES'),
        
        # "I want to..." patterns
        (r'(?:i\s+)?(?:want|would like|need)\s+to\s+(?:add|include|track)\s+(.+)', 'ADD_COMPANIES'),
        (r'(?:i\s+)?(?:want|would like|need)\s+(.+?)\s+(?:added|included|tracked)', 'ADD_COMPANIES'),
        
        # "Can you..." patterns
        (r'(?:can|could)\s+you\s+(?:add|include|put)\s+(.+)', 'ADD_COMPANIES'),
        (r'(?:please\s+)?(?:add|include)\s+(.+)', 'ADD_COMPANIES'),
        
        # "Track/Follow" patterns
        (r'(?:start\s+)?(?:track|follow|monitor)(?:ing)?\s+(.+)', 'ADD_COMPANIES'),
        
        # "Track X for news" patterns
        (r'track\s+(.+?)\s+(?:for|in)\s+(?:news|alerts|updates)', 'ADD_COMPANIES'),
        
        # Category-specific patterns
        (r'add\s+(?:to\s+)?(?:the\s+)?(.+?)\s+(?:list|section|category)', 'ADD_COMPANIES'),
        
        # ==========================================
        # REMOVE patterns (EXPANDED)
        # ==========================================
        (r'(?:remove|delete|drop)\s+(?:the\s+)?(.+?)(?:\s+from\s+(?:the\s+)?list)?', 'REMOVE_ITEM'),
        (r'take\s+(?:out|off)\s+(?:the\s+)?(.+?)(?:\s+from)?', 'REMOVE_ITEM'),
        (r'(?:i\s+)?(?:want|would like)\s+to\s+(?:remove|delete)\s+(.+)', 'REMOVE_ITEM'),
        (r'stop\s+(?:track|follow|monitor)(?:ing)?\s+(.+)', 'REMOVE_ITEM'),
        (r'remove\s+(.+?)\s+from\s+(?:the\s+)?(?:list|tracking)', 'REMOVE_ITEM'),
        
        # ==========================================
        # TIME/Schedule patterns (EXPANDED)
        # ==========================================
        (r'change\s+(?:the\s+)?time', 'CHANGE_TIME'),
        (r'set\s+(?:the\s+)?schedule', 'CHANGE_TIME'),
        (r'update\s+(?:the\s+)?(?:morning|evening|digest|news)?\s*time', 'CHANGE_TIME'),
        (r'move\s+(?:the\s+)?(?:morning|evening)?\s*(?:news|digest)?\s*(?:time\s+)?to', 'CHANGE_TIME'),
        (r'(?:make|set)\s+(?:the\s+)?(?:morning|evening)?\s*(?:news|digest)?\s*(?:at\s+)?(\d+)', 'CHANGE_TIME'),
        (r'(?:morning|evening)\s+(?:news|digest)\s+(?:at|time)\s+(\d+)', 'CHANGE_TIME'),
        (r'(?:change|update)\s+(?:the\s+)?schedule\s+to', 'CHANGE_TIME'),
        
        # ==========================================
        # LIST/Show patterns (EXPANDED)
        # ==========================================
        (r'(?:show|list|view|see|display|get)\s+(?:all\s+)?(?:the\s+)?(.+?)\s+(?:companies?|celebrities?|names?|actors?|players?|items?)', 'LIST_ITEMS'),
        (r'what\s+(?:companies?|celebrities?|names?|actors?|players?)\s+(?:do we|are we)\s+(?:have|tracking|monitoring|following)', 'LIST_ITEMS'),
        (r'(?:show|list|view)\s+(?:all\s+)?(?:the\s+)?tracked\s+(.+)', 'LIST_ITEMS'),
        (r'(?:show|list)\s+(?:the\s+)?(.+?)\s+(?:category|section|list)', 'LIST_ITEMS'),
        (r'what\s+(?:is|are)\s+(?:in\s+)?(?:the\s+)?(.+?)\s+(?:list|category)', 'LIST_ITEMS'),
        (r'(?:show|list)\s+everything', 'LIST_ITEMS'),
        
        # ==========================================
        # SOURCE patterns (EXPANDED)
        # ==========================================
        (r'add\s+(?:a\s+)?(?:new\s+)?(?:news\s+)?source', 'ADD_SOURCE'),
        (r'include\s+(?:a\s+)?(?:new\s+)?website', 'ADD_SOURCE'),
        (r'add\s+(?:a\s+)?news\s+website', 'ADD_SOURCE'),
        (r'track\s+(?:a\s+)?new\s+(?:website|source)', 'ADD_SOURCE'),
        
        # ==========================================
        # CHANGE_FREQUENCY patterns (NEW)
        # ==========================================
        (r'check\s+news\s+every\s+(\d+)\s+minutes?', 'CHANGE_FREQUENCY'),
        (r'scrape\s+(?:every\s+)?(\d+)\s+minutes?', 'CHANGE_FREQUENCY'),
        (r'(?:change|set|update)\s+(?:scraping\s+)?(?:frequency|interval)\s+(?:to\s+)?(\d+)', 'CHANGE_FREQUENCY'),
        (r'scrape\s+(?:more|less)\s+(?:often|frequently)', 'CHANGE_FREQUENCY'),
        (r'(?:make\s+)?(?:scraping|checking)\s+(?:faster|slower)', 'CHANGE_FREQUENCY'),

        # ==========================================
        # ENABLE_FEATURE patterns (NEW)
        # ==========================================
        (r'enable\s+(.+?)\s*(?:digest|alert|notification)?', 'ENABLE_FEATURE'),
        (r'turn\s+on\s+(.+?)\s*(?:digest|alert)?', 'ENABLE_FEATURE'),
        (r'activate\s+(.+?)\s*(?:digest|alert)?', 'ENABLE_FEATURE'),
        (r'start\s+(.+?)\s*(?:digest|alert)', 'ENABLE_FEATURE'),

        # ==========================================
        # DISABLE_FEATURE patterns (NEW)
        # ==========================================
        (r'disable\s+(.+?)\s*(?:digest|alert|notification)?', 'DISABLE_FEATURE'),
        (r'turn\s+off\s+(.+?)\s*(?:digest|alert)?', 'DISABLE_FEATURE'),
        (r'deactivate\s+(.+?)\s*(?:digest|alert)?', 'DISABLE_FEATURE'),
        (r'stop\s+(.+?)\s*(?:digest|alert)', 'DISABLE_FEATURE'),

        # ==========================================
        # SET_ALERT_THRESHOLD patterns (NEW)
        # ==========================================
        (r'alert\s+(?:me\s+)?on\s+(?:high|medium|low)\s+priority', 'SET_ALERT_THRESHOLD'),
        (r'set\s+(?:alert\s+)?(?:threshold|score)\s+(?:to\s+)?(\d+)', 'SET_ALERT_THRESHOLD'),
        (r'(?:minimum|min)\s+(?:alert\s+)?score\s+(?:of\s+)?(\d+)', 'SET_ALERT_THRESHOLD'),
        (r'only\s+alert\s+(?:on\s+)?(?:high|important|critical)', 'SET_ALERT_THRESHOLD'),

        # ==========================================
        # ADD_KEYWORD patterns (NEW)
        # ==========================================
        (r'add\s+keyword\s+["\'](.+?)["\']', 'ADD_KEYWORD'),
        (r'track\s+keyword\s+["\'](.+?)["\']', 'ADD_KEYWORD'),
        (r'add\s+["\'](.+?)["\']\s+(?:to\s+)?(?:keywords?|search)', 'ADD_KEYWORD'),
        (r'include\s+keyword\s+(.+)', 'ADD_KEYWORD'),

        # ==========================================
        # REMOVE_KEYWORD patterns (NEW)
        # ==========================================
        (r'remove\s+keyword\s+["\'](.+?)["\']', 'REMOVE_KEYWORD'),
        (r'delete\s+keyword\s+["\'](.+?)["\']', 'REMOVE_KEYWORD'),
        (r'stop\s+tracking\s+["\'](.+?)["\']', 'REMOVE_KEYWORD'),

        # ==========================================
        # SHOW_CONFIG patterns (NEW)
        # ==========================================
        (r'show\s+(?:current\s+)?(?:settings?|config(?:uration)?)', 'SHOW_CONFIG'),
        (r'what(?:\'s|\s+is)\s+(?:the\s+)?(?:current\s+)?(.+?)\s+(?:setting|config|value)', 'SHOW_CONFIG'),
        (r'display\s+(?:the\s+)?settings?', 'SHOW_CONFIG'),

        # ==========================================
        # SHOW_SCHEDULE patterns (NEW)
        # ==========================================
        (r'when\s+(?:do|does)\s+(?:the\s+)?(?:digests?|news)\s+run', 'SHOW_SCHEDULE'),
        (r'show\s+(?:the\s+)?schedule', 'SHOW_SCHEDULE'),
        (r'what\s+time\s+(?:is|are)\s+(?:the\s+)?(?:digests?|news)', 'SHOW_SCHEDULE'),

        # ==========================================
        # SHOW_STATS patterns (NEW)
        # ==========================================
        (r'how\s+many\s+(.+?)\s+(?:are\s+)?(?:tracked|monitoring)', 'SHOW_STATS'),
        (r'show\s+(?:me\s+)?(?:the\s+)?stats', 'SHOW_STATS'),
        (r'(?:give\s+me\s+)?statistics', 'SHOW_STATS'),

        # ==========================================
        # CHECK_STATUS patterns (NEW)
        # ==========================================
        (r'(?:is|are)\s+(?:the\s+)?(?:scrapers?|system|bot)\s+(?:running|working)', 'CHECK_STATUS'),
        (r'(?:system|bot)\s+status', 'CHECK_STATUS'),
        (r'(?:is\s+)?everything\s+(?:working|ok|fine)', 'CHECK_STATUS'),
        (r'check\s+status', 'CHECK_STATUS'),

        # ==========================================
        # HELP patterns
        # ==========================================
        (r'help|what\s+can\s+you\s+do|commands|how\s+to\s+use', 'HELP'),
        (r'how\s+do\s+i|how\s+to|how\s+can\s+i', 'HELP'),
        (r'what\s+(?:commands|options)\s+(?:are\s+)?available', 'HELP'),
    ]
    
    # Category keywords for entity extraction (EXPANDED)
    CATEGORY_KEYWORDS = {
        'automotive': [
            'car', 'automotive', 'vehicle', 'auto', 'automobile', 'motor',
            'mahindra', 'tata', 'maruti', 'hyundai', 'kia', 'toyota', 'honda',
            'bike', 'motorcycle', 'tractor', 'truck', 'bus', 'commercial vehicle',
            'sonalika', 'tafe', 'john deere', 'ashok leyland', 'eicher', 'bajaj',
            'tvs', 'force motors', 'skoda', 'volkswagen', 'bmw', 'mercedes'
        ],
        'bollywood': [
            'bollywood', 'actor', 'actress', 'movie', 'film', 'star', 'hero', 'heroine',
            'shah rukh', 'salman', 'amitabh', 'akshay', 'hrithik', 'ranveer', 'ranbir',
            'deepika', 'priyanka', 'alia', 'kareena', 'katrina', 'anushka', 'ajay',
            'cinema', 'hollywood', 'film star', 'celebrity'
        ],
        'cricket': [
            'cricket', 'player', 'batsman', 'bowler', 'wicketkeeper', 'all-rounder',
            'ipl', 'bcci', 'icc', 'test match', 'odi', 't20',
            'virat', 'rohit', 'dhoni', 'sachin', 'hardik', 'kl rahul', 'bumrah',
            'indian team', 'cricketer', 'match', 'world cup'
        ],
        'business': [
            'company', 'business', 'industrialist', 'tycoon', 'magnate', 'corporate',
            'mukesh ambani', 'gautam adani', 'ratan tata', 'kumar birla', 'azim premji',
            'entrepreneur', 'ceo', 'chairman', 'founder', 'owner', 'industry',
            'reliance', 'tata group', 'adani group', 'birl', 'wipro', 'infosys'
        ],
        'real_estate': [
            'real estate', 'property', 'realty', 'builder', 'developer', 'construction',
            'lodha', 'hiranandani', 'oberoi', 'godrej properties', 'dlf', 'unitech',
            'apartment', 'flat', 'house', 'land', 'plot', 'commercial property',
            'housing', 'infrastructure', 'building', 'project'
        ],
        'tech': [
            'tech', 'technology', 'startup', 'entrepreneur', 'founder', 'unicorn',
            'byju', 'ola', 'paytm', 'zomato', 'swiggy', 'flipkart', 'amazon india',
            'software', 'app', 'platform', 'digital', 'it company', 'fintech',
            'edtech', 'e-commerce', 'internet', 'ai', 'artificial intelligence'
        ],
        'politics': [
            'politician', 'minister', 'pm', 'chief minister', 'mp', 'mla',
            'modi', 'amit shah', 'rahul gandhi', 'kejriwal', 'mamata',
            'government', 'bjp', 'congress', 'election', 'parliament', 'cabinet'
        ],
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
    
    # Common typo corrections (typo -> correct)
    TYPO_CORRECTIONS = {
        'ad': 'add',
        'ads': 'add',
        'addd': 'add',
        'remov': 'remove',
        'remoove': 'remove',
        'delet': 'delete',
        'deleet': 'delete',
        'compnies': 'companies',
        'companes': 'companies',
        'companys': 'companies',
        'celbrities': 'celebrities',
        'celebritys': 'celebrities',
        'chek': 'check',
        'cheque': 'check',
        'evry': 'every',
        'minuts': 'minutes',
        'minuets': 'minutes',
        'schdule': 'schedule',
        'schedual': 'schedule',
        'mornin': 'morning',
        'evenin': 'evening',
        'evrything': 'everything',
        'evrythng': 'everything',
        'cmpletet': 'complete',
    }

    # Synonym expansion (synonym -> standard term)
    SYNONYM_MAP = {
        # Frequency synonyms
        'hourly': '60 minutes',
        'half hour': '30 minutes',
        'half-hour': '30 minutes',
        'quarter hour': '15 minutes',
        'quarter-hour': '15 minutes',
        'daily': '1440 minutes',

        # Time synonyms
        'morning': '7 AM',
        'afternoon': '2 PM',
        'evening': '5 PM',
        'night': '8 PM',

        # Action synonyms
        'turn on': 'enable',
        'turn off': 'disable',
        'activate': 'enable',
        'deactivate': 'disable',
        'switch on': 'enable',
        'switch off': 'disable',
        'start': 'enable',
        'stop': 'disable',

        # Other synonyms
        'firm': 'company',
        'corporation': 'company',
        'star': 'celebrity',
        'celeb': 'celebrity',
    }

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

        # Apply fuzzy correction for common typos
        message_corrected = self._fuzzy_correct_message(message)
        if message_corrected != message:
            logger.info(f"Fuzzy corrected: '{message}' → '{message_corrected}'")
            message = message_corrected

        # Try pattern matching first (highest confidence)
        for pattern, intent_type in self.compiled_patterns:
            match = pattern.search(message)
            if match:
                return self._build_intent(intent_type, match, message)

        # Pattern matching failed - try AI heuristic fallback
        fallback_intent = self._ai_heuristic_parse(message)
        if fallback_intent:
            logger.info(f"AI heuristic matched intent: {fallback_intent.intent_type}")
            return fallback_intent

        # No pattern matched - will fall back to generic /fix
        logger.info(f"No intent pattern matched for: {message}")
        return None
    
    def _ai_heuristic_parse(self, message: str) -> Optional[ParsedIntent]:
        """
        AI-style heuristic parsing for vague commands that don't match regex patterns
        Uses keyword matching and context analysis
        """
        message_lower = message.lower().strip()
        
        # Heuristic 1: Check for "add/increase/more" + category keywords
        add_keywords = ['add', 'include', 'more', 'extra', 'additional', 'new', 'put', 'insert']
        if any(kw in message_lower for kw in add_keywords):
            # Detect category
            category = self._detect_category(message)
            if category:
                entities = self._extract_entities(message, category)
                if entities:
                    return ParsedIntent(
                        intent_type='ADD_COMPANIES',
                        category=category,
                        entities=entities,
                        target_file='config/celebrities.yaml',
                        confidence=0.65,  # Lower confidence for heuristic
                        original_text=message,
                        suggested_changes=f"Add {len(entities)} {category} items: {', '.join(entities[:3])}..."
                    )
        
        # Heuristic 2: Check for "remove/delete/less/stop" 
        remove_keywords = ['remove', 'delete', 'stop', 'drop', 'less', 'exclude', 'take out']
        if any(kw in message_lower for kw in remove_keywords):
            category = self._detect_category(message)
            entities = self._extract_entities(message, category)
            if entities:
                return ParsedIntent(
                    intent_type='REMOVE_ITEM',
                    category=category,
                    entities=entities,
                    target_file='config/celebrities.yaml',
                    confidence=0.60,
                    original_text=message,
                    suggested_changes=f"Remove {', '.join(entities)}"
                )
        
        # Heuristic 3: Check for "show/list/what/see" 
        list_keywords = ['show', 'list', 'what', 'see', 'tell me', 'display', 'view', 'get']
        if any(kw in message_lower for kw in list_keywords):
            category = self._detect_category(message)
            return ParsedIntent(
                intent_type='LIST_ITEMS',
                category=category,
                entities=[],
                target_file='config/celebrities.yaml',
                confidence=0.55,
                original_text=message,
                suggested_changes=f"Show {category or 'all'} tracked items"
            )
        
        # Heuristic 4: Check for "time/schedule/when/hour" 
        time_keywords = ['time', 'schedule', 'when', 'hour', 'am', 'pm', 'morning', 'evening']
        if any(kw in message_lower for kw in time_keywords):
            return ParsedIntent(
                intent_type='CHANGE_TIME',
                category=None,
                entities=[],
                target_file='config/schedules.yaml',
                confidence=0.55,
                original_text=message,
                suggested_changes="Change digest schedule time"
            )
        
        # Heuristic 5: Check for capitalized names (likely adding someone)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', message)
        if len(capitalized_words) >= 1 and len(message.split()) <= 10:
            category = self._detect_category(message)
            return ParsedIntent(
                intent_type='ADD_COMPANIES',
                category=category,
                entities=capitalized_words,
                target_file='config/celebrities.yaml',
                confidence=0.50,  # Low confidence - just guessing
                original_text=message,
                suggested_changes=f"Possibly adding: {', '.join(capitalized_words[:3])}..."
            )
        
        return None
    
    def _build_intent(self, intent_type: str, match: re.Match, original_text: str) -> ParsedIntent:
        """Build ParsedIntent from regex match"""

        # Extract captured group
        captured = match.group(1).strip() if match.lastindex and match.lastindex >= 1 else ""

        # Detect category
        category = self._detect_category(original_text)

        # Extract entities based on intent type
        entities = []

        if intent_type in ['ADD_COMPANIES', 'REMOVE_ITEM']:
            entities = self._extract_entities(original_text, category)
        elif intent_type == 'CHANGE_FREQUENCY':
            freq = self._extract_frequency_value(original_text)
            if freq:
                entities = [str(freq)]
        elif intent_type == 'CHANGE_TIME':
            time_val = self._extract_time_value(original_text)
            if time_val:
                entities = [time_val]
        elif intent_type in ['ADD_KEYWORD', 'REMOVE_KEYWORD']:
            keyword = self._extract_keyword(original_text)
            if keyword:
                entities = [keyword]
        elif intent_type == 'SET_ALERT_THRESHOLD':
            threshold = self._extract_threshold_value(original_text)
            if threshold:
                entities = [str(threshold)]
        elif intent_type == 'SHOW_STATS':
            # Extract what to show stats for (e.g., "how many companies")
            if captured:
                entities = [captured]

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

    def _extract_time_value(self, text: str) -> Optional[str]:
        """Extract time value from text (e.g., '8 AM', '20:00', 'morning')"""
        # 12-hour format: "8 AM", "5:30 PM"
        time_12h = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', text, re.IGNORECASE)
        if time_12h:
            hour = int(time_12h.group(1))
            minute = time_12h.group(2) or '00'
            period = time_12h.group(3).lower()

            # Convert to 24-hour
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute}"

        # 24-hour format: "20:00", "08:30"
        time_24h = re.search(r'(\d{1,2}):(\d{2})', text)
        if time_24h:
            return f"{int(time_24h.group(1)):02d}:{time_24h.group(2)}"

        # Named times
        time_names = {
            'morning': '07:00',
            'afternoon': '14:00',
            'evening': '17:00',
            'night': '20:00',
        }

        for name, time_val in time_names.items():
            if name in text.lower():
                return time_val

        return None

    def _extract_frequency_value(self, text: str) -> Optional[int]:
        """Extract frequency in minutes from text"""
        # Direct minutes: "15 minutes", "30 mins"
        minutes = re.search(r'(\d+)\s*(?:minutes?|mins?)', text, re.IGNORECASE)
        if minutes:
            return int(minutes.group(1))

        # Hours: "1 hour", "2 hours"
        hours = re.search(r'(\d+)\s*hours?', text, re.IGNORECASE)
        if hours:
            return int(hours.group(1)) * 60

        # Named frequencies
        frequency_names = {
            'hourly': 60,
            'half hour': 30,
            'quarter hour': 15,
            'daily': 1440,
        }

        for name, freq_val in frequency_names.items():
            if name in text.lower():
                return freq_val

        return None

    def _extract_keyword(self, text: str) -> Optional[str]:
        """Extract keyword from quoted text or after 'keyword' marker"""
        # Quoted keywords: "keyword" or 'keyword'
        quoted = re.search(r'["\'](.+?)["\']', text)
        if quoted:
            return quoted.group(1)

        # After "keyword" marker: "add keyword smart city"
        after_keyword = re.search(r'keyword\s+(.+?)(?:\s+to|\s+in|$)', text, re.IGNORECASE)
        if after_keyword:
            return after_keyword.group(1).strip()

        return None

    def _extract_threshold_value(self, text: str) -> Optional[int]:
        """Extract alert threshold value (1-10)"""
        # Direct number: "set threshold to 8"
        number = re.search(r'(?:threshold|score)\s+(?:to\s+)?(\d+)', text, re.IGNORECASE)
        if number:
            return int(number.group(1))

        # Priority level to score mapping
        priority_scores = {
            'high': 9,
            'medium': 6,
            'low': 3,
            'critical': 10,
            'important': 8,
        }

        for level, score in priority_scores.items():
            if level in text.lower():
                return score

        return None

    def _fuzzy_correct_message(self, message: str) -> str:
        """
        Apply fuzzy correction and synonym expansion

        Args:
            message: Original message

        Returns:
            Corrected and expanded message
        """
        # First apply phrase-level synonym expansion
        message_lower = message.lower()
        for synonym, replacement in self.SYNONYM_MAP.items():
            if synonym in message_lower:
                # Replace while preserving case
                message = re.sub(
                    re.escape(synonym),
                    replacement,
                    message,
                    flags=re.IGNORECASE
                )
                logger.debug(f"Synonym expansion: '{synonym}' → '{replacement}'")

        words = message.split()
        corrected_words = []

        for word in words:
            word_lower = word.lower().strip('.,!?')

            # Check direct typo corrections first
            if word_lower in self.TYPO_CORRECTIONS:
                corrected = self.TYPO_CORRECTIONS[word_lower]
                # Preserve original capitalization
                if word and word[0].isupper():
                    corrected = corrected.capitalize()
                corrected_words.append(corrected)
                continue

            # Use fuzzy matching for intent keywords
            if FUZZY_MATCHING_AVAILABLE:
                # Common intent keywords to match against
                intent_keywords = [
                    'add', 'remove', 'delete', 'show', 'list', 'change', 'set',
                    'enable', 'disable', 'check', 'track', 'monitor', 'stop',
                    'companies', 'celebrities', 'keywords', 'schedule', 'time',
                    'frequency', 'alerts', 'digest', 'morning', 'evening',
                    'automotive', 'bollywood', 'cricket', 'business'
                ]

                # Only apply fuzzy matching to short words (typos are usually short)
                if len(word_lower) >= 3 and len(word_lower) <= 12:
                    match, score, _ = process.extractOne(
                        word_lower,
                        intent_keywords,
                        scorer=fuzz.ratio
                    )

                    # High similarity threshold (80%) to avoid false corrections
                    if score >= 80 and word_lower != match:
                        logger.debug(f"Fuzzy matched: '{word_lower}' → '{match}' (score: {score})")
                        # Preserve original capitalization
                        if word and word[0].isupper():
                            match = match.capitalize()
                        corrected_words.append(match)
                        continue

            # No correction needed
            corrected_words.append(word)

        return ' '.join(corrected_words)
    
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


class ConversationContext:
    """
    Track conversation context for pronoun resolution and context-aware parsing

    Usage:
        context = ConversationContext()
        intent1 = parser.parse("show automotive companies")
        context.update(intent1)  # Remember last category: automotive

        intent2 = parser.parse("add Tesla to it")  # "it" resolved to "automotive"
        intent2_with_context = context.resolve(intent2)
    """

    def __init__(self):
        self.last_intent_type: Optional[str] = None
        self.last_category: Optional[str] = None
        self.last_entities: List[str] = []

    def update(self, intent: ParsedIntent):
        """Update context with new intent"""
        if intent:
            self.last_intent_type = intent.intent_type
            if intent.category:
                self.last_category = intent.category
            if intent.entities:
                self.last_entities = intent.entities

    def resolve(self, intent: ParsedIntent) -> ParsedIntent:
        """
        Resolve pronouns and context references in an intent

        Args:
            intent: Intent to resolve

        Returns:
            Intent with resolved references
        """
        if not intent:
            return intent

        # Resolve "it" to last category
        if not intent.category and self.last_category:
            if 'it' in intent.original_text.lower():
                logger.info(f"Context resolved 'it' → '{self.last_category}'")
                intent.category = self.last_category

        return intent


def parse_intent(message: str) -> Optional[ParsedIntent]:
    """Convenience function"""
    parser = IntentParser()
    return parser.parse(message)
