# Selector Strategy Reference

Priority order for choosing Playwright locators. Always prefer higher-priority locators
as they are more resilient to UI changes.

## Priority Order

| Priority | Locator | When to Use |
|----------|---------|-------------|
| 1 | `getByRole` | Interactive elements with accessible roles (buttons, links, headings, textboxes, checkboxes) |
| 2 | `getByText` | Static text content, labels, messages |
| 3 | `getByLabel` | Form inputs associated with a `<label>` |
| 4 | `getByPlaceholder` | Inputs with placeholder text (when no label exists) |
| 5 | `getByTestId` | Elements with `data-testid` attributes (stable but requires dev cooperation) |
| 6 | CSS class/ID | Last resort — fragile, changes with styling |
| 7 | XPath / nth-child | Avoid — extremely brittle |

## Transformation Examples

### Buttons

```typescript
// Bad (codegen output)
page.locator('button.btn-primary')
page.locator('#submit-btn')
page.locator('form > div:nth-child(3) > button')

// Good
page.getByRole('button', { name: 'Submit' })
page.getByRole('button', { name: /submit/i })      // case-insensitive
```

### Links

```typescript
// Bad
page.locator('a.nav-link')
page.locator('a[href="/about"]')

// Good
page.getByRole('link', { name: 'About Us' })
```

### Headings

```typescript
// Bad
page.locator('h1.page-title')
page.locator('.header-text')

// Good
page.getByRole('heading', { name: 'Dashboard' })
page.getByRole('heading', { level: 1 })
```

### Form inputs

```typescript
// Bad
page.locator('#email')
page.locator('input[type="email"]')

// Good
page.getByLabel('Email address')
page.getByPlaceholder('Enter your email')
```

### Checkboxes and radios

```typescript
// Bad
page.locator('input[type="checkbox"]').first()

// Good
page.getByRole('checkbox', { name: 'Remember me' })
page.getByLabel('Remember me')
```

## Chaining and Filtering

When a single locator is ambiguous, chain or filter:

```typescript
// Filter within a section
page.getByRole('listitem').filter({ hasText: 'Product A' })

// Chain locators
page.getByRole('navigation').getByRole('link', { name: 'Home' })

// Filter by child element
page.getByRole('listitem').filter({ has: page.getByRole('button', { name: 'Buy' }) })
```

## Exact vs Substring Matching

```typescript
// Exact match (default for getByRole name)
page.getByRole('button', { name: 'Submit', exact: true })

// Substring / regex
page.getByText(/welcome/i)
page.getByRole('heading', { name: /dashboard/i })
```

## Common Codegen Patterns to Replace

| Codegen Output | Replacement |
|---------------|-------------|
| `page.locator('#id')` | `page.getByLabel(...)` or `page.getByRole(...)` |
| `page.locator('.class')` | `page.getByRole(...)` or `page.getByText(...)` |
| `page.locator('tag.class')` | `page.getByRole(...)` |
| `page.locator('div:nth-child(n)')` | `page.getByRole(...).filter(...)` |
| `page.locator('xpath=...')` | Any of the above |
| `page.locator('[data-testid="x"]')` | `page.getByTestId('x')` |
