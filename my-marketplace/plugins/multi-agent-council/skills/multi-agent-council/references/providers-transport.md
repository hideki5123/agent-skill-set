# Providers and Transport Reference

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Council Orchestrator                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Claude  │    │  OpenAI  │    │  Gemini  │
    │ Adapter  │    │ Adapter  │    │ Adapter  │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
              ┌─────────────────────┐
              │   Auto Transport    │
              │   (MCP → CLI)       │
              └──────────┬──────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        ┌───────────┐        ┌───────────┐
        │    MCP    │        │    CLI    │
        │ Transport │        │ Transport │
        └───────────┘        └───────────┘
```

## Provider Adapters

### Base Adapter Interface

```typescript
interface ProviderAdapter {
  // Identity
  readonly name: string;
  readonly supportedModels: string[];
  readonly defaultModel: string;

  // Capabilities
  readonly capabilities: ProviderCapabilities;

  // Operations
  query(request: ProviderRequest): Promise<ProviderResponse>;
  parseResponse(raw: any): CouncilOpinion | CouncilReview;
  buildPrompt(context: RoundContext): ProviderPrompt;
}

interface ProviderCapabilities {
  maxContextTokens: number;
  maxOutputTokens: number;
  supportsSystemMessage: boolean;
  supportsStreaming: boolean;
  supportsFunctionCalling: boolean;
}

interface ProviderPrompt {
  system?: string;
  messages: Message[];
  maxTokens: number;
  temperature: number;
}
```

### ClaudeAdapter

```typescript
class ClaudeAdapter implements ProviderAdapter {
  name = "claude";
  supportedModels = [
    "claude-sonnet-4-20250514",
    "claude-opus-4-5-20250514",
    "claude-3-5-haiku-20241022"
  ];
  defaultModel = "claude-sonnet-4-20250514";

  capabilities = {
    maxContextTokens: 200000,
    maxOutputTokens: 8192,
    supportsSystemMessage: true,
    supportsStreaming: true,
    supportsFunctionCalling: true
  };

  // Special role: Can act as Chair
  canActAsChair = true;
}
```

**Claude-Specific Considerations**:
- Preferred for Chair role due to integration
- Can use extended thinking for complex synthesis
- Native integration (no external transport needed for Chair)

### OpenAIAdapter

```typescript
class OpenAIAdapter implements ProviderAdapter {
  name = "openai";
  supportedModels = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "o1-preview",
    "o1-mini"
  ];
  defaultModel = "gpt-4o";

  capabilities = {
    maxContextTokens: 128000,
    maxOutputTokens: 4096,
    supportsSystemMessage: true,
    supportsStreaming: true,
    supportsFunctionCalling: true
  };
}
```

**OpenAI-Specific Considerations**:
- o1 models have different prompting requirements
- Rate limits vary by model/tier
- Function calling format differs slightly

### GeminiAdapter

```typescript
class GeminiAdapter implements ProviderAdapter {
  name = "gemini";
  supportedModels = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-thinking",
    "gemini-1.5-pro",
    "gemini-1.5-flash"
  ];
  defaultModel = "gemini-2.0-flash";

  capabilities = {
    maxContextTokens: 1000000,  // 1M for some models
    maxOutputTokens: 8192,
    supportsSystemMessage: true,
    supportsStreaming: true,
    supportsFunctionCalling: true
  };
}
```

**Gemini-Specific Considerations**:
- Very large context window
- Thinking models have different behavior
- Google Cloud vs AI Studio authentication

### Adding New Providers

To add a new provider:

1. Implement `ProviderAdapter` interface
2. Register in `ProviderRegistry`
3. Add transport mappings
4. Update default configuration

```typescript
// Example: Anthropic Claude via API (external)
class ExternalClaudeAdapter implements ProviderAdapter {
  name = "claude-external";
  // ... implementation
}

// Register
providerRegistry.register(new ExternalClaudeAdapter());
```

## Transport Layer

### Transport Interface

```typescript
interface Transport {
  readonly type: "mcp" | "cli";

  send(request: TransportRequest): Promise<TransportResult>;
  isAvailable(): Promise<boolean>;
  getStatus(): TransportStatus;
}

interface TransportRequest {
  provider: string;
  model: string;
  payload: {
    system?: string;
    messages: Message[];
    max_tokens: number;
    temperature: number;
  };
  timeout_ms: number;
}

interface TransportResult {
  status: "ok" | "error";
  content?: string;
  usage?: TokenUsage;
  error?: TransportError;
  latency_ms: number;
}

