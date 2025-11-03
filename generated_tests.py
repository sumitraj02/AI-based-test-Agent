import os
import requests
import pytest

BASE_URL = os.getenv('TEST_API_URL', 'http://localhost:8000')

def test_endpoint_with_max():
    response = requests.get(f"{BASE_URL}/api/endpoint?param=max")
    assert response.status_code == 200
    assert response.json() == {"result": "success"}

def test_endpoint_with_min():
    response = requests.get(f"{BASE_URL}/api/endpoint?param=min")
    assert response.status_code == 200
    assert response.json() == {"result": "success"}

def test_endpoint_no_auth():
    response = requests.get(f"{BASE_URL}/api/endpoint?param=random")
    assert response.status_code == 401

def test_endpoint_invalid_api_key():
    headers = {'Authorization': 'Bearer invalid-api-key'}
    response = requests.get(f"{BASE_URL}/api/endpoint?param=random", headers=headers)
    assert response.status_code == 403

def test_endpoint_random_auth_key():
    headers = {'Authorization': 'Bearer valid-api-key'}
    response = requests.get(f"{BASE_URL}/api/endpoint?param=random", headers=headers)
    assert response.status_code == 404

def test_nonexistent_endpoint():
    response = requests.get(f"{BASE_URL}/api/nonexistent")
    assert response.status_code == 404

def test_error_endpoint():
    response = requests.get(f"{BASE_URL}/api/error")
    assert response.status_code == 500