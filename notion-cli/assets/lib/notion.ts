// notion.ts — Notion REST API CLI on deno + npm:@notionhq/client@2.
//
// Run with:
//   deno run --allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE \
//     --allow-net=api.notion.com \
//     --allow-read=$HOME/.notion-cli --allow-write=$HOME/.notion-cli \
//     [--allow-read=$NOTION_TOKEN_FILE]   # add when resolving via file
//     <this> <command> [args]
//
// Token resolution order (first match wins):
//   1. NOTION_TOKEN         — direct value
//   2. NOTION_API_KEY       — alias (some setups standardize on this name)
//   3. NOTION_TOKEN_FILE    — path to a file whose contents are the token
//                             (use for sops-nix / agenix / 1Password CLI mounts)
//
// Never logs the token value — existence-only checks and read-then-discard.

// deno-lint-ignore-file no-explicit-any
import { Client } from "npm:@notionhq/client@2";

const HELP = `notion - operate Notion from the terminal via the official API.

Usage:
  notion <command> [subcommand] [options]

Commands:
  auth                          Smoke-test NOTION_TOKEN, show bot user
  search [query]                Search workspace pages and databases
                                Options: --filter pages|databases --limit N --start-cursor C
  page get <id>                 Retrieve a page
                                Options: --with-blocks
  page create                   Create a page
                                Options: --parent-db <id> | --parent-page <id> (one required)
                                         --title "<text>"   (required)
                                         --stdin            (read JSON {properties?, children?} from stdin)
  page update <id>              Update properties (reads JSON {properties: {...}} from stdin)
  page archive <id>             Archive (soft-delete) a page
  db get <id>                   Retrieve database schema
  db query <id>                 Query database rows
                                Options: --filter '<json>' --sorts '<json>'
                                         --limit N --start-cursor C
  db create                     Create a database under a parent page
                                Options: --parent-page <id>   (required)
                                         --name "<text>"      (required)
                                         --description "<text>"
                                         --schema-stdin       (read JSON {properties: {...}} from stdin)
  blocks list <id>              List top-level child blocks of a page or block
                                Options: --limit N --start-cursor C
  blocks append <id>            Append blocks (reads JSON array from stdin)
  blocks delete <id>            Delete a block
  users me                      Current bot user (alias for auth)
  users list                    List workspace users
                                Options: --limit N --start-cursor C
  users get <id>                Retrieve a single user

Global options:
  --format json|text            Output format (default: json)
  --help                        Show this message

Auth (any one of):
  NOTION_TOKEN           env var with the Internal Integration Secret.
  NOTION_API_KEY         env var alias (resolved if NOTION_TOKEN unset).
  NOTION_TOKEN_FILE      env var pointing at a file whose contents are the
                         token (e.g. agenix/sops-nix-managed file at
                         /run/agenix/<name>). Add --allow-read=<that-file>
                         to deno permissions when you use this.

  Get a token at https://www.notion.so/profile/integrations and share each
  target page or database with the integration (••• → Connections → Add).
  Full setup: references/auth-setup.md.
`;

// ── arg parsing ────────────────────────────────────────────────────

type Flags = Record<string, string | boolean>;

function parseArgv(
  argv: string[],
): { positional: string[]; flags: Flags } {
  const positional: string[] = [];
  const flags: Flags = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--") {
      positional.push(...argv.slice(i + 1));
      break;
    }
    if (a.startsWith("--")) {
      const eq = a.indexOf("=");
      if (eq !== -1) {
        flags[a.slice(2, eq)] = a.slice(eq + 1);
      } else {
        const next = argv[i + 1];
        if (next !== undefined && !next.startsWith("--")) {
          flags[a.slice(2)] = next;
          i++;
        } else {
          flags[a.slice(2)] = true;
        }
      }
    } else {
      positional.push(a);
    }
  }
  return { positional, flags };
}

// ── id normalization ───────────────────────────────────────────────

function normalizeId(input: string): string {
  // Accept full Notion URLs OR raw 32-char hex (with or without dashes).
  // A dashed form looks like 8-4-4-4-12.
  let s = input.trim();
  // Pull the trailing 32-hex chunk out of a URL if present.
  const fromUrl = s.match(/[0-9a-fA-F]{32}/);
  if (fromUrl) s = fromUrl[0];
  // If the user pasted with dashes already, strip them.
  s = s.replace(/-/g, "");
  if (!/^[0-9a-fA-F]{32}$/.test(s)) {
    throw new Error(
      `Invalid Notion id (expected 32-char hex or URL): ${input}`,
    );
  }
  // Re-insert dashes 8-4-4-4-12 (the SDK accepts both, but canonical helps).
  return `${s.slice(0, 8)}-${s.slice(8, 12)}-${s.slice(12, 16)}-${
    s.slice(16, 20)
  }-${s.slice(20)}`;
}

