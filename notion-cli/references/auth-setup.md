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
# zsh / bash / fish — direct env var
[ -n "$NOTION_TOKEN" ] && echo "set" || echo "missing"
# alias env var (the CLI accepts this if NOTION_TOKEN is unset)
[ -n "$NOTION_API_KEY" ] && echo "alias set" || echo "alias missing"
# file-based source
[ -r "$NOTION_TOKEN_FILE" ] && echo "file readable: $NOTION_TOKEN_FILE" || echo "file path unset/unreadable"
```

```powershell
if ($env:NOTION_TOKEN) { 'set' } else { 'missing' }
```

### 4b. Alternative: source the token from a file (Nix / agenix / sops-nix / 1Password / pass)

If you'd rather keep the token out of plain dotfiles — recommended on Nix-managed machines and any setup where dotfiles end up in a Git repo or the world-readable Nix store — use the `NOTION_TOKEN_FILE` env var. The CLI checks it last in the resolution chain (`NOTION_TOKEN` → `NOTION_API_KEY` → `NOTION_TOKEN_FILE`), reads the file once at startup, trims trailing whitespace, and discards the value after handing it to one HTTP client. The file's contents are exactly the token — no quoting, no `export ` prefix, no trailing newline issues (the CLI strips them).

#### agenix (encrypted secrets bound to host SSH keys)

The user's existing setup, generalized:

1. Encrypt the token in your nix-config repo:
   ```sh
   cd ~/code/nix-config/secrets
   agenix -i ~/.ssh/id_ed25519_local -e notion-api-key.age
   # paste the token, save, exit
   ```
   The `.age` file is safe to commit — only the host key and your personal SSH key can decrypt it.

2. Wire it into your nix-darwin / NixOS module so it materializes at activation time:
   ```nix
   # darwin/modules/agenix.nix (example)
   age.secrets.notion-api-key = {
     file  = ../../secrets/notion-api-key.age;
     owner = "hidekikoike";   # the user who runs the CLI
     mode  = "0400";
   };
   ```
   After `darwin-rebuild switch`, the file appears at `/run/agenix/notion-api-key` (NixOS uses `/run/agenix/` too; macOS via `darwin-agenix` uses the same path).

3. Export the path (not the value) in your shell. In home-manager:
   ```nix
   programs.zsh.sessionVariables = {
     NOTION_TOKEN_FILE = "/run/agenix/notion-api-key";
   };
   ```
   Or imperatively in `~/.zshrc` (if zsh is not Nix-managed):
   ```sh
   export NOTION_TOKEN_FILE=/run/agenix/notion-api-key
   ```

4. When invoking the CLI, add exactly that path to the deno read scope:
   ```sh
   deno run \
     --allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE \
     --allow-net=api.notion.com \
     --allow-read=$HOME/.notion-cli --allow-write=$HOME/.notion-cli \
     --allow-read=$NOTION_TOKEN_FILE \
     ~/.notion-cli/lib/notion.ts auth
   ```

   To rotate, re-run `agenix -e notion-api-key.age` and `darwin-rebuild switch` — the file is replaced atomically and any future CLI run picks up the new value. Sessions that have already cached the old value (none, in our case — the CLI doesn't cache) are unaffected; the next invocation reads fresh.

#### sops-nix (encrypted via age/PGP, decrypted to tmpfs)

Same pattern, different module:

```nix
# NixOS module (example)
sops.secrets."notion-api-key" = {
  owner = "hidekikoike";
  mode  = "0400";
  # path defaults to /run/secrets/notion-api-key
};
```

Then `NOTION_TOKEN_FILE = "/run/secrets/notion-api-key"`.

#### 1Password CLI

Use a one-shot subshell to materialize the token to a tmpfile owned by you:

```sh
op signin
op read "op://Personal/Notion CLI/credential" > /tmp/notion-api-key
chmod 600 /tmp/notion-api-key
export NOTION_TOKEN_FILE=/tmp/notion-api-key
```

Add `unset NOTION_TOKEN_FILE; rm /tmp/notion-api-key` to your shell exit hook, or use `op run -- deno run …` to inject it for one process only (in which case set `NOTION_TOKEN` from `OP_NOTION_TOKEN` and skip the file route).

#### `pass` (password-store)

```sh
pass show notion/cli > /run/user/$UID/notion-api-key
chmod 600 /run/user/$UID/notion-api-key
export NOTION_TOKEN_FILE=/run/user/$UID/notion-api-key
```

`/run/user/$UID/` is a per-user tmpfs on Linux that's wiped on logout — a sensible cache location.

#### Why a file beats a plain env-var on Nix

- The token never lives in the world-readable Nix store. `home.sessionVariables.NOTION_TOKEN = "ntn_…"` does land in `/nix/store/…-hm-session-vars.sh` which is readable by every user on the box.
- Dotfile diffs (and any backup tool that captures `~/.zshrc`) don't capture the token.
- Rotation is one `darwin-rebuild switch` away — no scrubbing of shell histories.
- `ps` listings never see the value (vs. one-shot `NOTION_TOKEN=ntn_… deno run …` invocations, which can briefly).

### 5. Share each page or database with the integration

> A new integration sees nothing in the workspace until pages are explicitly shared with it. This is the #1 source of "404 / object_not_found" errors after setup.

Per top-level page (children inherit):

1. Open the page in Notion.
2. Click `•••` (top-right corner of the page).
3. **Connections** → **Add connections** → search for the integration name → click it.
4. Confirm the access dialog.

Repeat for each top-level page or database the CLI should access.

### 6. Verify

Direct env var or alias route:
```sh
deno run \
  --allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE \
  --allow-net=api.notion.com \
  --allow-read=$HOME/.notion-cli \
  --allow-write=$HOME/.notion-cli \
  ~/.notion-cli/lib/notion.ts auth
```

File-based route (NOTION_TOKEN_FILE):
```sh
deno run \
  --allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE \
  --allow-net=api.notion.com \
  --allow-read=$HOME/.notion-cli \
  --allow-write=$HOME/.notion-cli \
  --allow-read=$NOTION_TOKEN_FILE \
  ~/.notion-cli/lib/notion.ts auth
```

Expected: a JSON object describing the bot user (`object: "user"`, `type: "bot"`, `bot.workspace_name`, etc.). If you get this, the token is valid.

Empty results from `notion search`? You haven't shared any pages with the integration yet — re-do step 5.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `401 unauthorized` on `auth` | Token wrong or revoked | Re-copy the Internal Integration Secret from the integration's Configuration tab. |
| `missing_token` (status 0) | None of `NOTION_TOKEN` / `NOTION_API_KEY` / `NOTION_TOKEN_FILE` is satisfied in the running shell | Pick one route from step 4 / 4b above. Remember `~/.zshrc` exports don't apply to already-open terminals. |
| `token_file_unreadable` | `NOTION_TOKEN_FILE` set but deno can't open it | Add `--allow-read=$NOTION_TOKEN_FILE` to the deno permission set. Also check the file mode (`stat -f '%Sp %Su:%Sg' $NOTION_TOKEN_FILE` — should be `r--------` and owned by you). |
| `empty_token_file` | The file exists but has zero bytes | The secrets manager hasn't materialized it yet. Run `darwin-rebuild switch` (agenix on macOS) / `home-manager switch` / re-run your `op read` or `pass show` step. |
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
