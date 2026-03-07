# PROJECT-KNOWLEDGE.md Template

Use this template when synthesizing the final profile. Replace all `{placeholders}`.
Omit sections that don't apply. Every bullet must contain a concrete file path,
function/class name, or specific detail — never generic descriptions.

Apply word-count targets based on depth:
- `quick`: ~2,000 words — keep only the most essential information per section
- `standard`: ~4,000 words — comprehensive but focused
- `deep`: ~6,000 words — thorough with more examples and edge cases

---

```markdown
# Project Knowledge: {project-name}

> Generated: {YYYY-MM-DD HH:mm} | Depth: {quick|standard|deep} | Source: `{absolute-path}`

## Identity

- **Purpose**: {one sentence — "A Next.js SaaS dashboard for managing IoT devices"}
- **Language(s)**: {TypeScript 92%, Python 8%}
- **Framework(s)**: {Next.js 14 (App Router), FastAPI}
- **Build system**: {npm, turborepo}
- **Package manager**: {pnpm}
- **Test runner(s)**: {vitest, pytest}
- **Monorepo**: {yes/no — if yes, list packages}

## Structure

### Module Map

<!-- Annotate each directory with its purpose. Show 2-3 levels deep. -->

{project-root}/
  src/
    app/           -- Next.js App Router pages and layouts
    components/    -- React components (atomic design: atoms/, molecules/, organisms/)
    lib/           -- Shared utilities and API clients
    services/      -- Business logic layer
  api/
    routes/        -- API endpoint definitions
    models/        -- SQLAlchemy models
    services/      -- Backend business logic
  packages/
    shared-types/  -- Shared TypeScript types between frontend and API

### Entry Points

| Entry Point | Type | Path | Description |
|------------|------|------|-------------|
| {Web app} | {Next.js} | {src/app/layout.tsx} | {Root layout, wraps AuthProvider} |
| {API server} | {FastAPI} | {api/main.py} | {Mounts all routers, CORS config} |
| {Worker} | {Celery} | {api/workers/sync.py} | {Background sync job} |

### Key Files

<!-- Files that are important but not obvious from directory structure -->

| File | Why It Matters |
|------|---------------|
| {src/lib/api-client.ts} | {All frontend API calls go through this; handles auth token injection} |
| {api/deps.py} | {Dependency injection for DB session, current user, permissions} |
| {config/features.ts} | {Feature flags that gate functionality} |

## Architecture

### Pattern

{e.g., "Layered architecture with frontend/backend split. Frontend uses
Next.js App Router with server components for data fetching. Backend is a
REST API with service-repository pattern. All data access goes through
repository interfaces defined in api/repos/base.py."}

### Data Flow

<!-- Text-based flow diagram. Show the most common request path. -->

User Action -> React Component -> API Client (src/lib/api-client.ts)
  -> FastAPI Route (api/routes/) -> Service (api/services/)
  -> Repository (api/repos/) -> PostgreSQL

Background: Celery Worker -> Service -> Repository -> PostgreSQL

### Module Dependencies

<!-- Non-obvious coupling between modules -->

- `src/components/DataTable` depends on `src/hooks/useQuery` which wraps `@tanstack/react-query`
- All API routes depend on `api/deps.get_current_user` for auth
- `api/services/sync.py` imports from `packages/shared-types` for validation schemas

### State Management

- **Frontend**: {React Query for server state, Zustand for UI state (stores in src/stores/)}
- **Backend**: {Stateless request handling; state in PostgreSQL + Redis cache}
- **Auth**: {JWT in httpOnly cookie, refreshed via src/lib/auth.ts}

## Conventions

### Naming

| Category | Convention | Example |
|----------|-----------|---------|
| Files | {kebab-case} | {user-profile.tsx} |
| Components | {PascalCase} | {UserProfile} |
| Functions | {camelCase} | {getUserById} |
| API routes | {snake_case} | {get_users} |
| DB models | {PascalCase class, snake_case table} | {class Device -> devices} |
| Tests | {*.test.ts colocated in __tests__/} | {user-profile.test.ts} |

### Patterns

- **Error handling**: {Frontend: ErrorBoundary + toast via src/lib/toast.ts. Backend: HTTPException with codes from api/errors.py}
- **Validation**: {Zod in src/schemas/ (frontend), Pydantic in api/models/ (backend)}
- **Auth guards**: {withAuth() HOC for pages, Depends(get_current_user) for API}
- **Data fetching**: {Server components use async functions; client components use useQuery hooks}

### Testing

- **Unit**: {vitest for frontend, pytest for backend}
- **E2E**: {Playwright in e2e/ directory}
- **Mocking**: {MSW for API mocking in frontend, unittest.mock + factory_boy for backend}
- **Fixtures**: {Factories in tests/factories/, fixtures in tests/fixtures/}

## Tech Stack

### Key Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| {next} | {Framework} | {14.2.x} |
| {@tanstack/react-query} | {Data fetching} | {5.x} |
| {fastapi} | {API framework} | {0.109.x} |
| {sqlalchemy} | {ORM} | {2.0.x} |

### Infrastructure

- **Database**: {PostgreSQL 15 — migrations via Alembic in api/migrations/}
- **Cache**: {Redis — sessions + query cache}
- **Queue**: {Celery + Redis broker}
- **CI**: {GitHub Actions — .github/workflows/}
- **Deployment**: {Docker Compose (dev), Kubernetes (prod)}

## Domain Concepts

### Glossary

<!-- Terms that have specific meaning in THIS codebase -->

| Term | Meaning |
|------|---------|
| {Device} | {IoT hardware unit with unique serial number} |
| {Fleet} | {Collection of devices belonging to one organization} |
| {Telemetry} | {Time-series data from device sensors} |

### Key Abstractions

| Abstraction | Type | File | Purpose |
|-------------|------|------|---------|
| {DeviceService} | {class} | {api/services/device.py} | {All device CRUD + fleet assignment} |
| {useDevice} | {hook} | {src/hooks/useDevice.ts} | {Frontend device state + mutations} |

### API Surface

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| {GET} | {/api/v1/devices} | {JWT} | {List devices, paginated} |
| {POST} | {/api/v1/devices} | {JWT+Admin} | {Create device} |

## Configuration

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| {DATABASE_URL} | {yes} | {PostgreSQL connection string} |
| {JWT_SECRET} | {yes} | {Token signing key} |
| {NEXT_PUBLIC_API_URL} | {yes} | {Frontend API base URL} |

### Config Files

| File | Purpose |
|------|---------|
| {.env.example} | {Template for required env vars} |
| {next.config.mjs} | {Next.js config — rewrites, env exposure} |
| {alembic.ini} | {Database migration config} |
```

---

*Generated by subagent-gen. Sections wrapped in `<!-- USER: ... -->` are preserved on update.*

## Notes for Synthesis

- The examples above use a hypothetical IoT project. Replace ALL content with actual findings.
- If a section has no findings (e.g., no API surface for a library), omit the section entirely.
- Prioritize specifics over coverage — 5 concrete details beat 15 vague ones.
- For `quick` depth, merge related sections (e.g., combine Architecture + Structure).
- Include the `Generated:` line with actual timestamp and depth level.
