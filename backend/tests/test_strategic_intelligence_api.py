"""
Test suite for Strategic Intelligence API

Tests endpoints for:
- Strategic events (market entries, M&A, partnerships, product launches, etc.)
- Entity management (products, people, companies, technologies)
- Entity relationships (knowledge graph)
- Strategic analytics

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.strategic_event import StrategicEvent
from app.models.entity import Entity
from app.models.entity_relationship import EntityRelationship
from app.utils.jwt import create_access_token


@pytest.fixture
def db():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_competitor(db, test_user):
    """Create test competitor"""
    competitor = Competitor(
        name="Test Competitor",
        domain="competitor.com",
        user_id=test_user.id
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers"""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestStrategicEventsAPI:
    """Test Strategic Events endpoints"""

    def test_get_strategic_events(self, client, db, test_user, test_competitor, auth_headers):
        """
        GIVEN: Competitor with strategic events
        WHEN: GET /strategic/competitors/{id}/events
        THEN: Returns list of strategic events
        """
        # Create strategic events
        event1 = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="market_entry",
            confidence=0.92,
            event_date=datetime.utcnow() - timedelta(days=5),
            title="European Market Expansion",
            description="Expanding to Germany, France, UK",
            entities_involved={"countries": ["Germany", "France", "UK"]},
            strategic_implications="Threat to our European operations",
            source_insights={}
        )
        event2 = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="acquisition",
            confidence=0.95,
            event_date=datetime.utcnow() - timedelta(days=2),
            title="Acquired TechCo",
            description="$50M acquisition for AI capabilities",
            entities_involved={"acquired_company": "TechCo", "amount": "$50M"},
            strategic_implications="Strengthens AI position",
            source_insights={}
        )
        db.add_all([event1, event2])
        db.commit()

        response = client.get(
            f"/strategic/competitors/{test_competitor.id}/events",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert any(e["event_category"] == "market_entry" for e in data)
        assert any(e["event_category"] == "acquisition" for e in data)

    def test_get_strategic_events_filtered_by_category(
        self, client, db, test_user, test_competitor, auth_headers
    ):
        """
        GIVEN: Multiple strategic events
        WHEN: GET /strategic/competitors/{id}/events?category=acquisition
        THEN: Returns only acquisition events
        """
        event1 = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="acquisition",
            confidence=0.95,
            event_date=datetime.utcnow(),
            title="Acquired Company A",
            description="Test",
            entities_involved={},
            strategic_implications="Test",
            source_insights={}
        )
        event2 = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="partnership",
            confidence=0.90,
            event_date=datetime.utcnow(),
            title="Microsoft Partnership",
            description="Test",
            entities_involved={},
            strategic_implications="Test",
            source_insights={}
        )
        db.add_all([event1, event2])
        db.commit()

        response = client.get(
            f"/strategic/competitors/{test_competitor.id}/events?category=acquisition",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(e["event_category"] == "acquisition" for e in data)

    def test_get_strategic_events_filtered_by_date(
        self, client, db, test_user, test_competitor, auth_headers
    ):
        """
        GIVEN: Strategic events from different dates
        WHEN: GET /strategic/competitors/{id}/events?days=7
        THEN: Returns only events from last 7 days
        """
        recent_event = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="product_launch",
            confidence=0.90,
            event_date=datetime.utcnow() - timedelta(days=3),
            title="New Product",
            description="Recent launch",
            entities_involved={},
            strategic_implications="Test",
            source_insights={}
        )
        old_event = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="funding",
            confidence=0.92,
            event_date=datetime.utcnow() - timedelta(days=30),
            title="Old Funding",
            description="Old news",
            entities_involved={},
            strategic_implications="Test",
            source_insights={}
        )
        db.add_all([recent_event, old_event])
        db.commit()

        response = client.get(
            f"/strategic/competitors/{test_competitor.id}/events?days=7",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Should only return recent event (not old event from 30 days ago)
        assert len(data) == 1
        assert data[0]["title"] == "New Product"

    def test_get_strategic_events_unauthorized(self, client, db, test_competitor):
        """
        GIVEN: No authentication
        WHEN: GET /strategic/competitors/{id}/events
        THEN: Returns 403 Forbidden
        """
        response = client.get(f"/strategic/competitors/{test_competitor.id}/events")
        assert response.status_code == 403


class TestEntitiesAPI:
    """Test Entities endpoints"""

    def test_get_entities(self, client, db, test_user, test_competitor, auth_headers):
        """
        GIVEN: Competitor with extracted entities
        WHEN: GET /strategic/competitors/{id}/entities
        THEN: Returns list of entities
        """
        entity1 = Entity(
            entity_type="product",
            name="AI Analytics Suite",
            aliases=["AI Suite"],
            first_mentioned=datetime.utcnow(),
            competitor_id=test_competitor.id,
            entity_metadata={"pricing": "$299/month"}
        )
        entity2 = Entity(
            entity_type="person",
            name="Jane Smith",
            aliases=["J. Smith"],
            first_mentioned=datetime.utcnow(),
            competitor_id=test_competitor.id,
            entity_metadata={"role": "CTO"}
        )
        db.add_all([entity1, entity2])
        db.commit()

        response = client.get(
            f"/strategic/competitors/{test_competitor.id}/entities",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert any(e["entity_type"] == "product" for e in data)
        assert any(e["entity_type"] == "person" for e in data)

    def test_get_entities_filtered_by_type(
        self, client, db, test_user, test_competitor, auth_headers
    ):
        """
        GIVEN: Multiple entity types
        WHEN: GET /strategic/competitors/{id}/entities?entity_type=company
        THEN: Returns only company entities
        """
        entity1 = Entity(
            entity_type="company",
            name="Microsoft",
            aliases=["MSFT"],
            first_mentioned=datetime.utcnow(),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        entity2 = Entity(
            entity_type="product",
            name="Product X",
            aliases=[],
            first_mentioned=datetime.utcnow(),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        db.add_all([entity1, entity2])
        db.commit()

        response = client.get(
            f"/strategic/competitors/{test_competitor.id}/entities?entity_type=company",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(e["entity_type"] == "company" for e in data)

    def test_get_entity_by_id(self, client, db, test_user, test_competitor, auth_headers):
        """
        GIVEN: Specific entity
        WHEN: GET /strategic/entities/{entity_id}
        THEN: Returns entity details
        """
        entity = Entity(
            entity_type="product",
            name="Enterprise Platform",
            aliases=["EP", "Platform"],
            first_mentioned=datetime.utcnow(),
            competitor_id=test_competitor.id,
            entity_metadata={"pricing": "$999/month", "features": ["Analytics", "Reporting"]}
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)

        response = client.get(
            f"/strategic/entities/{entity.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Enterprise Platform"
        assert "EP" in data["aliases"]
        assert data["entity_metadata"]["pricing"] == "$999/month"


class TestEntityRelationshipsAPI:
    """Test Entity Relationships endpoints"""

    def test_get_entity_relationships(
        self, client, db, test_user, test_competitor, auth_headers
    ):
        """
        GIVEN: Entities with relationships
        WHEN: GET /strategic/entities/{entity_id}/relationships
        THEN: Returns entity relationships
        """
        # Create entities
        company1 = Entity(
            entity_type="company",
            name="Competitor Inc",
            aliases=[],
            first_mentioned=datetime.utcnow(),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        company2 = Entity(
            entity_type="company",
            name="Microsoft",
            aliases=[],
            first_mentioned=datetime.utcnow(),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        db.add_all([company1, company2])
        db.commit()

        # Create relationship
        relationship = EntityRelationship(
            source_entity_id=company1.id,
            target_entity_id=company2.id,
            relationship_type="partner",
            confidence=0.95
        )
        db.add(relationship)
        db.commit()

        response = client.get(
            f"/strategic/entities/{company1.id}/relationships",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["relationship_type"] == "partner"
        assert data[0]["confidence"] == 0.95

    def test_get_knowledge_graph(
        self, client, db, test_user, test_competitor, auth_headers
    ):
        """
        GIVEN: Multiple entities and relationships
        WHEN: GET /strategic/competitors/{id}/knowledge-graph
        THEN: Returns graph structure (nodes and edges)
        """
        # Create entities
        entities = [
            Entity(
                entity_type="company",
                name=f"Company {i}",
                aliases=[],
                first_mentioned=datetime.utcnow(),
                competitor_id=test_competitor.id,
                entity_metadata={}
            )
            for i in range(3)
        ]
        db.add_all(entities)
        db.commit()

        # Create relationships
        rel1 = EntityRelationship(
            source_entity_id=entities[0].id,
            target_entity_id=entities[1].id,
            relationship_type="partner",
            confidence=0.9
        )
        rel2 = EntityRelationship(
            source_entity_id=entities[1].id,
            target_entity_id=entities[2].id,
            relationship_type="competitor",
            confidence=0.85
        )
        db.add_all([rel1, rel2])
        db.commit()

        response = client.get(
            f"/strategic/competitors/{test_competitor.id}/knowledge-graph",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) >= 3
        assert len(data["edges"]) >= 2


class TestStrategicAnalyticsAPI:
    """Test Strategic Analytics endpoints"""

    def test_get_event_summary(
        self, client, db, test_user, test_competitor, auth_headers
    ):
        """
        GIVEN: Multiple strategic events
        WHEN: GET /strategic/competitors/{id}/analytics/event-summary
        THEN: Returns event counts by category
        """
        events = [
            StrategicEvent(
                competitor_id=test_competitor.id,
                event_category="acquisition",
                confidence=0.9,
                event_date=datetime.utcnow(),
                title="Test 1",
                description="Test",
                entities_involved={},
                strategic_implications="Test",
                source_insights={}
            ),
            StrategicEvent(
                competitor_id=test_competitor.id,
                event_category="acquisition",
                confidence=0.92,
                event_date=datetime.utcnow(),
                title="Test 2",
                description="Test",
                entities_involved={},
                strategic_implications="Test",
                source_insights={}
            ),
            StrategicEvent(
                competitor_id=test_competitor.id,
                event_category="partnership",
                confidence=0.88,
                event_date=datetime.utcnow(),
                title="Test 3",
                description="Test",
                entities_involved={},
                strategic_implications="Test",
                source_insights={}
            )
        ]
        db.add_all(events)
        db.commit()

        response = client.get(
            f"/strategic/competitors/{test_competitor.id}/analytics/event-summary",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["acquisition"] == 2
        assert data["partnership"] == 1

    def test_get_entity_summary(
        self, client, db, test_user, test_competitor, auth_headers
    ):
        """
        GIVEN: Multiple entities
        WHEN: GET /strategic/competitors/{id}/analytics/entity-summary
        THEN: Returns entity counts by type
        """
        entities = [
            Entity(
                entity_type="product",
                name="Product 1",
                aliases=[],
                first_mentioned=datetime.utcnow(),
                competitor_id=test_competitor.id,
                entity_metadata={}
            ),
            Entity(
                entity_type="product",
                name="Product 2",
                aliases=[],
                first_mentioned=datetime.utcnow(),
                competitor_id=test_competitor.id,
                entity_metadata={}
            ),
            Entity(
                entity_type="person",
                name="Person 1",
                aliases=[],
                first_mentioned=datetime.utcnow(),
                competitor_id=test_competitor.id,
                entity_metadata={}
            )
        ]
        db.add_all(entities)
        db.commit()

        response = client.get(
            f"/strategic/competitors/{test_competitor.id}/analytics/entity-summary",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["product"] == 2
        assert data["person"] == 1

    def test_get_strategic_activity_timeline(
        self, client, db, test_user, test_competitor, auth_headers
    ):
        """
        GIVEN: Strategic events over time
        WHEN: GET /strategic/competitors/{id}/analytics/timeline
        THEN: Returns chronological event timeline
        """
        events = [
            StrategicEvent(
                competitor_id=test_competitor.id,
                event_category="market_entry",
                confidence=0.9,
                event_date=datetime.utcnow() - timedelta(days=10),
                title="Expansion",
                description="Test",
                entities_involved={},
                strategic_implications="Test",
                source_insights={}
            ),
            StrategicEvent(
                competitor_id=test_competitor.id,
                event_category="acquisition",
                confidence=0.92,
                event_date=datetime.utcnow() - timedelta(days=5),
                title="Acquired Company",
                description="Test",
                entities_involved={},
                strategic_implications="Test",
                source_insights={}
            )
        ]
        db.add_all(events)
        db.commit()

        response = client.get(
            f"/strategic/competitors/{test_competitor.id}/analytics/timeline",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        # Should be sorted chronologically (oldest first or newest first)
        assert "event_date" in data[0]
