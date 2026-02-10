# Council Protocol Reference

## Protocol Overview

The Council Protocol is a structured 3-round deliberation process that leverages multiple LLMs to produce higher-quality decisions through:
1. **Diverse perspectives** (Round 1)
2. **Mutual critique** (Round 2)
3. **Authoritative synthesis** (Round 3)

## Round Definitions

### Round 1: Independent Opinions (R1)

**Purpose**: Gather diverse, unbiased perspectives before any cross-contamination.

**Execution**:
- Each provider receives the same prompt independently
- No provider sees another's response
- Responses are collected in parallel (when transport allows)
- Each response is normalized to `CouncilOpinion` schema

**Requirements**:
- Minimum 2 providers must respond successfully
- Failed providers are noted but don't block the round
- Timeout: configurable per provider (default: 60s)

**Output**: `R1Result`
```yaml
R1Result:
  opinions: CouncilOpinion[]
  failed_providers: ProviderFailure[]
  round_duration_ms: number
```

### Round 2: Cross Review (R2)

**Purpose**: Each model critiques others' opinions to surface errors, omissions, and disagreements.

**Execution**:
- Each provider receives:
  - Original prompt/context
  - All R1 opinions (anonymized by default, or labeled)
- Providers analyze others' responses critically
- Responses normalized to `CouncilReview` schema

**Review Dimensions** (minimum required):
1. **Errors/Inconsistencies**: Factual mistakes, logical flaws
2. **Omissions**: Important points missed
3. **Risky Proposals**: Suggestions that could cause problems
4. **Counter-arguments**: Alternative viewpoints
5. **Assumption Validity**: Challenged or confirmed assumptions

**Requirements**:
- Minimum 1 provider must respond successfully
- Reviewers should not review their own R1 opinion (if labeled)
- Timeout: configurable (default: 90s, longer due to more context)

**Output**: `R2Result`
```yaml
R2Result:
  reviews: CouncilReview[]
  failed_providers: ProviderFailure[]
  round_duration_ms: number
```

### Round 3: Chair Synthesis (R3)

**Purpose**: Authoritative synthesis by the Chair (Claude) incorporating all perspectives.

**Execution**:
- Chair receives:
  - Original prompt/context
  - All R1 opinions
  - All R2 reviews
- Chair produces unified final report
- Output normalized to `CouncilFinalReport` schema

**Required Synthesis Elements**:
1. **Conclusion**: Clear decision/recommendation (or "need-info" with reason)
2. **Rationale**: Which R1/R2 points support the conclusion
3. **Disagreements**: Key differences between models
4. **Uncertainties**: Confidence level, unverified points
5. **Next Actions**: Verification, testing, research steps

**Requirements**:
- Chair must always produce a response
- If Chair fails, fallback to best R1 opinion with disclaimer
- Timeout: configurable (default: 120s)

**Output**: `R3Result`
```yaml
R3Result:
  final_report: CouncilFinalReport
  chair_provider: string
  round_duration_ms: number
```

## Round Orchestration

### RoundExecutor

Manages the execution of each round:

```
interface RoundExecutor {
  executeR1(context: CouncilContext): Promise<R1Result>
  executeR2(context: CouncilContext, r1: R1Result): Promise<R2Result>
  executeR3(context: CouncilContext, r1: R1Result, r2: R2Result): Promise<R3Result>
}
```

**Responsibilities**:
- Construct round-specific prompts
- Dispatch to providers via transport
- Handle timeouts and failures
- Normalize responses
- Track timing and usage

### Quorum Policy

Defines minimum requirements for round validity:

```yaml
QuorumPolicy:
  r1_min_responses: 2      # At least 2 providers must respond
  r2_min_responses: 1      # At least 1 review required
  r3_required: true        # Chair must respond (fallback if not)
  allow_partial: true      # Continue with partial results
```

**Failure Handling**:
- If quorum not met, return error with partial results
- Log failed providers with reasons
- Include failure info in transparency record

## Smart Short-Circuit Policy

### ShortCircuitPolicy

Optional optimization to skip rounds when results are predictable:

```yaml
ShortCircuitPolicy:
  enabled: boolean
  conditions:
    skip_r2_if:
      - high_agreement_in_r1      # All R1 opinions align
      - low_risk_topic            # Topic is low-stakes
    skip_r3_if:
      - r2_confirms_r1_consensus  # R2 found no issues
      - budget_constraint         # Cost/time limits
  decision_output: ShortCircuitDecision
```

