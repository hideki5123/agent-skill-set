# QA Perspectives (Lenses)

Ten quality perspectives for evaluating test coverage. Each lens defines what to
look for, code patterns to grep, example findings, and guidance on severity and
confidence scoring.

## How to Use This Reference

For each active lens:
1. Grep source files for the listed patterns
2. Check if matching code has corresponding test coverage (via test file mapping)
3. If uncovered, create a finding with the appropriate severity/confidence
4. Use the example findings as templates for your output

## Severity Definitions

| Level | Meaning |
|-------|---------|
| **critical** | Untested code that, if broken, causes data loss, security breach, or system outage |
| **high** | Untested code in core business logic or user-facing flows |
| **medium** | Untested code in secondary flows or internal utilities |
| **low** | Untested code in logging, formatting, or non-critical helpers |

## Confidence Definitions

| Level | Meaning |
|-------|---------|
| **high** | No test file exists for the module, or test file doesn't reference the function/class at all |
| **medium** | Test file exists but doesn't appear to test the specific pattern/branch |
| **low** | Test file exists and references the function, but specific branch/edge-case testing is unclear |

---

## 1. Functional

**Focus:** Business logic, validation rules, happy paths, sad paths, edge cases.

**Patterns to grep:**
- `if`, `else`, `switch`, `case`, `match` (branching logic)
- `validate`, `check`, `verify`, `assert`, `ensure` (validation functions)
- `throw`, `raise`, `Error`, `Exception` (error paths)
- Functions with > 3 parameters (complex logic)
- Functions > 50 lines (dense logic)

**Severity guidance:**
- critical: Validation of user input, financial calculations, data transformations
- high: Business rule branches, state transitions
- medium: Formatting, sorting, filtering logic
- low: Logging format, display helpers

**Example finding:**
> `src/billing/invoice.ts:42` — `calculateTotal()` has 6 branches (discounts, tax, rounding) but only happy-path is tested. **Severity: critical, Confidence: high**

---

## 2. Security

**Focus:** Auth, injection, data exposure, OWASP Top 10 patterns.

**Patterns to grep:**
- SQL: `query(`, `execute(`, `raw(`, string concatenation with SQL keywords
- Auth: `login`, `authenticate`, `authorize`, `jwt`, `token`, `session`, `password`, `bcrypt`, `hash`
- Input: `req.body`, `req.params`, `req.query`, `request.form`, `request.args`, user input handlers
- Crypto: `encrypt`, `decrypt`, `sign`, `verify`, `hmac`, `aes`, `rsa`
- Headers: `cors`, `csp`, `x-frame`, `helmet`, security middleware
- Secrets: `API_KEY`, `SECRET`, `PASSWORD`, `TOKEN` in code (not env)

**Severity guidance:**
- critical: SQL injection vectors, auth bypass, password handling, token validation
- high: Input sanitization, CORS config, session management
- medium: Security headers, rate limiting, CSRF protection
- low: Logging sensitive data warnings

**Example finding:**
> `src/api/users.ts:87` — `findUser()` builds SQL with string interpolation from `req.params.id`. No test verifies injection resistance. **Severity: critical, Confidence: high**

---

## 3. Infrastructure

**Focus:** Environment config, deployment, file I/O, system resources.

**Patterns to grep:**
- `process.env`, `os.environ`, `os.Getenv`, `env::var`, `Environment.GetEnvironmentVariable`
- Config loaders: `dotenv`, `config`, `yaml.load`, `json.load` for config
- File ops: `readFile`, `writeFile`, `open(`, `os.path`, `fs.`, `io.`
- Process: `exec`, `spawn`, `subprocess`, `os.system`, `child_process`
- Ports/networking: `listen(`, `bind(`, `createServer`

**Severity guidance:**
- critical: Missing env var handling (crashes on startup), file permission issues
- high: Config parsing errors, fallback behavior when config missing
- medium: File I/O error handling, temp file cleanup
- low: Log file rotation, debug config paths

