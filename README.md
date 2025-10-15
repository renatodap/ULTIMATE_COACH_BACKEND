# SHARPENED Backend

> AI-powered fitness and nutrition coaching platform - FastAPI backend

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment (.env)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
ANTHROPIC_API_KEY=sk-ant-your-key
CORS_ORIGINS=http://localhost:3000

# 3. Run dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API Docs: http://localhost:8000/docs
```

---

## Tech Stack

- **Framework:** FastAPI
- **Language:** Python 3.12+
- **Database:** Supabase (PostgreSQL)
- **Auth:** httpOnly cookies (Supabase JWT)
- **LLM:** Anthropic Claude 3.5 Sonnet
- **Logging:** structlog (JSON-formatted)
- **Error Tracking:** Sentry
- **Deployment:** Docker + Railway/Fly.io

---

## Documentation

**READ FIRST:**
- **[CLAUDE.md](./CLAUDE.md)** - Complete codebase index + development rules (AI assistants must read this)
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture and patterns

**Advanced Features:**
- **[CONSULTATION_KEYS_GUIDE.md](./CONSULTATION_KEYS_GUIDE.md)** - LLM consultation gating system
- **[CONSULTATION_SECURITY.md](./CONSULTATION_SECURITY.md)** - 5-layer security implementation
- **[CONSULTATION_MEMORY_AND_SEEDING.md](./CONSULTATION_MEMORY_AND_SEEDING.md)** - Memory system details

**Database:**
- **[migrations/README.md](./migrations/README.md)** - Database schema and migrations

---

## Project Structure

```
app/
├── api/
│   ├── dependencies.py         # Auth, DB injection
│   └── v1/                    # API v1 endpoints
│       ├── health.py          # Health check
│       ├── auth.py            # Login, signup, logout
│       ├── users.py           # User profile
│       └── onboarding.py      # Onboarding submission
├── services/
│   ├── supabase_service.py    # Database abstraction
│   ├── auth_service.py        # Auth business logic
│   └── consultation_ai_service.py  # LLM consultation (1000+ lines)
├── models/
│   ├── auth.py                # Auth models
│   ├── user.py                # User models
│   └── onboarding.py          # Onboarding models
├── config.py                  # Environment & settings
└── main.py                    # FastAPI app initialization

migrations/
└── *.sql                      # Database schema migrations
```

---

## Development

```bash
# Dev server with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Type checking
mypy app/

# Code formatting
black app/
isort app/
```

---

## API Endpoints

### **Auth**
- `POST /api/v1/auth/signup` - Create account
- `POST /api/v1/auth/login` - Login (sets httpOnly cookie)
- `POST /api/v1/auth/logout` - Logout (clears cookie)

### **Users**
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update profile

### **Onboarding**
- `POST /api/v1/onboarding` - Submit onboarding data

### **Health**
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/db` - Database health

**API Docs:** http://localhost:8000/docs (Swagger UI)

---

## Environment Variables

**Required:**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (full access)
- `SUPABASE_ANON_KEY` - Anonymous key (public operations)
- `SUPABASE_JWT_SECRET` - JWT signing secret

**Optional:**
- `SENTRY_DSN` - Error tracking (recommended for production)
- `ANTHROPIC_API_KEY` - For Claude AI consultation feature
- `ENVIRONMENT` - `development` or `production` (default: development)
- `LOG_LEVEL` - `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: INFO)
- `CORS_ORIGINS` - Allowed frontend origins (comma-separated)

---

## Database

**Provider:** Supabase (PostgreSQL)
**ORM:** Direct SQL via Supabase client
**Migrations:** See `migrations/README.md`

**Key Tables:**
- `users` - User accounts and profiles
- `onboarding_data` - Onboarding responses
- `meal_logs` - Meal tracking
- `activity_logs` - Workout tracking
- `consultation_sessions` - LLM consultation sessions
- `consultation_keys` - One-time use keys for consultations

**Security:** Row Level Security (RLS) enabled on all tables

---

## LLM Consultation System

**Status:** Backend complete, frontend not integrated

**Features:**
- Natural conversation (no forms!)
- Claude 3.5 Sonnet with tool calling
- Database search and insertion
- 7-section system prompts
- Progress tracking (0-100%)
- Gated by one-time use keys

**Documentation:**
- [CONSULTATION_KEYS_GUIDE.md](./CONSULTATION_KEYS_GUIDE.md) - Key system
- [CONSULTATION_SECURITY.md](./CONSULTATION_SECURITY.md) - Security layers
- [CONSULTATION_MEMORY_AND_SEEDING.md](./CONSULTATION_MEMORY_AND_SEEDING.md) - Memory system

**Service:** `app/services/consultation_ai_service.py` (1000+ lines)

---

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v
```

---

## Deployment

### **Docker**

```bash
# Build image
docker build -t sharpened-backend .

# Run container
docker run -p 8000:8000 --env-file .env sharpened-backend
```

### **Railway/Fly.io**

1. Connect GitHub repo
2. Set environment variables
3. Deploy automatically on push to main

---

## Logging

**Format:** JSON (structured logging via structlog)

```python
import structlog

logger = structlog.get_logger()

# Info log with context
logger.info("user_login", user_id=user.id, email=user.email)

# Error log with exception
try:
    operation()
except Exception as e:
    logger.error("operation_failed", error=str(e), user_id=user.id, exc_info=True)
```

**Output Example:**
```json
{
  "event": "user_login",
  "user_id": "123",
  "email": "user@example.com",
  "timestamp": "2025-10-12T10:30:00Z",
  "level": "info"
}
```

---

## Support

- **Email:** persimmonautomation@gmail.com
- **Privacy:** persimmonautomation@gmail.com

---

## For AI Assistants

1. **READ [CLAUDE.md](./CLAUDE.md) FIRST** - Contains complete codebase index and rules
2. Always use structured logging (no print statements)
3. Follow service layer pattern (route → service → DB)
4. Use Pydantic models for all validation
5. Be cautious with consultation system (complex feature)

---

**Last Updated:** 2025-10-12
