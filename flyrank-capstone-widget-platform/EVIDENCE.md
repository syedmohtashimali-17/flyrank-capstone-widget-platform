# Evidence

This document provides placeholders for demonstrating the FlyRank Widget Platform meets all acceptance requirements. Fill in actual command outputs and results after running the application.

## 1. Authenticated Widget CRUD

### Test
Demonstrate user registration, login, and widget management.

### cURL Commands
```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "password123"}'

# Login and get token  
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "password123"}'

# Create widget (replace <token> with actual token)
curl -X POST http://localhost:8000/widgets \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "signup",
    "title": "Evidence Widget",
    "form_fields": [
      {"name": "email", "label": "Email", "type": "email", "required": true}
    ]
  }'

# List widgets
curl -X GET http://localhost:8000/widgets \
  -H "Authorization: Bearer <token>"
```

### Output
```
[Paste actual command outputs here after testing]
```

### Database Evidence
```bash
# Query database to show widget was created
sqlite3 app.db "SELECT id, title, owner_id, type FROM widgets WHERE title='Evidence Widget';"
```

Output:
```
[Paste database query results here]
```

## 2. Tenant Isolation

### Tenant A Test
```bash
# Create widget as User A
curl -X POST http://localhost:8000/widgets \
  -H "Authorization: Bearer <token_a>" \
  -d '{"type": "signup", "title": "User A Widget", "form_fields": [{"name": "email", "label": "Email", "type": "email", "required": true}]}'

# List widgets as User A  
curl -X GET http://localhost:8000/widgets \
  -H "Authorization: Bearer <token_a>"
```

### Tenant B Test
```bash
# List widgets as User B (should not see User A's widgets)
curl -X GET http://localhost:8000/widgets \
  -H "Authorization: Bearer <token_b>"

# Try to access User A's widget as User B (should return 404)
curl -X GET http://localhost:8000/widgets/<user_a_widget_id> \
  -H "Authorization: Bearer <token_b>"
```

### Proof
```
[Show that User B cannot see or access User A's widgets]
```

## 3. Embed Snippet

### Request
```bash
curl -X GET http://localhost:8000/widgets/<widget_id>/embed \
  -H "Authorization: Bearer <token>"
```

### Response
```json
{
  "widget_id": "abc-123-def",
  "snippet": "<script src=\"http://localhost:8000/static/widget.v1.js?id=abc-123-def\"></script>"
}
```

## 4. Cached Config

### Request
```bash
curl -v http://localhost:8000/widgets/<widget_id>/config
```

### Response Headers
```
[Show Cache-Control headers and CORS headers here]
HTTP/1.1 200 OK
Cache-Control: public, max-age=300
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
```

## 5. Versioned Widget JavaScript

### Request
```bash
curl -v http://localhost:8000/static/widget.v1.js?id=<widget_id>
```

### Cache Headers
```
[Show long-lived cache headers here]
HTTP/1.1 200 OK
Cache-Control: public, max-age=31536000, immutable
Content-Type: application/javascript
```

## 6. Cross-Origin CORS

### OPTIONS Preflight
```bash
curl -X OPTIONS http://localhost:8000/submissions \
  -H "Origin: http://localhost:5500" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

### POST Submission
```bash
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d '{
    "widget_id": "<widget_id>",
    "data": {"email": "test@example.com"},
    "hp_field": ""
  }'
```

### Browser Evidence
```
[Screenshot or description of successful cross-origin request in browser developer tools]
- Network tab showing OPTIONS and POST requests
- Response headers showing CORS headers
- No CORS errors in console
```

## 7. Boundary Validation

### Malformed Payload
```bash
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d 'invalid json syntax'
```

Expected Response:
```json
{
  "error": {
    "code": "VALIDATION_ERROR", 
    "message": "Invalid request payload."
  }
}
```

### Oversized Payload
```bash
# Create 70KB payload (larger than 64KB limit)
python -c "
import requests
large_data = 'x' * 70000
payload = {
  'widget_id': '<widget_id>',
  'data': {'field': large_data},
  'hp_field': ''
}
response = requests.post('http://localhost:8000/submissions', json=payload)
print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')
"
```

Expected Response:
```json
{
  "error": {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "Request body exceeds the maximum allowed size."
  }
}
```

## 8. Rate Limiting

### Burst Test
```bash
# Send 15 rapid requests (exceeds limit of 10/minute per IP)
for i in {1..15}; do
  curl -X POST http://localhost:8000/submissions \
    -H "Content-Type: application/json" \
    -d '{"widget_id": "<widget_id>", "data": {"email": "test'$i'@example.com"}, "hp_field": ""}'
  echo "Request $i completed"