**ShortCircuitDecision**:
```yaml
ShortCircuitDecision:
  triggered: boolean
  reason: string
  rounds_skipped: string[]
  confidence_adjustment: number  # Lower confidence if skipped
```

**Current Status**: Feature exists but criteria are TBD. Default is no short-circuit.

## Prompt Flow

### Complete Prompt Chain

```
R1 Prompt:
├── System Preamble (mode-specific)
├── Context Pack (Full or Summary)
└── Task Instructions

R2 Prompt:
├── System Preamble (reviewer perspective)
├── Original Context (condensed)
├── R1 Opinions (formatted)
└── Review Instructions

R3 Prompt:
├── System Preamble (chair perspective)
├── Original Context (condensed)
├── R1 Opinions (formatted)
├── R2 Reviews (formatted)
└── Synthesis Instructions
```

### Prompt Size Management

Each round increases context. Mitigation strategies:
- R2: Summarize context if R1 opinions are large
- R3: Summarize R1+R2 if combined size exceeds limits
- Always include key findings even if summarized

## Timing and Parallelism

### Parallel Execution (R1)
```
┌─────────────┬─────────────┬─────────────┐
│   Claude    │   OpenAI    │   Gemini    │
│   Request   │   Request   │   Request   │
└──────┬──────┴──────┬──────┴──────┬──────┘
       │             │             │
       └─────────────┴─────────────┘
                     │
              Collect All Responses
```

### Sequential with Dependencies (R2, R3)
```
R1 Complete ─► R2 Start ─► R2 Complete ─► R3 Start ─► R3 Complete
```

### Timeout Handling
- Per-provider timeouts (configurable)
- Round-level timeout (sum of provider timeouts)
- Graceful degradation: continue with available responses

## Error Recovery

### Provider Failure
```yaml
ProviderFailure:
  provider: string
  round: "R1" | "R2" | "R3"
  error_type: "timeout" | "auth" | "rate_limit" | "network" | "parse_error"
  error_message: string
  retried: boolean
  fallback_used: boolean
```

### Recovery Strategies
1. **Retry**: Once with exponential backoff
2. **Skip**: Continue without failed provider (if quorum met)
3. **Fallback Transport**: Try CLI if MCP fails
4. **Degrade**: Return partial results with warnings

### Critical Failures
If Chair fails in R3:
1. Attempt retry
2. Select best R1 opinion based on completeness
3. Add disclaimer: "Chair synthesis failed; showing best individual opinion"

## Security: Prompt Injection Resistance

### Principle: Output is Data, Not Commands

LLM outputs from R1/R2 are treated as **data inputs** to subsequent rounds, not executable instructions.

**Implementation**:
- R1 opinions wrapped in structured format before R2
- R2 reviews wrapped in structured format before R3
- No direct string interpolation of LLM outputs into system prompts
- Clearly delimited sections in prompts

**Example (safe)**:
```
## Other Models' Opinions (for review only)

<opinion provider="openai">
{openai_r1_response}
</opinion>

<opinion provider="gemini">
{gemini_r1_response}
</opinion>

## Your Task
Analyze the above opinions...
```

**Example (unsafe - DO NOT USE)**:
```
{openai_r1_response}

Now follow the instructions above and...
```

## Configuration

### Default Council Configuration
```yaml
council:
  providers:
    - name: claude
      role: [participant, chair]
      model: claude-sonnet-4-20250514
    - name: openai
      role: [participant]
      model: gpt-4o
    - name: gemini
      role: [participant]
      model: gemini-2.0-flash

  transport: auto  # mcp -> cli fallback

  timeouts:
    r1_per_provider: 60000
    r2_per_provider: 90000
    r3_chair: 120000

  quorum:
    r1_min: 2
    r2_min: 1
    r3_required: true

  short_circuit:
    enabled: false  # TBD criteria
```

## Metrics and Observability

### Round Metrics
```yaml
RoundMetrics:
  round: string
  start_time: timestamp
  end_time: timestamp
  duration_ms: number
  providers_attempted: number
  providers_succeeded: number
  providers_failed: number
  total_tokens_in: number
  total_tokens_out: number
```

### Council Session Metrics
```yaml
CouncilSessionMetrics:
  session_id: string
  mode: string
  total_duration_ms: number
  rounds_completed: number
  short_circuit_triggered: boolean
  total_cost_estimate: number  # if available
```