// ── token + client ─────────────────────────────────────────────────

function failMissingToken(): never {
  console.error(JSON.stringify({
    error: {
      status: 0,
      code: "missing_token",
      message:
        "No Notion token found. Set one of: NOTION_TOKEN (direct), NOTION_API_KEY (alias), or NOTION_TOKEN_FILE (path to a file containing the token). See references/auth-setup.md.",
    },
  }));
  Deno.exit(2);
}

function getToken(): string {
  // 1. Direct env var.
  const direct = Deno.env.get("NOTION_TOKEN");
  if (direct && direct.length > 0) return direct;

  // 2. Aliased env var.
  const alias = Deno.env.get("NOTION_API_KEY");
  if (alias && alias.length > 0) return alias;

  // 3. File reference (e.g. agenix / sops-nix mounts).
  const path = Deno.env.get("NOTION_TOKEN_FILE");
  if (path && path.length > 0) {
    try {
      const raw = Deno.readTextFileSync(path);
      const trimmed = raw.trim();
      if (trimmed.length === 0) {
        console.error(JSON.stringify({
          error: {
            status: 0,
            code: "empty_token_file",
            message:
              `NOTION_TOKEN_FILE points at a file with no content: ${path}`,
          },
        }));
        Deno.exit(2);
      }
      return trimmed;
    } catch (err) {
      const msg = (err as Error).message ?? String(err);
      console.error(JSON.stringify({
        error: {
          status: 0,
          code: "token_file_unreadable",
          message:
            `Could not read NOTION_TOKEN_FILE (${path}). Add --allow-read=${path} to deno permissions, or check the file mode/owner. Underlying error: ${msg}`,
        },
      }));
      Deno.exit(2);
    }
  }

  failMissingToken();
}

// Lazily-instantiated client so `--help` and arg-only paths don't require the env.
let _client: Client | null = null;
function client(): Client {
  if (!_client) _client = new Client({ auth: getToken() });
  return _client;
}

// ── output ─────────────────────────────────────────────────────────

function printJson(data: unknown) {
  console.log(JSON.stringify(data, null, 2));
}

function richTextToPlain(rt: any): string {
  if (!Array.isArray(rt)) return "";
  return rt.map((r: any) => r?.plain_text ?? "").join("");
}

function pageTitle(page: any): string {
  // Pages with a database parent: find the property with type === "title".
  const props = page?.properties ?? {};
  for (const v of Object.values(props)) {
    const p = v as any;
    if (p?.type === "title") return richTextToPlain(p.title);
  }
  // Pages with a page parent: top-level "title" key.
  if (Array.isArray((page as any)?.title)) {
    return richTextToPlain((page as any).title);
  }
  return "";
}

function dbTitle(db: any): string {
  if (Array.isArray(db?.title)) return richTextToPlain(db.title);
  return "";
}

function blockSummary(b: any): string {
  const t = b?.type;
  if (!t) return "";
  const inner = b[t];
  if (inner?.rich_text) return richTextToPlain(inner.rich_text);
  if (t === "child_page") return inner?.title ?? "";
  if (t === "child_database") return inner?.title ?? "";
  return "";
}

function printText(data: any) {
  const items = Array.isArray(data?.results)
    ? data.results
    : Array.isArray(data)
    ? data
    : [data];
  for (const item of items) printItem(item);
}

function printItem(item: any) {
  if (!item || typeof item !== "object") {
    console.log(String(item));
    return;
  }
  switch (item.object) {
    case "page": {
      const title = pageTitle(item) || "(untitled)";
      console.log(`page  ${item.id}  ${title}`);
      if (item.url) console.log(`        ${item.url}`);
      break;
    }
    case "database": {
      const title = dbTitle(item) || "(untitled)";
      console.log(`db    ${item.id}  ${title}`);
      if (item.url) console.log(`        ${item.url}`);
      break;
    }
    case "user": {
      const name = item.name ?? "(unnamed)";
      const type = item.type ?? "?";
      console.log(`user  ${item.id}  ${name}  (${type})`);
      break;
    }
    case "block": {
      const t = item.type ?? "?";
      const summary = blockSummary(item);
      console.log(`block ${item.id}  ${t}`);
      if (summary) console.log(`        ${summary}`);
      break;
    }
    default:
      printJson(item);
  }
}