done
```

### 429 Evidence
```
[Show that some requests return 429 status code]
Status: 429 Too Many Requests
{
  "error": {
    "code": "TOO_MANY_REQUESTS",
    "message": "Too many requests. Please try again later."
  }
}
```

### Legitimate Request After Burst
```bash
# Wait for rate limit window to reset, then send valid request
sleep 60
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{"widget_id": "<widget_id>", "data": {"email": "after@example.com"}, "hp_field": ""}'
```

Expected: Should succeed with 200 status.

## 9. Honeypot

### Spam Request
```bash
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "widget_id": "<widget_id>",
    "data": {"email": "spam@bot.com"},
    "hp_field": "I am a spam bot"
  }'
```

### Database Verification
```bash
# Check that no submission was stored for spam request
sqlite3 app.db "SELECT COUNT(*) FROM submissions WHERE submitted_data LIKE '%spam@bot.com%';"
```

Expected Result: `0` (no submissions stored)

## 10. Geo Provider A Success

### Test with Mock Provider
```bash
# Set environment to use first provider
export GEO_PROVIDER_A_URL="http://ip-api.com/json/"
python -c "
import asyncio
from services.geo_service import IPApiProvider
provider = IPApiProvider()
result = asyncio.run(provider.get_location('8.8.8.8'))
print(f'Geo result: {result}')
"
```

### Output
```
[Show successful geo enrichment result]
Geo result: ('United States', 'Mountain View')
```

## 11. Geo Provider A Failure → Provider B

### Test Fallback Chain
```bash
# Test with first provider failing, second succeeding
python -c "
import asyncio
from services.geo_service import GeoService, MockGeoProvider

# Provider A fails, Provider B succeeds
provider_a = MockGeoProvider(should_fail=True)
provider_b = MockGeoProvider(should_fail=False, response=('Canada', 'Toronto'))
service = GeoService([provider_a, provider_b])

result = asyncio.run(service.get_location('8.8.8.8'))
print(f'Fallback result: {result}')
"
```

### Output
```
[Show fallback working]
Fallback result: ('Canada', 'Toronto')
```

## 12. Both Geo Providers Failure

### Test All Providers Failing
```bash
python -c "
import asyncio
from services.geo_service import GeoService, MockGeoProvider

# Both providers fail
provider_a = MockGeoProvider(should_fail=True)
provider_b = MockGeoProvider(should_fail=True)
service = GeoService([provider_a, provider_b])

result = asyncio.run(service.get_location('8.8.8.8'))
print(f'All fail result: {result}')
"
```

### Output
```
[Show that submission still succeeds without geo]
All fail result: (None, None)
```

### Submission Test
```bash
# Submit while geo providers are failing
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{"widget_id": "<widget_id>", "data": {"email": "nogeo@example.com"}, "hp_field": ""}'
```

Expected: 200 OK response, submission stored without geo data.

## 13. Safe Side Effect

### Successful Side Effect
Set `SIDE_EFFECT_FAIL=false` and submit:

```bash
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{"widget_id": "<widget_id>", "data": {"email": "success@example.com"}, "hp_field": ""}'
```

### Log Output
```
[Show successful side effect logs]
INFO - Sending confirmation email for submission 123 (attempt 1)
INFO - Confirmation email sent successfully for submission 123
```

## 14. Side Effect Failure

### Force Failure
Set `SIDE_EFFECT_FAIL=true` and submit:

```bash
export SIDE_EFFECT_FAIL=true
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{"widget_id": "<widget_id>", "data": {"email": "failtest@example.com"}, "hp_field": ""}'
```

### Failure Log
```
[Show side effect failure with retries]
ERROR - Confirmation email failed for submission 124 (attempt 1): Simulated side effect failure
INFO - Retrying confirmation email in 1 seconds
ERROR - Confirmation email failed for submission 124 (attempt 2): Simulated side effect failure
INFO - Retrying confirmation email in 2 seconds
ERROR - All retry attempts failed for confirmation email, submission 124
```

### Successful Submission
Response should still be:
```json
{
  "success": true,
  "message": "Submission received successfully"
}
```

### Database Verification
```bash
sqlite3 app.db "SELECT id, submitted_data FROM submissions WHERE submitted_data LIKE '%failtest@example.com%';"
```

Expected: Submission exists in database despite side effect failure.

## 15. Idempotency

### First Request
```bash
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-test-key-123" \
  -d '{"widget_id": "<widget_id>", "data": {"email": "idem@example.com"}, "hp_field": ""}'
```

### Repeated Request
```bash
# Same idempotency key
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-test-key-123" \
  -d '{"widget_id": "<widget_id>", "data": {"email": "idem@example.com"}, "hp_field": ""}'
