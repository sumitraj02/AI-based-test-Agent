import os
import requests
import pytest

BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")

def test_endpoint_with_max():
    """
    main.py returns 200 if param == 'max' (and never checks auth).
    """
    response = requests.get(f"{BASE_URL}/api/endpoint?param=max")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json() == {"result": "success"}

def test_endpoint_with_min():
    """
    main.py returns 200 if param == 'min'.
    """
    response = requests.get(f"{BASE_URL}/api/endpoint?param=min")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json() == {"result": "success"}

def test_endpoint_no_param_no_auth_header():
    """
    If param != 'max'/'min' and no Authorization header, main.py returns 401.
    """
    response = requests.get(f"{BASE_URL}/api/endpoint")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

def test_endpoint_invalid_api_key():
    """
    If param != 'max'/'min' and header == 'Bearer invalid-api-key', main.py returns 403.
    """
    headers = {"Authorization": "Bearer invalid-api-key"}
    response = requests.get(f"{BASE_URL}/api/endpoint?param=something", headers=headers)
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"

def test_endpoint_random_auth_key():
    """
    If param != 'max'/'min' and header != 'Bearer invalid-api-key', main.py returns 404.
    """
    headers = {"Authorization": "Bearer some-random-key"}
    response = requests.get(f"{BASE_URL}/api/endpoint?param=something", headers=headers)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

def test_nonexistent_endpoint():
    """
    /api/nonexistent always returns 404.
    """
    response = requests.get(f"{BASE_URL}/api/nonexistent")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

def test_error_endpoint():
    """
    /api/error always returns 500.
    """
    response = requests.get(f"{BASE_URL}/api/error")
    assert response.status_code == 500, f"Expected 500, got {response.status_code}"
