# Test Patterns Reference

Canonical patterns for structuring Playwright tests. Use these when transforming raw
codegen output into production-quality test suites.

## Test File Skeleton

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/start-page');
  });

  test('should perform expected behavior', async ({ page }) => {
    // Arrange — set up preconditions (if any beyond beforeEach)

    // Act — perform the user action
    await page.getByRole('button', { name: 'Submit' }).click();

    // Assert — verify the outcome
    await expect(page).toHaveURL('/success');
    await expect(page.getByText('Submitted successfully')).toBeVisible();
  });
});
```

## Assertion Catalog

### Page-level assertions

```typescript
await expect(page).toHaveURL('/dashboard');
await expect(page).toHaveURL(/\/dashboard/);       // regex
await expect(page).toHaveTitle('Dashboard');
await expect(page).toHaveTitle(/Dashboard/);        // regex
```

### Visibility and presence

```typescript
await expect(locator).toBeVisible();
await expect(locator).toBeHidden();
await expect(locator).toBeAttached();               // in DOM but maybe not visible
await expect(locator).not.toBeVisible();
```

### Text content

```typescript
await expect(locator).toHaveText('Exact text');
await expect(locator).toHaveText(/partial/i);       // regex, case-insensitive
await expect(locator).toContainText('substring');
```

### Element count

```typescript
await expect(page.getByRole('listitem')).toHaveCount(5);
```

### Input state

```typescript
await expect(page.getByLabel('Email')).toHaveValue('user@example.com');
await expect(page.getByLabel('Email')).toHaveValue(/user@/);
await expect(page.getByRole('checkbox')).toBeChecked();
await expect(page.getByRole('textbox')).toBeEditable();
await expect(page.getByRole('button')).toBeEnabled();
await expect(page.getByRole('button')).toBeDisabled();
```

### CSS and attributes

```typescript
await expect(locator).toHaveClass(/active/);
await expect(locator).toHaveCSS('color', 'rgb(0, 128, 0)');
await expect(locator).toHaveAttribute('href', '/about');
```

### Visual comparison (screenshot)

```typescript
await expect(page).toHaveScreenshot();                        // full page
await expect(page).toHaveScreenshot('homepage.png');           // named
await expect(locator).toHaveScreenshot('component.png');       // element only
```

## Soft Assertions

Soft assertions collect all failures without stopping the test:

```typescript
test('check multiple things', async ({ page }) => {
  await expect.soft(page.getByText('Title')).toBeVisible();
  await expect.soft(page.getByText('Subtitle')).toBeVisible();
  await expect.soft(page.getByRole('button')).toBeEnabled();
  // Test continues even if some assertions fail
});
```

## Tagged Tests

```typescript
test.describe('Checkout', { tag: '@smoke' }, () => {
  test('should complete purchase', async ({ page }) => {
    // ...
  });
});

// Run only smoke tests:
// npx playwright test --grep @smoke
```

## Parameterized Tests

```typescript
const users = [
  { name: 'admin', expected: '/admin' },
  { name: 'viewer', expected: '/dashboard' },
];

for (const user of users) {
  test(`should redirect ${user.name} to ${user.expected}`, async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Username').fill(user.name);
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL(user.expected);
  });
}
```

## Before / After Example: Raw Codegen to Structured Test

### Raw codegen output

```typescript
import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('https://example.com/login');
  await page.locator('#email').click();
  await page.locator('#email').fill('user@test.com');
  await page.locator('#password').click();
  await page.locator('#password').fill('secret');
  await page.locator('button.btn-primary').click();
  await page.locator('.dashboard-header').click();
});
```

### After enhancement

```typescript
import { test, expect } from '@playwright/test';

test.describe('Login', () => {
  test('should log in and reach the dashboard', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel('Email').fill('user@test.com');
    await page.getByLabel('Password').fill('secret');
    await page.getByRole('button', { name: 'Log in' }).click();

    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });
});
```

**Changes made:**
- Removed redundant `.click()` before `.fill()` (fill auto-focuses)
- Replaced CSS selectors (`#email`, `.btn-primary`) with semantic locators
- Added `test.describe` wrapper
- Added descriptive test name
- Used `baseURL`-relative paths
- Added URL and visibility assertions
- Removed meaningless click on `.dashboard-header`
