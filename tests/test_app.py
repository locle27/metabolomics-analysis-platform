"""
Basic tests for the metabolomics application
"""

import pytest
import json
from app import app


@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] in ['healthy', 'degraded']
    assert 'timestamp' in data
    assert 'version' in data


def test_ping(client):
    """Test ping endpoint"""
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.data == b'pong'


def test_status_endpoint(client):
    """Test status endpoint"""
    response = client.get('/status')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'status' in data
    assert 'features' in data


def test_homepage(client):
    """Test homepage loads"""
    response = client.get('/')
    assert response.status_code == 200


def test_login_page(client):
    """Test login page loads"""
    response = client.get('/auth/login')
    assert response.status_code == 200


def test_404_error(client):
    """Test 404 error handling"""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404


def test_security_headers(client):
    """Test that security headers are present"""
    response = client.get('/')
    
    # Test for common security headers
    headers = response.headers
    assert 'X-Content-Type-Options' in headers
    assert 'X-Frame-Options' in headers
    
    # These will only be present if Talisman is installed
    if 'Content-Security-Policy' in headers:
        assert headers['X-Content-Type-Options'] == 'nosniff'
        assert headers['X-Frame-Options'] == 'DENY'


def test_performance_headers(client):
    """Test that performance timing headers are present"""
    response = client.get('/health')
    assert 'X-Response-Time' in response.headers


if __name__ == '__main__':
    pytest.main([__file__])