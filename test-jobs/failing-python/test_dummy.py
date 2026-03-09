import requests

def test_api_call():
    response = requests.get("https://api.example.com/data")
    assert response.status_code == 200

def test_math():
    result = 10 / 0  # ZeroDivisionError
    assert result == 5
