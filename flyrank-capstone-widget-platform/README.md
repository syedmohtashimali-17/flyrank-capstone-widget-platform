# FlyRank Widget Platform

A complete embeddable lead-capture platform with multi-tenancy, CORS support, rate limiting, geo enrichment, and background processing.

## Overview

The FlyRank Widget Platform allows customers (tenants) to create embeddable widgets such as signup forms, contact forms, and CTA popover forms. Customers receive a single JavaScript snippet that can be embedded on external websites to capture leads with full cross-origin support.

### Problem & Solution

**Problem:** Businesses need an easy way to capture leads on their websites without building complex forms and backend infrastructure.

**Solution:** A complete widget platform that provides:
- Easy-to-embed JavaScript widgets
- Secure cross-origin data collection
- Real-time analytics and lead management
- Robust spam protection and rate limiting
- Geographic enrichment of submissions

## Features

### Core Functionality
- ✅ **JWT Authentication** - Secure user registration and login
- ✅ **Multi-tenancy** - Strict isolation between customer data
- ✅ **Widget CRUD** - Create, manage, and configure widgets
- ✅ **Embed Snippets** - One-line JavaScript embedding
- ✅ **Cached Config** - Fast widget configuration delivery
- ✅ **Versioned JS** - Long-lived cache with version control

### Cross-Origin & Security
- ✅ **CORS Support** - Full cross-origin request handling
- ✅ **Input Validation** - Comprehensive payload validation
- ✅ **Payload Limits** - 64KB request size enforcement
- ✅ **Rate Limiting** - Per-IP and per-widget rate limits
- ✅ **Honeypot Protection** - Automated spam detection
- ✅ **Idempotency** - Duplicate submission prevention

### Data & Analytics
- ✅ **Geo Fallback** - IP-to-location with provider chain
- ✅ **Data Persistence** - Reliable SQLite/PostgreSQL storage
- ✅ **Background Side Effects** - Email/webhook processing
- ✅ **Retry Logic** - Resilient failure handling
- ✅ **Analytics Dashboard** - Submissions, geography, trends

## Architecture

```text
                    ┌──────────────────────────────┐
                    │        Widget Owner          │
                    └──────────────┬───────────────┘
                                   │ JWT Auth
                                   ▼
                    ┌──────────────────────────────┐
                    │      Admin API / Routers     │
                    │       Widget Management      │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      Tenant-Isolated DB       │
                    └──────────────────────────────┘


Customer Website / External Origin
        │
        │ <script src="/static/widget.v1.js?id=123">
        ▼
┌──────────────────────────────┐
│ Versioned Widget JS          │
│ Long-lived browser cache     │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ GET /widgets/{id}/config     │
│ Public + CORS + Cache        │
└──────────────────────────────┘


Website Visitor
       │
       │ POST /submissions
       ▼
┌──────────────────────────────┐
│ CORS / OPTIONS               │
├──────────────────────────────┤
│ Request Size Boundary        │
├──────────────────────────────┤
│ Pydantic Validation          │
├──────────────────────────────┤
│ Rate Limit: IP + Widget     │
├──────────────────────────────┤
│ Honeypot / Spam Check        │
├──────────────────────────────┤
│ Idempotency                  │
├──────────────────────────────┤
│ Geo Provider A               │
│       ↓ failure              │
│ Geo Provider B               │
│       ↓ failure              │
│ Continue Without Geo         │
├──────────────────────────────┤
│ Database Storage             │
├──────────────────────────────┤
│ Background Side Effect       │
│ Email/Webhook + Retry        │
└──────────────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Owner Dashboard API          │
│ Leads + Counts + Geo Stats   │
└──────────────────────────────┘
```

## Setup

### Prerequisites
- Python 3.10+
- pip

### Installation

1. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   ```

2. **Activate Virtual Environment**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/macOS
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run Database Migrations**
   ```bash
   alembic upgrade head
   ```

6. **Seed Database**
   ```bash
   python seed.py
   ```

7. **Start Server**
   ```bash
   python main.py
   ```

8. **Run Tests**
   ```bash
   pytest -q
   ```

### Test Page Setup

Run the cross-origin test page:

```bash
cd test_page
python -m http.server 5500
```

Then open: http://localhost:5500

The API server runs on: http://localhost:8000

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `DATABASE_URL` | sqlite:///./app.db | Database connection string |
| `SECRET_KEY` | supersecretkey_change_in_production | JWT secret key |
| `GEO_PROVIDER_A_URL` | http://ip-api.com/json/ | Primary geo provider |
| `GEO_PROVIDER_B_URL` | https://ipapi.co/ | Fallback geo provider |
| `GEO_ENABLED` | true | Enable geo enrichment |
| `RATE_LIMIT_PER_IP` | 10/minute | IP rate limit |
| `RATE_LIMIT_PER_WIDGET` | 5/minute | Widget rate limit |
| `MAX_REQUEST_SIZE` | 65536 | Maximum request body size (bytes) |
| `SIDE_EFFECT_ENABLED` | true | Enable background side effects |
| `SIDE_EFFECT_FAIL` | false | Force side effect failures (testing) |

## API Documentation

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2026-09-12T10:00:00Z"
}
```

#### POST /auth/login
Login and receive JWT token.

**Request:**
```json
{
  "email": "user@example.com", 
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "token_type": "bearer"
}
```

#### GET /auth/me
Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2026-09-12T10:00:00Z"
}
```

### Widget Management Endpoints

All widget management endpoints require JWT authentication.

#### POST /widgets
Create a new widget.

**Request:**
```json
{
  "type": "signup",
  "title": "Join our newsletter",
  "description": "Get product updates",
  "form_fields": [
    {
      "name": "name",
      "label": "Full Name", 
      "type": "text",
      "required": true
    },
    {
      "name": "email",
      "label": "Email",
      "type": "email",
      "required": true
    }
  ],
  "button_text": "Subscribe",
  "display_options": {
    "position": "bottom-right"
  }
}
```

#### GET /widgets
List all widgets for authenticated user.

#### GET /widgets/{widget_id}
Get specific widget details.

#### PUT /widgets/{widget_id}
Update widget configuration.

#### DELETE /widgets/{widget_id}
Delete widget.

#### GET /widgets/{widget_id}/embed
Get embed snippet for widget.

**Response:**
```json
{
  "widget_id": "abc123",
  "snippet": "<script src=\"http://localhost:8000/static/widget.v1.js?id=abc123\"></script>"
}
```

### Public Endpoints

#### GET /widgets/{widget_id}/config
Get public widget configuration (no authentication required).

**Cache Headers:**
```
Cache-Control: public, max-age=300
```

**CORS Headers:**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
```

#### OPTIONS /submissions
CORS preflight for submissions.

#### POST /submissions
Submit form data (public endpoint).

**Request:**
```json
{
  "widget_id": "abc123",
  "data": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "hp_field": ""
}
```

**Optional Headers:**
```
Idempotency-Key: unique-key-123
```

### Dashboard Endpoints

All dashboard endpoints require JWT authentication.

#### GET /dashboard/submissions
Get submissions for authenticated user.

**Query Parameters:**
- `widget_id` (optional): Filter by widget
- `limit` (default: 100): Number of results
- `offset` (default: 0): Skip results

#### GET /dashboard/stats
Get dashboard statistics.

**Response:**
```json
{
  "total_submissions": 150,
  "daily_counts": [
    {"date": "2026-09-01", "count": 5},
    {"date": "2026-09-02", "count": 8}
  ],
  "geo_breakdown": [
    {"country": "United States", "count": 45},
    {"country": "Canada", "count": 12}
  ],
  "widget_stats": [
    {"widget_id": "abc123", "title": "Newsletter", "total_submissions": 89}
  ]
}
```

#### GET /dashboard/widgets/{widget_id}/stats
Get analytics for specific widget.

### Static Files

#### GET /static/widget.v1.js
Versioned widget JavaScript.

**Cache Headers:**
```
Cache-Control: public, max-age=31536000, immutable
```

## cURL Examples

### Register and Login
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

### Create Widget
```bash
curl -X POST http://localhost:8000/widgets \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "signup",
    "title": "Newsletter Signup",
    "form_fields": [
      {"name": "email", "label": "Email", "type": "email", "required": true}
    ]
  }'
```

