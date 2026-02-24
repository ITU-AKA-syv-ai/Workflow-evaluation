from app.main import index

def test_index():
    result = index()
    assert "Message" in result
    assert result["Message"] == "Hello, World!"