interface TransportError {
  type: "auth" | "network" | "timeout" | "rate_limit" | "invalid_request";
  message: string;
  retryable: boolean;
  retry_after_ms?: number;
}

interface TransportStatus {
  available: boolean;
  last_check: string;
  error?: string;
}
```

### MCPTransport

Uses Model Context Protocol for communication.

```typescript
class MCPTransport implements Transport {
  type = "mcp" as const;

  // MCP tool names per provider
  private toolMappings = {
    openai: "mcp__openai__chat",      // Example
    gemini: "mcp__gemini__ask-gemini"
  };

  async send(request: TransportRequest): Promise<TransportResult> {
    const tool = this.toolMappings[request.provider];
    if (!tool) {
      return { status: "error", error: { type: "invalid_request", message: "No MCP tool for provider" }};
    }

    // Invoke MCP tool
    const result = await invokeMCPTool(tool, {
      model: request.model,
      messages: request.payload.messages,
      // ... other params
    });

    return this.normalizeResult(result);
  }

  async isAvailable(): Promise<boolean> {
    // Check if MCP server is connected
    // Check if required tools are available
  }
}
```

**MCP Considerations**:
- Requires MCP server to be running
- Tools must be registered/discovered
- May have connection issues

### CLITransport

Uses command-line tools for communication.

```typescript
class CLITransport implements Transport {
  type = "cli" as const;

  // CLI commands per provider
  private cliMappings = {
    openai: {
      command: "openai",  // or custom script
      args: ["api", "chat.completions.create"]
    },
    gemini: {
      command: "gemini",  // or gcloud ai
      args: ["chat"]
    }
  };

  async send(request: TransportRequest): Promise<TransportResult> {
    const cli = this.cliMappings[request.provider];
    if (!cli) {
      return { status: "error", error: { type: "invalid_request", message: "No CLI for provider" }};
    }

    // Execute command
    const result = await executeCommand(
      cli.command,
      [...cli.args, ...this.buildArgs(request)],
      { timeout: request.timeout_ms }
    );

    return this.normalizeResult(result);
  }

  async isAvailable(): Promise<boolean> {
    // Check if CLI tools are installed
    // Check if credentials are configured
  }
}
```

**CLI Considerations**:
- Requires CLI tools installed
- Credentials via environment variables or config files
- Cross-platform command differences

### AutoTransport

Default transport that tries MCP first, falls back to CLI.

```typescript
class AutoTransport implements Transport {
  type = "auto" as const;

  private mcp = new MCPTransport();
  private cli = new CLITransport();

  async send(request: TransportRequest): Promise<TransportResult> {
    // Try MCP first
    if (await this.mcp.isAvailable()) {
      const result = await this.mcp.send(request);
      if (result.status === "ok") {
        return { ...result, transport_used: "mcp" };
      }
      // Log MCP failure, try CLI
    }

    // Fallback to CLI
    if (await this.cli.isAvailable()) {
      const result = await this.cli.send(request);
      return { ...result, transport_used: "cli", fallback: true };
    }

    // Both failed
    return {
      status: "error",
      error: {
        type: "network",
        message: "No transport available (MCP and CLI both failed)",
        retryable: false
      },
      latency_ms: 0
    };
  }
}
```

**Fallback Conditions**:
- MCP not connected/available
- MCP tool not found
- MCP request timeout
- MCP authentication error
- MCP rate limit exceeded

## Request Flow

### Complete Request Lifecycle

```
1. Orchestrator creates ProviderRequest
   ├── mode: architecture|review
   ├── round: R1|R2|R3
   ├── context_pack: Full|Summary
   └── timeout: configurable

2. Adapter builds provider-specific prompt
   ├── Format system message
   ├── Format user messages
   └── Apply provider quirks

3. Transport sends request
   ├── AutoTransport tries MCP
   ├── Falls back to CLI if needed
   └── Handles retries

4. Response received and normalized
   ├── Parse raw response
   ├── Extract content and usage
   └── Handle errors

5. Adapter parses into schema
   ├── CouncilOpinion (R1)
   ├── CouncilReview (R2)
   └── Raw for R3 (Chair handles)
```

### Timeout Configuration

```yaml
timeouts:
  mcp_connection: 5000      # MCP availability check
  cli_availability: 3000    # CLI command check

  per_round:
    R1: 60000               # Independent opinions
    R2: 90000               # Cross review (more context)
    R3: 120000              # Synthesis (complex task)

  per_provider:             # Override per provider
    gemini: 90000           # Slower sometimes
    openai: 60000