**Example finding:**
> `src/config/database.ts:12` — `DATABASE_URL` read from env with no fallback or validation. No test for missing env var scenario. **Severity: high, Confidence: high**

---

## 4. Network & Integration

**Focus:** APIs, retries, timeouts, database queries, third-party integrations.

**Patterns to grep:**
- HTTP: `fetch(`, `axios`, `http.get`, `requests.`, `HttpClient`, `net/http`
- Retry: `retry`, `backoff`, `attempt`, `maxRetries`
- Timeout: `timeout`, `deadline`, `AbortController`, `context.WithTimeout`
- DB: `query`, `find`, `findOne`, `select`, `insert`, `update`, `delete`, `aggregate`
- Queue: `publish`, `subscribe`, `enqueue`, `dequeue`, `emit`, `on(`
- GraphQL: `gql`, `mutation`, `query`, resolver functions

**Severity guidance:**
- critical: No timeout on external calls, missing retry for idempotent operations
- high: Untested error responses (4xx, 5xx), connection failure handling
- medium: Retry exhaustion behavior, circuit breaker tests
- low: Request logging, header propagation

**Example finding:**
> `src/services/payment.ts:55` — `chargeCard()` calls Stripe API with no timeout and no test for network failure scenario. **Severity: critical, Confidence: high**

---

## 5. Frontend / UX

**Focus:** Rendering, accessibility, state management, responsive behavior.

**Patterns to grep:**
- Components: `render`, `Component`, `function.*Page`, `function.*View`, `.tsx`, `.jsx`, `.vue`, `.svelte`
- State: `useState`, `useReducer`, `useContext`, `store`, `dispatch`, `commit`, `setState`
- Events: `onClick`, `onChange`, `onSubmit`, `addEventListener`, `@click`, `v-on`
- A11y: `aria-`, `role=`, `alt=`, `tabIndex`, `<label`, screen reader references
- Forms: `<form`, `<input`, `<select`, `<textarea`, form validation
- Routing: `Route`, `router`, `navigate`, `useParams`, `useLocation`

**Severity guidance:**
- critical: Form submission without validation test, auth UI flows untested
- high: Core page rendering, navigation flows, critical user interactions
- medium: Loading states, error boundaries, empty states
- low: Animation, tooltip, cosmetic rendering

**Example finding:**
> `src/components/CheckoutForm.tsx:23` — Form has 5 validation rules but no test renders the component or simulates submission. **Severity: critical, Confidence: high**

---

## 6. Customer Journey

**Focus:** End-to-end flows, multi-step processes, cross-page interactions.

**Patterns to grep:**
- Routes/endpoints: route definitions, controller classes, handler registrations
- Middleware: auth middleware, validation middleware, rate limiters in the chain
- Multi-step: wizard patterns, step/stage enums, state machines
- Redirects: `redirect`, `navigate`, `push`, `replace` in flow context
- Session: `session`, `cookie`, `localStorage`, `sessionStorage` in flow context

**Severity guidance:**
- critical: Complete user journeys with no E2E test (signup, purchase, onboarding)
- high: Partial journey steps untested (e.g., payment step tested but redirect after payment not)
- medium: Secondary flows (password reset, settings change)
- low: Edge journeys (expired link handling, deep link entry)

**Example finding:**
> The signup flow spans 4 routes (`/register` -> `/verify` -> `/onboarding` -> `/dashboard`) but no test exercises the full chain. Individual route handlers are tested, but transitions are not. **Severity: critical, Confidence: medium**

---

## 7. Resilience

**Focus:** Error recovery, concurrency safety, graceful degradation.

**Patterns to grep:**
- `try`, `catch`, `finally`, `except`, `rescue`, `recover`, `defer`
- `throw`, `raise`, `panic`, error creation patterns
- Locks: `mutex`, `lock`, `synchronized`, `semaphore`, `atomic`
- Concurrency: `Promise.all`, `async`, `await`, `goroutine`, `thread`, `Task.WhenAll`
- Graceful shutdown: `SIGTERM`, `SIGINT`, `process.on`, signal handlers
- Circuit breaker: `breaker`, `circuit`, `fallback`, `degrade`

