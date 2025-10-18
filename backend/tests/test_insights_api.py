import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor, DataSource, RawContent, ProcessedInsights


@pytest.fixture
def client():
    """Create test client"""
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user_and_token(client):
    """Create test user and get auth token"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    # Register user
    client.post("/auth/register", json=user_data)
    
    # Login to get token
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    
    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


@pytest.fixture
def test_data_with_insights(test_user_and_token):
    """Create test data with processed insights"""
    db = SessionLocal()
    try:
        # Get user
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        # Create competitor
        competitor = Competitor(
            name="Test Company",
            domain="testcompany.com",
            user_id=user.id
        )
        db.add(competitor)
        db.commit()
        
        # Create data source
        data_source = DataSource(
            competitor_id=competitor.id,
            source_type="website",
            url="https://testcompany.com/blog",
            is_active=True
        )
        db.add(data_source)
        db.commit()
        
        # Create raw content
        raw_content = RawContent(
            data_source_id=data_source.id,
            content="Test Company announces new AI product with advanced features",
            content_type="text/html",
            url="https://testcompany.com/blog/ai-product"
        )
        db.add(raw_content)
        db.commit()
        
        # Create processed insights
        processed_insights = ProcessedInsights(
            raw_content_id=raw_content.id,
            summary="Company announces new AI product",
            key_points=["AI product launch", "Advanced features", "Market expansion"],
            sentiment="positive",
            insights="Strategic move into AI market with competitive features"
        )
        db.add(processed_insights)
        db.commit()
        
        db.refresh(competitor)
        db.refresh(raw_content)
        db.refresh(processed_insights)
        
        return {
            "competitor_id": competitor.id,
            "raw_content_id": raw_content.id,
            "insights_id": processed_insights.id,
            **test_user_and_token
        }
    finally:
        db.close()


def test_get_competitor_insights_success(client, test_data_with_insights):
    """Test successful retrieval of competitor insights"""
    competitor_id = test_data_with_insights["competitor_id"]
    headers = test_data_with_insights["headers"]
    
    response = client.get(f"/competitors/{competitor_id}/insights", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["summary"] == "Company announces new AI product"
    assert data[0]["sentiment"] == "positive"
    assert "key_points" in data[0]
    assert "insights" in data[0]


def test_get_specific_insight_success(client, test_data_with_insights):
    """Test successful retrieval of specific insight"""
    insights_id = test_data_with_insights["insights_id"]
    headers = test_data_with_insights["headers"]
    
    response = client.get(f"/insights/{insights_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Company announces new AI product"
    assert data["sentiment"] == "positive"
    assert data["key_points"] == ["AI product launch", "Advanced features", "Market expansion"]


def test_process_raw_content_endpoint(client, test_data_with_insights):
    """Test processing raw content through API"""
    raw_content_id = test_data_with_insights["raw_content_id"]
    headers = test_data_with_insights["headers"]
    
    # First delete existing insights to test processing
    db = SessionLocal()
    try:
        existing_insights = db.query(ProcessedInsights).filter(
            ProcessedInsights.raw_content_id == raw_content_id
        ).first()
        if existing_insights:
            db.delete(existing_insights)
            db.commit()
    finally:
        db.close()
    
    with patch('app.api.insights.ContentProcessingService') as mock_service:
        mock_instance = Mock()
        mock_result = Mock()
        mock_result.id = 1
        mock_result.raw_content_id = raw_content_id
        mock_result.summary = "Processed summary"
        mock_result.sentiment = "positive"
        mock_result.insights = "Processed insights"
        mock_result.key_points = ["Key point 1"]
        mock_result.created_at = datetime.now()
        mock_result.updated_at = datetime.now()
        mock_instance.process_raw_content.return_value = mock_result
        mock_service.return_value = mock_instance
        
        response = client.post(f"/insights/process/{raw_content_id}", headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["summary"] == "Processed summary"
    assert data["sentiment"] == "positive"


def test_get_insights_by_sentiment(client, test_data_with_insights):
    """Test filtering insights by sentiment"""
    competitor_id = test_data_with_insights["competitor_id"]
    headers = test_data_with_insights["headers"]
    
    response = client.get(f"/competitors/{competitor_id}/insights?sentiment=positive", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["sentiment"] == "positive"


def test_get_insights_unauthenticated(client, test_data_with_insights):
    """Test insights access without authentication fails"""
    competitor_id = test_data_with_insights["competitor_id"]
    
    response = client.get(f"/competitors/{competitor_id}/insights")
    
    assert response.status_code == 403


def test_get_insights_nonexistent_competitor(client, test_user_and_token):
    """Test insights for nonexistent competitor"""
    headers = test_user_and_token["headers"]
    
    response = client.get("/competitors/99999/insights", headers=headers)
    
    assert response.status_code == 404


def test_get_insight_nonexistent_id(client, test_user_and_token):
    """Test getting nonexistent insight"""
    headers = test_user_and_token["headers"]
    
    response = client.get("/insights/99999", headers=headers)
    
    assert response.status_code == 404


def test_process_nonexistent_raw_content(client, test_user_and_token):
    """Test processing nonexistent raw content"""
    headers = test_user_and_token["headers"]
    
    with patch('app.api.insights.ContentProcessingService') as mock_service:
        mock_instance = Mock()
        mock_instance.process_raw_content.return_value = None
        mock_service.return_value = mock_instance
        
        response = client.post("/insights/process/99999", headers=headers)
    
    assert response.status_code == 404