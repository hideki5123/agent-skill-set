# Data Models Reference

This document defines the canonical data schemas used throughout the Council skill. All provider responses must be normalized to these schemas.

## Core Council Schemas

### CouncilOpinion (R1 Output)

Normalized output from Round 1 independent analysis.

```typescript
interface CouncilOpinion {
  // Identification
  provider: string;          // "claude" | "openai" | "gemini" | etc.
  model: string;             // Specific model ID used
  round: "R1";
  timestamp: string;         // ISO 8601

  // Mode context
  mode: "architecture" | "review";

  // Content
  summary: string;           // 1-2 sentence conclusion
  details: {
    understanding: string;   // Problem restatement
    key_considerations: string[];
    recommendation: string;
    rationale: string;
  };

  // Analysis
  risks: Risk[];
  assumptions: string[];
  questions: string[];       // Info gaps identified

  // Metadata
  confidence: "low" | "medium" | "high";
  token_usage?: TokenUsage;
  latency_ms?: number;
}

interface Risk {
  description: string;
  severity: "low" | "medium" | "high";
  mitigation?: string;
}

interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}
```

### CouncilReview (R2 Output)

Normalized output from Round 2 cross-review.

```typescript
interface CouncilReview {
  // Identification
  reviewer_provider: string;
  reviewer_model: string;
  round: "R2";
  timestamp: string;

  // Reviewed targets
  targets: ReviewTarget[];

  // Metadata
  token_usage?: TokenUsage;
  latency_ms?: number;
}

interface ReviewTarget {
  target_provider: string;

  // Critiques
  critiques: Critique[];

  // Agreements/disagreements
  agreement_points: string[];
  disagreement_points: DisagreementPoint[];
}

interface Critique {
  type: CritiqueType;
  message: string;
  severity: "low" | "medium" | "high";
  location?: string;        // Reference to specific part of opinion
  suggested_correction?: string;
}

type CritiqueType =
  | "error"          // Factual mistake
  | "inconsistency"  // Internal contradiction
  | "omission"       // Missing important point
  | "risk"           // Dangerous proposal
  | "assumption"     // Questionable assumption
  | "alternative";   // Better approach exists

interface DisagreementPoint {
  topic: string;
  reviewer_position: string;
  target_position: string;
  rationale: string;
}
```

### CouncilFinalReport (R3 Output)

Final synthesized output from Chair.

```typescript
interface CouncilFinalReport {
  // Identification
  run_id: string;
  mode: "architecture" | "review";
  chair_provider: string;
  chair_model: string;
  timestamp: string;

  // Core decision
  final_summary: string;     // Executive summary (2-3 sentences)
  decision: Decision;

  // Supporting analysis
  rationale: Rationale;
  risks: SynthesizedRisk[];
  next_actions: NextAction[];

  // Multi-model synthesis
  disagreements: Disagreement[];
  uncertainties: Uncertainty[];
  consensus_points: string[];

  // Metadata
  rounds_completed: number;
  providers_participated: string[];
  short_circuit?: ShortCircuitDecision;
  total_duration_ms: number;
}

// Architecture mode decision
interface ArchitectureDecision {
  type: "architecture";
  outcome: "adopt" | "reject" | "need-info";
  recommendation: string;
  alternatives?: Alternative[];
  verification_plan?: VerificationStep[];
}

// Review mode decision
interface ReviewDecision {
  type: "review";
  findings: Finding[];
  summary: ReviewSummary;
}

type Decision = ArchitectureDecision | ReviewDecision;

interface Rationale {
  summary: string;
  supporting_opinions: OpinionReference[];
  supporting_reviews: ReviewReference[];
}

interface OpinionReference {
  provider: string;
  key_point: string;
  weight: "primary" | "supporting" | "context";
}

interface ReviewReference {
  reviewer: string;
  critique_type: CritiqueType;
  key_point: string;
}

interface SynthesizedRisk {
  description: string;
  severity: "low" | "medium" | "high" | "critical";
  mentioned_by: string[];    // Which providers flagged this
  mitigation: string;
  consensus: "agreed" | "disputed";
}

interface NextAction {
  action: string;
  priority: "immediate" | "short-term" | "long-term";
  rationale: string;
  success_criteria?: string;
}

interface Disagreement {
  topic: string;
  positions: {
    provider: string;
    position: string;
  }[];
  chair_resolution: string;
  resolution_rationale: string;
}

interface Uncertainty {
  area: string;
  confidence_level: "low" | "medium";
  reason: string;
  suggested_verification: string;
}

interface ShortCircuitDecision {
  triggered: boolean;
  reason: string;
  rounds_skipped: ("R2" | "R3")[];
  confidence_adjustment: number;
}
```

## Review Mode Specific Schemas

### Finding

