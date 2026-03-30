# .NET 8 LTS & C# 12 Knowledge Base

.NET 8 (November 2023) is the current Long-Term Support release, supported until November 2026. Ships with C# 12.

## C# 12 Features

### Primary Constructors for Classes and Structs

Available on any `class` or `struct` (previously `record` only). Parameters are in scope for the entire body but are NOT auto-promoted to properties.

```csharp
public class UserService(ILogger<UserService> logger, IUserRepository repo)
{
    public User? GetById(int id)
    {
        logger.LogInformation("Fetching user {Id}", id);
        return repo.Find(id);
    }
}
```

**Rules:**
- Parameters are parameters, not members — cannot access via `this.param`
- No parameterless constructor generated when primary constructor exists (classes)
- Every explicit constructor must chain via `this()`

### Collection Expressions

Unified syntax for arrays, lists, spans. Spread operator `..` inlines elements.

```csharp
int[] a = [1, 2, 3, 4, 5];
List<string> names = ["Alice", "Bob"];
Span<char> vowels = ['a', 'e', 'i', 'o', 'u'];

// Spread
int[] first = [1, 2, 3];
int[] second = [4, 5, 6];
int[] combined = [.. first, .. second];

// Empty
List<int> empty = [];
```

Compiler chooses optimal backing storage. For `Span<T>`, may use `stackalloc`.

### Inline Arrays

Fixed-size array inside a `struct`, safe alternative to `unsafe` fixed buffers.

```csharp
[System.Runtime.CompilerServices.InlineArray(10)]
public struct TenIntBuffer
{
    private int _element0;
}
```

Primarily consumed as `Span<T>` from runtime APIs.

### Default Lambda Parameters

```csharp
var greet = (string name = "World") => $"Hello, {name}!";
greet();        // "Hello, World!"
greet("Alice"); // "Hello, Alice!"
```

### Alias Any Type

`using` alias now works with tuples, arrays, generics — not just named types.

```csharp
using Point = (double X, double Y);
using StringMap = System.Collections.Generic.Dictionary<string, string>;

Point origin = (0.0, 0.0);
```

### Experimental Attribute

Signal unstable APIs. Compiler emits diagnostic for callers.

```csharp
[Experimental("MYLIB001")]
public class BetaFeature { }
```

### ref readonly Parameters

Signals caller must pass by reference, callee won't modify. Fills gap between `ref` and `in`.

---

## .NET 8 Runtime

### Native AOT

First-class Native AOT for ASP.NET Core (Minimal APIs, gRPC, Worker Services).

```xml
<PropertyGroup>
  <PublishAot>true</PublishAot>
</PropertyGroup>
```

- **`CreateSlimBuilder()`** — minimal builder, omits HTTPS/HTTP3, smaller binaries
- **`CreateEmptyBuilder()`** — zero built-in behavior, ~8.5 MB Linux x64
- **Request Delegate Generator** — source generator using C# 12 interceptors, zero-overhead startup
- **MVC/Razor Pages NOT AOT-compatible** in .NET 8

```csharp
// AOT-compatible JSON
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.TypeInfoResolverChain
        .Insert(0, AppJsonSerializerContext.Default);
});

[JsonSerializable(typeof(Todo[]))]
internal partial class AppJsonSerializerContext : JsonSerializerContext { }
```

### Frozen Collections

`FrozenDictionary<K,V>` and `FrozenSet<T>` — immutable, read-optimized. High creation cost, ~40% faster lookups than `Dictionary`.

```csharp
using System.Collections.Frozen;

private static readonly FrozenDictionary<string, bool> s_config =
    LoadConfig().ToFrozenDictionary();
```

Ideal for app-lifetime caches initialized at startup.

### Time Abstraction (TimeProvider)

Testable time abstraction replacing `DateTime.UtcNow`.

```csharp
public class AuctionService(TimeProvider clock)
{
    public bool IsExpired(Auction auction)
        => clock.GetUtcNow() > auction.EndsAt;
}

// Test with FakeTimeProvider from Microsoft.Extensions.Time.Testing
```

Integrated with `Task.Delay`, `Task.WaitAsync`, `CancellationTokenSource`.

### Keyed Dependency Injection

Register and resolve services by key.