// ── stdin helpers ──────────────────────────────────────────────────

async function readStdin(): Promise<string> {
  const chunks: Uint8Array[] = [];
  for await (const chunk of Deno.stdin.readable) chunks.push(chunk);
  let total = 0;
  for (const c of chunks) total += c.length;
  const buf = new Uint8Array(total);
  let off = 0;
  for (const c of chunks) {
    buf.set(c, off);
    off += c.length;
  }
  return new TextDecoder().decode(buf).trim();
}

async function readStdinJson<T = unknown>(): Promise<T> {
  const raw = await readStdin();
  if (!raw) throw new Error("Expected JSON on stdin (got empty input)");
  try {
    return JSON.parse(raw) as T;
  } catch (e) {
    throw new Error(`Invalid JSON on stdin: ${(e as Error).message}`);
  }
}

// ── error sanitization ─────────────────────────────────────────────

function sanitizeError(err: unknown): {
  status: number;
  code: string;
  message: string;
  hint?: string;
} {
  const e = err as any;
  const status = typeof e?.status === "number" ? e.status : 0;
  const code = typeof e?.code === "string" ? e.code : "unknown";
  const message = typeof e?.message === "string" ? e.message : String(err);
  let hint: string | undefined;
  if (status === 401 || code === "unauthorized") {
    hint = "Token wrong or revoked. Re-copy from https://www.notion.so/profile/integrations.";
  } else if (status === 403 || code === "restricted_resource") {
    hint = "Integration is missing a required capability — toggle it in the integration's settings.";
  } else if (status === 404 || code === "object_not_found") {
    hint = "Share the page/database with the integration in Notion (••• → Connections → Add connections).";
  } else if (status === 429 || code === "rate_limited") {
    hint = "Rate limited. Wait per Retry-After header and retry.";
  }
  return { status, code, message, hint };
}

function fail(err: unknown, format: string): never {
  const s = sanitizeError(err);
  if (format === "text") {
    console.error(
      `error: ${s.status} ${s.code}: ${s.message}` + (s.hint ? `\nhint: ${s.hint}` : ""),
    );
  } else {
    console.error(JSON.stringify({ error: s }));
  }
  Deno.exit(1);
}

// ── confirmation gate (destructive ops outside Claude) ─────────────
// When Claude orchestrates the skill, it confirms via the user before
// invoking. When this script is run directly from a terminal, we honor
// --yes for destructive ops. Otherwise we refuse, on principle.

function requireYes(flags: Flags, what: string) {
  if (flags.yes === true || flags.yes === "true") return;
  console.error(
    `Refusing destructive op (${what}) without --yes. ` +
      `Re-run with --yes if you're sure.`,
  );
  Deno.exit(2);
}

// ── command dispatch ───────────────────────────────────────────────

