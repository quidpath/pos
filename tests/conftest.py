"""
Conftest for POS integration tests
"""
import pytest


@pytest.fixture
def pos_url():
    return "http://localhost:8003"
