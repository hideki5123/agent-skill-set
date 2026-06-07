# BDD spec for codex-server.
#
# Read only by /skill-improve or audit tooling — NOT loaded during normal
# execution. Adding/changing behavior should start with editing scenarios
# here, then implementing.

Feature: codex-server — ChatGPT-subscription chat via Codex App Server

  Scenario: New chat via decoupled async invocation
    Given the user has run `codex login` and codex is on PATH
    When Claude invokes `chat.ts new "summarize this repo"`
    Then the call returns within 1 second with {turn_id, out_path, events_path, done_marker, error_marker, meta_path}
    And a detached worker is running in the background under ~/.codex-server/turns/<id>/
    And the worker streams agent_message text into out.txt incrementally
    And on completion the worker writes a `done` marker file
    And Claude uses Monitor on out.txt to observe the streaming in real time
    And no Bash timeout applies because the original `new` call exited in <1s

  Scenario: Continue the most recent thread in this cwd
    Given a prior codex-server turn completed in the current working directory
    When Claude invokes `chat.ts continue --last "implement the fix"`
    Then chat.ts walks ~/.codex/sessions/ for the latest thread_id whose session ran in this cwd
    And forks a worker that resumeThread()s and runStreamed()s the new turn
    And returns turn-id JSON in <1s

  Scenario: Continue a specific thread by ID
    Given Claude remembers a thread_id from an earlier turn
    When Claude invokes `chat.ts continue --thread <UUID> "follow-up"`
    Then chat.ts forks a worker that resumeThread(UUID).runStreamed(prompt)
    And returns turn-id JSON in <1s

  Scenario: Wait for a specific turn synchronously
    Given a turn-id from a prior `new` / `continue` call
    When Claude invokes `chat.ts wait <turn-id>`
    Then chat.ts polls the marker files at 250ms intervals
    And on `done` it prints the final out.txt content and exits 0
    And on `error` it prints out.txt to stderr and exits 1
    And on `abandoned` / `missing` it exits non-zero

  Scenario: Tail a turn's output as it streams
    Given a turn is currently running and out.txt is growing
    When Claude invokes `chat.ts tail <turn-id> --follow`
    Then chat.ts streams new bytes from out.txt to stdout
    And exits 0 when the `done` marker appears
    And exits 1 when the `error` marker appears

  Scenario: Inspect an in-flight turn's status
    Given a turn is currently running (no done/error marker, worker pid alive)
    When Claude invokes `chat.ts status <turn-id>`
    Then chat.ts prints JSON with state="running", thread_id, cwd, started_at, last_event_at, pid

  Scenario: A freshly forked turn is not mistaken for abandoned
    Given a turn was just created by `new` and the worker is still starting up
    And neither `done` nor `error` marker exists yet
    When Claude invokes `chat.ts wait <turn-id>` immediately
    Then within the ~10s startup grace chat.ts reports state="running"
    And it does not exit early as "abandoned"

  Scenario: Detect an orphaned (crashed) worker
    Given a turn-dir exists but neither `done` nor `error` marker is present
    And the turn is past its ~10s startup grace
    And the worker pid is no longer alive
    When Claude invokes `chat.ts status <turn-id>`
    Then chat.ts prints JSON with state="abandoned"

  Scenario: List recent turns
    Given several turns exist under ~/.codex-server/turns/
    When Claude invokes `chat.ts list-turns --limit 5`
    Then chat.ts prints a JSON array of the 5 most recent turns with state, thread_id, cwd, started_at

  Scenario: List recent threads from codex sessions
    Given codex has logged sessions to ~/.codex/sessions/
    When Claude invokes `chat.ts list`
    Then chat.ts prints a JSON array of recent threads with thread_id, path, cwd, mtime

  Scenario: Show thread metadata
    Given a thread_id from list or from earlier
    When Claude invokes `chat.ts show <thread-id>`
    Then chat.ts locates the matching .jsonl under ~/.codex/sessions/
    And prints JSON with thread_id, path, head (first event), tail (last 10 lines)

  Scenario: Old turn cleanup on setup
    Given turn-dirs older than 7 days exist under ~/.codex-server/turns/
    When setup.ts runs
    Then those turn-dirs are deleted to keep disk usage bounded

  Scenario: Structured output via JSON schema
    Given the user has a schema.json describing the desired output shape
    When `chat.ts new --schema schema.json "<prompt>"` is invoked
    Then the worker forwards { outputSchema } to thread.runStreamed
    And the final agent_message conforms to the schema

  Scenario: Attach images to a turn
    Given the user has local PNG/JPG files
    When `chat.ts new --image ui.png --image diagram.jpg "<prompt>"` is invoked
    Then the worker passes structured input entries with local_image items to thread.runStreamed

  Scenario: codex login not yet completed
    Given ~/.codex/auth.json does not exist
    When any `chat.ts` subcommand that needs auth is invoked
    Then the skill prints the login guide
    And exits with code 2
    And no API-key fallback is offered (the skill is ChatGPT-subscription-only by design)

  Scenario: ChatGPT subscription used for every turn
    Given the user has run `codex login` once and ~/.codex/auth.json exists
    When codex-server runs any turn
    Then the spawned codex binary uses the ChatGPT auth from auth.json
    And no API-key billing is consumed
    And OPENAI_API_KEY is not readable from inside the deno process (not in --allow-env)

  Scenario: OPENAI_API_KEY is exported but ignored
    Given the user has OPENAI_API_KEY exported in their shell
    And ~/.codex/auth.json exists
    When codex-server runs
    Then the env var is not in --allow-env, deno cannot see it
    And the spawned codex binary uses the ChatGPT subscription via auth.json
    And no API-key billing is incurred even though the env var is present

  Scenario: codex binary missing
    Given `codex` is not installed on PATH
    When setup.ts runs
    Then it prints install instructions (Homebrew / npm) and exits non-zero

  Scenario: Long-running turn (Bash 2-min timeout structurally bypassed)
    Given a turn that will take ~5 minutes to complete
    When Claude invokes `chat.ts new "<prompt>"`
    Then the call returns turn-id in <1s — the worker continues running in the background detached from the Bash invocation
    And Claude uses Monitor on out.txt to follow progress
    And no `run_in_background:true` or `timeout: 600000` is required

  Scenario: Feedback Check surfaces a recurring issue
    Given codex-server/feedback/log.md has 5+ entries with a common keyword
    When the skill is invoked
    Then it warns the user about the pattern and suggests `/skill-improve --skill codex-server`
    And continues normally

  Scenario: Retrospective recorded after a run with corrections
    Given the user corrected a wrong CLI flag mid-session
    When the run completes
    Then the skill asks for a 1-5 rating in Japanese
    And creates feedback/log.md if missing
    And prepends an entry capturing the correction and user note
