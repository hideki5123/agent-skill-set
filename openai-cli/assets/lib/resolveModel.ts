// resolveModel.ts — model discovery and preference management for openai-cli.
//
// Modes:
//   resolveModel.ts <family>            Resolve and print the preferred model id
//                                       for the family. If a newer stable model
//                                       is detected vs the persisted preference,
//                                       prints UPGRADE_NEEDED:<family>:<current>:<newest>
//                                       and exits 2 (so the orchestrating skill
//                                       can prompt the user via AskUserQuestion).
//   resolveModel.ts --set <family> <id> Persist the user's choice to models.json.
//   resolveModel.ts --init              Initialize models.json from a fresh
//                                       models.list (used after first setup).
//
// Cross-OS. No bash.
//
// Permissions:
//   --allow-env=OPENAI_API_KEY
//   --allow-net=api.openai.com
//   --allow-read=$HOME/.openai-cli
//   --allow-write=$HOME/.openai-cli
//
// Exit codes:
//   0  success (resolved model id printed to stdout)
//   1  fatal error (e.g., OPENAI_API_KEY missing, models.json corrupt, no model found)
//   2  upgrade detected; UPGRADE_NEEDED line written to stdout

import OpenAI from "npm:openai@5";
import { join } from "jsr:@std/path@1";

type Family =
  | "chat"
  | "reasoning"
  | "embeddings"
  | "image"
  | "transcription"
  | "tts"
  | "moderation";

const FAMILIES: Family[] = [
  "chat",
  "reasoning",
  "embeddings",
  "image",
  "transcription",
  "tts",
  "moderation",
];

interface ModelsJson {
  version: number;
  preferenceMode: "stable" | "preview";
  preferred: Record<Family, string | null>;
  lastUpgradePromptedAt?: string;
}

interface CachedListEntry {
  id: string;
  created: number;
  object: string;
}

interface CachedList {
  fetchedAt: string;
  data: CachedListEntry[];
}

const TTL_MS = 60 * 60 * 1000; // 1 hour

function home(): string {
  const h = Deno.env.get("HOME") ?? Deno.env.get("USERPROFILE");
  if (!h) throw new Error("HOME/USERPROFILE not set");
  return h;
}

const workspace = join(home(), ".openai-cli");
const modelsJsonPath = join(workspace, "models.json");
const cacheDir = join(workspace, ".cache");
const cachePath = join(cacheDir, "models-list.json");

async function readJson<T>(p: string): Promise<T | null> {
  try {
    const txt = await Deno.readTextFile(p);
    return JSON.parse(txt) as T;
  } catch {
    return null;
  }
}

async function writeJson(p: string, v: unknown): Promise<void> {
  await Deno.writeTextFile(p, JSON.stringify(v, null, 2) + "\n");
}

function defaultModelsJson(): ModelsJson {
  return {
    version: 1,
    preferenceMode: "stable",
    preferred: {
      chat: null,
      reasoning: null,
      embeddings: null,
      image: null,
      transcription: null,
      tts: null,
      moderation: null,
    },
  };
}

function isPreview(id: string): boolean {
  return /(preview|alpha|beta|deprecated)/i.test(id);
}

// Family classifier — first-match wins. Order matters: more specific patterns first.
function classify(id: string): Family | null {
  if (id.includes("transcribe") || id.startsWith("whisper")) return "transcription";
  if (id.startsWith("tts-") || /-tts(-|$)/.test(id)) return "tts";
  if (id.startsWith("gpt-image-") || id.startsWith("dall-e-")) return "image";
  if (id.startsWith("text-embedding-")) return "embeddings";
  if (id.startsWith("omni-moderation-") || id.startsWith("text-moderation-")) return "moderation";
  if (/^o\d/.test(id)) return "reasoning";
  if (/^gpt-\d/.test(id)) return "chat";
  return null;
}

