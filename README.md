# EVE Healthcare — Diagnostic Booking Service

Backend API for diagnostic test bookings and simulated payments, built with FastAPI and PostgreSQL.

## Tech Stack

- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0
- **Auth**: JWT (python-jose + passlib/bcrypt)
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest with SQLite for isolation
- **Docs**: Auto-generated Swagger UI at `/docs`

## Quick Start

### Using Docker (Recommended)

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`. The database is automatically seeded with sample data.

### Local Development

**Prerequisites**: Python 3.12+, PostgreSQL running locally

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set database URL (adjust as needed)
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/eve_healthcare

# Create the database
createdb eve_healthcare

# Seed sample data
python seed.py

# Run the server
uvicorn app.main:app --reload
```

### Running Tests

```bash
source .venv/bin/activate
pytest -v
```

Tests use SQLite in-memory so no PostgreSQL instance is needed.

## API Documentation

Interactive Swagger docs are available at: `http://localhost:8000/docs`

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/login` | Login and get JWT token |
| GET | `/auth/me` | Get current user profile |

### Diagnostic Centres

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/centres/` | Create a diagnostic centre |
| GET | `/centres/` | List centres (supports `?location=` and pagination) |
| GET | `/centres/{id}` | Get centre details with tests |
| POST | `/centres/{id}/tests` | Add a test to a centre |
| GET | `/centres/{id}/tests` | List tests for a centre |

### Bookings

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bookings/` | Create a booking |
| GET | `/bookings/` | List my bookings (supports `?status=` filter and pagination) |
| GET | `/bookings/{id}` | Get booking details |
| PATCH | `/bookings/{id}/cancel` | Cancel a pending booking |

### Payments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/payments/` | Initiate payment for a booking |
| POST | `/payments/webhook/` | Payment status webhook (idempotent) |
| GET | `/payments/{id}` | Get payment details |

## Example API Requests

### 1. Sign Up
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "securepass123", "full_name": "John Doe", "phone": "+919876543210"}'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "patient@example.com", "password": "password123"}'
```

### 3. List Centres
```bash
curl http://localhost:8000/centres/
```

### 4. Create a Booking
```bash
curl -X POST http://localhost:8000/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"test_id": "<test-uuid>", "centre_id": "<centre-uuid>", "appointment_time": "2026-10-15T10:00:00+05:30"}'
```

### 5. Pay for a Booking
```bash
curl -X POST http://localhost:8000/payments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"booking_id": "<booking-uuid>"}'
```

### 6. Webhook (Simulated Provider Callback)
```bash
curl -X POST http://localhost:8000/payments/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"transaction_id": "txn_abc123", "status": "SUCCESS", "idempotency_key": "webhook_evt_001"}'
```

## Database Schema

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────────┐
│    users      │     │ diagnostic_centres │     │ diagnostic_tests │
├──────────────┤     ├────────────────────┤     ├──────────────────┤
│ id (PK, UUID)│     │ id (PK, UUID)      │     │ id (PK, UUID)    │
│ email (UQ)   │     │ name               │     │ name             │
│ password_hash│     │ location           │     │ description      │
│ full_name    │     │ address            │     │ price            │
│ phone        │     │ created_at         │     │ centre_id (FK)   │
│ created_at   │     └────────────────────┘     │ created_at       │
└──────────────┘              │                  └──────────────────┘
       │                      │ 1:N                       │
       │                      └───────────────────────────┘
       │
       │ 1:N
       ▼
┌──────────────────┐         ┌──────────────────┐
│    bookings      │         │    payments      │
├──────────────────┤         ├──────────────────┤
│ id (PK, UUID)    │ 1:1     │ id (PK, UUID)    │
│ user_id (FK)     │────────▶│ booking_id (FK,UQ│
│ test_id (FK)     │         │ amount           │
│ centre_id (FK)   │         │ status           │
│ appointment_time │         │ transaction_id(UQ│
│ amount           │         │ idempotency_key  │
│ status           │         │ created_at       │
│ created_at       │         │ updated_at       │
│ updated_at       │         └──────────────────┘
└──────────────────┘
```

### Key Design Decisions

- **UUIDs** as primary keys to avoid sequential ID enumeration
- **`booking_id` is unique** on payments table — one payment per booking
- **`idempotency_key`** on payments ensures webhook deduplication
- **`transaction_id`** is unique and used for external reference
- **Decimal(10,2)** for monetary fields to avoid floating point issues

## Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| Duplicate signup email | 409 Conflict |
| Invalid JWT token | 401 Unauthorized |
| Booking test not at selected centre | 400 Bad Request |
| Past appointment time | 400 Bad Request |
| Double payment for same booking | 409 Conflict |
| Paying for another user's booking | 403 Forbidden |
| Cancelling already cancelled booking | 400 Bad Request |
| Cancelling confirmed booking | 400 Bad Request |
| Duplicate webhook (same idempotency_key) | 200 OK (no side effects) |
| Webhook for already settled payment | 200 OK (skipped) |
| Viewing another user's booking | 403 Forbidden |
| Non-existent resource IDs | 404 Not Found |

## Assumptions

- Authentication is session-less (JWT only, no refresh tokens for simplicity)
- The simulated payment has an 80% success rate (configurable via code)
- Any authenticated user can create diagnostic centres and tests (in production, this would be admin-only)
- Webhook endpoint is publicly accessible (in production, signature verification would be added)
- Cancellation is only allowed for PENDING bookings
- Single payment attempt per booking — no retries on the payment model itself

## What I Would Improve With More Time

- **Admin role separation**: Role-based access control for centre/test management
- **Refresh tokens**: Token rotation and revocation
- **Webhook signature verification**: HMAC-based payload signing
- **Rate limiting**: Redis-backed rate limiting middleware
- **Celery workers**: Async payment processing and retry logic
- **Redis caching**: Cache centre/test listings with TTL-based invalidation
- **Alembic migrations**: Proper migration files instead of auto-create
- **Structured logging**: JSON logging with correlation IDs for request tracing
- **CI/CD pipeline**: GitHub Actions for linting, testing, and deployment
- **Load testing**: k6 or locust scripts for performance benchmarking
