# AI Competitive Intelligence Platform

An automated competitive intelligence platform with AI-powered insights, semantic search, and real-time alerts.

## 🎯 Overview

This platform helps businesses monitor their competitors by automatically scraping web content, analyzing it using AI (OpenAI GPT), storing insights in a vector database, and providing intelligent search and alerting capabilities.

## ✨ Features

### 🔐 Authentication & User Management
- JWT-based authentication
- Secure user registration and login
- User-specific data isolation

### 🏢 Competitor Management
- Add and track multiple competitors
- Manage competitor profiles (name, domain, industry)
- Full CRUD operations on competitors

### 🕷️ Automated Web Scraping
- BeautifulSoup and Scrapy-based scrapers
- Scheduled scraping with Celery background tasks
- Rate limiting and respectful scraping
- Content deduplication
- Multiple data source types support

### 🤖 AI-Powered Content Analysis
- **OpenAI Integration**:
  - Content summarization (2-3 sentences)
  - Key insight extraction
  - Sentiment analysis (positive/negative/neutral)
- **LangChain Workflows**:
  - Custom prompt templates
  - Chain orchestration for complex analysis
  - Strategic competitive intelligence extraction
- **Quality Scoring**:
  - Multi-factor quality assessment
  - Weighted scoring algorithm

### 🔍 Advanced Search
- **Semantic Search**: Vector-based similarity search using Pinecone
- **Traditional Search**: Keyword-based SQL search with filters
- **Saved Searches**: Save and manage frequently used searches
- **Search History**: Track all search activity with automatic logging

### 📊 Analytics & Insights
- Trend analysis over time
- Sentiment distribution tracking
- Multi-competitor comparison
- Export to CSV/JSON formats
- Quality score metrics

### 🔔 Alert System
- **Alert Types**:
  - Sentiment change detection
  - New content notifications
  - Keyword match alerts
- **Notification Delivery**:
  - Email notifications (configurable)
  - Batch delivery support
  - Read/unread tracking
- **Automatic Triggers**:
  - Celery-based background processing
  - Periodic alert checking (every 10 minutes)

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **ORM**: SQLAlchemy
- **Background Jobs**: Celery
- **Testing**: Pytest (100+ tests)

### AI & ML
- **LLM**: OpenAI GPT-3.5-turbo
- **Embeddings**: OpenAI text-embedding-ada-002
- **Vector DB**: Pinecone
- **AI Framework**: LangChain

### Web Scraping
- BeautifulSoup4
- Scrapy
- Requests

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── auth.py
│   │   ├── competitors.py
│   │   ├── data_sources.py
│   │   ├── scraping.py
│   │   ├── schedules.py
│   │   ├── insights.py
│   │   ├── search.py
│   │   ├── analytics.py
│   │   └── alerts.py
│   ├── core/             # Core configuration
│   │   ├── config.py
│   │   ├── database.py
│   │   └── celery_app.py
│   ├── models/           # Database models
│   │   ├── user.py
│   │   ├── competitor.py
│   │   ├── data_source.py
│   │   ├── raw_content.py
│   │   ├── processed_insights.py
│   │   ├── scraping_schedule.py
│   │   ├── alert.py
│   │   └── search.py
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── scraper_service.py
│   │   ├── openai_client.py
│   │   ├── langchain_service.py
│   │   ├── embedding_service.py
│   │   ├── pinecone_client.py
│   │   ├── quality_scoring_service.py
│   │   ├── alert_trigger_service.py
│   │   └── notification_delivery_service.py
│   ├── tasks/            # Celery tasks
│   │   ├── scraping_tasks.py
│   │   ├── scheduling_tasks.py
│   │   └── alert_tasks.py
│   ├── utils/            # Utilities
│   └── main.py           # FastAPI app
├── tests/                # Test suite (100+ tests)
└── requirements.txt
```

## 🚀 Setup Instructions

### Prerequisites
- Python 3.12+
- PostgreSQL
- Redis
- OpenAI API key
- Pinecone API key

### 1. Clone the Repository
```bash
git clone <repository-url>
cd RecipeMind/backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the `backend` directory:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/competitive_intel

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
```

### 5. Create Database
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE competitive_intel;
\q
```

### 6. Initialize Database Tables
```bash
# Start the FastAPI app (tables will be created automatically)
uvicorn app.main:app --reload
```

Or run this Python command:
```bash
python3 << 'EOF'
from app.core.database import Base, engine
from app.models.user import User
from app.models.competitor import Competitor
from app.models.data_source import DataSource
from app.models.raw_content import RawContent
from app.models.processed_insights import ProcessedInsights
from app.models.scraping_schedule import ScrapingSchedule
from app.models.alert import Alert, Notification
from app.models.search import SavedSearch, SearchHistory

Base.metadata.create_all(bind=engine)
print("✅ Tables created!")
EOF
```

