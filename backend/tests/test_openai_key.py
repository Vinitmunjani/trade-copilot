import pytest
from app.config import get_settings
import asyncio


@pytest.mark.asyncio
async def test_openai_key_works():
    settings = get_settings()
    key = settings.OPENAI_API_KEY
    if not key or key.startswith("your-"):
        pytest.skip("OPENAI_API_KEY not configured in .env")

    try:
        import openai
        client = openai.AsyncOpenAI(api_key=key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello in one word."}],
            max_tokens=10,
        )
        content = resp.choices[0].message.content if resp.choices else None
        assert content and len(content) > 0
    except Exception as e:
        pytest.fail(f"OpenAI request failed: {e}")
