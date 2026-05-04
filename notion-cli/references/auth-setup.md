# Auth setup — Notion Internal Integration

The CLI authenticates with a single env var: `NOTION_TOKEN`. There is no `.env` fallback, no OAuth flow, no browser-based login. Internal Integrations are the right fit: their tokens never expire and don't require a deployed callback URL.

## Step-by-step

### 1. Create the integration

1. Sign in to the Notion workspace you want to control.
2. Open <https://www.notion.so/profile/integrations>. (On older accounts: <https://www.notion.so/my-integrations>.)
3. Click **+ New integration**.
4. Fill in:
   - **Name** — anything memorable, e.g. `cli-bot` or `claude-code`.
   - **Associated workspace** — pick the workspace.
   - **Type** — choose **Internal**. Public integrations require an OAuth flow with a deployed redirect URL — out of scope for a CLI.
5. Click **Save**.

### 2. Choose capabilities

After saving, Notion shows the integration's settings. Under **Capabilities** select the abilities the integration should have. For typical CLI use:

- ✅ Read content
- ✅ Update content
- ✅ Insert content
- ✅ Read comments (optional)
- ✅ Insert comments (optional)
- ✅ Read user information (with or without email — your choice)

Save.

### 3. Copy the Internal Integration Secret

- Go to the **Configuration** tab.
- Find **Internal Integration Secret** and click **Show**, then **Copy**.
- The token starts with `ntn_…` (newer accounts) or `secret_…` (older accounts). Both work.

> Treat this token like a password. It grants full access (within the chosen capabilities) to every page or database that gets shared with the integration.

### 4. Export the token in your shell

Do this in your **own terminal**, not pasted into the agent. The agent never needs to see the value — it only needs the env var to exist.

#### macOS / Linux (zsh, bash)

Append to `~/.zshrc` or `~/.bashrc`:

```sh
export NOTION_TOKEN="ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Reload:

```sh
source ~/.zshrc   # or ~/.bashrc
```

Or just open a new terminal window.

#### fish

Append to `~/.config/fish/config.fish`:

```fish
set -gx NOTION_TOKEN ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Or persist for all future shells:

```fish
set -Ux NOTION_TOKEN ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### PowerShell (Windows)

Append to `$PROFILE`:

```powershell
$env:NOTION_TOKEN = 'ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

For a system-wide setting:

```powershell
[Environment]::SetEnvironmentVariable('NOTION_TOKEN', 'ntn_…', 'User')
```

#### Verify it's set (without revealing the value)

```sh
# zsh / bash / fish
[ -n "$NOTION_TOKEN" ] && echo "set" || echo "missing"
```

```powershell
if ($env:NOTION_TOKEN) { 'set' } else { 'missing' }
```

### 5. Share each page or database with the integration

> A new integration sees nothing in the workspace until pages are explicitly shared with it. This is the #1 source of "404 / object_not_found" errors after setup.

Per top-level page (children inherit):

1. Open the page in Notion.
2. Click `•••` (top-right corner of the page).
3. **Connections** → **Add connections** → search for the integration name → click it.
4. Confirm the access dialog.

Repeat for each top-level page or database the CLI should access.

### 6. Verify

```sh
deno run \
  --allow-env=NOTION_TOKEN \
  --allow-net=api.notion.com \
  --allow-read=$HOME/.notion-cli \
  --allow-write=$HOME/.notion-cli \
  ~/.notion-cli/lib/notion.ts auth
```

Expected: a JSON object describing the bot user (`object: "user"`, `type: "bot"`, `bot.workspace_name`, etc.). If you get this, the token is valid.

Empty results from `notion search`? You haven't shared any pages with the integration yet — re-do step 5.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `401 unauthorized` on `auth` | Token wrong or revoked | Re-copy the Internal Integration Secret from the integration's Configuration tab. |
| `auth` works, `search` returns `[]` | No pages shared with integration | Per page: `•••` → Connections → add the integration. |
| `404 object_not_found` on a known page | Page not shared with integration; or page archived | Add the connection on the page (or its top-level ancestor). |
| `403 restricted_resource` | Capability missing on the integration | Toggle the missing capability in the integration's settings. |
| `validation_error` with `Notion-Version` | SDK upgraded mid-flight | `cd ~/.notion-cli && mise install` to pull the matching deno; clear `~/.notion-cli/.cache/`. |

## Rotating the token

If the token leaks (e.g. accidentally pasted into a chat, committed to git, etc.):

1. Open the integration in <https://www.notion.so/profile/integrations>.
2. Configuration → **Internal Integration Secret** → **Regenerate token**.
3. Update `NOTION_TOKEN` in your shell rc and re-source.

The old token is invalidated immediately; any caller still using it gets `401`.

## Why not OAuth?

OAuth public integrations require a deployed app with a public redirect URL. They're meant for SaaS products that connect to many users' Notion workspaces. For a personal CLI driving your own workspace, Internal is simpler, avoids token-refresh plumbing, and never expires. If you need OAuth, that's a different tool than this skill.
