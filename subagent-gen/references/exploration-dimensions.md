# Exploration Dimensions

Pattern catalog for each exploration dimension. Each agent receives its dimension's
section as exploration instructions.

---

## Dimension: Structure

**Focus**: Directory layout, entry points, module boundaries, build outputs

### What to Look For

1. **Directory tree** (top 3 levels) — annotate each directory's purpose
2. **Entry points** — files that start execution:
   - `main.*`, `index.*`, `app.*`, `server.*`, `cli.*`, `worker.*`
   - Scripts referenced in `package.json` scripts, `Makefile` targets, `Dockerfile` CMD/ENTRYPOINT
3. **Module boundaries** — how code is organized:
   - Flat structure vs nested modules vs monorepo packages
   - Shared code directories (`lib/`, `utils/`, `shared/`, `common/`, `packages/`)
4. **Key files** — files that are important but not obvious from structure:
   - Dependency injection setup, middleware registration, route mounting
   - Config loaders, feature flag definitions, constants/enums
5. **Build outputs** — `dist/`, `build/`, `.next/`, `target/`, `out/`

### Grep Signals

```
# Entry points
main\.(ts|js|py|go|rs|java|rb)
index\.(ts|js|py)
app\.(ts|js|py)
server\.(ts|js|py)

# Route/endpoint registration
app\.(get|post|put|delete|patch|use)\(
router\.(get|post|put|delete|patch)
@(Get|Post|Put|Delete|Patch|Controller|Router)
urlpatterns
Blueprint

# Middleware/plugin registration
app\.use\(
middleware
plugin
```

### Sampling Strategy

- Read the full directory tree (3 levels)
- Read all manifest/config files at root
- Sample 2-3 files from each major source directory to understand its purpose
- Read entry point files in full

### Output Format

```markdown
### Module Map

{project-root}/
  {dir}/    -- {purpose annotation}
  {dir}/
    {subdir}/  -- {purpose annotation}

### Entry Points

| Entry Point | Type | Path | Description |
|------------|------|------|-------------|
| ... | ... | ... | ... |

### Key Files

| File | Why It Matters |
|------|---------------|
| ... | ... |
```

---

## Dimension: Architecture

**Focus**: How modules connect, dependency graph, data flow, layering, state management

### What to Look For

1. **Architectural pattern** — identify the dominant pattern:
   - Layered (controllers → services → repositories)
   - Hexagonal / ports-and-adapters
   - MVC / MVVM
   - Microservices / modular monolith
   - Event-driven / message-based
   - Serverless functions
2. **Data flow** — trace from user action to data store and back:
   - Frontend → API client → backend route → service → data layer → database
   - Event producer → queue → consumer → side effects
3. **Module dependencies** — non-obvious coupling:
   - Which modules import from which
   - Shared types/interfaces between layers
   - Circular dependency risks
4. **State management**:
   - Frontend: Redux, Zustand, Context, signals, stores
   - Backend: stateless request handling, sessions, cache layers
   - Auth state: how authentication flows (JWT, sessions, OAuth)
5. **Middleware/plugin chains** — what runs before/after request handling

### Grep Signals

```
# Import patterns (trace dependencies)
import .* from ['"]\./
import .* from ['"]@/
require\(['"]\.
from \. import

# State management
createStore|configureStore|useReducer
zustand|create\(|useStore
createContext|useContext|Provider
useState|useMemo|useCallback

# Dependency injection
@Inject|@Injectable|inject\(
Depends\(|dependency_injector
container\.register|bind\(

# Data access patterns
Repository|repository
\.query\(|\.execute\(
prisma\.|knex\.|sequelize\.
Session\(\)|engine\.connect

# Event/message patterns
emit\(|on\(|subscribe\(|publish\(
EventEmitter|EventBus
queue\.|channel\.|exchange\.
```

### Sampling Strategy

- Read 3-5 files from each architectural layer to understand the pattern
- Trace one complete request path end-to-end (pick a common API endpoint)
- Check import statements in 10-15 files to map dependency directions
- Look for DI containers, middleware registration, and plugin setup

### Output Format

```markdown
### Architectural Pattern

{Pattern name and 2-3 sentence description of how it manifests in this codebase}

### Data Flow

{Text-based flow diagram showing the path from user action to data store}

```
{Component} -> {Component} -> {Component} -> {Data Store}
```

### Module Dependencies

- {Module A} depends on {Module B} for {reason} ({file path})
- ...

### State Management

- **Frontend**: {approach} — {key files}
- **Backend**: {approach} — {key files}
- **Auth**: {flow description} — {key files}
```

---

## Dimension: Conventions

**Focus**: Naming patterns, error handling, logging, validation, testing patterns

### What to Look For

1. **Naming conventions**:
   - File naming: kebab-case, snake_case, PascalCase, camelCase
   - Component/class naming
   - Function/method naming
   - Database table/column naming
   - API endpoint naming (REST paths, GraphQL types)
2. **Error handling patterns**:
   - Try/catch style, Result types, error boundaries
   - Custom error classes/types
   - Error response format (API error shape)
   - How errors propagate between layers
3. **Logging approach**:
   - Logger library used
   - Log levels and when they're used
   - Structured logging (JSON) vs plain text