### 7. Start Services

**Terminal 1 - FastAPI Server:**
```bash
uvicorn app.main:app --reload
```

**Terminal 2 - Celery Worker:**
```bash
celery -A app.core.celery_app worker --loglevel=info
```

**Terminal 3 - Celery Beat (Scheduler):**
```bash
celery -A app.core.celery_app beat --loglevel=info
```

### 8. Access the API
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user

### Competitors
- `GET /competitors` - List all competitors
- `POST /competitors` - Create competitor
- `GET /competitors/{id}` - Get competitor details
- `PUT /competitors/{id}` - Update competitor
- `DELETE /competitors/{id}` - Delete competitor
- `GET /competitors/{id}/data` - Get all scraped data
- `GET /competitors/{id}/insights` - Get AI insights

### Data Sources
- `POST /competitors/{id}/sources` - Add data source
- `GET /competitors/{id}/sources` - List data sources
- `PUT /competitors/{id}/sources/{source_id}` - Update data source
- `DELETE /competitors/{id}/sources/{source_id}` - Delete data source

### Scraping
- `POST /scraping/scrape` - Trigger manual scrape
- `GET /scraping/content/{id}` - Get raw content

### Schedules
- `POST /schedules` - Create scraping schedule
- `GET /schedules` - List all schedules
- `PUT /schedules/{id}` - Update schedule
- `DELETE /schedules/{id}` - Delete schedule

### Insights
- `GET /competitors/{id}/insights` - Get competitor insights
- `GET /insights/{id}` - Get specific insight
- `POST /insights/process/{raw_content_id}` - Process raw content

### Search
- `POST /search/semantic` - Semantic vector search
- `GET /search/traditional` - Keyword search
- `POST /search/saved` - Create saved search
- `GET /search/saved` - List saved searches
- `GET /search/saved/{id}` - Get saved search
- `PUT /search/saved/{id}` - Update saved search
- `DELETE /search/saved/{id}` - Delete saved search
- `GET /search/history` - Get search history
- `DELETE /search/history` - Clear search history

### Analytics
- `GET /analytics/trends` - Trend analysis
- `GET /analytics/summary/{competitor_id}` - Competitor summary
- `GET /analytics/comparison` - Multi-competitor comparison
- `GET /analytics/export` - Export data (CSV/JSON)

### Alerts
- `POST /alerts` - Create alert
- `GET /alerts` - List all alerts
- `GET /alerts/{id}` - Get alert
- `PUT /alerts/{id}` - Update alert
- `DELETE /alerts/{id}` - Delete alert
- `GET /notifications` - Get notifications
- `PUT /notifications/{id}/read` - Mark as read

## 🧪 Testing

Run all tests:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_auth.py -v
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

**Test Coverage**: 180+ tests covering all major functionality

## 🗄️ Database Schema

### Tables (10 total)
1. **users** - User accounts
2. **competitors** - Competitor tracking
3. **data_sources** - Data sources per competitor
4. **raw_content** - Scraped content
5. **processed_insights** - AI-analyzed insights
6. **scraping_schedules** - Scheduled jobs
7. **alerts** - Alert configurations
8. **notifications** - Alert notifications
9. **saved_searches** - User saved searches
10. **search_history** - Search activity log

## 🎯 Development Status

### ✅ Completed (Phases 1-4)
- ✅ Phase 1: Foundation & Authentication
- ✅ Phase 2: Data Collection Infrastructure
- ✅ Phase 3: AI Processing Pipeline
- ✅ Phase 4: Core API Development

### 🚧 Upcoming
- Phase 5: Frontend Development (React + TypeScript)
- Phase 6: Advanced Features (WebSockets, ML)
- Phase 7: Production Deployment & Monitoring

## 📊 Architecture Highlights

### Background Processing
- Celery workers handle scraping, AI processing, and alerts
- Redis message broker for task queue
- Celery Beat for scheduled tasks (every 5-10 minutes)

### AI Pipeline
1. Raw content scraped from sources
2. OpenAI processes content (summarize, extract, analyze)
3. Embeddings generated and stored in Pinecone
4. Quality scoring applied
5. Alerts triggered based on conditions
6. Notifications delivered to users

### Vector Search Flow
1. User query converted to embedding
2. Pinecone finds similar vectors
3. Metadata filtered by competitor/user
4. Results ranked by relevance score

## 🔒 Security Features
- JWT authentication with secure tokens
- Password hashing
- User data isolation (row-level security)
- Input validation with Pydantic
- SQL injection protection via ORM



## 🙏 Acknowledgments

Built with:
- FastAPI
- OpenAI
- Pinecone
- LangChain
- PostgreSQL
- Redis
- Celery

---

**Status**: Backend Complete (Phases 1-4) | Frontend In Progress (Phase 5)