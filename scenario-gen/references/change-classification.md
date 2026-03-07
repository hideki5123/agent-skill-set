# Change Classification Rules

Classify each changed file into one or more categories using the signals below. A file may belong to multiple categories (e.g., `src/api/routes/users.tsx` is both **api** and **frontend**).

## Frontend

**Extensions**: `.tsx`, `.jsx`, `.vue`, `.svelte`, `.html`, `.css`, `.scss`, `.less`, `.sass`, `.styl`

**Path patterns**:
- `components/`, `pages/`, `views/`, `layouts/`, `screens/`
- `public/`, `static/`, `assets/` (non-config assets)
- `styles/`, `themes/`, `css/`
- `src/app/` (Next.js, Angular app directories)
- `src/routes/` (SvelteKit, Remix)

**Import signals** (in file content):
- React: `import React`, `from 'react'`, `useState`, `useEffect`
- Vue: `<template>`, `<script setup>`, `defineComponent`
- Angular: `@Component`, `@NgModule`
- Svelte: `<script>`, `$:` reactive declarations
- CSS-in-JS: `styled.`, `css\``, `makeStyles`

## API

**Path patterns**:
- `routes/`, `controllers/`, `handlers/`, `api/`, `endpoints/`
- `graphql/`, `resolvers/`, `schema/`

**File name patterns**:
- `*.controller.*`, `*.route.*`, `*.handler.*`, `*.resolver.*`
- `swagger.*`, `openapi.*`, `*.api.*`

**Content signals**:
- HTTP method decorators: `@Get`, `@Post`, `@Put`, `@Delete`, `app.get(`, `router.post(`
- Express/Fastify/Koa route definitions
- GraphQL type definitions, resolvers

## Backend

**Path patterns**:
- `services/`, `models/`, `repositories/`, `utils/`, `lib/`, `helpers/`
- `middleware/`, `plugins/`, `providers/`
- `database/`, `db/`, `migrations/`, `seeds/`, `fixtures/`
- `queues/`, `workers/`, `jobs/`, `tasks/`, `cron/`

**File name patterns**:
- `*.service.*`, `*.model.*`, `*.repository.*`, `*.entity.*`
- `*.migration.*`, `*.seed.*`
- `*.middleware.*`, `*.guard.*`, `*.interceptor.*`

## Config

**Dot files**: `.env*`, `.eslintrc*`, `.prettierrc*`, `.babelrc*`, `.editorconfig`

**Config files**:
- `*config*`, `*settings*` (e.g., `webpack.config.js`, `tsconfig.json`)
- `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`
- `go.mod`, `go.sum`, `Cargo.toml`, `Cargo.lock`
- `Dockerfile`, `docker-compose.*`, `Makefile`, `Procfile`

**CI/CD**: `.github/workflows/`, `.gitlab-ci.yml`, `.circleci/`, `Jenkinsfile`, `azure-pipelines.yml`

## Test

**Path patterns**: `test/`, `tests/`, `__tests__/`, `spec/`, `e2e/`, `integration/`, `cypress/`, `playwright/`

**File name patterns**: `*.test.*`, `*.spec.*`, `test_*.*`, `*_test.*`

**Config**: `jest.config.*`, `vitest.config.*`, `playwright.config.*`, `cypress.config.*`

## Docs

**Extensions**: `.md`, `.mdx`, `.txt`, `.rst`, `.adoc`

**Path patterns**: `docs/`, `documentation/`, `wiki/`

**File names**: `README*`, `CHANGELOG*`, `CONTRIBUTING*`, `LICENSE*`, `ARCHITECTURE*`

## Classification Priority

When a file matches multiple categories, assign all matching categories. For scenario generation:
1. **frontend** files get UI interaction scenarios + screenshots
2. **api** files get request/response scenarios
3. **backend** files get data flow scenarios
4. **config** files get impact verification scenarios
5. **test** files are noted but do not generate new scenarios (they ARE scenarios)
6. **docs** files are noted but typically do not generate scenarios
