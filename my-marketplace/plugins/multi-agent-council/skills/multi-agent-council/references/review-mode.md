# Review Mode Reference

## Purpose
Review project state for risks, defects, and improvement opportunities. Unlike traditional code review, this is not Git/diff-based - it reviews the current state of the project snapshot.

## Input Schema

```yaml
ReviewModeInput:
  project_snapshot: ProjectSnapshot  # Current project state (required)
  focus_areas: string[]              # Optional: specific concerns
  severity_threshold: string         # Optional: minimum severity to report
  exclude_patterns: string[]         # Optional: files/patterns to skip
```

## Output Schema

```yaml
ReviewModeOutput:
  findings:
    - id: string
      title: string
      severity: "low" | "medium" | "high" | "critical"
      category: string              # security, performance, maintainability, etc.
      location: string              # file:line or general area
      description: string
      rationale: string             # why this is a problem
      fix_approach: string          # suggested resolution
      impact_scope: string[]        # affected areas
      test_considerations: string[] # how to verify the fix
      priority: number              # suggested fix order
  summary:
    critical_count: number
    high_count: number
    medium_count: number
    low_count: number
    top_concerns: string[]
    recommended_actions: string[]
```

## System Preamble (for all providers)

```
You are participating in a multi-LLM code review council. Your role is to
thoroughly analyze the project state and identify issues that could cause
problems in production, maintenance, or future development.

Review Categories:
1. Security - vulnerabilities, unsafe practices, data exposure
2. Performance - inefficiencies, memory leaks, blocking operations
3. Reliability - error handling, edge cases, failure modes
4. Maintainability - code clarity, coupling, technical debt
5. Correctness - bugs, logic errors, incorrect assumptions

Guidelines:
- Be thorough but prioritize actionable findings
- Explain why something is problematic, not just what
- Consider the project context (don't flag intentional trade-offs)
- Suggest specific fixes, not just "improve this"
- Your review will be cross-examined by other LLMs
```

## Round 1 Prompt Template

```
## Review Task
Analyze the following project snapshot for issues and improvement opportunities.

## Project Context
{manifest_and_structure}

## Key Files
{key_files_content}

## Full Project Content
{project_content_or_summary}

## Focus Areas (if specified)
{focus_areas}

## Your Task
Perform a thorough review following this structure:

1. **Overview**: What kind of project is this? What's its purpose?
2. **Architecture Assessment**: How is it structured? Any concerns?
3. **Security Findings**: Any vulnerabilities or unsafe practices?
4. **Performance Findings**: Any inefficiencies or bottlenecks?
5. **Reliability Findings**: Error handling, edge cases, failure modes?
6. **Maintainability Findings**: Code quality, coupling, clarity?
7. **Other Findings**: Anything else noteworthy?
8. **Positive Observations**: What's done well?

For each finding, provide:
- Severity (critical/high/medium/low)
- Location (file:line or general area)
- Description
- Why it matters
- Suggested fix
```

## Round 2 Prompt Template

```
## Original Project
{project_summary}

## Other Reviewers' Findings
{r1_findings_formatted}

## Your Task
Review the other models' findings critically:

1. **False Positives**: Any findings that aren't actually issues?
2. **Missed Issues**: Important problems no one mentioned?
3. **Severity Disputes**: Any findings over/under-rated?
4. **Better Fixes**: Improved solutions for identified issues?
5. **Context Missing**: Any findings that ignore valid reasons?
6. **Priority Disagreements**: Should anything be prioritized differently?

Be constructive. Goal is to produce the most accurate, actionable review.
```

## Review Categories

### Security
- Injection vulnerabilities (SQL, command, XSS)
- Authentication/authorization issues
- Secrets/credentials in code
- Insecure dependencies
- Data exposure risks
- CSRF, SSRF, path traversal

### Performance
- N+1 queries
- Missing indexes
- Memory leaks
- Blocking I/O in async contexts
- Unnecessary computation
- Missing caching opportunities

### Reliability
- Unhandled errors/exceptions
- Missing input validation
- Race conditions
- Resource leaks
- Missing timeouts
- Inadequate logging

### Maintainability
- Code duplication
- High coupling
- Missing abstractions
- Unclear naming
- Missing documentation (for complex logic)
- Dead code

### Correctness
- Logic errors
- Off-by-one errors
- Incorrect type handling
- Race conditions
- Invalid assumptions

## Example Workflow

### Input
```yaml
project_snapshot:
  root: "/project/web-app"
  focus_areas:
    - "authentication"
    - "database queries"
```

### Expected Council Flow

1. **R1**: Each provider reviews independently
   - Claude: Deep analysis of auth flow, SQL patterns
   - OpenAI: Focus on security vulnerabilities, API safety
   - Gemini: Performance patterns, error handling gaps

2. **R2**: Cross-review
   - Validate each other's findings
   - Add missed issues
   - Debate severity levels
   - Refine fix suggestions

3. **R3**: Chair synthesis
   - Consolidate findings (remove duplicates)
   - Finalize severity ratings
   - Prioritize by impact
   - Produce actionable report

### Sample Output
```yaml
findings:
  - id: "SEC-001"
    title: "SQL injection in user search"
    severity: "critical"
    category: "security"
    location: "src/api/users.js:45"
    description: "User input directly concatenated into SQL query"
    rationale: "Allows attackers to execute arbitrary SQL, potentially dumping entire database"
    fix_approach: "Use parameterized queries: db.query('SELECT * FROM users WHERE name = ?', [searchTerm])"
    impact_scope: ["user data", "authentication", "database integrity"]
    test_considerations: ["Test with SQL injection payloads", "Verify parameterized query works"]
    priority: 1

  - id: "PERF-001"
    title: "N+1 query in order listing"
    severity: "high"
    category: "performance"
    location: "src/api/orders.js:78-92"
    description: "Fetching customer details inside loop for each order"
    rationale: "With 100 orders, this generates 101 queries instead of 2"
    fix_approach: "Use JOIN or batch fetch customers upfront"
    impact_scope: ["order listing page", "admin dashboard"]
    test_considerations: ["Load test with 100+ orders", "Monitor query count"]
    priority: 2

summary:
  critical_count: 1
  high_count: 3
  medium_count: 7
  low_count: 4
  top_concerns:
    - "Critical SQL injection must be fixed immediately"
    - "Authentication token not properly validated"
    - "Multiple N+1 query patterns affecting performance"
  recommended_actions:
    - "Address SEC-001 before next deployment"
    - "Implement input validation middleware"
    - "Add database query logging to catch N+1 patterns"
```

## Mode-Specific Components

### ReviewModePromptBuilder

Responsibilities:
1. Format project snapshot clearly
2. Highlight focus areas if specified
3. Generate round-specific prompts
4. Include relevant context without overwhelming

### SnapshotScanner

Responsibilities:
1. Walk project directory tree
2. Identify file types and purposes
3. Extract key files (config, entry points, auth, I/O)
4. Respect exclusion patterns
5. Handle cross-platform path differences

### OutputSchemaFormatter

Responsibilities:
1. Parse diverse review formats into standard schema
2. Deduplicate findings across providers
3. Normalize severity ratings
4. Generate summary statistics
5. Sort by priority
