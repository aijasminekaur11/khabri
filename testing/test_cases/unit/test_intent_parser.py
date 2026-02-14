import pytest
from src.utils.intent_parser import parse_intent, ParsedIntent

def test_add_companies_automotive_simple():
    message = "add automotive companies like Mahindra & Mahindra, Tata Motors"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "ADD_COMPANIES"
    assert intent.category == "automotive"
    assert "Mahindra & Mahindra" in intent.entities
    assert "Tata Motors" in intent.entities
    assert intent.target_file == "config/celebrities.yaml"
    assert intent.confidence >= 0.7

def test_add_companies_tech_include():
    message = "include some tech companies like Google, Amazon, Microsoft"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "ADD_COMPANIES"
    assert intent.category == "tech"
    assert "Google" in intent.entities
    assert "Amazon" in intent.entities
    assert "Microsoft" in intent.entities
    assert intent.target_file == "config/celebrities.yaml"
    assert intent.confidence >= 0.7

def test_add_companies_bollywood_put():
    message = "put some bollywood actors in the list: Shah Rukh Khan, Salman Khan"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "ADD_COMPANIES"
    assert intent.category == "bollywood"
    assert "Shah Rukh Khan" in intent.entities
    assert "Salman Khan" in intent.entities
    assert intent.target_file == "config/celebrities.yaml"
    assert intent.confidence >= 0.7

def test_add_companies_no_entities_vague():
    message = "add some new companies"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "ADD_COMPANIES"
    assert intent.category == "business"  # Default category based on "companies"
    assert len(intent.entities) == 0
    assert intent.target_file == "config/celebrities.yaml"
    assert intent.confidence >= 0.5 # Lower confidence without specific entities

def test_add_companies_real_estate_mixed_case():
    message = "Add sOme Real EstAte developers like DLF, GODREJ PROPERTIES"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "ADD_COMPANIES"
    assert intent.category == "real_estate"
    assert "DLF" in intent.entities
    assert "GODREJ PROPERTIES" in intent.entities
    assert intent.target_file == "config/celebrities.yaml"
    assert intent.confidence >= 0.7

def test_remove_item_simple():
    message = "remove John Deere from automotive"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "REMOVE_ITEM"
    assert intent.category == "automotive"
    assert "John Deere" in intent.entities
    assert intent.target_file == "config/celebrities.yaml"
    assert intent.confidence >= 0.7

def test_remove_item_delete():
    message = "delete Tata Motors"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "REMOVE_ITEM"
    assert intent.category == "automotive" # Inferred from "Tata Motors"
    assert "Tata Motors" in intent.entities
    assert intent.target_file == "config/celebrities.yaml"
    assert intent.confidence >= 0.7

def test_change_time_morning():
    message = "change morning time to 8 AM"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "CHANGE_TIME"
    assert intent.category is None # Time changes don't have a category in this scheme
    assert len(intent.entities) == 0 # No specific entities to extract for time itself
    assert intent.target_file == "config/schedules.yaml"
    assert intent.confidence >= 0.5

def test_change_time_evening_schedule():
    message = "set evening schedule to 5 PM"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "CHANGE_TIME"
    assert intent.target_file == "config/schedules.yaml"

def test_list_items_bollywood():
    message = "show all bollywood celebrities"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "LIST_ITEMS"
    assert intent.category == "bollywood"
    assert intent.target_file == "config/celebrities.yaml"

def test_list_items_automotive():
    message = "list automotive companies"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "LIST_ITEMS"
    assert intent.category == "automotive"
    assert intent.target_file == "config/celebrities.yaml"

def test_add_source_simple():
    message = "add a new news source"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "ADD_SOURCE"
    assert intent.target_file == "config/sources.yaml"

def test_help_command():
    message = "what can you do"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "HELP"

def test_no_match():
    message = "hello world this is a test"
    intent = parse_intent(message)
    assert intent is None

def test_message_too_short():
    message = "add"
    intent = parse_intent(message)
    assert intent is None # Parse_intent returns None if no pattern matched

def test_entities_with_and_or():
    message = "add tech companies like Google, Amazon and Microsoft"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "ADD_COMPANIES"
    assert "Google" in intent.entities
    assert "Amazon" in intent.entities
    assert "Microsoft" in intent.entities

def test_entities_including_multiple_words():
    message = "add cricketers including Virat Kohli and MS Dhoni"
    intent = parse_intent(message)
    assert intent is not None
    assert intent.intent_type == "ADD_COMPANIES" # Mapped to ADD_COMPANIES by pattern
    assert intent.category == "cricket"
    assert "Virat Kohli" in intent.entities
    assert "MS Dhoni" in intent.entities

def test_confidence_calculation():
    message_high_confidence = "add automotive companies like Mahindra & Mahindra"
    intent_high = parse_intent(message_high_confidence)
    assert intent_high.confidence > 0.8 # Has entities and category

    message_medium_confidence = "change the time"
    intent_medium = parse_intent(message_medium_confidence)
    assert intent_medium.confidence >= 0.5 and intent_medium.confidence < 0.7 # No entities or category

def test_suggested_changes_description():
    message = "add automotive companies like Mahindra & Mahindra"
    intent = parse_intent(message)
    assert "Add 1 Automotive companies/people: Mahindra & Mahindra" in intent.suggested_changes

    message_remove = "remove John Deere"
    intent_remove = parse_intent(message_remove)
    assert "Remove: John Deere" in intent_remove.suggested_changes

    message_time = "change the morning time"
    intent_time = parse_intent(message_time)
    assert "Change digest schedule time" in intent_time.suggested_changes

def test_target_file_mapping():
    assert parse_intent("add companies").target_file == "config/celebrities.yaml"
    assert parse_intent("remove item").target_file == "config/celebrities.yaml"
    assert parse_intent("change time").target_file == "config/schedules.yaml"
    assert parse_intent("add source").target_file == "config/sources.yaml"
