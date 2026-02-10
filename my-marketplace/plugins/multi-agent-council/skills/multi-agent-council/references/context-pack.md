# Context Pack Reference

## Overview

Context Packs are structured representations of project state sent to external LLMs. They ensure consistent, safe, and efficient transmission of project information.

## Design Principles

1. **Structured, not raw**: Never send raw project files directly; always pack
2. **Egress control**: Built-in exclusions for credentials and unnecessary data
3. **Size management**: Full vs Summary packs for different constraints
4. **Cross-platform**: Handle path/encoding differences internally

## Project Snapshot

Before creating a Context Pack, the project state is captured as a Snapshot.

### SnapshotScanner

Scans the project directory and produces a normalized representation.

```typescript
interface ProjectSnapshot {
  // Location
  root_path: string;
  scan_timestamp: string;

  // Structure
  directory_tree: DirectoryNode;
  total_files: number;
  total_directories: number;
  total_size_bytes: number;

  // File metadata
  files: FileMetadata[];

  // Exclusions
  excluded_files: ExcludedFile[];
  exclusion_stats: {
    by_pattern: number;
    by_size: number;
    by_binary: number;
    by_credentials: number;
  };
}

interface DirectoryNode {
  name: string;
  path: string;
  children: (DirectoryNode | FileNode)[];
}

interface FileNode {
  name: string;
  path: string;
  size_bytes: number;
  type: FileType;
}

interface FileMetadata {
  path: string;
  relative_path: string;
  name: string;
  extension: string;
  size_bytes: number;
  type: FileType;
  category: FileCategory;
  is_key_file: boolean;
  content_extractable: boolean;
}

type FileType = "text" | "binary" | "image" | "data" | "unknown";

type FileCategory =
  | "config"        // package.json, tsconfig.json, etc.
  | "entrypoint"    // main.ts, index.js, app.py
  | "auth"          // auth.ts, login.js, etc.
  | "api"           // routes, controllers, handlers
  | "database"      // models, migrations, queries
  | "test"          // test files
  | "documentation" // markdown, docs
  | "build"         // build outputs
  | "dependency"    // node_modules, vendor
  | "source"        // general source code
  | "other";

interface ExcludedFile {
  path: string;
  reason: ExclusionReason;
}

type ExclusionReason =
  | "credentials"      // Contains secrets
  | "binary"           // Non-text file
  | "size_limit"       // Exceeds size limit
  | "pattern_match"    // Matches exclusion pattern
  | "dependency_dir"   // node_modules, vendor, etc.
  | "build_output"     // dist, build, etc.
  | "cache";           // .cache, __pycache__, etc.
```

## Context Pack Types

### Full Pack

Default pack type. Attempts to include complete project information.

```typescript
interface FullPack {
  type: "full";

  // Project overview
  manifest: Manifest;

  // File listing
  file_index: FileIndexEntry[];

  // Key files with content
  key_files: KeyFile[];

  // All extractable content
  contents: FileContent[];

  // Metadata
  metadata: PackMetadata;
}

interface Manifest {
  project_name: string;       // Inferred or from package.json
  project_type: string;       // "node", "python", "rust", etc.
  purpose_guess: string;      // Brief description of what project does
  structure_summary: string;  // High-level structure description
  dependencies: Dependency[]; // Major dependencies
  entry_points: string[];     // Main entry files
  build_system?: string;      // npm, cargo, make, etc.
  test_framework?: string;    // jest, pytest, etc.
}

interface Dependency {
  name: string;
  version?: string;
  type: "runtime" | "dev" | "peer";
}

interface FileIndexEntry {
  path: string;
  type: FileType;
  category: FileCategory;
  size_bytes: number;
  included: boolean;
  exclusion_reason?: ExclusionReason;
}

interface KeyFile {
  path: string;
  category: FileCategory;
  importance: "critical" | "high" | "medium";
  content: string;
  truncated: boolean;
}

interface FileContent {
  path: string;
  content: string;
  truncated: boolean;
  original_size_bytes: number;
}

interface PackMetadata {
  pack_type: "full" | "summary";
  created_at: string;
  source_root: string;
  total_files_scanned: number;
  files_included: number;
  files_excluded: number;
  total_content_bytes: number;
  truncation_applied: boolean;
}
```