### Submit Form Data
```bash
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-123" \
  -d '{
    "widget_id": "your-widget-id",
    "data": {"email": "user@example.com"},
    "hp_field": ""
  }'
```

## Testing

### Automated Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Acceptance Probes

The system includes specific acceptance probes as required:

1. **Cross-origin submission** - Test page → API server
2. **Malformed payloads** - Returns 4xx, never 500
3. **Rate limiting** - Burst → 429, then normal traffic works  
4. **Geo fallback** - Provider A fails → Provider B → Both fail
5. **Side-effect failure** - Submission succeeds, logs failure
6. **Honeypot** - Filled hp_field → not stored

## Security

### Authentication & Authorization
- JWT tokens with configurable expiration
- Secure password hashing with bcrypt
- Strict tenant isolation in all queries
- 404 responses for cross-tenant access (no info leakage)

### Input Validation & Protection
- Pydantic schema validation on all inputs
- Request size limits (64KB default)
- Field length limits and type validation
- SQL injection protection via ORM
- XSS protection via input sanitization

### Rate Limiting
- Dual-dimension limits (IP + Widget)
- Configurable windows and thresholds
- In-memory implementation (suitable for development)
- Graceful degradation after limit exceeded

### Spam Protection
- Honeypot field detection
- Silent dropping of suspected spam
- No feedback to potential attackers
- Extensible for additional spam checks

### CORS Configuration
- Explicit origin handling
- Proper preflight support
- Secure credential policies
- No wildcard with credentials

## Caching

### Widget Configuration
- Public config cached for 5 minutes
- Reduces database load for popular widgets
- Proper cache-control headers

### Versioned Static Assets
- JavaScript cached for 1 year
- Immutable cache with version URLs
- Instant cache busting on updates

## Graceful Degradation

### Geo Provider Failures
- Primary provider timeout → Fallback provider
- All providers fail → Continue without geo data
- No impact on submission success
- Configurable timeouts and retry logic

### Side Effect Failures  
- Database write succeeds first
- Background processing failures logged
- Exponential backoff retry logic
- Never blocks submission response

## Limitations

### Development-Focused
- **SQLite Database** - Single-file, good for development
- **In-Memory Rate Limiting** - Not shared across instances
- **Simulated Side Effects** - No real email/webhook delivery
- **Basic Geo Providers** - Free tier limitations

### Security Considerations
- **JWT Secret** - Must be changed in production
- **CORS Origins** - Should be restricted in production
- **HTTPS** - Required for production deployment
- **Input Sanitization** - Additional XSS protection recommended

### Scalability
- **Single Instance** - No horizontal scaling support
- **File Storage** - No CDN or distributed assets
- **Background Jobs** - In-process, not queued
- **Database Connections** - Single connection pool

## Future Enhancements

### Infrastructure
- **PostgreSQL** migration for production
- **Redis** for shared rate limiting and caching
- **Real Email Provider** (SendGrid, Mailgun)
- **Webhook Delivery** with proper retry queues
- **CDN Integration** for static assets

### Features
- **CAPTCHA Integration** for additional spam protection
- **Real-time Dashboard** with WebSocket updates
- **Advanced Targeting** rules and A/B testing
- **GDPR Compliance** workflows and data export
- **White-label** customization options

### Security
- **Two-Factor Authentication** for admin accounts
- **API Rate Limiting** per authenticated user
- **Advanced Monitoring** and alerting
- **Audit Logging** for compliance requirements

## Troubleshooting

### Common Issues

**Database Errors:**
```bash
# Reset database
rm app.db
alembic upgrade head
python seed.py
```

**CORS Errors:**
- Check origins are different (localhost:5500 vs localhost:8000)
- Verify preflight OPTIONS request succeeds
- Check browser developer tools for CORS headers

**Rate Limiting:**
- Wait for rate limit window to reset
- Check IP and widget limits in configuration
- Monitor rate limiter logs for debugging

**Geo Enrichment:**
- Verify external API connectivity
- Check timeout settings
- Review provider fallback logs

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure all tests pass
5. Submit pull request

## License

MIT License - see LICENSE file for details.