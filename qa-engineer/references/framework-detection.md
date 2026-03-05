# Framework Detection

Auto-detect the project's test framework, runner command, and coverage tool.

## Detection Procedure

1. Check for config files in the project root (and common subdirs)
2. Check dependency declarations (package.json, pyproject.toml, go.mod, etc.)
3. If multiple frameworks detected, list all and ask user which to target
4. User can always override with `--test-cmd`

## Detection Table

| Language | Framework | Config Signal | Runner Command | Coverage Flag | Coverage Format |
|----------|-----------|---------------|----------------|---------------|-----------------|
| JS/TS | Jest | `jest.config.*`, `"jest"` in package.json | `npx jest` | `--coverage` | Istanbul JSON, lcov |
| JS/TS | Vitest | `vitest.config.*`, `"vitest"` in package.json | `npx vitest run` | `--coverage` | Istanbul JSON, v8 |
| JS/TS | Mocha | `.mocharc.*`, `"mocha"` in package.json | `npx mocha` | (use `nyc npx mocha`) | Istanbul JSON, lcov |
| JS/TS | Playwright | `playwright.config.*` | `npx playwright test` | (none built-in) | — |
| JS/TS | Cypress | `cypress.config.*`, `cypress/` dir | `npx cypress run` | (`@cypress/code-coverage`) | Istanbul JSON |
| JS/TS | AVA | `"ava"` in package.json | `npx ava` | `npx c8 npx ava` | v8 |
| Python | Pytest | `pytest.ini`, `pyproject.toml [tool.pytest]`, `conftest.py` | `pytest` | `--cov --cov-report=json` | coverage.py JSON |
| Python | unittest | `test_*.py` files, no pytest config | `python -m unittest discover` | `coverage run -m unittest discover` | coverage.py |
| Go | go test | `*_test.go` files | `go test ./...` | `-coverprofile=cover.out` | Go cover profile |
| Rust | cargo test | `Cargo.toml`, `#[cfg(test)]` blocks | `cargo test` | (use `cargo-tarpaulin`) | lcov |
| C# | xUnit | `*.csproj` with `xunit` ref | `dotnet test` | `--collect:"XPlat Code Coverage"` | Cobertura XML |
| C# | NUnit | `*.csproj` with `NUnit` ref | `dotnet test` | `--collect:"XPlat Code Coverage"` | Cobertura XML |
| C# | MSTest | `*.csproj` with `MSTest` ref | `dotnet test` | `--collect:"XPlat Code Coverage"` | Cobertura XML |
| Java | JUnit | `pom.xml` with `junit`, `build.gradle` with `junit` | `mvn test` / `gradle test` | (JaCoCo plugin) | JaCoCo XML |
| Java | TestNG | `pom.xml` with `testng` | `mvn test` | (JaCoCo plugin) | JaCoCo XML |
| Ruby | RSpec | `.rspec`, `Gemfile` with `rspec` | `bundle exec rspec` | (SimpleCov in spec_helper) | SimpleCov JSON |
| Ruby | Minitest | `Gemfile` with `minitest` | `bundle exec rake test` | (SimpleCov) | SimpleCov JSON |
| PHP | PHPUnit | `phpunit.xml*`, `composer.json` with `phpunit` | `vendor/bin/phpunit` | `--coverage-clover` | Clover XML |
| Elixir | ExUnit | `mix.exs`, `test/` dir | `mix test` | `--cover` | Elixir cover |
| Swift | XCTest | `Package.swift`, `.xcodeproj` | `swift test` / `xcodebuild test` | `--enable-code-coverage` | llvm-cov |
| Kotlin | JUnit | `build.gradle.kts` with `junit` | `gradle test` | (JaCoCo plugin) | JaCoCo XML |

## Script Runner Detection

Also check for script aliases that wrap the test runner:

| File | Key | Example |
|------|-----|---------|
| `package.json` | `"scripts"."test"` | `"test": "vitest run"` |
| `package.json` | `"scripts"."test:unit"` | `"test:unit": "jest --config jest.unit.config.ts"` |
| `package.json` | `"scripts"."test:e2e"` | `"test:e2e": "playwright test"` |
| `Makefile` | `test:` target | `test: pytest -v` |
| `pyproject.toml` | `[tool.pytest.ini_options]` | `addopts = "--cov=src"` |
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
