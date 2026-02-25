from app.api.hello_world import hello_world

import asyncio

def test_hello_world():
    result = asyncio.run(hello_world())
    assert "Message" in result
    assert result["Message"] == "Hello, World!"
