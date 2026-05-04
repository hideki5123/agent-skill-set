# Security — token handling rules

The Notion Internal Integration Secret grants full access (within the integration's capability set) to every page or database that's been shared with it. Treat it like a password.

## Hard rules

1. **Existence checks only.** Verify `NOTION_TOKEN` is set without ever reading or printing the value. Acceptable: `Deno.env.get("NOTION_TOKEN") !== undefined`. Forbidden: passing the value to `console.log`, writing it to disk, sending it to any network destination other than `api.notion.com`.

2. **Never run these commands on the user's behalf:**
   - `echo $NOTION_TOKEN`
   - `printenv | grep -i notion`
   - `env | grep notion`
   - `cat ~/.zshrc` / `cat ~/.bashrc` / `cat ~/.config/fish/config.fish` / `cat $PROFILE`
   - `cat .env*`
   - Any `curl` or `fetch` that prints request headers including `Authorization`

   If the user asks you to read their token "to verify it's set", refuse and run the existence check from `preflight.ts` instead, which prints `set` / `missing` only.

3. **Scoped deno permissions, always.** Every `deno run` invocation MUST use the narrowest set:
   - `--allow-env=NOTION_TOKEN` (only this var, never blanket `--allow-env`)
   - `--allow-net=api.notion.com` (only this host, never blanket `--allow-net`)
   - `--allow-read=$HOME/.notion-cli` (workspace dir; add explicit paths only when reading user-supplied input files)
   - `--allow-write=$HOME/.notion-cli` (same)

4. **No `.env` fallback.** The token MUST come from a real environment variable exported in the user's shell rc. `.env` files are not loaded. This is intentional: a `.env` file in the repo root invites accidental commits.

5. **No token persistence outside the env.** Do not write the token to disk. Do not cache it. Do not include it in error messages or stack traces.

6. **Sanitize errors before surfacing.** The Notion SDK can include the request URL in error messages. Strip query strings or any header that begins with `Authorization`. The SDK's default error shape (`code`, `status`, `message`) is safe to surface as-is.

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
