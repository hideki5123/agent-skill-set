# .NET 10 & C# 14 Knowledge Base

.NET 10 (November 11, 2025) is a **Long-Term Support** release, supported until November 14, 2028. Ships with C# 14 and Visual Studio 2026.

---

## C# 14 Features

### Extension Members (Headline Feature)

Dedicated `extension` block syntax replaces old `static class` pattern. Enables extension **properties**, **operators**, and **static members** — not just methods.

```csharp
public static class Enumerable
{
    // Instance extension members
    extension<TSource>(IEnumerable<TSource> source)
    {
        public bool IsEmpty => !source.Any();

        public IEnumerable<TSource> WhereNot(Func<TSource, bool> predicate)
            => source.Where(x => !predicate(x));
    }

    // Static extension members
    extension<TSource>(IEnumerable<TSource>)
    {
        public static IEnumerable<TSource> Identity => Enumerable.Empty<TSource>();

        public static IEnumerable<TSource> operator +(
            IEnumerable<TSource> left, IEnumerable<TSource> right) => left.Concat(right);
    }
}

// Usage
bool empty = myList.IsEmpty;          // extension property
var id = IEnumerable<int>.Identity;   // static extension
var combined = listA + listB;         // extension operator
```

**Limitation:** No extension fields. Properties must be computed on every access.

### `field` Keyword in Properties

Access compiler-synthesized backing field without declaring it.

```csharp
// Before
private string _msg;
public string Message
{
    get => _msg;
    set => _msg = value ?? throw new ArgumentNullException(nameof(value));
}

// C# 14
public string Message
{
    get;
    set => field = value ?? throw new ArgumentNullException(nameof(value));
}
```

If type has existing `field` symbol, use `@field` or `this.field` to disambiguate.

### Null-Conditional Assignment

`?.` and `?[]` on left side of assignments.

```csharp
customer?.Order = GetCurrentOrder();  // RHS evaluated only if customer != null
customer?.Name += " Jr.";            // compound assignment works too
// NOT supported: customer?.Count++
```

### Unbound Generic Types in `nameof`

```csharp
string name = nameof(List<>);    // "List" — no type argument needed
```

### First-Class Span Support

Implicit conversions between `Span<T>`, `ReadOnlySpan<T>`, and `T[]`. Spans work as extension method receivers and compose with generic type inference.

### Simple Lambda Parameters with Modifiers

```csharp
TryParse<int> parse = (text, out result) => Int32.TryParse(text, out result);
// Previously required explicit types: (string text, out int result) => ...
```

### More Partial Members

