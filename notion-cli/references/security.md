# Security — token handling rules

The Notion Internal Integration Secret grants full access (within the integration's capability set) to every page or database that's been shared with it. Treat it like a password.

## Hard rules

1. **Existence checks only.** Verify a token source resolves without ever reading or printing the value. The CLI checks three sources in order: `NOTION_TOKEN`, `NOTION_API_KEY`, then the file at `NOTION_TOKEN_FILE`. Acceptable: `Deno.env.get("NOTION_TOKEN") !== undefined`, `Deno.stat(tokenFilePath)` (size, mode — not contents). Forbidden: passing any of these values to `console.log`, writing to disk, sending to any network destination other than `api.notion.com`.

2. **Never run these commands on the user's behalf:**
   - `echo $NOTION_TOKEN` / `echo $NOTION_API_KEY`
   - `printenv | grep -i notion` / `env | grep notion`
   - `cat ~/.zshrc` / `cat ~/.bashrc` / `cat ~/.config/fish/config.fish` / `cat $PROFILE`
   - `cat .env*`
   - `cat $NOTION_TOKEN_FILE` (or any other path the user uses as a token source — agenix, sops-nix, 1Password CLI mounts, etc.)
   - Any `curl` or `fetch` that prints request headers including `Authorization`
   - Any `ps`/`top`-style command that could leak a value passed on a command line

   If the user asks you to read their token "to verify it's set", refuse and run the existence check from `preflight.ts` instead, which only reports the resolved source name (e.g. `token: NOTION_API_KEY` or `token: NOTION_TOKEN_FILE → /run/agenix/notion-api-key (51 bytes)`).

3. **Scoped deno permissions, always.** Every `deno run` invocation MUST use the narrowest set:
   - `--allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE` (only these three vars, never blanket `--allow-env`)
   - `--allow-net=api.notion.com` (only this host, never blanket `--allow-net`)
   - `--allow-read=$HOME/.notion-cli` (workspace dir; add explicit paths only when reading user-supplied input files)
   - `--allow-write=$HOME/.notion-cli` (same)
   - `--allow-read=$NOTION_TOKEN_FILE` only when the user resolves their token via a file (route (c) of the auth flow). This is exactly that one path — never `--allow-read=/run/agenix/` or any directory.

4. **No `.env` fallback.** The token MUST come from one of the three approved sources (env var, alias env var, or env-var-pointed file). `.env` files are not loaded. This is intentional: a `.env` file in the repo root invites accidental commits.

5. **No token persistence outside the env / file source.** Do not write the token to disk (other than the secrets-manager-managed file the user already maintains). Do not cache it. Do not include it in error messages or stack traces. When reading from a file, the token is held in memory for one HTTP client and discarded.

6. **Sanitize errors before surfacing.** The Notion SDK can include the request URL in error messages. Strip query strings or any header that begins with `Authorization`. The SDK's default error shape (`code`, `status`, `message`) is safe to surface as-is.

7. **Never pass the token on a command line.** Command-line args are visible to other users via `ps`. Do not invoke the CLI as `NOTION_TOKEN=ntn_… deno run …` followed by a value pasted from chat. Use the file route (option (c)) when in doubt — `cat /run/agenix/notion-api-key` does not expose the value to `ps`, and the CLI reads it directly.

## Token leak playbook

If the token is leaked (pasted into a chat the user didn't intend, committed to a repo, screenshotted into a ticket, etc.):

1. Open <https://www.notion.so/profile/integrations>.
2. Pick the integration → Configuration tab → **Internal Integration Secret** → **Regenerate token**.
3. Update `NOTION_TOKEN` in the user's shell rc and re-source.
4. Old token is invalidated immediately; any cached copy fails with `401`.
5. Audit: in Notion's audit log (Settings → Workspace → Identity & provisioning, on plans that include it), check for unexpected page accesses since the leak window.

## What "secret" means here

A Notion Internal Integration Secret can:

- Read every page and every database that's been shared with the integration.
- Write to / archive any page or database the integration has been shared with.
- Read workspace user list (if the capability is enabled).

It cannot:

- Read pages that haven't been shared with the integration (this is a strong default).
- Cross workspaces (each integration is bound to one workspace).
- Access the OAuth-authorized scopes of any user.

Even with the strong default, if the integration has been added to the workspace's "Everyone" page or to a top-level page that contains everything else, the token has effectively full read/write across the workspace. Treat any leak as full-workspace exposure until you confirm scope.
