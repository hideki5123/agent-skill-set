# Multi-Agent Council Plugin

A Claude Code plugin that orchestrates a council of multiple LLMs (Claude + OpenAI + Gemini) for architecture decisions and code reviews through a structured 3-round protocol.

## Features

- **Multi-LLM Collaboration**: Combines perspectives from Claude, OpenAI, and Gemini
- **3-Round Protocol**: Independent Opinions -> Cross Review -> Chair Synthesis
- **Two Modes**: Architecture decisions and Code/Project reviews
- **Transparency**: Full audit trail of what was sent to each provider

## Installation

### Option 1: From Local Path (Development)

```bash
# Add the marketplace
/plugin marketplace add D:/Shared/agents/my-skills/multi-agent-council

# Install the plugin
/plugin install multi-agent-council@hideki-plugins
```

### Option 2: From GitHub (After Publishing)

```bash
# Add the marketplace (replace with your GitHub repo)
/plugin marketplace add your-username/claude-plugins

# Install the plugin
/plugin install multi-agent-council@your-marketplace-name
```

### Option 3: Direct Plugin Load (Testing)

```bash
claude --plugin-dir D:/Shared/agents/my-skills/multi-agent-council
```

## Usage

### Architecture Mode

Evaluate design choices, technology selection, and trade-offs:

```
/multi-agent-council:multi-agent-council architecture

Question: Should we use Redis or PostgreSQL for session storage?
Constraints: High availability required, team familiar with PostgreSQL
```

### Review Mode

Thorough analysis of project state from multiple perspectives:

```
/multi-agent-council:multi-agent-council review

Target: Current project state
Focus: Security and performance concerns
```

## Protocol Details

### Round 1: Independent Opinions
Each provider responds independently without seeing other models' answers.

### Round 2: Cross Review
Each provider reviews other models' responses for:
- Errors/inconsistencies
- Omissions (missing critical points)
- Risky proposals (security, operations, cost)
- Counter-arguments/alternatives

### Round 3: Chair Synthesis
Chair (Claude) synthesizes all inputs into a final report containing:
- Conclusion
- Rationale
- Disagreements
- Uncertainties
- Next actions

## Requirements

- Claude Code CLI
- MCP or CLI access to OpenAI and Gemini (optional, degrades gracefully)

## License

MIT
