import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

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

    client.post("/auth/register", json=user_data)

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
def test_analytics_data(test_user_and_token):
    """Create test data for analytics"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()

        # Create competitors
        competitor1 = Competitor(
            name="Company A",
            domain="companya.com",
            user_id=user.id
        )
        competitor2 = Competitor(
            name="Company B",
            domain="companyb.com",
            user_id=user.id
        )
        db.add_all([competitor1, competitor2])
        db.commit()

        # Create data sources
        source1 = DataSource(
            competitor_id=competitor1.id,
            source_type="website",
            url="https://companya.com",
            is_active=True
        )
        source2 = DataSource(
            competitor_id=competitor2.id,
            source_type="website",
            url="https://companyb.com",
            is_active=True
        )
        db.add_all([source1, source2])
        db.commit()

        # Create raw content and insights
        for i in range(5):
            raw_content = RawContent(
                data_source_id=source1.id,
                content=f"Test content {i}",
                content_type="text/html",
                url=f"https://companya.com/post{i}"
            )
            db.add(raw_content)
            db.commit()

            insight = ProcessedInsights(
                raw_content_id=raw_content.id,
                summary=f"Summary {i}",
                sentiment="positive" if i % 2 == 0 else "negative",
                insights=f"Insights {i}",
                quality_score=0.8 + (i * 0.02)
            )
            db.add(insight)
            db.commit()

        return {
            "competitor1_id": competitor1.id,
            "competitor2_id": competitor2.id,
            **test_user_and_token
        }
    finally:
        db.close()


def test_get_trends_analysis(client, test_analytics_data):
    """Test getting trend analysis"""
    headers = test_analytics_data["headers"]

    response = client.get("/analytics/trends", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert "period" in data


def test_get_trends_with_time_range(client, test_analytics_data):
    """Test trends with custom time range"""
    headers = test_analytics_data["headers"]

    response = client.get(
        "/analytics/trends?days=7",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "trends" in data


def test_get_competitor_summary(client, test_analytics_data):
    """Test getting competitor summary"""
    competitor_id = test_analytics_data["competitor1_id"]
    headers = test_analytics_data["headers"]

    response = client.get(
        f"/analytics/summary/{competitor_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "competitor_id" in data
    assert "total_insights" in data
    assert "sentiment_distribution" in data
    assert "average_quality_score" in data
    assert "recent_activity" in data


def test_get_competitor_summary_not_found(client, test_user_and_token):
    """Test summary for non-existent competitor"""
    headers = test_user_and_token["headers"]

    response = client.get("/analytics/summary/99999", headers=headers)

    assert response.status_code == 404


def test_compare_competitors(client, test_analytics_data):
    """Test comparing multiple competitors"""
    competitor1_id = test_analytics_data["competitor1_id"]
    competitor2_id = test_analytics_data["competitor2_id"]
    headers = test_analytics_data["headers"]

    response = client.get(
        f"/analytics/comparison?competitor_ids={competitor1_id},{competitor2_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "comparisons" in data
    assert len(data["comparisons"]) == 2


def test_compare_competitors_single(client, test_analytics_data):
    """Test comparison with single competitor"""
    competitor1_id = test_analytics_data["competitor1_id"]
    headers = test_analytics_data["headers"]

    response = client.get(
        f"/analytics/comparison?competitor_ids={competitor1_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["comparisons"]) == 1


def test_export_insights_csv(client, test_analytics_data):
    """Test exporting insights as CSV"""
    competitor_id = test_analytics_data["competitor1_id"]
    headers = test_analytics_data["headers"]

    response = client.get(
        f"/analytics/export?competitor_id={competitor_id}&format=csv",
        headers=headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


def test_export_insights_json(client, test_analytics_data):
    """Test exporting insights as JSON"""
    competitor_id = test_analytics_data["competitor1_id"]
    headers = test_analytics_data["headers"]

    response = client.get(
        f"/analytics/export?competitor_id={competitor_id}&format=json",
        headers=headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


def test_get_sentiment_trends(client, test_analytics_data):
    """Test getting sentiment trends over time"""
    competitor_id = test_analytics_data["competitor1_id"]
    headers = test_analytics_data["headers"]

    response = client.get(
        f"/analytics/trends?competitor_id={competitor_id}&metric=sentiment",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "trends" in data


def test_get_quality_score_distribution(client, test_analytics_data):
    """Test getting quality score distribution"""
    headers = test_analytics_data["headers"]

    response = client.get("/analytics/quality-distribution", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "high" in data
    assert "medium" in data
    assert "low" in data


def test_analytics_unauthorized(client, test_analytics_data):
    """Test analytics endpoints without authentication"""
    response = client.get("/analytics/trends")

    assert response.status_code == 403