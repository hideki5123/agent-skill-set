# Scenario Templates

Use these templates to generate test scenarios for each change type. Adapt the level of detail to the complexity of the change.

## UI Scenario Template

```markdown
### TS-NNN: [Title - what user action/flow is being tested]

**Type**: ui | **Priority**: [critical|high|medium|low]
**Preconditions**: [What must be true before starting - auth state, data, page]
**Changed files**: [file1.tsx, file2.css]

#### Steps

| # | Action | Target | Input | Expected Result |
|---|--------|--------|-------|-----------------|
| 1 | Navigate to | [URL or page name] | | [Expected page state on load] |
| 2 | Verify visible | [Component/element description] | | [What should be visible] |
| 3 | Click | [Button/link - human-readable label] | | [Result of click] |
| 4 | Type | [Input field - by label or placeholder] | [test data] | [Field shows input] |
| 5 | Verify | [Outcome element] | | [Expected state after interaction] |

#### Screenshot Targets
- [component-name] at [page URL]: capture [specific area]
```

### UI Scenario Worked Example

```markdown
### TS-001: User can submit the contact form

**Type**: ui | **Priority**: high
**Preconditions**: User is logged in, on the Contact page
**Changed files**: src/components/ContactForm.tsx, src/styles/form.css

#### Steps

| # | Action | Target | Input | Expected Result |
|---|--------|--------|-------|-----------------|
| 1 | Navigate to | /contact | | Contact page loads with empty form |
| 2 | Verify visible | Contact form heading | | "Get in Touch" heading visible |
| 3 | Type | Name input field | John Doe | Name field shows "John Doe" |
| 4 | Type | Email input field | john@example.com | Email field populated |
| 5 | Type | Message textarea | Hello there | Message field populated |
| 6 | Click | Submit button | | Success toast appears: "Message sent!" |
| 7 | Verify | Form state | | Form fields are cleared |

#### Screenshot Targets
- ContactForm at /contact: capture the full form before and after submission
- SuccessToast at /contact: capture the toast notification
```

## API Scenario Template

```markdown
### TS-NNN: [Title - endpoint + operation being tested]

**Type**: api | **Priority**: [critical|high|medium|low]
**Preconditions**: [Auth state, required data in system]
**Changed files**: [route-file.ts, controller-file.ts]

#### Endpoint
- **Method**: [GET|POST|PUT|PATCH|DELETE]
- **Path**: [/api/v1/resource]
- **Headers**: [Required headers]

#### Test Cases

| # | Case | Request | Expected Status | Expected Response |
|---|------|---------|-----------------|-------------------|
| 1 | Success | [body/params] | 200 OK | [response structure] |
| 2 | Validation error | [invalid body] | 400 Bad Request | [error structure] |
| 3 | Unauthorized | [no auth header] | 401 Unauthorized | [error message] |
| 4 | Not found | [invalid id] | 404 Not Found | [error message] |

#### Example curl

\`\`\`bash
curl -X POST http://localhost:3000/api/v1/resource \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"field": "value"}'
\`\`\`
```

### API Scenario Worked Example

```markdown
### TS-005: Create a new todo item via POST /api/todos

**Type**: api | **Priority**: critical
**Preconditions**: User authenticated with valid JWT
**Changed files**: src/routes/todos.ts, src/controllers/todoController.ts

#### Endpoint
- **Method**: POST
- **Path**: /api/todos
- **Headers**: Content-Type: application/json, Authorization: Bearer <token>

#### Test Cases

| # | Case | Request | Expected Status | Expected Response |
|---|------|---------|-----------------|-------------------|
| 1 | Create todo | {"title": "Buy milk", "done": false} | 201 Created | {"id": "...", "title": "Buy milk", "done": false} |
| 2 | Missing title | {"done": false} | 400 Bad Request | {"error": "title is required"} |
| 3 | No auth | {"title": "Test"} (no auth header) | 401 Unauthorized | {"error": "Unauthorized"} |

#### Example curl

\`\`\`bash
curl -X POST http://localhost:3000/api/todos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbG..." \
  -d '{"title": "Buy milk", "done": false}'
\`\`\`
```

## Backend Scenario Template

```markdown
### TS-NNN: [Title - service/function being tested]

**Type**: backend | **Priority**: [critical|high|medium|low]
**Preconditions**: [System state, database state]
**Changed files**: [service-file.ts, model-file.ts]

#### Data Flow
1. **Input**: [What enters the function/service]
2. **Processing**: [What transformation happens]
3. **Output**: [What is returned/emitted]

#### Verification Points

| # | Checkpoint | Expected State |
|---|-----------|---------------|
| 1 | [Entry point / input validation] | [Input accepted/rejected correctly] |
| 2 | [Business logic step] | [Correct transformation applied] |
| 3 | [Database/external call] | [Correct data persisted/fetched] |
| 4 | [Return value / side effects] | [Correct output, events emitted] |

#### Edge Cases
- [What happens with null/empty input]
- [What happens with duplicate data]
- [What happens on external service failure]
```

## Config Scenario Template

```markdown
### TS-NNN: [Title - what config change affects]

**Type**: config | **Priority**: [critical|high|medium|low]
**Preconditions**: [Current deployment state]
**Changed files**: [config-file]

#### Impact Analysis
- **Setting changed**: [key = old_value -> new_value]
- **Affects**: [What functionality/behavior this controls]
- **Requires restart**: [yes/no]

#### Verification Points

| # | Check | Expected Behavior |
|---|-------|-------------------|
| 1 | [Feature controlled by setting] | [Behaves according to new value] |
| 2 | [Dependent feature] | [Still works correctly] |
| 3 | [Rollback] | [Reverting config restores old behavior] |
```

## Priority Guidelines

| Priority | When to use |
|----------|------------|
| **critical** | Core user flows, authentication, data integrity, payment |
| **high** | Important features, API contracts, form submissions |
| **medium** | UI polish, non-critical validations, secondary flows |
| **low** | Cosmetic changes, documentation updates, logging changes |