```csharp
builder.Services.AddKeyedSingleton<ICache, BigCache>("big");
builder.Services.AddKeyedSingleton<ICache, SmallCache>("small");

class OrderService([FromKeyedServices("big")] ICache cache) { }
```

### IHostedLifecycleService

Six lifecycle hooks: `StartingAsync` → `StartAsync` → `StartedAsync` → `StoppingAsync` → `StopAsync` → `StoppedAsync`.

```csharp
public class MigrationService : IHostedLifecycleService
{
    public Task StartingAsync(CancellationToken ct)
        => RunMigrationsAsync(ct); // Before StartAsync
    // ... implement other hooks
}
```

---

## ASP.NET Core 8

### Minimal API Improvements

**Form binding:**
```csharp
app.MapPost("/upload", async ([FromForm] FileUploadRequest req) =>
{
    await ProcessUploadAsync(req);
    return Results.Ok();
});
```

**Typed results:**
```csharp
app.MapGet("/todos/{id}", Results<Ok<Todo>, NotFound> (int id, TodoDb db) =>
    db.Find(id) is Todo todo ? TypedResults.Ok(todo) : TypedResults.NotFound());
```

**Antiforgery built in:**
```csharp
builder.Services.AddAntiforgery();
app.UseAntiforgery();
```

### Short-Circuit Routing

Skip middleware pipeline entirely for specific endpoints:

```csharp
app.MapGet("/health", () => "OK").ShortCircuit();
app.MapShortCircuit(404, "robots.txt", "favicon.ico");
```

Incompatible with `[Authorize]` or `[RequireCors]`.

### Identity API Endpoints

JSON API endpoints for `/register` and `/login`:

```csharp
builder.Services.AddIdentityApiEndpoints<IdentityUser>()
    .AddEntityFrameworkStores<AppDbContext>();
app.MapIdentityApi<IdentityUser>();
```

### Output Caching Enhancements

Redis-backed distributed cache, ETag revalidation, tag-based eviction, locking control.

```csharp
builder.Services.AddOutputCache(options =>
{
    options.AddBasePolicy(p => p.Expire(TimeSpan.FromMinutes(5)));
    options.AddPolicy("NoLock", p => p.SetLocking(false));
});
app.MapGet("/data", () => GetData()).CacheOutput();
```

### Rate Limiting

Built-in: Fixed Window, Sliding Window, Token Bucket, Concurrency.

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.AddFixedWindowLimiter("fixed", opt =>
    {
        opt.PermitLimit = 10;
        opt.Window = TimeSpan.FromSeconds(10);
    });
});
app.MapGet("/api/data", GetData).RequireRateLimiting("fixed");
```

Partitioned by IP, user, API key:

```csharp
options.GlobalLimiter = PartitionedRateLimiter
    .Create<HttpContext, string>(ctx =>
        RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: ctx.Connection.RemoteIpAddress?.ToString() ?? "unknown",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = 50, Window = TimeSpan.FromMinutes(1)
            }));
```

---

## EF Core 8

### Complex Types (Value Objects)

Map value objects inline in parent table. No identity, value equality.

```csharp
[ComplexType]
public class Address
{
    public required string Line1 { get; set; }
    public required string City { get; set; }
    public required string Country { get; set; }
    public required string PostCode { get; set; }
}
```

### Primitive Collections

`List<string>`, `int[]` etc. map to JSON columns automatically.

```csharp
public class Product
{
    public int Id { get; set; }
    public List<string> Tags { get; set; } = [];
}

var tagged = await context.Products
    .Where(p => p.Tags.Contains("sale"))
    .ToListAsync();
```

### Raw SQL for Unmapped Types

`SqlQuery<T>` returns any CLR type, composable with LINQ.

```csharp
var summaries = await context.Database
    .SqlQuery<PostSummary>(
        $"SELECT b.Name AS BlogName, p.Title FROM Posts p JOIN Blogs b ON p.BlogId = b.Id WHERE p.PublishedOn >= {start}")
    .Where(s => s.PublishedOn < end)
    .ToListAsync();
```

### HierarchyId Support

First-class `hierarchyid` for SQL Server.

```csharp
options.UseSqlServer(connStr, x => x.UseHierarchyId());
```

### Sentinel Values

Configure a non-default sentinel to mean "use database default":

```csharp
modelBuilder.Entity<Course>()
    .Property(e => e.Credits)
    .HasDefaultValueSql("10")
    .HasSentinel(-1);
