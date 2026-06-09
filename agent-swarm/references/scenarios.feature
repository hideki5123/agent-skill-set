Feature: Agent Swarm orchestration and consistency observation
  Coordinate multiple coding-agent sessions over mcp_agent_mail, observe them,
  and prevent file/edit conflicts and contradictory decisions.

  Scenario: Orchestrate from scratch
    Given the user wants to coordinate several sessions on different tasks
    When the user runs /agent-swarm in a git repo
    Then the skill ensures the agent-mail server is up
    And derives project_key from the git toplevel basename
    And registers as the orchestrator
    And runs the observe loop emitting a worker/task/conflict status table

  Scenario: Server not connected in this session
    Given the mcp__mcp-agent-mail__ tools are absent from the session
    When /agent-swarm runs preflight
    Then it starts the server in the background
    And tells the user MCP loads at session start so they must open a new session and re-run

  Scenario: Orchestrator auto-loops the observe cycle
    Given the user runs /agent-swarm in orchestrator mode
    When the first observe cycle completes
    Then the skill starts a recurring watch via the /loop skill at the interval
         from the args (default 30s) without the user invoking /loop
    And it stops scheduling when the user says stop or all tasks are done and acked

  Scenario: Disable auto-loop
    Given the user runs /agent-swarm orchestrator off
    When orchestrator mode initializes
    Then auto-looping is skipped and observe cycles are run manually

  Scenario: Join as a worker
    Given the orchestrator has assigned a task to this session
    When /agent-swarm worker <name> <task> runs
    Then it joins via macro_start_session with the shared project_key
    And reserves its owned paths before editing
    And reports progress and obeys HOLD messages

  Scenario: Detect and resolve a path-overlap conflict
    Given two workers hold exclusive reservations on intersecting paths
    When the orchestrator reads resource://tooling/locks during an observe cycle
    Then it flags the overlap
    And sends an urgent HOLD to both workers
    And serializes or re-assigns ownership, then releases the hold

  Scenario: Onboard a session that is already running but not joined
    Given a session is working but has not registered with agent-mail
    When the user asks to bring it into the swarm
    Then the skill provides the worker join prompt with an explicit agent_name
    And the orchestrator addresses that session by name once it appears in the roster

  Scenario: Target an already-participating session by name
    Given other sessions are already registered under the same project_key
    When the orchestrator builds the roster
    Then it reads resource://agents/{project_key}, inspects each with whois,
         and addresses them by name

  Scenario: Not in a git repo
    Given the working directory is not a git repository
    When /agent-swarm resolves the room key
    Then it asks the user for a short project_key once and proceeds
