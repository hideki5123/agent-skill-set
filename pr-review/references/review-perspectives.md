# Review Perspectives (Lenses)

Each lens defines what to look for, common patterns, and severity guidance. Apply active lenses to the PR diff and generate inline comments where issues are found.

---

## bugs

Logic errors, incorrect behavior, and runtime failures.

**What to look for:**
- Off-by-one errors in loops and slicing
- Null/undefined dereference without guard
- Missing error handling (uncaught exceptions, ignored return values)
- Wrong operator (`=` vs `==`, `&&` vs `||`)
- Race conditions in async code
- Type coercion bugs (loose equality, implicit conversions)
- Incorrect variable shadowing
- Missing `break` in switch/case
- Unreachable code after early return

**Severity guidance:**
- **critical** — Will crash or corrupt data in production
- **high** — Incorrect behavior under common conditions
- **medium** — Bug under edge-case conditions
- **low** — Cosmetic bug, unlikely to affect users

---

## security

Vulnerabilities and unsafe patterns.

**What to look for:**
- SQL injection (string concatenation in queries)
- XSS (unsanitized user input rendered in HTML)
- Command injection (shell commands with user input)
- Path traversal (`../` in file operations)
- Hardcoded secrets (API keys, passwords, tokens in source)
- Missing authentication/authorization checks
- Insecure cryptographic usage (weak algorithms, predictable randomness)
- SSRF (user-controlled URLs in server-side requests)
- Open redirect
- Sensitive data in logs or error messages

**Severity guidance:**
- **critical** — Exploitable in production, data breach risk
- **high** — Exploitable with specific conditions
- **medium** — Defense-in-depth concern, not directly exploitable
- **low** — Informational, best-practice deviation

---

## performance

Inefficiency, resource waste, and scalability issues.

**What to look for:**
- N+1 queries (DB query inside a loop)
- Unbounded allocations (loading all rows into memory)
- Missing pagination on large datasets
- Unnecessary re-renders (React) or recomputations
- Synchronous I/O on hot paths
- Redundant API calls or network requests
- Missing caching for expensive operations
- O(n^2) algorithms where O(n log n) or O(n) exists
- Large objects in closures causing memory leaks

**Severity guidance:**
- **critical** — Will cause outage or OOM under normal load
- **high** — Noticeable degradation at expected scale
- **medium** — Inefficient but tolerable at current scale
- **low** — Micro-optimization, marginal impact

---

## style

Naming, formatting, and convention adherence.

**What to look for:**
- Inconsistent naming (camelCase vs snake_case within the same codebase)
- Dead code (unused imports, unreachable branches, commented-out code)
- Inconsistent formatting (spacing, brace style, line length)
- Magic numbers/strings without named constants
- Misleading variable or function names
- Overly abbreviated names (`x`, `tmp`, `val` in non-trivial contexts)
- Import ordering inconsistencies

**Severity guidance:**
- **medium** — Violates project conventions or reduces readability significantly
- **low** — Nitpick, subjective preference

---

## complexity

Code that is unnecessarily hard to understand or maintain.

**What to look for:**
- Deep nesting (>3 levels of indentation)
- God objects / god functions (>100 lines, many responsibilities)
- Complex conditionals (>3 conditions chained)
- Duplicated logic that should be extracted
- Excessive abstraction (wrapper classes that add no value)
- Circular dependencies between modules
- Long parameter lists (>5 parameters)
- Deeply nested callbacks or promise chains

**Severity guidance:**
- **high** — Makes the code unmaintainable, high bug risk
- **medium** — Harder to understand than necessary
- **low** — Could be cleaner but is acceptable

---

## testing

Missing or inadequate test coverage for the changes.

**What to look for:**
- New public functions/methods without corresponding tests
- Changed behavior without updated tests
- Tests that don't assert meaningful outcomes (snapshot-only, no real assertions)
- Missing edge-case tests (empty input, null, boundary values)
- Tests tightly coupled to implementation details (will break on refactor)
- Missing error/exception path tests
- No integration test for new API endpoints
- Flaky test patterns (time-dependent, order-dependent)

**Severity guidance:**
- **high** — Critical path with zero test coverage
- **medium** — Happy path tested but missing edge cases
- **low** — Would benefit from a test but low risk

---

## docs

Stale, misleading, or missing documentation.

**What to look for:**
- Changed function signatures without updated docstrings/JSDoc
- README references to removed features or renamed files
- Misleading comments that describe old behavior
- Public API without any documentation
- Missing changelog entry for user-facing changes
- Outdated examples in doc comments
- TODO/FIXME/HACK comments that should be tracked as issues

**Severity guidance:**
- **medium** — Public API without docs, or actively misleading docs
- **low** — Minor gap, internal-only code