function pickNewest(
  list: CachedListEntry[],
  family: Family,
  mode: "stable" | "preview",
): string | null {
  let candidates = list.filter((m) => classify(m.id) === family);
  if (mode === "stable") candidates = candidates.filter((m) => !isPreview(m.id));

  // Family-specific ordering: prefer modern variant first, then newest by `created`.
  const score = (id: string): number => {
    if (family === "moderation") return id.startsWith("omni-") ? 1 : 0;
    if (family === "image") return id.startsWith("gpt-image-") ? 1 : 0;
    if (family === "embeddings") return id.includes("-large") ? 1 : 0;
    return 0;
  };

  candidates.sort((a, b) => {
    const sa = score(a.id);
    const sb = score(b.id);
    if (sa !== sb) return sb - sa;
    return b.created - a.created;
  });

  return candidates[0]?.id ?? null;
}

async function fetchListWithCache(client: OpenAI): Promise<CachedList> {
  const cached = await readJson<CachedList>(cachePath);
  if (cached && Date.now() - new Date(cached.fetchedAt).getTime() < TTL_MS) {
    return cached;
  }
  const fresh = await client.models.list();
  const data: CachedListEntry[] = fresh.data.map((m) => ({
    id: m.id,
    created: m.created,
    object: m.object,
  }));
  const newCached: CachedList = {
    fetchedAt: new Date().toISOString(),
    data,
  };
  await Deno.mkdir(cacheDir, { recursive: true });
  await writeJson(cachePath, newCached);
  return newCached;
}

async function cmdResolve(family: Family): Promise<void> {
  if (!FAMILIES.includes(family)) {
    console.error(`unknown family: ${family}`);
    Deno.exit(1);
  }
  const json = (await readJson<ModelsJson>(modelsJsonPath)) ??
    defaultModelsJson();

  let cache: CachedList;
  try {
    const client = new OpenAI();
    cache = await fetchListWithCache(client);
  } catch (e) {
    const fallback = json.preferred[family];
    if (fallback) {
      console.error(
        `# warn: models.list failed (${(e as Error).message}); using preferred`,
      );
      console.log(fallback);
      Deno.exit(0);
    }
    console.error(
      `fatal: models.list failed and no preferred model recorded for "${family}".`,
    );
    console.error((e as Error).message);
    Deno.exit(1);
  }

  const newest = pickNewest(cache.data, family, json.preferenceMode);
  if (!newest) {
    const fallback = json.preferred[family];
    if (fallback) {
      console.log(fallback);
      Deno.exit(0);
    }
    console.error(
      `fatal: no model found for family "${family}" and no preferred recorded.`,
    );
    Deno.exit(1);
  }

  const current = json.preferred[family];

  if (!current) {
    json.preferred[family] = newest;
    await writeJson(modelsJsonPath, json);
    console.log(newest);
    return;
  }

  if (current === newest) {
    console.log(newest);
    return;
  }

  // Upgrade detected — emit signal, exit 2. The orchestrator handles AskUserQuestion.
  console.log(`UPGRADE_NEEDED:${family}:${current}:${newest}`);
  Deno.exit(2);
}

async function cmdSet(family: Family, modelId: string): Promise<void> {
  if (!FAMILIES.includes(family)) {
    console.error(`unknown family: ${family}`);
    Deno.exit(1);
  }
  const json = (await readJson<ModelsJson>(modelsJsonPath)) ??
    defaultModelsJson();
  json.preferred[family] = modelId;
  json.lastUpgradePromptedAt = new Date().toISOString();
  await writeJson(modelsJsonPath, json);
  console.log(`set preferred.${family} = ${modelId}`);
}

async function cmdInit(): Promise<void> {
  const json = defaultModelsJson();
  const client = new OpenAI();
  const cache = await fetchListWithCache(client);
  for (const f of FAMILIES) {
    json.preferred[f] = pickNewest(cache.data, f, json.preferenceMode);
  }
  await writeJson(modelsJsonPath, json);
  console.log("models.json initialized");
  console.log(JSON.stringify(json.preferred, null, 2));
}

const [arg0, arg1, arg2] = Deno.args;
if (arg0 === "--set") {
  if (!arg1 || !arg2) {
    console.error("usage: resolveModel.ts --set <family> <id>");
    Deno.exit(1);
  }
  await cmdSet(arg1 as Family, arg2);
} else if (arg0 === "--init") {
  await cmdInit();
} else if (arg0) {
  await cmdResolve(arg0 as Family);
} else {
  console.error(
    "usage:\n  resolveModel.ts <family>\n  resolveModel.ts --set <family> <id>\n  resolveModel.ts --init",
  );
  Deno.exit(1);
}
