"""
Test suite for Entity Extraction Service

Tests AI-powered entity extraction using LangChain:
- Extract products, people, companies, technologies
- Structured Pydantic output
- Alias resolution and deduplication

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.entity import Entity
from app.services.entity_extraction_service import EntityExtractionService


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
def mock_llm_factory():
    """Mock LLMFactory.create to avoid real LLM initialization."""
    with patch('app.core.llm_factory.LLMFactory.create') as mock:
        mock.return_value = Mock()
        yield mock


@pytest.fixture
def mock_langchain():
    """Mock LangChain extraction chain"""
    with patch('app.services.entity_extraction_service.create_extraction_chain') as mock:
        yield mock


class TestEntityExtractionService:
    """Test EntityExtractionService"""

    def test_service_initialization(self, mock_llm_factory, mock_langchain):
        """
        GIVEN: EntityExtractionService class
        WHEN: Initializing the service
        THEN: Service is created with LangChain dependency
        """
        service = EntityExtractionService()
        assert service is not None

    def test_extract_product_entities(self, mock_llm_factory, db, test_competitor, mock_langchain):
        """
        GIVEN: Content mentioning products
        WHEN: Extracting entities
        THEN: Product entities are extracted
        """
        content = """
        We're excited to announce the launch of our new AI Analytics Suite,
        featuring Predictive Insights and Real-time Dashboard capabilities.
        """

        # Mock extraction chain response
        mock_chain = Mock()
        mock_chain.run.return_value = [
            {
                "entity_type": "product",
                "name": "AI Analytics Suite",
                "context": "new product launch"
            },
            {
                "entity_type": "product",
                "name": "Predictive Insights",
                "context": "product feature"
            }
        ]
        mock_langchain.return_value = mock_chain

        service = EntityExtractionService()
        entities = service.extract_entities(
            content=content,
            competitor_id=test_competitor.id,
            db=db
        )

        assert len(entities) >= 1
        assert any(e.entity_type == "product" for e in entities)
        assert any("AI Analytics" in e.name for e in entities)

    def test_extract_person_entities(self, mock_llm_factory, db, test_competitor, mock_langchain):
        """
        GIVEN: Content mentioning people
        WHEN: Extracting entities
        THEN: Person entities are extracted with roles
        """
        content = """
        We're pleased to announce that Jane Smith has joined as our new
        Chief Technology Officer. Jane comes from Google where she led
        AI research.
        """

        mock_chain = Mock()
        mock_chain.run.return_value = [
            {
                "entity_type": "person",
                "name": "Jane Smith",
                "context": "Chief Technology Officer, from Google"
            }
        ]
        mock_langchain.return_value = mock_chain

        service = EntityExtractionService()
        entities = service.extract_entities(
            content=content,
            competitor_id=test_competitor.id,
            db=db
        )

        assert len(entities) >= 1
        person_entities = [e for e in entities if e.entity_type == "person"]
        assert len(person_entities) >= 1
        assert "Jane Smith" in person_entities[0].name

    def test_extract_company_entities(self, mock_llm_factory, db, test_competitor, mock_langchain):
        """
        GIVEN: Content mentioning companies
        WHEN: Extracting entities
        THEN: Company entities are extracted
        """
        content = """
        We're excited to announce our strategic partnership with Microsoft
        to integrate with Azure cloud platform.
        """

        mock_chain = Mock()
        mock_chain.run.return_value = [
            {
                "entity_type": "company",
                "name": "Microsoft",
                "context": "strategic partnership"
            }
        ]
        mock_langchain.return_value = mock_chain

        service = EntityExtractionService()
        entities = service.extract_entities(
            content=content,
            competitor_id=test_competitor.id,
            db=db
        )

        company_entities = [e for e in entities if e.entity_type == "company"]
        assert len(company_entities) >= 1
        assert "Microsoft" in company_entities[0].name

    def test_extract_technology_entities(self, mock_llm_factory, db, test_competitor, mock_langchain):
        """
        GIVEN: Content mentioning technologies
        WHEN: Extracting entities
        THEN: Technology entities are extracted
        """
        content = """
        Our platform is powered by GPT-4 and runs on Kubernetes infrastructure
        with PostgreSQL database.
        """

        mock_chain = Mock()
        mock_chain.run.return_value = [
            {
                "entity_type": "technology",
                "name": "GPT-4",
                "context": "AI platform"
            },
            {
                "entity_type": "technology",
                "name": "Kubernetes",
                "context": "infrastructure"
            }
        ]
        mock_langchain.return_value = mock_chain

        service = EntityExtractionService()
        entities = service.extract_entities(
            content=content,
            competitor_id=test_competitor.id,
            db=db
        )

        tech_entities = [e for e in entities if e.entity_type == "technology"]
        assert len(tech_entities) >= 1

    def test_alias_resolution(self, mock_llm_factory, db, test_competitor, mock_langchain):
        """
        GIVEN: Content with multiple names for same entity
        WHEN: Extracting entities
        THEN: Aliases are detected and stored
        """
        content = """
        Our Enterprise Analytics Platform (EAP) provides real-time insights.
        The EAP system integrates with existing tools.
        """

        mock_chain = Mock()
        mock_chain.run.return_value = [
            {
                "entity_type": "product",
                "name": "Enterprise Analytics Platform",
                "context": "also known as EAP"
            }
        ]
        mock_langchain.return_value = mock_chain

        service = EntityExtractionService()
        entities = service.extract_entities(
            content=content,
            competitor_id=test_competitor.id,
            db=db
        )

        # Service should detect EAP as alias
        assert len(entities) >= 1
        # Check if entity has aliases property
        assert hasattr(entities[0], 'aliases')

    def test_deduplication(self, mock_llm_factory, db, test_competitor, mock_langchain):
        """
        GIVEN: Content mentioning same entity multiple times
        WHEN: Extracting entities
        THEN: Entity is only created once
        """
        content = """
        Microsoft Azure provides cloud services. Microsoft is a key partner.
        We integrate deeply with Microsoft products.
        """

        mock_chain = Mock()
        mock_chain.run.return_value = [
            {
                "entity_type": "company",
                "name": "Microsoft",
                "context": "cloud partner"
            },
            {
                "entity_type": "company",
                "name": "Microsoft",
                "context": "key partner"
            },
            {
                "entity_type": "company",
                "name": "Microsoft",
                "context": "product integration"
            }
        ]
        mock_langchain.return_value = mock_chain

        service = EntityExtractionService()
        entities = service.extract_entities(
            content=content,
            competitor_id=test_competitor.id,
            db=db
        )

        # Should deduplicate to single Microsoft entity
        microsoft_entities = [e for e in entities if "Microsoft" in e.name]
        assert len(microsoft_entities) == 1

    def test_entity_metadata_extraction(self, mock_llm_factory, db, test_competitor, mock_langchain):
        """
        GIVEN: Content with entity details
        WHEN: Extracting entities
        THEN: Metadata is extracted and stored
        """
        content = """
        Introducing our new Enterprise Plan at $999/month with advanced
        analytics, custom reporting, and dedicated support.
        """

        mock_chain = Mock()
        mock_chain.run.return_value = [
            {
                "entity_type": "product",
                "name": "Enterprise Plan",
                "context": "$999/month, advanced analytics, custom reporting"
            }
        ]
        mock_langchain.return_value = mock_chain

        service = EntityExtractionService()
        entities = service.extract_entities(
            content=content,
            competitor_id=test_competitor.id,
            db=db
        )

        assert len(entities) >= 1
        # Metadata should be stored
        assert hasattr(entities[0], 'entity_metadata')

    def test_mixed_entity_types(self, mock_llm_factory, db, test_competitor, mock_langchain):
        """
        GIVEN: Content with multiple entity types
        WHEN: Extracting entities
        THEN: All entity types are extracted
        """
        content = """
        CEO John Doe announced partnership with Microsoft to launch
        AI Platform powered by GPT-4 at $499/month.
        """

        mock_chain = Mock()
        mock_chain.run.return_value = [
            {"entity_type": "person", "name": "John Doe", "context": "CEO"},
            {"entity_type": "company", "name": "Microsoft", "context": "partner"},
            {"entity_type": "product", "name": "AI Platform", "context": "new launch"},
            {"entity_type": "technology", "name": "GPT-4", "context": "AI engine"}
        ]
        mock_langchain.return_value = mock_chain

        service = EntityExtractionService()
        entities = service.extract_entities(
            content=content,
            competitor_id=test_competitor.id,
            db=db
        )

        entity_types = {e.entity_type for e in entities}
        assert "person" in entity_types
        assert "company" in entity_types
        assert "product" in entity_types or "technology" in entity_types

    def test_empty_content(self, mock_llm_factory, db, test_competitor, mock_langchain):
        """
        GIVEN: Empty or minimal content
        WHEN: Extracting entities
        THEN: Returns empty list gracefully
        """
        mock_chain = Mock()
        mock_chain.run.return_value = []
        mock_langchain.return_value = mock_chain

        service = EntityExtractionService()
        entities = service.extract_entities(
            content="",
            competitor_id=test_competitor.id,
            db=db
        )

        assert entities == []

    def test_error_handling(self, mock_llm_factory, db, test_competitor, mock_langchain):
        """
        GIVEN: LangChain extraction fails
        WHEN: Extracting entities
        THEN: Error is handled gracefully
        """
        mock_chain = Mock()
        mock_chain.run.side_effect = Exception("LLM Error")
        mock_langchain.return_value = mock_chain

        service = EntityExtractionService()
        entities = service.extract_entities(
            content="Test content",
            competitor_id=test_competitor.id,
            db=db
        )

        # Should return empty list on error
        assert entities == []
