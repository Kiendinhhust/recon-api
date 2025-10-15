"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import create_app
from app.deps import get_db, Base


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Create test client with test database"""
    Base.metadata.create_all(bind=engine)
    
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    Base.metadata.drop_all(bind=engine)


class TestScanEndpoints:
    """Test scan API endpoints"""
    
    def test_create_scan(self, client):
        """Test creating a new scan"""
        response = client.post(
            "/api/v1/scans",
            json={"domain": "example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["domain"] == "example.com"
        assert data["status"] == "pending"
    
    def test_create_scan_invalid_domain(self, client):
        """Test creating scan with invalid domain"""
        response = client.post(
            "/api/v1/scans",
            json={"domain": "invalid"}
        )
        
        assert response.status_code == 400
        assert "Invalid domain format" in response.json()["detail"]
    
    def test_get_scan_not_found(self, client):
        """Test getting non-existent scan"""
        response = client.get("/api/v1/scans/nonexistent-job-id")
        
        assert response.status_code == 404
        assert "Scan job not found" in response.json()["detail"]
    
    def test_list_scans_empty(self, client):
        """Test listing scans when none exist"""
        response = client.get("/api/v1/scans")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_scan_workflow(self, client):
        """Test complete scan workflow"""
        # Create scan
        create_response = client.post(
            "/api/v1/scans",
            json={"domain": "example.com"}
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]
        
        # Get scan details
        get_response = client.get(f"/api/v1/scans/{job_id}")
        assert get_response.status_code == 200
        
        scan_data = get_response.json()
        assert scan_data["job_id"] == job_id
        assert scan_data["domain"] == "example.com"
        assert scan_data["status"] in ["pending", "running", "completed", "failed"]
        
        # List scans
        list_response = client.get("/api/v1/scans")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1
        assert list_response.json()[0]["job_id"] == job_id


class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    def test_openapi_schema(self, client):
        """Test OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Recon API"
    
    def test_swagger_docs(self, client):
        """Test Swagger documentation page"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_docs(self, client):
        """Test ReDoc documentation page"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestRootEndpoint:
    """Test root endpoint and frontend"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Recon API" in response.text