async function main(argv: string[]) {
  const { positional, flags } = parseArgv(argv);
  const format = (flags.format as string) || "json";

  if (flags.help === true || positional.length === 0) {
    console.log(HELP);
    Deno.exit(0);
  }

  const cmd = positional[0];
  const sub = positional[1];

  try {
    switch (cmd) {
      case "auth":
      case "users": {
        if (cmd === "users" && sub === "list") {
          const result = await client().users.list({
            page_size: clampLimit(flags.limit, 100),
            start_cursor: stringFlag(flags["start-cursor"]),
          });
          emit(result, format);
          return;
        }
        if (cmd === "users" && sub === "get") {
          const id = positional[2];
          if (!id) throw new Error("users get requires <user-id>");
          const u = await client().users.retrieve({ user_id: id });
          emit(u, format);
          return;
        }
        // auth, users me — both call /users/me.
        const me = await client().users.me({});
        emit(me, format);
        return;
      }

      case "search": {
        const query = positional.slice(1).filter((p) => !p.startsWith("--"))
          .join(" ");
        const filterFlag = stringFlag(flags.filter);
        const params: any = {
          page_size: clampLimit(flags.limit, 100),
          start_cursor: stringFlag(flags["start-cursor"]),
        };
        if (query) params.query = query;
        if (filterFlag) {
          if (filterFlag !== "page" && filterFlag !== "database" &&
              filterFlag !== "pages" && filterFlag !== "databases") {
            throw new Error(
              `--filter must be one of: pages, databases (got: ${filterFlag})`,
            );
          }
          // Notion expects singular "page" / "database".
          params.filter = {
            property: "object",
            value: filterFlag.replace(/s$/, ""),
          };
        }
        const result = await client().search(params);
        emit(result, format);
        return;
      }

      case "page": {
        if (sub === "get") {
          const id = normalizeId(requirePos(positional, 2, "page get <id>"));
          const page = await client().pages.retrieve({ page_id: id });
          if (flags["with-blocks"]) {
            const blocks = await client().blocks.children.list({
              block_id: id,
              page_size: 100,
            });
            emit({ page, blocks }, format);
          } else {
            emit(page, format);
          }
          return;
        }
        if (sub === "create") {
          const parentDb = stringFlag(flags["parent-db"]);
          const parentPage = stringFlag(flags["parent-page"]);
          const title = stringFlag(flags.title) ?? "Untitled";
          if (!parentDb && !parentPage) {
            throw new Error(
              "page create requires --parent-db <id> or --parent-page <id>",
            );
          }
          if (parentDb && parentPage) {
            throw new Error(
              "page create: pass only one of --parent-db / --parent-page",
            );
          }
          const parent: any = parentDb
            ? { database_id: normalizeId(parentDb) }
            : { page_id: normalizeId(parentPage!) };

          // Default title shape: for db parents, find the title-typed property.
          // For page parents, use the special top-level `title` property.
          let properties: Record<string, unknown>;
          let children: unknown[] | undefined;

          if (flags.stdin) {
            const body = await readStdinJson<{
              properties?: Record<string, unknown>;
              children?: unknown[];
            }>();
            children = body.children;
            properties = body.properties ?? {};
          } else {
            properties = {};
          }

          if (parentDb) {
            // Resolve title property name from db schema if user didn't set one.
            const haveTitleProp = Object.values(properties).some(
              (v: any) => v && typeof v === "object" && "title" in v,
            );
            if (!haveTitleProp) {
              const db = await client().databases.retrieve({
                database_id: normalizeId(parentDb),
              });
              const titlePropName = Object.entries((db as any).properties ?? {})
                .find(([_, p]) => (p as any).type === "title")?.[0] ?? "Name";
              properties[titlePropName] = {
                title: [{ type: "text", text: { content: title } }],
              };
            }
          } else {
            // page-parent: top-level "title" key
            if (!("title" in properties)) {
              properties.title = [{ type: "text", text: { content: title } }];
            }
          }

          const created = await client().pages.create({
            parent,
            properties: properties as any,
            children: children as any,
          });
          emit(created, format);
          return;
        }
        if (sub === "update") {
          const id = normalizeId(requirePos(positional, 2, "page update <id>"));
          const body = await readStdinJson<Record<string, unknown>>();
          const updated = await client().pages.update({
            page_id: id,
            ...body,
          } as any);
          emit(updated, format);
          return;
        }
        if (sub === "archive") {
          const id = normalizeId(requirePos(positional, 2, "page archive <id>"));
          requireYes(flags, "page archive");
          const archived = await client().pages.update({
            page_id: id,
            archived: true,
          });
          emit(archived, format);
          return;
        }
        throw new Error(`Unknown subcommand: page ${sub ?? ""}`);
      }

      case "db":
      case "database": {
        if (sub === "get") {
          const id = normalizeId(requirePos(positional, 2, "db get <id>"));
          const db = await client().databases.retrieve({ database_id: id });
          emit(db, format);
          return;
        }
        if (sub === "query") {
          const id = normalizeId(requirePos(positional, 2, "db query <id>"));
          const filter = stringFlag(flags.filter);
          const sorts = stringFlag(flags.sorts);
          const params: any = {
            database_id: id,
            page_size: clampLimit(flags.limit, 100),
            start_cursor: stringFlag(flags["start-cursor"]),
          };
          if (filter) {
            try {
              params.filter = JSON.parse(filter);
            } catch (e) {
              throw new Error(`--filter is not valid JSON: ${(e as Error).message}`);
            }
          }
          if (sorts) {
            try {
              params.sorts = JSON.parse(sorts);
            } catch (e) {
              throw new Error(`--sorts is not valid JSON: ${(e as Error).message}`);
            }
          }
          const result = await client().databases.query(params);
          emit(result, format);
          return;
        }
        if (sub === "create") {
          const parentPage = stringFlag(flags["parent-page"]);
          if (!parentPage) {
            throw new Error("db create requires --parent-page <id>");
          }
          const parentPageId = normalizeId(parentPage);
          const name = stringFlag(flags.name);
          if (!name) {
            throw new Error('db create requires --name "<text>"');
          }
          const description = stringFlag(flags.description);

          let properties: Record<string, unknown>;
          if (flags["schema-stdin"]) {
            const body = await readStdinJson<{
              properties?: Record<string, unknown>;
            }>();
            if (
              !body.properties ||
              typeof body.properties !== "object" ||
              Array.isArray(body.properties)
            ) {
              throw new Error(
                "db create --schema-stdin: stdin JSON must have an object 'properties'",
              );
            }
            properties = body.properties;
          } else {
            // Minimal default schema: a single title property named "Name"
            properties = { Name: { title: {} } };
          }

          const hasTitle = Object.values(properties).some(
            (v: any) => v && typeof v === "object" && "title" in v,
          );
          if (!hasTitle) {
            throw new Error(
              "db create: schema must include at least one property of type 'title'",
            );
          }

          // Reject silent overwrite — fail if a same-titled database already
          // exists under the same parent page.
          const existing = await client().search({
            query: name,
            filter: { value: "database", property: "object" },
            page_size: 50,
          });
          const conflict = (existing.results as any[]).find((db: any) => {
            if (db.object !== "database") return false;
            const titleStr = ((db.title ?? []) as any[])
              .map((t: any) => t.plain_text ?? "")
              .join("")
              .trim();
            if (titleStr !== name) return false;
            const parent = db.parent ?? {};
            if (parent.type !== "page_id") return false;
            try {
              return normalizeId(parent.page_id) === parentPageId;
            } catch {
              return false;
            }
          });
          if (conflict) {
            throw new Error(
              `db create: a database titled "${name}" already exists under parent ${parentPageId} (id: ${
                (conflict as any).id
              }). Refusing to silently overwrite.`,
            );
          }

          const params: any = {
            parent: { type: "page_id", page_id: parentPageId },
            title: [{ type: "text", text: { content: name } }],
            properties,
          };
          if (description) {
            params.description = [
              { type: "text", text: { content: description } },
            ];
          }

          const created = await client().databases.create(params);
          emit(created, format);
          return;
        }
        throw new Error(`Unknown subcommand: ${cmd} ${sub ?? ""}`);
      }

      case "blocks": {
        if (sub === "list") {
          const id = normalizeId(requirePos(positional, 2, "blocks list <id>"));
          const result = await client().blocks.children.list({
            block_id: id,
            page_size: clampLimit(flags.limit, 100),
            start_cursor: stringFlag(flags["start-cursor"]),
          });
          emit(result, format);
          return;
        }
        if (sub === "append") {
          const id = normalizeId(requirePos(positional, 2, "blocks append <id>"));
          const body = await readStdinJson<unknown>();
          const children = Array.isArray(body)
            ? body
            : (body as any)?.children;
          if (!Array.isArray(children)) {
            throw new Error(
              "blocks append: stdin must be a JSON array of blocks (or an object with .children).",
            );
          }
          const result = await client().blocks.children.append({
            block_id: id,
            children: children as any,
          });
          emit(result, format);
          return;
        }
        if (sub === "delete") {
          const id = normalizeId(requirePos(positional, 2, "blocks delete <id>"));
          requireYes(flags, "blocks delete");
          const result = await client().blocks.delete({ block_id: id });
          emit(result, format);
          return;
        }
        throw new Error(`Unknown subcommand: blocks ${sub ?? ""}`);
      }

      default:
        console.error(`Unknown command: ${cmd}`);
        console.error(HELP);
        Deno.exit(2);
    }
  } catch (err) {
    fail(err, format);
  }
}

function emit(data: unknown, format: string) {
  if (format === "text") printText(data);
  else printJson(data);
}

function requirePos(arr: string[], i: number, name: string): string {
  const v = arr[i];
  if (!v) throw new Error(`Missing argument: ${name}`);
  return v;
}

function stringFlag(v: string | boolean | undefined): string | undefined {
  if (typeof v === "string") return v;
  return undefined;
}

function clampLimit(v: string | boolean | undefined, max: number): number {
  if (typeof v !== "string") return max;
  const n = Number(v);
  if (!Number.isFinite(n) || n <= 0) return max;
  return Math.min(Math.floor(n), max);
}

await main(Deno.args);