**Partial constructors** and **partial events** join partial methods/properties (C# 13).

- Only implementing declaration can have `:this()` / `:base()` initializer
- Implementing declaration of partial event must include `add`/`remove` accessors

### User-Defined Compound Assignment Operators

Custom `+=`, `-=`, `++`, `--` operators.

---

## .NET 10 Runtime

### JIT Improvements

| Improvement | Impact |
|---|---|
| Struct argument code generation | Physical promotion — struct members placed directly into registers |
| Loop inversion | Graph-based loop recognition, better `for`/`while` optimization |
| Array interface devirtualization | Devirtualize + inline `IEnumerable<T>` over arrays |
| Improved code layout | Models as TSP, 3-opt heuristic for near-optimal layout |
| Inlining | Methods with `try-finally`, better profile data, return type refinement |

### Stack Allocation (Escape Analysis)

Dramatically expanded:
- Small arrays of value types AND reference types
- Local struct fields — referenced objects no longer marked escaping
- Delegates (`Func`) that don't outlive scope → stack-allocated

### GC Improvements

- **DATAS enabled by default** — dynamically adjusts heap sizes based on actual memory pressure
- **Arm64 write-barrier improvements** — 8-20%+ GC pause reduction
- **8-12% memory footprint reduction** for many workloads

### NativeAOT

- Startup from ~800ms → under 50ms
- 60-70% memory reduction for typical API apps
- Type preinitializer supports all `conv.*` and `neg` opcodes

---

## .NET 10 Libraries

### Post-Quantum Cryptography (PQC)

FIPS 203/204/205 algorithms:

```csharp
// ML-KEM (Key Encapsulation)
using MLKem key = MLKem.GenerateKey(MLKemAlgorithm.MLKem768);

// ML-DSA (Digital Signatures)
using MLDsa signingKey = MLDsa.ImportFromPem(File.ReadAllText(keyPath));
bool valid = signingKey.VerifyData(data, signature);

// Composite ML-DSA (hybrid classical + PQC)
using var privateKey = CompositeMLDsa.GenerateKey(
    CompositeMLDsaAlgorithm.MLDsa65WithRSA4096Pss);
```

### JSON Serialization Enhancements

```csharp
// Strict mode — best practices by default
JsonSerializerOptions options = JsonSerializerOptions.Strict;

// Disallow duplicate properties
var opts = new JsonSerializerOptions { AllowDuplicateProperties = false };

// PipeReader support — no Stream conversion needed
var result = await JsonSerializer.DeserializeAsync<Person>(pipeReader);
```

### WebSocketStream

Stream-based abstraction over WebSocket:

```csharp
using Stream transport = WebSocketStream.Create(
    connectedWebSocket, WebSocketMessageType.Text, ownsWebSocket: true);
using var reader = new StreamReader(transport, leaveOpen: true);
var line = await reader.ReadLineAsync(ct);
```

### Numeric Ordering for Strings

```csharp
var comparer = StringComparer.Create(
    CultureInfo.CurrentCulture, CompareOptions.NumericOrdering);
// "2" < "10" (numeric, not lexicographic)
```

### Async ZIP APIs

```csharp
await ZipFile.CreateFromDirectoryAsync(sourceDir, destPath);
await ZipFile.ExtractToDirectoryAsync(archivePath, extractDir);
```

### LINQ: LeftJoin / RightJoin

```csharp
var query = students.LeftJoin(
    departments,
    s => s.DepartmentID,
    d => d.ID,
    (s, d) => new { s.FirstName, Department = d.Name ?? "[NONE]" });
```

### OpenTelemetry Improvements

- `ActivitySource` and `Meter` support telemetry schema URLs
- Out-of-proc trace support for events and links
- Rate-limiting trace sampling

---

## ASP.NET Core 10

### Passkey / WebAuthn Authentication

Built-in FIDO2/WebAuthn passkey support in ASP.NET Core Identity — fingerprint, Face ID, hardware keys. Blazor template includes passkey management UI.

### Built-in Minimal API Validation

```csharp
builder.Services.AddValidation();  // Source-generated, AOT-compatible
```

Supports DataAnnotations, `IValidatableObject`, record types.

### Server-Sent Events (SSE)

```csharp
app.MapGet("/heartrate", (CancellationToken ct) =>
{
    async IAsyncEnumerable<HeartRateRecord> Stream(
        [EnumeratorCancellation] CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            yield return new(Random.Shared.Next(60, 100));
            await Task.Delay(2000, ct);
        }
    }
    return TypedResults.ServerSentEvents(Stream(ct), eventType: "heartRate");
});
```

### OpenAPI 3.1

- Full 3.1 with JSON Schema draft 2020-12
- YAML output support
- **Breaking:** `OpenApiAny` replaced with `JsonNode` in transformers
- Build-time document generation

### Memory Pool Eviction

Automatic eviction of unused memory pool entries — reduces pressure in long-running apps.

---

## Blazor 10

### Performance

- `blazor.web.js` **76% size reduction** (183 KB → ~43 KB)
- Framework assets preloaded via `Link` headers
- Client-side static asset fingerprinting

### Declarative State Persistence

```csharp
// Before: ~30 lines with PersistentComponentState
// After:
[PersistentState]
public List<Movie>? MoviesList { get; set; }

protected override async Task OnInitializedAsync()
{
    MoviesList ??= await MovieService.GetMoviesAsync();
}
```

### Circuit State Persistence

Server-side sessions survive tab throttling, mobile app switching, network interruptions.

### Enhanced JS Interop

```csharp
// New methods on IJSRuntime
await js.InvokeConstructorAsync("MyClass", args);  // new MyClass(...)
var val = await js.GetValueAsync<string>("obj.prop");
await js.SetValueAsync("obj.prop", newValue);
```

### Source-Generated Validation

AOT-compatible, supports nested objects and collections:

```csharp
builder.Services.AddValidation();

[ValidatableType]
public class Order
{
    public Customer Customer { get; set; } = new();
    public List<OrderItem> OrderItems { get; set; } = [];
}
```

### NotFoundPage Router Parameter

```razor
<Router AppAssembly="@typeof(Program).Assembly"
        NotFoundPage="typeof(Pages.NotFound)">
```

### Reconnection UI Component

New `ReconnectModal` component — CSP-compliant, no programmatic style injection.

### Metrics and Tracing

Comprehensive observability for component lifecycle, navigation, events, circuits.

---

## EF Core 10

### Vector Search (SQL Server / Azure SQL)

```csharp
public class Blog
{
    [Column(TypeName = "vector(1536)")]
    public SqlVector<float> Embedding { get; set; }
}

var similar = context.Blogs
    .OrderBy(b => EF.Functions.VectorDistance("cosine", b.Embedding, queryVector))
    .Take(3).ToListAsync();
```

### Native JSON Column Type

Auto-uses `json` instead of `nvarchar(max)` when SQL Server 2025 / Azure SQL compatibility level >= 170.

### Named Query Filters

```csharp
modelBuilder.Entity<Blog>()
    .HasQueryFilter("SoftDelete", b => !b.IsDeleted)
    .HasQueryFilter("Tenant", b => b.TenantId == tenantId);

// Selectively disable
var all = await context.Blogs.IgnoreQueryFilters(["SoftDelete"]).ToListAsync();
```

### LeftJoin / RightJoin LINQ Operators

First-class support — replaces verbose `SelectMany` + `GroupJoin` + `DefaultIfEmpty`.

### Improved Collection Translation

Each value gets its own SQL parameter (with padding for plan cache efficiency). Override with `EF.Constant(ids)` or `UseParameterizedCollectionMode`.

### ExecuteUpdateAsync Improvements

- Supports JSON columns via complex types
- Non-expression lambdas — no manual expression tree construction:

```csharp
await context.Blogs.ExecuteUpdateAsync(s =>
{
    s.SetProperty(b => b.Views, 8);
    if (nameChanged) s.SetProperty(b => b.Name, "foo");
});
```

### Complex Types Enhancements

- Optional complex types
- JSON mapping for complex types
- Struct support
- **Recommended over owned entity types** for table splitting and JSON

### Cosmos DB

- Full-text search (`FullTextContains`, `FullTextScore`)
- Hybrid search (RRF combining vector + full-text)
- Vector similarity exits preview

### Security

- Inlined constants **redacted from logs** by default
- **Analyzer warns** about string concatenation in `FromSqlRaw`

---

## MAUI 10

### Deprecations

| Deprecated | Replacement |
|---|---|
| `ListView` | `CollectionView` |
| `TableView` | `CollectionView` |
| `MessagingCenter` | `WeakReferenceMessenger` (CommunityToolkit.Mvvm) |
| `FadeTo`, `RotateTo`, etc. | `FadeToAsync`, `RotateToAsync`, etc. |
| `DisplayAlert` | `DisplayAlertAsync` |

### New Features

- **.NET Aspire integration**
- **HybridWebView**: Request interception, init events, JS exception forwarding
- **MediaPicker**: Multi-file selection, image compression, EXIF handling
- **DatePicker/TimePicker**: Nullable selection
- **XAML Source Generator**: Compile-time strongly-typed XAML code
- **Global XML Namespaces**: Eliminate boilerplate `xmlns:` declarations
- **SafeArea**: Granular `SafeAreaEdges` control
- **Diagnostics**: Layout performance metrics
- **Android**: API 36, JDK 21, `dotnet run`, CoreCLR experimental option

---

## Breaking Changes: .NET 8 → .NET 10

Migration crosses both .NET 9 and .NET 10 changes.

### High-Impact

| Category | Change |
|---|---|
| **Containers** | Default images now Ubuntu (not Debian) |
| **C# 14** | Span implicit conversions may change overload resolution |
| **Libraries** | `System.Linq.AsyncEnumerable` in core — may conflict custom implementations |
| **Libraries** | `BufferedStream.WriteByte` no longer implicit flush |
| **Interop** | Single-file apps don't look for native libs in exe directory |
| **Networking** | HTTP/3 disabled by default with `PublishTrimmed` |
| **Networking** | Streaming HTTP responses enabled by default in browser clients |
| **SDK** | `dotnet new sln` defaults to SLNX format |
| **SDK** | `PackageReference` without version → error |
| **SDK** | `dotnet restore` audits transitive packages |
| **JSON** | Property name conflict checks on by default |
| **JSON** | `XmlSerializer` no longer ignores `[Obsolete]` properties |
| **Crypto** | OpenSSL 1.1.1+ required on Unix |
| **Extensions** | `BackgroundService` runs all of `ExecuteAsync` as Task |
| **Extensions** | Null values preserved in config (was discarded) |
| **ASP.NET** | OpenAPI `OpenApiAny` → `JsonNode` |
| **Blazor** | WASM HTTP response streaming by default |
| **EF Core** | EF tools require `--framework` for multi-target projects |

---

## Migration Path: .NET 8 → .NET 10

### Step 1: Preparation

```bash
# Install .NET 10 SDK
dotnet --list-sdks  # verify 10.0.x present
```

Verify third-party NuGet packages have .NET 10 compatible versions.

### Step 2: Update TFM

```xml
<!-- Before -->
<TargetFramework>net8.0</TargetFramework>
<!-- After -->
<TargetFramework>net10.0</TargetFramework>
```

### Step 3: Update Packages

```bash
dotnet list package --outdated
```

Update all `Microsoft.AspNetCore.*`, `Microsoft.EntityFrameworkCore.*`, `Microsoft.Extensions.*` to 10.0.x.

### Step 4: Upgrade Assistant (Optional)

```bash
dotnet tool install -g upgrade-assistant
upgrade-assistant upgrade MyProject.csproj
```

### Step 5: Address Breaking Changes

Key areas:
- **JSON**: Property name conflict checks, `Strict` mode
- **Containers**: Ubuntu base images
- **SDK**: SLNX default, `PackageReference` requires version
- **EF Core**: `--framework` flag for multi-target
- **OpenAPI**: `OpenApiAny` → `JsonNode`
- **Blazor WASM**: Returns `BrowserHttpReadStream`, not `MemoryStream`

### Step 6: Opt Into New Features

- C# 14 features (automatic with `net10.0`)
- `[PersistentState]` for Blazor
- Named query filters in EF Core
- Passkey authentication
- `AddValidation()` for Minimal API
- `JsonSerializerOptions.Strict`

### Step 7: Test

- Full test suite
- GC behavior under load (DATAS enabled by default)
- EF Core migration generation
- Blazor reconnection and not-found routing

### Timeline

.NET 8 support ends **November 10, 2026**. Begin testing Q3 2025, complete migration by mid-2026.

---

## Senior Best Practices for .NET 10

1. **Extension members** for cleaner API surfaces — extension properties eliminate helper methods
2. **`field` keyword** in property accessors — reduce backing field boilerplate
3. **Null-conditional assignment** for null-safe mutation chains
4. **`[PersistentState]`** in Blazor — eliminates 30+ lines of state persistence boilerplate
5. **Named query filters** in EF Core — selective `IgnoreQueryFilters` instead of all-or-nothing
6. **Vector search** in EF Core for RAG / AI scenarios
7. **`AddValidation()`** for AOT-compatible Minimal API validation
8. **Post-quantum cryptography** for forward-looking security
9. **DATAS GC** — monitor and tune for your workload's memory profile
10. **Passkey auth** — adopt WebAuthn for modern passwordless auth
