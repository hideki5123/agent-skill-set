# Audio — transcription, translation, TTS

OpenAI's audio APIs cover three flows:

- **Transcription** (speech → text in source language) → `client.audio.transcriptions.create`
- **Translation** (speech → English text) → `client.audio.translations.create`
- **Text-to-speech** (text → audio) → `client.audio.speech.create`

## Families and resolved models (as of 2026-04)

| Flow | Family | Current resolve | Notes |
|------|--------|-----------------|-------|
| Transcription | `transcription` | `gpt-4o-transcribe` | newer than whisper-1; whisper-1 still works as fallback |
| Translation | `transcription` | `whisper-1` | gpt-4o-transcribe is transcription-only; translations stay on whisper |
| Text-to-speech | `tts` | `tts-1-hd` | `gpt-4o-mini-tts` was deprecated in 2026 Q2 |

## Permissions

Base perms PLUS scoped read/write for I/O:

```
--allow-env=OPENAI_API_KEY
--allow-net=api.openai.com
--allow-read=$HOME/.openai-cli
--allow-write=$HOME/.openai-cli
--allow-read=<input-audio-path>      # transcription / translation
--allow-write=<output-audio-path>    # tts
```

## Transcription template

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();
const inputPath = "INPUT_AUDIO_PATH";   // .mp3, .m4a, .wav, .webm, etc.

const file = await Deno.open(inputPath, { read: true });

const r = await client.audio.transcriptions.create({
  model: "RESOLVED_ID",
  file: file.readable,
  // optional:
  // language: "en",                // ISO-639-1; speeds up if you know the source
  // prompt: "Glossary terms ...",  // bias the transcription toward expected vocab
  // response_format: "verbose_json", // gives timestamps; default "json" gives plain text
  // timestamp_granularities: ["segment", "word"],
});

console.log(r.text);
console.log(`# meta: model=RESOLVED_ID source=${inputPath}`);
```

For timestamped transcripts (subtitle generation):

```typescript
const r = await client.audio.transcriptions.create({
  model: "RESOLVED_ID",
  file: file.readable,
  response_format: "verbose_json",
  timestamp_granularities: ["segment"],
});

// Build a .vtt sidecar
const vtt = ["WEBVTT", ""];
for (const seg of r.segments ?? []) {
  vtt.push(`${formatTime(seg.start)} --> ${formatTime(seg.end)}`);
  vtt.push(seg.text.trim());
  vtt.push("");
}
function formatTime(s: number): string {
  const h = Math.floor(s / 3600).toString().padStart(2, "0");
  const m = Math.floor((s % 3600) / 60).toString().padStart(2, "0");
  const ss = (s % 60).toFixed(3).padStart(6, "0");
  return `${h}:${m}:${ss}`;
}
await Deno.writeTextFile(inputPath.replace(/\.[^.]+$/, ".vtt"), vtt.join("\n"));
```

(Add `--allow-write=<vtt-output-path>` to the deno run flags.)

## Translation template

Translates non-English audio into English text. Always uses `whisper-1` (gpt-4o-transcribe doesn't have a translation mode):

```typescript
const r = await client.audio.translations.create({
  model: "whisper-1",
  file: file.readable,
});
console.log(r.text);
console.log(`# meta: model=whisper-1 source=${inputPath}`);
```

This is one of the rare places the skill can name a literal model id (`whisper-1`) because the resolver returns `whisper-1` for translation — but prefer running `lib/resolveModel.ts transcription` and using the result.

## Text-to-speech template

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();
const outPath = "OUTPUT_AUDIO_PATH";   // e.g., $HOME/Downloads/hello.mp3

const r = await client.audio.speech.create({
  model: "RESOLVED_ID",
  voice: "alloy",          // alloy | ash | ballad | coral | echo | sage | shimmer | verse | ...
  input: "TEXT_TO_SPEAK",
  response_format: "mp3",  // mp3 | opus | aac | flac | wav | pcm
});

const buf = new Uint8Array(await r.arrayBuffer());
await Deno.writeFile(outPath, buf);

console.log(`wrote ${outPath} (${buf.length} bytes)`);
console.log(`# meta: model=RESOLVED_ID voice=alloy format=mp3`);
```

Voices, formats, and pricing all evolve — verify in the OpenAI docs. The skill resolves the model dynamically; the user can pin a voice via natural language ("use the sage voice").

## Cost-awareness

| Flow | Trigger gate when |
|------|-------------------|
| Transcription | Audio file > 25 MB (API has a hard 25 MB limit anyway — chunk first) or > 30 min |
| Translation | Same as transcription |
| TTS | Text > 4K characters |

The skill should also inspect the audio file size before sending; if > 25 MB, refuse and instruct the user to split or compress (e.g., `ffmpeg -i in.wav -b:a 64k out.mp3`).

## File size limit

OpenAI's audio endpoints accept files up to 25 MB. For longer recordings, split with ffmpeg before sending. The skill can shell out to ffmpeg via `--allow-run=ffmpeg` (only when the user explicitly approves) or instruct the user to split manually.
