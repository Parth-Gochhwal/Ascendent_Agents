import pytest
from backend.app.core.config import get_settings
from backend.app.providers.llm_provider import get_llm_provider, reset_llm_provider, DemoLLMProvider, GeminiProvider

def test_provider_switching():
    settings = get_settings()
    
    # A: Start in demo mode
    settings.demo_mode = True
    reset_llm_provider()
    provider = get_llm_provider()
    assert isinstance(provider, DemoLLMProvider), "Provider should be DemoLLMProvider in demo mode"
    
    # B & C: Switch to live mode
    settings.demo_mode = False
    reset_llm_provider()
    provider_live = get_llm_provider()
    assert not isinstance(provider_live, DemoLLMProvider), "Provider should NOT be DemoLLMProvider in live mode"
    assert isinstance(provider_live, GeminiProvider), "Provider should be GeminiProvider in live mode"
    
    # D & E: Switch back to demo mode
    settings.demo_mode = True
    reset_llm_provider()
    provider_demo_again = get_llm_provider()
    assert isinstance(provider_demo_again, DemoLLMProvider), "Provider should be DemoLLMProvider after switching back"