```

### Retry Configuration

```yaml
retry:
  max_attempts: 2
  backoff:
    initial_ms: 1000
    multiplier: 2
    max_ms: 10000

  retryable_errors:
    - timeout
    - rate_limit
    - network

  non_retryable_errors:
    - auth
    - invalid_request
```

## Provider Registry

```typescript
class ProviderRegistry {
  private adapters: Map<string, ProviderAdapter> = new Map();

  register(adapter: ProviderAdapter): void {
    this.adapters.set(adapter.name, adapter);
  }

  get(name: string): ProviderAdapter | undefined {
    return this.adapters.get(name);
  }

  getAll(): ProviderAdapter[] {
    return Array.from(this.adapters.values());
  }

  getParticipants(config: CouncilConfig): ProviderAdapter[] {
    return config.providers
      .map(p => this.get(p.name))
      .filter(Boolean);
  }

  getChair(config: CouncilConfig): ProviderAdapter {
    const chairName = config.chair || "claude";
    return this.get(chairName) || this.get("claude")!;
  }
}
```

## Error Handling

### Error Categories

| Category | Examples | Retryable | Action |
|----------|----------|-----------|--------|
| Auth | Invalid API key, expired token | No | Report, skip provider |
| Rate Limit | Too many requests | Yes | Backoff, retry |
| Network | Connection refused, DNS failure | Yes | Retry, try alt transport |
| Timeout | Request exceeded limit | Yes | Retry with longer timeout |
| Invalid Request | Malformed prompt, bad model | No | Fix and retry manually |
| Parse Error | Unexpected response format | No | Try to extract partial |

### Graceful Degradation

```typescript
class ProviderErrorHandler {
  handle(error: TransportError, context: RequestContext): ErrorHandling {
    if (error.retryable && context.retriesRemaining > 0) {
      return { action: "retry", delay_ms: this.calculateBackoff(context) };
    }

    if (context.round === "R1" && context.providersRemaining >= 2) {
      return { action: "skip_provider", reason: error.message };
    }

    if (context.round === "R3") {
      return { action: "fallback_to_best_r1", reason: "Chair unavailable" };
    }

    return { action: "fail", error };
  }
}
```

## Security Considerations

### Credential Handling

- Never log API keys or tokens
- Use environment variables or secure credential stores
- Rotate keys periodically
- Scope permissions minimally

### Request Sanitization

- Strip potential injection patterns from prompts
- Limit context pack size
- Validate all inputs before sending

### Response Validation

- Verify response format before parsing
- Limit response size
- Detect and log anomalies

## Cross-Platform Support

### Path Handling

```typescript
// Normalize paths for all platforms
function normalizePath(p: string): string {
  return p.replace(/\\/g, '/');
}
```

### Command Execution

```typescript
class CrossPlatformExecutor {
  execute(command: string, args: string[]): Promise<ExecResult> {
    const isWindows = process.platform === 'win32';

    if (isWindows) {
      // Use cmd.exe or PowerShell
      return this.executeWindows(command, args);
    } else {
      // Use bash/sh
      return this.executeUnix(command, args);
    }
  }
}
```

### CLI Tool Discovery

```typescript
class ToolDiscovery {
  async findTool(name: string): Promise<string | null> {
    const candidates = [
      name,
      `${name}.exe`,           // Windows
      `${name}.cmd`,           // Windows batch
      `/usr/local/bin/${name}` // macOS/Linux common
    ];

    for (const candidate of candidates) {
      if (await this.exists(candidate)) {
        return candidate;
      }
    }

    return null;
  }
}
```

## Configuration

### Default Provider Configuration

```yaml
providers:
  - name: claude
    role: [participant, chair]
    model: claude-sonnet-4-20250514
    enabled: true

  - name: openai
    role: [participant]
    model: gpt-4o
    enabled: true
    transport_preference: auto

  - name: gemini
    role: [participant]
    model: gemini-2.0-flash
    enabled: true
    transport_preference: auto

transport:
  default: auto
  mcp:
    connection_timeout: 5000
  cli:
    discovery_paths:
      - /usr/local/bin
      - ~/.local/bin
```

### Runtime Override

Providers and transport can be overridden at runtime:

```typescript
const council = new Council({
  providers: ["claude", "openai"],  // Exclude Gemini
  transport: "cli",                  // Force CLI
  chair: "claude"
});
```