4. **Validation patterns**:
   - Input validation (Zod, Joi, Pydantic, class-validator)
   - Where validation happens (controller, service, middleware)
   - Schema definition location
5. **Testing patterns**:
   - Test file naming and location (colocated vs separate directory)
   - Test structure (describe/it, test classes, BDD)
   - Mocking approach (jest.mock, unittest.mock, testdoubles)
   - Fixture/factory patterns
   - Test data management

### Grep Signals

```
# Error handling
try\s*{|try:|except |catch\s*\(
throw new|raise |Error\(|Exception\(
ErrorBoundary|error_handler
class \w+Error|class \w+Exception

# Logging
logger\.|log\.|console\.(log|warn|error|info|debug)
winston|pino|bunyan|log4j|logging\.
structlog|slog\.

# Validation
z\.|zod\.|Zod\.|yup\.|Joi\.
@IsString|@IsNumber|@Validate
class-validator|class-transformer
BaseModel|Field\(|validator
Schema\(|validate\(

# Testing
describe\(|it\(|test\(|expect\(
@Test|@pytest|def test_
jest\.mock|vi\.mock|patch\(|Mock\(
factory|fixture|seed
```

### Sampling Strategy

- Sample 10-15 files across different directories to detect naming consistency
- Look at 3-5 error handling locations (try/catch, error boundaries, error responses)
- Check 2-3 test files to understand testing patterns
- Read validation schemas if they exist in dedicated directories

### Output Format

```markdown
### Naming Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| Files | {case style} | `{example}` |
| Components/Classes | {case style} | `{example}` |
| Functions/Methods | {case style} | `{example}` |
| API endpoints | {style} | `{example}` |
| DB tables/columns | {style} | `{example}` |
| Tests | {pattern} | `{example}` |

### Error Handling

- **Style**: {description with file path examples}
- **Custom errors**: {list with file paths}
- **API error format**: {shape description}
- **Propagation**: {how errors flow between layers}

### Validation

- **Library**: {name}
- **Location**: {where validation runs}
- **Schemas**: {where defined, pattern used}

### Testing Patterns

- **Runner**: {test runner name}
- **Location**: {colocated vs separate, naming pattern}
- **Structure**: {describe/it, test classes, etc.}
- **Mocking**: {approach and library}
- **Fixtures**: {approach — factories, fixtures, seed files}
```

---

## Dimension: Domain

**Focus**: Business/domain concepts, key abstractions, API surface, configuration

### What to Look For

1. **Domain glossary** — business terms encoded in the codebase:
   - Class/type names that represent business concepts
   - Enum values that encode domain states
   - Comments/docstrings that explain domain logic
   - Variable names that use domain terminology
2. **Key abstractions** — the most important classes/types/interfaces:
   - Core domain models (User, Order, Device, etc.)
   - Service classes that orchestrate business logic
   - Repository/data access interfaces
   - Shared types/interfaces used across modules
3. **API surface** — external-facing interfaces:
   - REST endpoints (method, path, auth, description)
   - GraphQL types and resolvers
   - CLI commands and flags
   - Event/message types published/consumed
   - WebSocket channels
4. **Configuration**:
   - Environment variables (required vs optional)
   - Config files and their purpose
   - Feature flags
   - Infrastructure settings (DB, cache, queue, CDN)

### Grep Signals

```
# Domain models
class \w+(Model|Entity|Schema|Type|Dto)
interface I?\w+(Service|Repository|Store|Manager)
type \w+ = {|type \w+ struct
enum \w+|class \w+\(Enum\)

# API surface
@(Get|Post|Put|Delete|Patch|Controller)\(
@app\.(get|post|put|delete|route)\(
router\.(get|post|put|delete)
@api_view|@action

# Configuration
process\.env\.|os\.environ|os\.getenv
ENV\[|config\.|Settings\(
NEXT_PUBLIC_|VITE_|REACT_APP_

# Feature flags
feature[_-]?flag|isEnabled|isFeatureEnabled
LaunchDarkly|unleash|flagsmith
```

### Sampling Strategy

- Read all model/entity/type definition files
- Read API route/controller files to map endpoints
- Read config/env files (.env.example, config.ts, settings.py)
- Check 5-10 service/business logic files for domain terms
- Read docstrings/JSDoc comments on key abstractions

### Output Format

```markdown
### Domain Glossary

| Term | Meaning in This Codebase |
|------|--------------------------|
| {Term} | {What it means specifically here} |
| ... | ... |

### Key Abstractions

| Abstraction | Type | File | Purpose |
|-------------|------|------|---------|
| {Name} | {class/interface/type} | {path} | {what it does} |
| ... | ... | ... | ... |

### API Surface

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| {GET/POST/...} | {/api/...} | {auth type} | {what it does} |
| ... | ... | ... | ... |

### Configuration

#### Environment Variables

| Variable | Required | Purpose | Example |
|----------|----------|---------|---------|
| {VAR_NAME} | {yes/no} | {what it does} | {example value} |
| ... | ... | ... | ... |

#### Config Files

| File | Purpose |
|------|---------|
| {path} | {what it configures} |
| ... | ... |
```