```typescript
interface Finding {
  id: string;                // e.g., "SEC-001", "PERF-003"
  title: string;
  severity: "low" | "medium" | "high" | "critical";
  category: FindingCategory;
  location: string;          // file:line or general area
  description: string;
  rationale: string;
  fix_approach: string;
  impact_scope: string[];
  test_considerations: string[];
  priority: number;          // 1 = highest

  // Multi-model context
  reported_by: string[];     // Which providers found this
  confirmed_by: string[];    // Which providers agreed in R2
  disputed_by?: string[];    // Which providers disagreed
}

type FindingCategory =
  | "security"
  | "performance"
  | "reliability"
  | "maintainability"
  | "correctness"
  | "documentation"
  | "testing"
  | "other";

interface ReviewSummary {
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  categories_affected: FindingCategory[];
  top_concerns: string[];
  recommended_actions: string[];
}
```

## Architecture Mode Specific Schemas

### Alternative

```typescript
interface Alternative {
  option: string;
  description: string;
  pros: string[];
  cons: string[];
  when_to_use: string;
  mentioned_by: string[];
}

interface VerificationStep {
  step: string;
  description: string;
  success_criteria: string;
  estimated_effort?: string;
}
```

## Provider/Transport Schemas

### ProviderRequest

```typescript
interface ProviderRequest {
  provider: string;
  model: string;

  // Prompt components
  system_preamble: string;
  task_prompt: string;
  context_pack: ContextPack;

  // Round context
  round_context: R1Context | R2Context | R3Context;

  // Options
  max_tokens?: number;
  temperature?: number;
  timeout_ms?: number;
}

interface R1Context {
  round: "R1";
  mode: "architecture" | "review";
}

interface R2Context {
  round: "R2";
  mode: "architecture" | "review";
  r1_opinions: CouncilOpinion[];
}

interface R3Context {
  round: "R3";
  mode: "architecture" | "review";
  r1_opinions: CouncilOpinion[];
  r2_reviews: CouncilReview[];
}
```

### ProviderResponse

```typescript
interface ProviderResponse {
  provider: string;
  model: string;
  status: "ok" | "error" | "timeout";

  // Content (when status = "ok")
  content?: string;

  // Error info (when status != "ok")
  error?: {
    type: "auth" | "rate_limit" | "network" | "parse" | "timeout" | "unknown";
    message: string;
    retryable: boolean;
  };

  // Metadata
  usage?: TokenUsage;
  latency_ms: number;
  transport_used: "mcp" | "cli";
}
```

### TransportRequest / TransportResult

```typescript
interface TransportRequest {
  provider: string;
  model: string;
  payload: {
    messages: Message[];
    max_tokens?: number;
    temperature?: number;
  };
  timeout_ms: number;
}

interface Message {
  role: "system" | "user" | "assistant";
  content: string;
}

interface TransportResult {
  status: "ok" | "error";
  raw?: any;                 // Raw provider response
  error?: string;
  transport: "mcp" | "cli";
  latency_ms: number;
}
```

## Context Pack Schemas

See [context-pack.md](context-pack.md) for full details.

```typescript
interface ContextPack {
  type: "full" | "summary";
  manifest: Manifest;
  file_index: FileIndexEntry[];
  content: FullPackContent | SummaryPackContent;
  metadata: PackMetadata;
}
```

## Transparency Record Schema

```typescript
interface TransparencyRecord {
  // Identification
  run_id: string;
  timestamp: string;

  // Session info
  mode: "architecture" | "review";
  user_query?: string;       // Sanitized

  // Transport info
  transport_config: "auto" | "mcp" | "cli";
  transport_results: {
    provider: string;
    transport_used: "mcp" | "cli";
    fallback_triggered: boolean;
  }[];

  // Provider details
  providers: ProviderRecord[];

  // Pack info
  context_pack_type: "full" | "summary";
  files_sent_count: number;
  total_prompt_bytes: number;

  // Aggregate metrics
  total_tokens_in?: number;
  total_tokens_out?: number;
  total_duration_ms: number;
  estimated_cost?: number;
}

interface ProviderRecord {
  provider: string;
  model: string;
  rounds_participated: ("R1" | "R2" | "R3")[];
  status: "ok" | "partial" | "failed";
  token_usage?: TokenUsage;
  latency_ms: number;
  error?: string;
}
```

## Validation

All schemas should be validated at boundaries:
- After receiving provider responses
- Before passing to next round
- Before returning final report

Validation rules:
- Required fields must be present
- Enums must match allowed values
- Arrays can be empty but not null
- Timestamps must be valid ISO 8601
- IDs must be non-empty strings

## Schema Evolution

When extending schemas:
1. Add new optional fields (backward compatible)
2. Never remove required fields
3. Document changes in version history
4. Consider migration for stored records
