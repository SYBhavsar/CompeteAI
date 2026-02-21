"""
Test suite for Phase 2: Strategic Intelligence Models

Tests for:
- StrategicEvent (market entries, M&A, partnerships, product launches)
- Entity (products, people, companies, technologies)
- EntityRelationship (competitive knowledge graph)

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor

# Models to be created
from app.models.strategic_event import StrategicEvent
from app.models.entity import Entity
from app.models.entity_relationship import EntityRelationship


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


class TestStrategicEvent:
    """Test StrategicEvent model"""

    def test_create_market_entry_event(self, db, test_competitor):
        """
        GIVEN: Valid market entry data
        WHEN: Creating StrategicEvent
        THEN: Event is saved with correct attributes
        """
        event = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="market_entry",
            confidence=0.92,
            event_date=datetime(2026, 3, 1),
            title="Expanding to European Market",
            description="Competitor announced expansion into Germany, France, and UK",
            entities_involved={"countries": ["Germany", "France", "UK"]},
            strategic_implications="Potential threat to our European operations",
            source_insights={"insight_ids": [1, 2]}
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        assert event.id is not None
        assert event.event_category == "market_entry"
        assert event.confidence == 0.92
        assert event.title == "Expanding to European Market"

    def test_create_acquisition_event(self, db, test_competitor):
        """
        GIVEN: Acquisition announcement data
        WHEN: Creating StrategicEvent
        THEN: Event is saved with acquisition category
        """
        event = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="acquisition",
            confidence=0.98,
            event_date=datetime(2026, 2, 15),
            title="Acquired AI Startup TechCo",
            description="Acquired TechCo for $50M to enhance AI capabilities",
            entities_involved={
                "acquired_company": "TechCo",
                "amount": "$50M",
                "technology": "AI"
            },
            strategic_implications="Strengthens their AI position - we need to respond",
            source_insights={"insight_ids": [3]}
        )
        db.add(event)
        db.commit()

        assert event.event_category == "acquisition"
        assert event.entities_involved["acquired_company"] == "TechCo"

    def test_create_partnership_event(self, db, test_competitor):
        """
        GIVEN: Partnership announcement
        WHEN: Creating StrategicEvent
        THEN: Event is saved with partnership details
        """
        event = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="partnership",
            confidence=0.95,
            event_date=datetime(2026, 1, 20),
            title="Strategic Partnership with Microsoft",
            description="Announced integration with Microsoft Azure",
            entities_involved={
                "partner": "Microsoft",
                "platform": "Azure",
                "integration_type": "cloud"
            },
            strategic_implications="Microsoft partnership gives them enterprise credibility",
            source_insights={"insight_ids": [4, 5]}
        )
        db.add(event)
        db.commit()

        assert event.event_category == "partnership"
        assert "Microsoft" in str(event.entities_involved)

    def test_all_event_categories(self, db, test_competitor):
        """
        GIVEN: All 7 event categories
        WHEN: Creating StrategicEvents
        THEN: All categories are supported
        """
        categories = [
            "market_entry",
            "acquisition",
            "partnership",
            "product_launch",
            "pricing_change",
            "leadership_change",
            "funding"
        ]

        for category in categories:
            event = StrategicEvent(
                competitor_id=test_competitor.id,
                event_category=category,
                confidence=0.85,
                event_date=datetime.now(timezone.utc),
                title=f"Test {category}",
                description=f"Test event for {category}",
                entities_involved={},
                strategic_implications="Test implications",
                source_insights={}
            )
            db.add(event)

        db.commit()

        events = db.query(StrategicEvent).all()
        assert len(events) == len(categories)

    def test_confidence_score_range(self, db, test_competitor):
        """
        GIVEN: StrategicEvent with confidence score
        WHEN: Score is between 0.0 and 1.0
        THEN: Event is saved successfully
        """
        event = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="product_launch",
            confidence=0.87,
            event_date=datetime.now(timezone.utc),
            title="New Product Launch",
            description="Launched AI Analytics Suite",
            entities_involved={"product": "AI Analytics Suite"},
            strategic_implications="Competitive threat",
            source_insights={}
        )
        db.add(event)
        db.commit()

        assert 0.0 <= event.confidence <= 1.0

    def test_event_requires_competitor_id(self, db):
        """
        GIVEN: StrategicEvent without competitor_id
        WHEN: Attempting to save
        THEN: IntegrityError raised
        """
        with pytest.raises(IntegrityError):
            event = StrategicEvent(
                competitor_id=None,
                event_category="product_launch",
                confidence=0.9,
                event_date=datetime.now(timezone.utc),
                title="Test",
                description="Test",
                entities_involved={},
                strategic_implications="Test",
                source_insights={}
            )
            db.add(event)
            db.commit()


class TestEntity:
    """Test Entity model"""

    def test_create_product_entity(self, db, test_competitor):
        """
        GIVEN: Product entity data
        WHEN: Creating Entity
        THEN: Product entity is saved
        """
        entity = Entity(
            entity_type="product",
            name="AI Analytics Suite",
            aliases=["AI Suite", "Analytics Platform"],
            first_mentioned=datetime(2026, 1, 15),
            competitor_id=test_competitor.id,
            entity_metadata={
                "features": ["Predictive Analytics", "Real-time Insights"],
                "pricing": "$299/month",
                "target_market": "Enterprise"
            }
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)

        assert entity.id is not None
        assert entity.entity_type == "product"
        assert entity.name == "AI Analytics Suite"
        assert "AI Suite" in entity.aliases

    def test_create_person_entity(self, db, test_competitor):
        """
        GIVEN: Person entity (executive hire)
        WHEN: Creating Entity
        THEN: Person entity is saved with role entity_metadata
        """
        entity = Entity(
            entity_type="person",
            name="Jane Smith",
            aliases=["J. Smith"],
            first_mentioned=datetime(2026, 2, 1),
            competitor_id=test_competitor.id,
            entity_metadata={
                "role": "Chief AI Officer",
                "previous_company": "Google",
                "expertise": "Machine Learning"
            }
        )
        db.add(entity)
        db.commit()

        assert entity.entity_type == "person"
        assert entity.entity_metadata["role"] == "Chief AI Officer"

    def test_create_company_entity(self, db, test_competitor):
        """
        GIVEN: Company entity (partner or acquired company)
        WHEN: Creating Entity
        THEN: Company entity is saved
        """
        entity = Entity(
            entity_type="company",
            name="Microsoft",
            aliases=["MSFT"],
            first_mentioned=datetime(2026, 1, 20),
            competitor_id=test_competitor.id,
            entity_metadata={
                "relationship": "partner",
                "industry": "Technology",
                "partnership_type": "cloud_integration"
            }
        )
        db.add(entity)
        db.commit()

        assert entity.entity_type == "company"
        assert entity.name == "Microsoft"

    def test_create_technology_entity(self, db, test_competitor):
        """
        GIVEN: Technology entity
        WHEN: Creating Entity
        THEN: Technology entity is saved
        """
        entity = Entity(
            entity_type="technology",
            name="GPT-4",
            aliases=["GPT4", "OpenAI GPT-4"],
            first_mentioned=datetime(2026, 1, 10),
            competitor_id=test_competitor.id,
            entity_metadata={
                "vendor": "OpenAI",
                "use_case": "AI-powered features"
            }
        )
        db.add(entity)
        db.commit()

        assert entity.entity_type == "technology"
        assert entity.name == "GPT-4"

    def test_all_entity_types(self, db, test_competitor):
        """
        GIVEN: All 5 entity types
        WHEN: Creating entities
        THEN: All types are supported
        """
        entity_types = ["product", "person", "company", "technology", "partnership"]

        for entity_type in entity_types:
            entity = Entity(
                entity_type=entity_type,
                name=f"Test {entity_type}",
                aliases=[],
                first_mentioned=datetime.now(timezone.utc),
                competitor_id=test_competitor.id,
                entity_metadata={}
            )
            db.add(entity)

        db.commit()

        entities = db.query(Entity).all()
        assert len(entities) == len(entity_types)

    def test_entity_alias_search(self, db, test_competitor):
        """
        GIVEN: Entity with multiple aliases
        WHEN: Searching by alias
        THEN: Entity can be found
        """
        entity = Entity(
            entity_type="product",
            name="Enterprise Analytics Platform",
            aliases=["EAP", "Analytics Platform", "EA Platform"],
            first_mentioned=datetime.now(timezone.utc),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        db.add(entity)
        db.commit()

        # Verify aliases are stored
        assert len(entity.aliases) == 3
        assert "EAP" in entity.aliases


class TestEntityRelationship:
    """Test EntityRelationship model"""

    def test_create_competitor_relationship(self, db, test_competitor, test_user):
        """
        GIVEN: Two competing companies
        WHEN: Creating competitor relationship
        THEN: Relationship is saved
        """
        # Create two company entities
        company1 = Entity(
            entity_type="company",
            name="Company A",
            aliases=[],
            first_mentioned=datetime.now(timezone.utc),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        company2 = Entity(
            entity_type="company",
            name="Company B",
            aliases=[],
            first_mentioned=datetime.now(timezone.utc),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        db.add_all([company1, company2])
        db.commit()

        # Create relationship
        relationship = EntityRelationship(
            source_entity_id=company1.id,
            target_entity_id=company2.id,
            relationship_type="competitor",
            confidence=0.95
        )
        db.add(relationship)
        db.commit()
        db.refresh(relationship)

        assert relationship.id is not None
        assert relationship.relationship_type == "competitor"
        assert relationship.confidence == 0.95

    def test_create_partnership_relationship(self, db, test_competitor):
        """
        GIVEN: Company and partner
        WHEN: Creating partner relationship
        THEN: Partnership relationship is saved
        """
        company = Entity(
            entity_type="company",
            name="Competitor Inc",
            aliases=[],
            first_mentioned=datetime.now(timezone.utc),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        partner = Entity(
            entity_type="company",
            name="Microsoft",
            aliases=[],
            first_mentioned=datetime.now(timezone.utc),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        db.add_all([company, partner])
        db.commit()

        relationship = EntityRelationship(
            source_entity_id=company.id,
            target_entity_id=partner.id,
            relationship_type="partner",
            confidence=0.92
        )
        db.add(relationship)
        db.commit()

        assert relationship.relationship_type == "partner"

    def test_all_relationship_types(self, db, test_competitor):
        """
        GIVEN: Various relationship types
        WHEN: Creating relationships
        THEN: All types are supported
        """
        # Create entities
        entities = []
        for i in range(5):
            entity = Entity(
                entity_type="company",
                name=f"Company {i}",
                aliases=[],
                first_mentioned=datetime.now(timezone.utc),
                competitor_id=test_competitor.id,
                entity_metadata={}
            )
            entities.append(entity)
        db.add_all(entities)
        db.commit()

        relationship_types = [
            "competitor",
            "partner",
            "acquired_by",
            "uses_technology",
            "employs"
        ]

        for i, rel_type in enumerate(relationship_types):
            relationship = EntityRelationship(
                source_entity_id=entities[i].id,
                target_entity_id=entities[(i + 1) % len(entities)].id,
                relationship_type=rel_type,
                confidence=0.9
            )
            db.add(relationship)

        db.commit()

        relationships = db.query(EntityRelationship).all()
        assert len(relationships) == len(relationship_types)

    def test_bidirectional_relationships(self, db, test_competitor):
        """
        GIVEN: Two entities with bidirectional relationship
        WHEN: Creating both directions
        THEN: Both relationships are saved
        """
        company1 = Entity(
            entity_type="company",
            name="Company A",
            aliases=[],
            first_mentioned=datetime.now(timezone.utc),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        company2 = Entity(
            entity_type="company",
            name="Company B",
            aliases=[],
            first_mentioned=datetime.now(timezone.utc),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        db.add_all([company1, company2])
        db.commit()

        # A partners with B
        rel1 = EntityRelationship(
            source_entity_id=company1.id,
            target_entity_id=company2.id,
            relationship_type="partner",
            confidence=0.95
        )
        # B partners with A
        rel2 = EntityRelationship(
            source_entity_id=company2.id,
            target_entity_id=company1.id,
            relationship_type="partner",
            confidence=0.95
        )
        db.add_all([rel1, rel2])
        db.commit()

        relationships = db.query(EntityRelationship).all()
        assert len(relationships) == 2
