# ULTIMATE COACH Backend

**Production-ready FastAPI backend for ULTIMATE COACH fitness application**

## 🚀 Features

- ✅ FastAPI REST API with automatic OpenAPI docs
- ✅ Supabase PostgreSQL database with pgvector
- ✅ JWT authentication & RLS (Row Level Security)
- ✅ AI-powered coach with tool-calling architecture
- ✅ Multimodal input processing (text, voice, images)
- ✅ Comprehensive test coverage (≥80%)
- ✅ Production-ready error handling & logging
- ✅ Docker support for easy deployment

## 📋 Prerequisites

- Python 3.11+
- Poetry (dependency management)
- PostgreSQL with pgvector extension (via Supabase)
- Redis (for caching and background jobs)

## 🛠️ Quick Start

### 1. Install Dependencies

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values
# Required: SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY
```

### 3. Run Development Server

```bash
# Activate virtual environment
poetry shell

# Run FastAPI with auto-reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access API

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test file
poetry run pytest tests/unit/test_main.py -v

# Run integration tests only
poetry run pytest tests/integration/ -v
```

## 🏗️ Project Structure

```
ULTIMATE_COACH_BACKEND/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Environment configuration
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── nutrition.py     # Meal logging endpoints
│   │   │   ├── activities.py    # Workout logging endpoints
│   │   │   ├── coach.py         # AI coach endpoints
│   │   │   └── health.py        # Health check endpoints
│   │   └── middleware/
│   │       └── auth.py           # JWT authentication middleware
│   ├── services/
│   │   ├── supabase_service.py  # Supabase database client
│   │   ├── auth_service.py      # Authentication logic
│   │   ├── meal_logging_service.py
│   │   ├── activity_logging_service.py
│   │   ├── tool_service.py      # Agentic coach tools
│   │   └── context_builder.py   # RAG context building
│   ├── models/                   # Pydantic request/response models
│   └── core/
│       ├── security.py          # JWT, password hashing
│       └── deps.py              # FastAPI dependencies
├── migrations/                   # SQL database migrations
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── conftest.py              # Pytest fixtures
├── pyproject.toml               # Poetry dependencies
├── Dockerfile                   # Docker container definition
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## 🔧 Code Quality

```bash
# Format code with Black
poetry run black app/

# Lint with Ruff
poetry run ruff check app/

# Type check with mypy
poetry run mypy app/

# Run all checks
poetry run black app/ && poetry run ruff check app/ && poetry run mypy app/
```

## 🚢 Deployment

### Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Docker

```bash
# Build image
docker build -t ultimate-coach-backend .

# Run container
docker run -p 8000:8000 --env-file .env ultimate-coach-backend
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Security

- JWT-based authentication with Supabase Auth
- Row Level Security (RLS) on all database tables
- Input validation with Pydantic
- CORS configured for specific origins only
- API rate limiting (100 req/min per user)
- Secrets management via environment variables

## 🎯 Cost Optimization

- **Agentic Coach**: Tool-calling architecture reduces AI costs by 91%
- **Tier System**:
  - FREE: Local embeddings, Whisper Tiny
  - CHEAP: Groq Llama 3.3, DeepSeek Chat
  - MEDIUM: Llama 4 Scout, GPT-4o Mini
  - EXPENSIVE: Claude 3.5 Sonnet (only when necessary)
- **Target**: <$0.50/user/month for AI APIs

## 📝 Contributing

1. Create feature branch
2. Write tests first (TDD)
3. Implement feature
4. Ensure tests pass (≥80% coverage)
5. Format and lint code
6. Submit pull request

## 📞 Support

For issues or questions: support@ultimatecoach.com

## 📄 License

Private - ULTIMATE COACH Application
