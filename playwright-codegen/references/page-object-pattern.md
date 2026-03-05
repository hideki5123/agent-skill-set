# Page Object Pattern Reference

When and how to extract page objects from Playwright tests.

## When to Use

- **3+ tests** interact with the same page
- **Complex forms** with many fields and validation states
- **Reusable flows** shared across test files (e.g., login, checkout)
- **Page has 10+ interactive elements** that tests reference

Do NOT extract a page object for simple, one-off tests. Premature abstraction
adds complexity without value.

## Class Template

```typescript
// tests/pages/login.page.ts
import { type Locator, type Page, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Log in' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message: string) {
    await expect(this.errorMessage).toHaveText(message);
  }
}
```

## Usage in Tests

```typescript
// tests/login.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/login.page';

test.describe('Login', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('should log in with valid credentials', async ({ page }) => {
    await loginPage.login('user@test.com', 'password');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should show error for invalid password', async () => {
    await loginPage.login('user@test.com', 'wrong');
    await loginPage.expectError('Invalid credentials');
  });
});
```

## File Organization

```
tests/
  pages/
    login.page.ts
    checkout.page.ts
    dashboard.page.ts
  login.spec.ts
  checkout.spec.ts
  dashboard.spec.ts
```

## Guidelines

- Define locators in the constructor, not in methods
- Action methods should perform a single user-meaningful action (e.g., `login`, `addToCart`)
- Assertion helper methods are optional — only add for frequently repeated checks
- Page objects should NOT contain test logic (`test()`, `test.describe()`)
- Keep page objects focused — one class per page or major component
