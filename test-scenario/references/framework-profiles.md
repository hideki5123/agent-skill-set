# Framework Profiles

Detection logic and syntax mappings for each supported test framework.

## Framework Detection

Scan the project in this order. Stop at the first match unless `--framework` overrides.

### .NET Detection

Search for `.csproj` or `.fsproj` files, then check PackageReference elements:

| Package pattern | Framework |
|----------------|-----------|
| `xunit` or `xunit.v3` | xUnit |
| `NUnit` or `NUnit3TestAdapter` | NUnit |
| `MSTest.TestFramework` or `Microsoft.VisualStudio.TestPlatform` | MSTest |

If multiple test frameworks are referenced in different projects, ask the user which one to target.

### Python Detection

| File / section | Framework |
|---------------|-----------|
| `pyproject.toml` with `[tool.pytest]` or `[project.optional-dependencies]` containing `pytest` | pytest |
| `pytest.ini` exists | pytest |
| `setup.cfg` with `[tool:pytest]` | pytest |
| `conftest.py` exists in project root or test directory | pytest |

### TypeScript Detection

| File | Framework |
|------|-----------|
| `vitest.config.ts` / `vitest.config.js` / `vitest.config.mts` | Vitest |
| `vite.config.*` with `test` section | Vitest |
| `jest.config.ts` / `jest.config.js` / `jest.config.mjs` | Jest |
| `package.json` with `"jest"` config key | Jest |

If no config found, check `package.json` devDependencies for `vitest` or `jest`.

## Syntax Mapping

### xUnit (.NET)

| Aspect | Syntax |
|--------|--------|
| Test class | `public class XxxTests : IAsyncLifetime` |
| Test method | `[Fact]` / `[Theory]` with `[InlineData]` or `[MemberData]` |
| TODO marker | `[Fact(Skip = "TODO")]` or `[Theory(Skip = "TODO")]` |
| Display name | `[Fact(DisplayName = "...")]` |
| Setup | `public async Task InitializeAsync()` (from `IAsyncLifetime`) |
| Cleanup | `public async Task DisposeAsync()` (from `IAsyncLifetime`) |
| Grouping | Nested classes or `[Collection]` |
| Assertions | `Assert.Equal()`, `Assert.Throws<T>()`, or FluentAssertions (`actual.Should().Be()`) |
| Runner | `dotnet test --filter "FullyQualifiedName~XxxTests"` |

### NUnit (.NET)

| Aspect | Syntax |
|--------|--------|
| Test class | `[TestFixture] public class XxxTests` |
| Test method | `[Test]` / `[TestCase(...)]` |
| TODO marker | `[Test, Ignore("TODO")]` |
| Display name | `[Test, Description("...")]` |
| Setup | `[SetUp] public async Task SetUp()` |
| Cleanup | `[TearDown] public async Task TearDown()` |
| Grouping | `[TestFixture]` classes with `[Category]` |
| Assertions | `Assert.That(actual, Is.EqualTo(expected))` or `Assert.Throws<T>()` |
| Runner | `dotnet test --filter "TestCategory=Xxx"` |

### MSTest (.NET)

| Aspect | Syntax |
|--------|--------|
| Test class | `[TestClass] public class XxxTests` |
| Test method | `[TestMethod]` / `[DataTestMethod]` with `[DataRow]` |
| TODO marker | `[TestMethod, Ignore("TODO")]` or `[Ignore]` |
| Display name | `[TestMethod("...")]` |
| Setup | `[TestInitialize] public async Task Initialize()` |
| Cleanup | `[TestCleanup] public async Task Cleanup()` |
| Grouping | `[TestClass]` with `[TestCategory]` |
| Assertions | `Assert.AreEqual(expected, actual)`, `Assert.ThrowsException<T>()` |
| Runner | `dotnet test --filter "TestCategory=Xxx"` |

### pytest (Python)

| Aspect | Syntax |
|--------|--------|
| Test module | `test_xxx.py` |
| Test function | `def test_xxx():` or `async def test_xxx():` |
| Test class | `class TestXxx:` (no inheritance needed) |
| TODO marker | `@pytest.mark.skip(reason="TODO")` above the function |
| Display name | Function name itself, or `@pytest.mark.parametrize` |
| Setup | `@pytest.fixture(autouse=True)` in conftest or test module |
| Cleanup | `yield` inside fixture (code after yield runs as cleanup) |
| Grouping | Classes, modules, or `@pytest.mark.xxx` markers |
| Assertions | `assert actual == expected`, `with pytest.raises(XxxError):` |
| Runner | `pytest test_xxx.py -v` or `pytest -k "test_xxx"` |

### Vitest (TypeScript)

| Aspect | Syntax |
|--------|--------|
| Test file | `xxx.test.ts` / `xxx.spec.ts` |
| Test function | `it("description", () => { ... })` |
| Grouping | `describe("context", () => { ... })` |
| TODO marker | `it.todo("description")` |
| Setup | `beforeEach(() => { ... })` |
| Cleanup | `onTestFinished(() => { ... })` inside `beforeEach` |
| Assertions | `expect(actual).toBe(expected)`, `expect(() => fn()).toThrow()` |
| Runner | `npx vitest run xxx.test.ts` |

### Jest (TypeScript)

| Aspect | Syntax |
|--------|--------|
| Test file | `xxx.test.ts` / `xxx.spec.ts` |
| Test function | `it("description", () => { ... })` |
| Grouping | `describe("context", () => { ... })` |
| TODO marker | `it.todo("description")` |
| Setup | `beforeEach(() => { ... })` |
| Cleanup | `afterEach(() => { ... })` in the same `describe` |
| Assertions | `expect(actual).toBe(expected)`, `expect(() => fn()).toThrow()` |
| Runner | `npx jest xxx.test.ts` |

## Language Auto-Detection for Test Names

To determine `--lang` when not specified:

1. Check existing test files in the project for Japanese characters in test names
2. Check if `.editorconfig` or project docs indicate a primary language
3. Default to `en` if no signal found
