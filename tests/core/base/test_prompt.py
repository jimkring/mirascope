"""Tests for the `base_prompt` module."""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import computed_field

from mirascope.core import BasePrompt, metadata, prompt_template


def test_base_prompt() -> None:
    """Tests the `BasePrompt` class."""

    @prompt_template("Recommend a {genre} book.")
    class BookRecommendationPrompt(BasePrompt):
        genre: str

    prompt = BookRecommendationPrompt(genre="fantasy")
    assert str(prompt) == "Recommend a fantasy book."
    assert prompt.dump() == {
        "metadata": {},
        "prompt": "Recommend a fantasy book.",
        "template": "Recommend a {genre} book.",
        "inputs": {"genre": "fantasy"},
    }


def test_base_prompt_with_computed_fields() -> None:
    """Tests the `BasePrompt` class with list and list[list] computed fields."""

    @prompt_template("Recommend a {genre} book.")
    class BookRecommendationPrompt(BasePrompt):
        @computed_field
        @property
        def genre(self) -> str:
            return "fantasy"

    prompt = BookRecommendationPrompt()
    assert str(prompt) == "Recommend a fantasy book."


def test_base_prompt_run() -> None:
    """Tests the `BasePrompt.run` method."""
    mock_decorator = MagicMock()
    mock_call_fn = MagicMock()
    mock_decorator.return_value = mock_call_fn
    mock_call_fn.return_value = "response"

    @prompt_template("Recommend a {genre} book.")
    class BookRecommendationPrompt(BasePrompt):
        genre: str

    prompt = BookRecommendationPrompt(genre="fantasy")
    response = prompt.run(mock_decorator)
    assert response == mock_call_fn.return_value

    # Ensure the decorator was called with the correct function
    mock_decorator.assert_called_once()
    decorator_arg = mock_decorator.call_args[0][0]
    assert callable(decorator_arg)
    assert hasattr(decorator_arg, "_prompt_template")
    assert getattr(decorator_arg, "_prompt_template") == "Recommend a {genre} book."

    # Ensure the decorated function was called with the correct arguments
    mock_call_fn.assert_called_once_with(genre="fantasy")


@pytest.mark.asyncio
async def test_base_prompt_run_async() -> None:
    mock_decorator = MagicMock()
    mock_call_fn = AsyncMock()
    mock_decorator.return_value = mock_call_fn
    mock_call_fn.return_value = "response"

    @prompt_template("Recommend a {genre} book.")
    class BookRecommendationPrompt(BasePrompt):
        genre: str

    prompt = BookRecommendationPrompt(genre="fantasy")
    response = await prompt.run_async(mock_decorator)
    assert response == mock_call_fn.return_value

    # Ensure the decorator was called with the correct function
    mock_decorator.assert_called_once()
    decorator_arg = mock_decorator.call_args[0][0]
    assert callable(decorator_arg)
    assert hasattr(decorator_arg, "_prompt_template")
    assert getattr(decorator_arg, "_prompt_template") == "Recommend a {genre} book."

    # Ensure the decorated function was called with the correct arguments
    mock_call_fn.assert_called_once_with(genre="fantasy")


def test_prompt_template_docstring() -> None:
    """Tests the `prompt_template` decorator on a `BasePrompt`."""

    os.environ["MIRASCOPE_DOCSTRING_PROMPT_TEMPLATE"] = "ENABLED"

    class BookRecommendationPrompt(BasePrompt):
        """Recommend a {genre} book."""

        genre: str

    prompt = BookRecommendationPrompt(genre="fantasy")
    assert str(prompt) == "Recommend a fantasy book."

    os.environ["MIRASCOPE_DOCSTRING_PROMPT_TEMPLATE"] = "DISABLED"


def test_metadata_decorator() -> None:
    """Tests the `metadata` decorator on a `BasePrompt`."""

    @metadata({"tags": {"version:0001"}})
    @prompt_template("Recommend a book.")
    class BookRecommendationPrompt(BasePrompt): ...

    prompt = BookRecommendationPrompt()
    assert prompt.dump()["metadata"] == {"tags": {"version:0001"}}