### Summary Pack

Used when Full Pack exceeds limits or by configuration.

```typescript
interface SummaryPack {
  type: "summary";

  // Project overview (same as Full)
  manifest: Manifest;

  // File listing (same as Full)
  file_index: FileIndexEntry[];

  // Summarized content
  repo_summary: RepoSummary;
  key_files_summary: KeyFileSummary[];
  entrypoints: EntrypointSummary[];
  risk_hotspots: RiskHotspot[];

  // Metadata
  metadata: PackMetadata;
}

interface RepoSummary {
  description: string;           // 2-3 paragraph overview
  architecture_pattern: string;  // MVC, microservices, monolith, etc.
  key_technologies: string[];
  notable_patterns: string[];
  potential_concerns: string[];
}

interface KeyFileSummary {
  path: string;
  category: FileCategory;
  summary: string;               // What this file does
  exports: string[];             // Key exports/interfaces
  dependencies: string[];        // What it imports
  notable_code: string[];        // Important patterns/logic
}

interface EntrypointSummary {
  path: string;
  type: "cli" | "web" | "api" | "library" | "script";
  description: string;
  routes_or_commands?: string[];
}

interface RiskHotspot {
  path: string;
  risk_type: "security" | "performance" | "complexity" | "coupling";
  description: string;
  indicators: string[];
}
```

## Pack Selection

### PackSelector

Determines whether to use Full or Summary pack.

```typescript
interface PackSelector {
  select(snapshot: ProjectSnapshot, constraints: PackConstraints): PackType;
}

interface PackConstraints {
  max_content_bytes?: number;    // Default: 500KB
  max_files?: number;            // Default: 200
  prefer_summary?: boolean;      // Force summary
  provider_limits?: {
    [provider: string]: number;  // Provider-specific limits
  };
}
```

**Selection Logic**:
1. If `prefer_summary` is true → Summary
2. Calculate Full Pack size estimate
3. If exceeds `max_content_bytes` → Summary
4. If file count exceeds `max_files` → Summary
5. Otherwise → Full

### FullPackBuilder

```typescript
interface FullPackBuilder {
  build(snapshot: ProjectSnapshot, constraints: PackConstraints): FullPack;
}
```

**Building Steps**:
1. Generate Manifest from snapshot
2. Create FileIndex from file metadata
3. Identify and extract key files
4. Extract all text content (with truncation)
5. Generate metadata

### SummaryPackBuilder

```typescript
interface SummaryPackBuilder {
  build(snapshot: ProjectSnapshot, constraints: PackConstraints): SummaryPack;
}
```

**Building Steps**:
1. Generate Manifest (same as Full)
2. Create FileIndex (same as Full)
3. Generate RepoSummary from structure + key files
4. Summarize key files (not full content)
5. Identify entrypoints
6. Detect risk hotspots
7. Generate metadata

## Exclusion Rules

### Default Exclusion Patterns

```yaml
credentials:
  - "**/*.pem"
  - "**/*.key"
  - "**/*.crt"
  - "**/*.p12"
  - "**/.env*"
  - "**/credentials*"
  - "**/secrets*"
  - "**/*_secret*"
  - "**/*_token*"
  - "**/*.keystore"

dependencies:
  - "**/node_modules/**"
  - "**/vendor/**"
  - "**/.venv/**"
  - "**/venv/**"
  - "**/env/**"
  - "**/__pypackages__/**"
  - "**/packages/*/node_modules/**"

build_outputs:
  - "**/dist/**"
  - "**/build/**"
  - "**/out/**"
  - "**/target/**"
  - "**/.next/**"
  - "**/.nuxt/**"
  - "**/coverage/**"

caches:
  - "**/.cache/**"
  - "**/__pycache__/**"
  - "**/*.pyc"
  - "**/.pytest_cache/**"
  - "**/.eslintcache"
  - "**/.tsbuildinfo"

large_data:
  - "**/*.sql"          # Database dumps
  - "**/*.db"
  - "**/*.sqlite*"
  - "**/*.log"
  - "**/logs/**"

binaries:
  - "**/*.exe"
  - "**/*.dll"
  - "**/*.so"
  - "**/*.dylib"
  - "**/*.wasm"
  - "**/*.png"
  - "**/*.jpg"
  - "**/*.jpeg"
  - "**/*.gif"
  - "**/*.ico"
  - "**/*.svg"
  - "**/*.mp4"
  - "**/*.mp3"
  - "**/*.pdf"
  - "**/*.zip"
  - "**/*.tar*"
  - "**/*.gz"

version_control:
  - "**/.git/**"
  - "**/.svn/**"
  - "**/.hg/**"
```

