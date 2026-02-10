# Architecture Mode Reference

## Purpose
Improve quality of design decisions by gathering diverse AI perspectives, critiques, and synthesized recommendations.

## Input Schema

```yaml
ArchitectureModeInput:
  question: string           # The design question to be answered
  constraints: string[]      # Known constraints (technical, business, team)
  relevant_files: string[]   # Optional: specific files to include
  project_snapshot: boolean  # Optional: include project snapshot (default: false)
  focus_areas: string[]      # Optional: specific areas to emphasize
```

## Output Schema

```yaml
ArchitectureModeOutput:
  conclusion: string         # Final recommendation
  decision: "adopt" | "reject" | "need-info"
  rationale: string          # Why this conclusion
  alternatives:              # Other options considered
    - option: string
      pros: string[]
      cons: string[]
      when_to_use: string
  risks:                     # Identified risks
    - risk: string
      severity: "low" | "medium" | "high"
      mitigation: string
  verification_plan:         # How to validate the decision
    - step: string
      success_criteria: string
  in_out_boundary:           # What's in/out of scope
    in_scope: string[]
    out_of_scope: string[]
  additional_info_needed:    # If decision is "need-info"
    - question: string
      why_needed: string
```

## System Preamble (for all providers)

```
You are participating in a multi-LLM architecture council. Your role is to provide
independent, well-reasoned analysis of the design question presented.

Guidelines:
1. Be specific and actionable - avoid vague recommendations
2. Consider real-world trade-offs (cost, complexity, team skills, timeline)
3. Identify assumptions you're making
4. Flag risks and propose mitigations
5. Think about maintainability and evolution over time
6. Consider failure modes and edge cases

Your response will be reviewed by other LLMs, so be precise and defensible.
```

## Round 1 Prompt Template

```
## Architecture Question
{question}

## Known Constraints
{constraints}

## Context
{context_pack_content}

## Your Task
Provide your independent analysis following this structure:

1. **Understanding**: Restate the problem in your own words
2. **Key Considerations**: What factors matter most?
3. **Recommendation**: Your suggested approach
4. **Rationale**: Why this approach?
5. **Alternatives**: What else could work?
6. **Risks**: What could go wrong?
7. **Assumptions**: What are you assuming?
8. **Questions**: What additional info would help?
```

## Round 2 Prompt Template

```
## Original Question
{question}

## Other Models' Opinions
{r1_opinions_formatted}

## Your Task
Review the other models' responses critically:

1. **Errors/Inconsistencies**: Any factual mistakes or logical flaws?
2. **Omissions**: What important points did they miss?
3. **Risky Proposals**: Any suggestions that could cause problems?
4. **Alternative Views**: Do you disagree with any conclusions?
5. **Assumption Challenges**: Are their assumptions valid?
6. **Agreements**: What points do you strongly agree with?

Be constructive but thorough. Your goal is to improve the final decision quality.
```

## Example Workflow

### Input
```yaml
question: "Should we migrate from REST to GraphQL for our mobile API?"
constraints:
  - "6-month timeline"
  - "Team has no GraphQL experience"
  - "Mobile app has 50+ API calls"
  - "Backend is Node.js/Express"
focus_areas:
  - "Learning curve"
  - "Migration strategy"
  - "Performance implications"
```

### Expected Council Flow

1. **R1**: Each provider analyzes independently
   - Claude: Considers team experience, migration complexity
   - OpenAI: Focuses on technical trade-offs, performance
   - Gemini: Explores hybrid approaches, timeline risks

2. **R2**: Cross-review
   - Models critique each other's assumptions
   - Identify overlooked risks (e.g., mobile caching)
   - Challenge timeline feasibility

3. **R3**: Chair synthesis
   - Weighs competing perspectives
   - Identifies areas of agreement
   - Produces actionable recommendation

### Sample Output
```yaml
conclusion: "Adopt incremental migration strategy starting with read-heavy endpoints"
decision: "adopt"
rationale: |
  While full GraphQL migration offers long-term benefits, the team's lack of
  experience and 6-month timeline create significant risk. A phased approach:
  1. Start with 10 read-heavy endpoints (months 1-2)
  2. Evaluate and train team (month 3)
  3. Expand to remaining endpoints if successful (months 4-6)

  This reduces risk while building GraphQL competency.
alternatives:
  - option: "Full migration to GraphQL"
    pros: ["Cleaner architecture", "Better mobile performance", "Single source of truth"]
    cons: ["High risk given timeline", "Team learning curve", "Migration complexity"]
    when_to_use: "If timeline extends to 12+ months or team has GraphQL experience"
  - option: "Stay with REST, optimize existing API"
    pros: ["No migration risk", "Team already proficient", "Faster delivery"]
    cons: ["Over-fetching continues", "Multiple endpoints for related data"]
    when_to_use: "If mobile performance is acceptable and no new major features planned"
risks:
  - risk: "Team struggles with GraphQL concepts"
    severity: "medium"
    mitigation: "Allocate training budget, start with simpler schemas"
  - risk: "Migration takes longer than expected"
    severity: "medium"
    mitigation: "Define clear go/no-go criteria at month 3"
verification_plan:
  - step: "Pilot with 3 least critical read endpoints"
    success_criteria: "Team can implement without external help within 2 weeks"
  - step: "Performance benchmark on pilot endpoints"
    success_criteria: "Response time within 20% of REST baseline"
```

## Mode-Specific Prompt Builders

### ArchitectureModePromptBuilder

Responsibilities:
1. Format the question and constraints clearly
2. Include relevant context from Context Pack
3. Generate round-specific prompts
4. Handle focus areas by emphasizing them in prompts

### OutputSchemaFormatter

Responsibilities:
1. Parse provider responses into structured format
2. Normalize different response styles
3. Validate required fields are present
4. Handle partial or malformed responses gracefully
