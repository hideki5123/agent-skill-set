# Framework Detection

Auto-detect the project's test framework and runner command.

## Detection Procedure

1. Check for config files in the project root (and common subdirs)
2. Check dependency declarations (package.json, pyproject.toml, go.mod, etc.)
3. If multiple frameworks detected, list all and ask user which to target
4. User can always override with `--test-cmd`

## Detection Table

| Language | Framework | Config Signal | Runner Command |
|----------|-----------|---------------|----------------|
| JS/TS | Jest | `jest.config.*`, `"jest"` in package.json | `npx jest` |
| JS/TS | Vitest | `vitest.config.*`, `"vitest"` in package.json | `npx vitest run` |
| JS/TS | Mocha | `.mocharc.*`, `"mocha"` in package.json | `npx mocha` |
| JS/TS | Playwright | `playwright.config.*` | `npx playwright test` |
| JS/TS | Cypress | `cypress.config.*`, `cypress/` dir | `npx cypress run` |
| JS/TS | AVA | `"ava"` in package.json | `npx ava` |
| Python | Pytest | `pytest.ini`, `pyproject.toml [tool.pytest]`, `conftest.py` | `pytest` |
| Python | unittest | `test_*.py` files, no pytest config | `python -m unittest discover` |
| Go | go test | `*_test.go` files | `go test ./...` |
| Rust | cargo test | `Cargo.toml`, `#[cfg(test)]` blocks | `cargo test` |
| C# | xUnit | `*.csproj` with `xunit` ref | `dotnet test` |
| C# | NUnit | `*.csproj` with `NUnit` ref | `dotnet test` |
| C# | MSTest | `*.csproj` with `MSTest` ref | `dotnet test` |
| Java | JUnit | `pom.xml` with `junit`, `build.gradle` with `junit` | `mvn test` / `gradle test` |
| Java | TestNG | `pom.xml` with `testng` | `mvn test` |
| Ruby | RSpec | `.rspec`, `Gemfile` with `rspec` | `bundle exec rspec` |
| Ruby | Minitest | `Gemfile` with `minitest` | `bundle exec rake test` |
| PHP | PHPUnit | `phpunit.xml*`, `composer.json` with `phpunit` | `vendor/bin/phpunit` |
| Elixir | ExUnit | `mix.exs`, `test/` dir | `mix test` |
| Swift | XCTest | `Package.swift`, `.xcodeproj` | `swift test` / `xcodebuild test` |
| Kotlin | JUnit | `build.gradle.kts` with `junit` | `gradle test` |

## Script Runner Detection

Also check for script aliases that wrap the test runner:

| File | Key | Example |
|------|-----|---------|
| `package.json` | `"scripts"."test"` | `"test": "vitest run"` |
| `package.json` | `"scripts"."test:unit"` | `"test:unit": "jest --config jest.unit.config.ts"` |
| `package.json` | `"scripts"."test:e2e"` | `"test:e2e": "playwright test"` |
| `Makefile` | `test:` target | `test: pytest -v` |
| `pyproject.toml` | `[tool.pytest.ini_options]` | `addopts = "-v"` |
| `Taskfile.yml` | `test:` task | `cmds: ["go test ./..."]` |

Prefer script aliases (e.g., `npm test`) over raw commands when they exist, as they
may include project-specific flags and environment setup.

## Monorepo Detection

| Signal | Type |
|--------|------|
| `"workspaces"` in `package.json` | npm/yarn workspaces |
| `pnpm-workspace.yaml` | pnpm workspaces |
| `lerna.json` | Lerna monorepo |
| `Cargo.toml` with `[workspace]` | Rust workspace |
| `go.work` | Go workspace |
| Multiple `*.csproj` with a `*.sln` | .NET solution |
| `nx.json` | Nx monorepo |
| `turbo.json` | Turborepo |

When a monorepo is detected, each package/project may have its own test framework.
Detect independently per package.