**Severity guidance:**
- critical: Unhandled promise rejections, empty catch blocks in critical paths, race conditions in shared state
- high: Missing error recovery in data pipelines, no fallback for service dependencies
- medium: Graceful shutdown handling, resource cleanup on error
- low: Logging in catch blocks, retry delay strategy

**Example finding:**
> `src/workers/sync.ts:78` — `processQueue()` uses `Promise.all` for batch DB writes with no error handling. One failure silently drops all writes. **Severity: critical, Confidence: high**

---

## 8. Idempotence

**Focus:** Safe retries, duplicate prevention, state consistency.

**Patterns to grep:**
- `PUT`, `DELETE`, `PATCH` HTTP handlers
- `upsert`, `insertOrUpdate`, `ON CONFLICT`, `MERGE`, `REPLACE INTO`
- Payment: `charge`, `refund`, `transfer`, `payout`, idempotency keys
- Message queues: `ack`, `nack`, `processMessage`, consumer handlers
- Deduplication: `dedup`, `idempotencyKey`, `requestId`, `transactionId`, `nonce`
- Retry: functions called from retry loops or message consumers

**Severity guidance:**
- critical: Payment/billing operations without idempotency test, message handlers without dedup test
- high: PUT/DELETE handlers without idempotency verification, upsert logic untested
- medium: Background job retry safety, cache invalidation on retry
- low: Logging dedup, metric emission dedup

**Example finding:**
> `src/api/payments.ts:34` — `processPayment()` has an `idempotencyKey` parameter but no test verifies that duplicate calls produce the same result without double-charging. **Severity: critical, Confidence: high**

---

## 9. Performance

**Focus:** Response time, resource usage, scalability patterns.

**Patterns to grep:**
- N+1: Loop containing DB query (`for.*query`, `map.*find`, `forEach.*select`)
- Unbounded: `findAll`, `find({})`, `SELECT *` without `LIMIT`, missing pagination
- Large payloads: `JSON.stringify` on unbounded data, no streaming for large responses
- Caching: `cache`, `redis`, `memcached`, `lru`, `memoize`, cache invalidation
- Bulk ops: `bulkWrite`, `insertMany`, `batchUpdate`, batch processing patterns
- Indices: Complex query filters that may lack DB index support

**Severity guidance:**
- critical: N+1 queries in request handlers, unbounded queries on large tables
- high: Missing pagination on list endpoints, no cache for hot paths
- medium: Suboptimal batch sizes, missing connection pooling
- low: Redundant serialization, unoptimized sorting

**Example finding:**
> `src/api/orders.ts:67` — `listOrders()` calls `findAll()` with no LIMIT. Table has 2M+ rows based on migration history. No test verifies pagination or performance under load. **Severity: critical, Confidence: medium**

---

## 10. Observability

**Focus:** Logging, metrics, traces, alerting, health checks.

**Patterns to grep:**
- Logging: `logger`, `console.log`, `log.`, `logging.`, `slog.`, `Log.`
- Metrics: `metrics`, `counter`, `histogram`, `gauge`, `prometheus`, `statsd`, `datadog`
- Traces: `span`, `trace`, `opentelemetry`, `tracing`, `context` propagation
- Health: `health`, `ready`, `live`, `/healthz`, `/readyz`, status endpoints
- Error reporting: `sentry`, `bugsnag`, `rollbar`, `errorHandler`, `reportError`
- Alerting: `alert`, `notify`, `pager`, `oncall`, `webhook` for monitoring

**Severity guidance:**
- critical: No health check endpoint, error reporting completely absent
- high: Critical error paths with no logging, missing trace context in service calls
- medium: Inconsistent log levels, missing metrics for key operations
- low: Verbose debug logging, metric naming conventions

**Example finding:**
> `src/services/` has 12 service files but no structured logging or error reporting integration. Failures would be invisible in production. **Severity: high, Confidence: high**