```

### Lazy Loading Improvements

- No-tracking lazy loading
- Per-navigation opt-out: `.EnableLazyLoading(false)`

---

## Blazor 8

### Render Modes

| Mode | Location | Interactive | Description |
|------|----------|-------------|-------------|
| Static Server | Server | No | Static SSR — fast initial load |
| Interactive Server | Server | Yes | SignalR (Blazor Server) |
| Interactive WebAssembly | Client | Yes | WASM with prerender |
| Interactive Auto | Server→Client | Yes | Server first, then WASM |

```razor
@page "/dashboard"
@rendermode InteractiveAuto
```

### Streaming Rendering

Render placeholder, stream updates when async completes.

```razor
@attribute [StreamRendering(true)]

@if (data is null) { <p>Loading...</p> }
else { <DataGrid Items="@data" /> }
```

### Sections

Define outlets in layouts, fill from child pages.

```razor
@* Layout *@
<SectionOutlet SectionId="TopbarSection" />

@* Page *@
<SectionContent SectionId="MainLayout.TopbarSection">
    <button @onclick="DoAction">Action</button>
</SectionContent>
```

### Enhanced Navigation

Static SSR pages get SPA-like behavior — Blazor intercepts links and forms, patches DOM.

### QuickGrid

Production-ready data grid with sorting, filtering, paging, virtualization.

```razor
<QuickGrid Items="@people" Pagination="@pagination">
    <PropertyColumn Property="@(p => p.Name)" Sortable="true" />
    <TemplateColumn Title="Actions">
        <button @onclick="() => Edit(context)">Edit</button>
    </TemplateColumn>
</QuickGrid>
```

---

## Performance APIs

### SearchValues\<T\>

Pre-computed optimized search for repeated char/byte searches.

```csharp
private static readonly SearchValues<char> s_vowels =
    SearchValues.Create("aeiouAEIOU");

public static int CountVowels(ReadOnlySpan<char> text)
{
    int count = 0;
    int idx;
    while ((idx = text.IndexOfAny(s_vowels)) >= 0)
    {
        count++;
        text = text[(idx + 1)..];
    }
    return count;
}
```

### CompositeFormat

Pre-parse runtime-loaded format strings for faster formatting.

```csharp
private static readonly CompositeFormat s_msg =
    CompositeFormat.Parse(LoadFromResources("RangeMessage"));

string result = string.Format(CultureInfo.InvariantCulture, s_msg, min, max);
```

### Serialization

- `JsonStringEnumConverter<TEnum>` — AOT-compatible
- Source generator parity: `required`, `init`, nested contexts
- `TypeInfoResolverChain` — compose multiple `JsonSerializerContext`

---

## MAUI 8

### Keyboard Accelerators

```csharp
menuItem.KeyboardAccelerators.Add(new KeyboardAccelerator
{
    Modifiers = KeyboardAcceleratorModifiers.Ctrl, Key = "X"
});
```

### Handler Disconnection

Control native handler cleanup lifecycle.

```xml
<controls:Video HandlerProperties.DisconnectPolicy="Manual" />
```

### Other Improvements

- Inline media in WebView on iOS
- `Grid.AddWithSpan` extension
- `HideSoftInputOnTapped` for iOS/Android
- Gesture recognizer improvements

---

## Senior Best Practices for .NET 8

1. **Primary constructors** for DI — eliminates boilerplate, but assign to fields when mutation matters
2. **Collection expressions** `[1, 2, 3]` as default syntax for all collection init
3. **FrozenDictionary/FrozenSet** for read-heavy, write-once data (config, lookup tables)
4. **TimeProvider** over `DateTime.UtcNow` for testable time
5. **Keyed DI** over factory patterns for multi-implementation scenarios
6. **Native AOT** for microservices/serverless — use `CreateSlimBuilder()` + JSON source generators
7. **IHostedLifecycleService** for pre-start hooks (migrations, cache warmup)
8. **Blazor render modes** strategically — Static SSR for content, Interactive Auto for UX
9. **SearchValues<T>** for hot-path string searching
10. **ComplexType** over owned entities for true value objects