```

### Database Count
```bash
sqlite3 app.db "SELECT COUNT(*) FROM submissions WHERE idempotency_key='unique-test-key-123';"
```

Expected Result: `1` (only one submission created)

## 16. Dashboard

### Submission List
```bash
curl -X GET http://localhost:8000/dashboard/submissions \
  -H "Authorization: Bearer <token>"
```

### Response
```json
[
  {
    "id": 1,
    "widget_id": "abc-123",
    "submitted_data": {"email": "test@example.com"},
    "country": "United States",
    "city": "New York",
    "created_at": "2026-09-12T10:00:00Z"
  }
]
```

### Counts Over Time
```bash
curl -X GET http://localhost:8000/dashboard/stats \
  -H "Authorization: Bearer <token>"
```

### Response
```json
{
  "total_submissions": 15,
  "daily_counts": [
    {"date": "2026-09-10", "count": 3},
    {"date": "2026-09-11", "count": 7}, 
    {"date": "2026-09-12", "count": 5}
  ],
  "geo_breakdown": [
    {"country": "United States", "count": 8},
    {"country": "Canada", "count": 4},
    {"country": "Germany", "count": 3}
  ]
}
```

### Geo Breakdown
```
[Show geographic distribution of submissions]
```

## 17. Automated Test Suite

### pytest Output
```bash
pytest -v
```

### Results
```
[Paste full test results showing all tests passing]

========================= test session starts =========================
tests/test_auth.py::TestAuthentication::test_register_success PASSED
tests/test_auth.py::TestAuthentication::test_login_success PASSED
tests/test_widgets.py::TestWidgetCRUD::test_create_widget_success PASSED
tests/test_tenant_isolation.py::TestTenantIsolation::test_user_cannot_access_other_widget PASSED
tests/test_public_config.py::TestPublicConfig::test_get_widget_config_success PASSED
tests/test_submissions.py::TestSubmissions::test_create_submission_success PASSED
tests/test_rate_limiting.py::TestRateLimiting::test_submission_rate_limiting_integration PASSED
tests/test_geo_fallback.py::TestGeoFallback::test_geo_first_provider_fails_second_succeeds PASSED
tests/test_side_effects.py::TestSideEffects::test_submission_succeeds_despite_side_effect_failure PASSED
tests/test_honeypot.py::TestHoneypot::test_honeypot_submission_not_stored PASSED
tests/test_dashboard.py::TestDashboard::test_dashboard_stats_tenant_isolation PASSED

========================= XX passed in X.XXs =========================
```

## 18. Database / Migration Evidence

### Alembic Upgrade
```bash
alembic upgrade head
```

### Output
```
[Show successful migration output]
INFO [alembic.runtime.migration] Context impl SQLiteImpl.
INFO [alembic.runtime.migration] Will assume non-transactional DDL.
INFO [alembic.runtime.migration] Running upgrade  -> 0001, Initial schema
```

### Database Schema
```bash
sqlite3 app.db ".schema"
```

### Output
```
[Show complete database schema created by migrations]
CREATE TABLE users (
    id INTEGER NOT NULL,
    email VARCHAR NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_users_email ON users (email);
...
```

## 19. Final Acceptance Checklist

- [ ] **Widget CRUD** - Create, read, update, delete widgets with authentication
- [ ] **Tenant isolation** - Users cannot access each other's data
- [ ] **Embed snippet** - Generate JavaScript embed code
- [ ] **Cached config** - Public config with cache headers
- [ ] **Versioned JS** - Long-lived cache for static assets
- [ ] **CORS** - Cross-origin requests work from test page
- [ ] **Validation** - Malformed requests return 4xx, not 500
- [ ] **Oversized payload** - Returns 413 for requests > 64KB
- [ ] **Rate limiting** - Returns 429 after burst, then allows normal traffic
- [ ] **Honeypot** - Filled hp_field prevents database storage
- [ ] **Idempotency** - Duplicate keys don't create duplicate submissions
- [ ] **Geo fallback** - Provider A → Provider B → None (graceful)
- [ ] **Graceful degradation** - Side effects fail but submission succeeds
- [ ] **Background side effect** - Async processing with retry logic
- [ ] **Retry behavior** - Multiple attempts on failure
- [ ] **Dashboard** - Analytics and submission management
- [ ] **Tests** - Comprehensive automated test suite passes

## Notes

Fill in this document with actual command outputs and results after:

1. Starting the application: `python main.py`
2. Running the seed script: `python seed.py`  
3. Testing with the cross-origin test page
4. Running the automated test suite: `pytest`
5. Executing each acceptance probe manually

This evidence demonstrates that the FlyRank Widget Platform meets all specified requirements for the backend capstone project.