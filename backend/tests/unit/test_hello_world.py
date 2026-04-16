import asyncio

from app.api.hello_world import hello_world


def test_hello_world() -> None:
    result = asyncio.run(hello_world())
    assert "Message" in result
    assert result["Message"] == "Hello, World!"
