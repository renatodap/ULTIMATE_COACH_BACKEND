
import pytest
from unittest.mock import MagicMock, AsyncMock
from services.message_classifier_service import MessageClassifierService
import json

@pytest.fixture
def mock_groq_client():
    """Fixture to create a mock Groq client."""
    mock_client = MagicMock()
    # Mock the async chat.completions.create method
    mock_client.chat.completions.create = AsyncMock()
    return mock_client

@pytest.fixture
def classifier(mock_groq_client):
    """Fixture to create a MessageClassifierService with a mock client."""
    return MessageClassifierService(groq_client=mock_groq_client)

def test_should_show_log_preview_true(classifier):
    """
    Test that should_show_log_preview returns True for a high-confidence log.
    """
    classification = {
        "is_log": True,
        "confidence": 0.9,
        "log_type": "meal"
    }
    assert classifier.should_show_log_preview(classification) is True

def test_should_show_log_preview_false_low_confidence(classifier):
    """
    Test that should_show_log_preview returns False for a low-confidence log.
    """
    classification = {
        "is_log": True,
        "confidence": 0.7,
        "log_type": "meal"
    }
    assert classifier.should_show_log_preview(classification) is False

def test_should_show_log_preview_false_not_log(classifier):
    """
    Test that should_show_log_preview returns False if it's not a log.
    """
    classification = {
        "is_log": False,
        "confidence": 0.9,
        "log_type": "meal"
    }
    assert classifier.should_show_log_preview(classification) is False

def test_should_show_log_preview_false_no_log_type(classifier):
    """
    Test that should_show_log_preview returns False if there is no log_type.
    """
    classification = {
        "is_log": True,
        "confidence": 0.9,
        "log_type": None
    }
    assert classifier.should_show_log_preview(classification) is False

@pytest.mark.asyncio
async def test_classify_message_success_log(classifier, mock_groq_client):
    """
    Test successful classification of a LOG message.
    """
    expected_response = {
        "is_log": True,
        "is_chat": False,
        "log_type": "meal",
        "confidence": 0.95,
        "reasoning": "Past tense eating with specific foods and quantities",
        "has_question": False
    }

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(expected_response)))]
    mock_groq_client.chat.completions.create.return_value = mock_response

    result = await classifier.classify_message("I ate 3 eggs and oatmeal for breakfast")
    assert result == expected_response
    mock_groq_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_classify_message_success_chat(classifier, mock_groq_client):
    """
    Test successful classification of a CHAT message.
    """
    expected_response = {
        "is_log": False,
        "is_chat": True,
        "log_type": None,
        "confidence": 0.98,
        "reasoning": "Future-oriented question asking for advice",
        "has_question": True
    }
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(expected_response)))]
    mock_groq_client.chat.completions.create.return_value = mock_response

    result = await classifier.classify_message("What should I eat for breakfast?")
    assert result == expected_response

@pytest.mark.asyncio
async def test_classify_message_api_failure(classifier, mock_groq_client):
    """
    Test the fallback mechanism when the Groq API fails.
    """
    mock_groq_client.chat.completions.create.side_effect = Exception("API Error")

    message = "This is a test message?"
    result = await classifier.classify_message(message)

    assert result["is_log"] is False
    assert result["is_chat"] is True
    assert result["log_type"] is None
    assert result["confidence"] == 0.5
    assert "Classification failed" in result["reasoning"]
    assert result["has_question"] is True
