from app.api.auth import create_token
from fastapi.testclient import TestClient
def test_unauthenticated_user(client_with_registry:TestClient) -> None:
    response = client_with_registry.get("/evaluators")
    assert response.status_code == 401

def test_authenticated_user(client_with_registry:TestClient) -> None:
    token = create_token("test-user")

    headers = {"Authorization": f"Bearer {token}"}

    response = client_with_registry.get("/evaluators",headers=headers)
    assert response.status_code == 200

def test_invalid_bearer_token(client_with_registry:TestClient) -> None:
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30"
    headers = {"Authorization": f"Bearer {token}"}
    response = client_with_registry.get("/evaluators",headers=headers)
    assert response.status_code == 401