### Exclusion Customization (TBD)

Future: Allow user/project-level customization via:
- `.councilignore` file
- Skill configuration
- Runtime parameters

## Key File Detection

### KeyFileDetector

Identifies files that are critical for understanding the project.

**Detection Criteria**:

| Category | Patterns | Priority |
|----------|----------|----------|
| Config | `package.json`, `tsconfig.json`, `pyproject.toml`, etc. | Critical |
| Entrypoint | `main.*`, `index.*`, `app.*`, `server.*` | Critical |
| Auth | `*auth*`, `*login*`, `*session*`, `*jwt*` | High |
| API | `*route*`, `*controller*`, `*handler*`, `*api*` | High |
| Database | `*model*`, `*schema*`, `*migration*` | High |
| Security | `*permission*`, `*rbac*`, `*acl*` | High |

### Key File Limits

```yaml
key_files:
  max_per_category: 5
  max_total: 25
  max_content_per_file_bytes: 50000
  prioritize_by:
    - category_importance
    - file_size (smaller preferred)
    - path_depth (shallower preferred)
```

## Content Truncation

When files exceed limits, truncation is applied.

```typescript
interface TruncationConfig {
  max_file_bytes: number;        // Default: 50KB per file
  max_total_bytes: number;       // Default: 500KB total
  preserve_head_lines: number;   // Keep first N lines
  preserve_tail_lines: number;   // Keep last N lines
  truncation_marker: string;     // e.g., "\n... [truncated] ...\n"
}
```

**Truncation Strategy**:
1. Keep first `preserve_head_lines` (default: 100)
2. Keep last `preserve_tail_lines` (default: 50)
3. Insert truncation marker between
4. Mark file as `truncated: true` in metadata

## Cross-Platform Handling

### Path Normalization

```typescript
function normalizePath(path: string): string {
  // Convert Windows backslashes to forward slashes
  // Remove drive letters for consistency
  // Ensure consistent separator
}
```

### Encoding Handling

```typescript
interface EncodingConfig {
  default_encoding: "utf-8";
  fallback_encodings: ["utf-16", "latin-1"];
  on_decode_error: "replace" | "skip";
}
```

- Try UTF-8 first
- Fall back to other encodings
- Replace undecodable characters with placeholder
- Log encoding issues in metadata

## Pack Serialization

Context Packs are serialized for transmission.

```typescript
interface PackSerializer {
  serialize(pack: ContextPack): string;
  deserialize(data: string): ContextPack;
}
```

**Format Options**:
- JSON (default): Human-readable, good for debugging
- MessagePack: Smaller, faster (future option)

## Usage Example

```typescript
// 1. Scan project
const scanner = new SnapshotScanner();
const snapshot = await scanner.scan("/path/to/project");

// 2. Select pack type
const selector = new PackSelector();
const packType = selector.select(snapshot, {
  max_content_bytes: 500000,
  max_files: 200
});

// 3. Build pack
const pack = packType === "full"
  ? new FullPackBuilder().build(snapshot, constraints)
  : new SummaryPackBuilder().build(snapshot, constraints);

// 4. Serialize for transmission
const serialized = new PackSerializer().serialize(pack);
```

## Transparency Integration

Pack creation is logged in the Transparency Record:

```yaml
context_pack_info:
  type: "full" | "summary"
  selection_reason: string
  files_scanned: number
  files_included: number
  files_excluded: number
  exclusions_by_reason:
    credentials: number
    binary: number
    size: number
    pattern: number
  content_bytes: number
  truncated_files: number
```
