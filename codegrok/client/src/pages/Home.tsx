/* Signal Yard / Codegrok page: expressive shell, precise data surfaces, and calm readable code. */
import { FormEvent, KeyboardEvent, useEffect, useMemo, useState } from "react";
import Prism from "prismjs";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-typescript";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Braces,
  Check,
  ChevronDown,
  CircleDot,
  Clipboard,
  Code2,
  Command,
  Database,
  FileCode2,
  FolderTree,
  Github,
  Hash,
  Layers3,
  LoaderCircle,
  PanelLeft,
  Search,
  Send,
  SlidersHorizontal,
  Sparkles,
  TriangleAlert,
  UploadCloud,
  X,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const API_KEY = import.meta.env.VITE_API_KEY || "";
const API_HEADERS = { "Content-Type": "application/json", "X-Codegrok-Key": API_KEY };

type AstType = "all" | "function_declaration" | "method_definition" | "arrow_function";
type SearchResult = {
  id: number;
  file_path: string;
  function_name: string;
  ast_type: Exclude<AstType, "all">;
  start_line: number;
  end_line: number;
  code_text: string;
  similarity: number;
};

type IngestState = "idle" | "loading" | "success" | "error";

type Notice = { tone: "success" | "error"; message: string } | null;

const TYPE_META: Record<Exclude<AstType, "all">, { label: string; short: string; className: string }> = {
  function_declaration: { label: "Function", short: "FN", className: "type-function" },
  method_definition: { label: "Method", short: "MT", className: "type-method" },
  arrow_function: { label: "Arrow", short: "AR", className: "type-arrow" },
};

const DEMO_RESULTS: SearchResult[] = [
  {
    id: 601,
    file_path: "./src/validators/email.ts",
    function_name: "isValidEmail",
    ast_type: "function_declaration",
    start_line: 12,
    end_line: 23,
    code_text: `export function isValidEmail(value: string) {\n  const normalized = value.trim().toLowerCase();\n  return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(normalized);\n}`,
    similarity: 0.612,
  },
  {
    id: 602,
    file_path: "./src/forms/SignupForm.tsx",
    function_name: "validateFields",
    ast_type: "method_definition",
    start_line: 86,
    end_line: 100,
    code_text: `validateFields(fields: FormFields) {\n  const errors: Record<string, string> = {};\n  if (!fields.email || !isValidEmail(fields.email)) {\n    errors.email = \"Enter a valid email address\";\n  }\n  return errors;\n}`,
    similarity: 0.566,
  },
  {
    id: 603,
    file_path: "./lib/guards/contact.ts",
    function_name: "anonymous",
    ast_type: "arrow_function",
    start_line: 31,
    end_line: 37,
    code_text: `const hasContactEmail = (contact?: Contact) => {\n  if (!contact?.email) return false;\n  return contact.email.includes(\"@\");\n};`,
    similarity: 0.489,
  },
];

function formatScore(score: number) {
  return `${Math.round(score * 100)}%`;
}

function highlightCode(code: string) {
  return Prism.highlight(code, Prism.languages.typescript, "typescript");
}

function prettyPath(filePath: string) {
  return filePath.split("/").filter(Boolean);
}

function TypeBadge({ type }: { type: SearchResult["ast_type"] }) {
  const meta = TYPE_META[type];
  return (
    <span className={cn("type-badge", meta.className)}>
      <span className="type-badge__sigil">{meta.short}</span>
      {meta.label}
    </span>
  );
}

function BrandMark({ small = false }: { small?: boolean }) {
  return (
    <div className={cn("brand-mark", small && "brand-mark--small")} aria-hidden="true">
      <span className="brand-mark__glyph">{"{}"}</span>
    </div>
  );
}

function AppHeader({ onMenu, apiOnline }: { onMenu: () => void; apiOnline: boolean }) {
  return (
    <header className="topbar">
      <div className="topbar__mobile-brand">
        <button className="icon-button icon-button--quiet" onClick={onMenu} aria-label="Toggle navigation">
          <PanelLeft size={18} />
        </button>
        <BrandMark small />
        <span className="mobile-wordmark">codegrok</span>
      </div>
      <div className="breadcrumb-line">
        <span className="crumb-dot" />
        <span>WORKSPACE</span>
        <span className="crumb-slash">/</span>
        <strong>SEMANTIC SEARCH</strong>
      </div>
      <div className="topbar__actions">
        <span className={cn("api-status", !apiOnline && "api-status--offline")}><span className="status-pulse" /> API {apiOnline ? "ONLINE" : "OFFLINE"}</span>
        <div className="topbar__divider" />
        <button className="icon-button icon-button--quiet" aria-label="Keyboard shortcuts"><Command size={17} /></button>
        <button className="avatar-button" aria-label="Current user">CG</button>
      </div>
    </header>
  );
}

function SideRail({ activeView, onNavigate, isIndexed }: { activeView: "search" | "ingest"; onNavigate: (view: "search" | "ingest") => void; isIndexed: boolean }) {
  return (
    <aside className="side-rail">
      <div className="side-rail__brand">
        <BrandMark />
        <div>
          <div className="wordmark">codegrok<span className="wordmark__dot">.</span></div>
          <div className="wordmark__sub">semantic code search</div>
        </div>
      </div>

      <div className="rail-kicker"><span>01</span> NAVIGATE</div>
      <nav className="rail-nav" aria-label="Primary">
        <button className={cn("rail-nav__item", activeView === "search" && "rail-nav__item--active")} onClick={() => onNavigate("search")}>
          <Search size={17} />
          <span>Search code</span>
          <ArrowUpRight className="rail-nav__arrow" size={15} />
        </button>
        <button className={cn("rail-nav__item", activeView === "ingest" && "rail-nav__item--active")} onClick={() => onNavigate("ingest")}>
          <UploadCloud size={17} />
          <span>Index repository</span>
          {isIndexed ? <Check className="rail-nav__check" size={15} /> : <span className="rail-nav__count">1</span>}
        </button>
      </nav>

      <div className="rail-kicker rail-kicker--lower"><span>02</span> CONTEXT</div>
      <div className="context-card">
        <div className="context-card__top"><Database size={14} /><span>INDEX STATUS</span></div>
        <div className="context-card__value">{isIndexed ? "READY" : "WAITING"}</div>
        <div className="context-card__bar"><span style={{ width: isIndexed ? "100%" : "12%" }} /></div>
        <p>{isIndexed ? "Search is unlocked across your indexed repository." : "Index a repository to unlock semantic search."}</p>
      </div>

      <div className="side-rail__footer">
        <div className="rail-telemetry"><span className="telemetry-dot" /> LOCAL WORKSPACE</div>
        <a href="https://github.com" target="_blank" rel="noreferrer" className="rail-github"><Github size={15} /> View on GitHub</a>
        <span className="rail-version">v0.1.0 / fastapi bridge</span>
      </div>
    </aside>
  );
}

function IngestPanel({
  repoPath,
  repoName,
  setRepoPath,
  setRepoName,
  ingestState,
  notice,
  totalChunks,
  onSubmit,
}: {
  repoPath: string;
  repoName: string;
  setRepoPath: (value: string) => void;
  setRepoName: (value: string) => void;
  ingestState: IngestState;
  notice: Notice;
  totalChunks: number | null;
  onSubmit: (event: FormEvent) => void;
}) {
  const isLoading = ingestState === "loading";
  return (
    <section className="ingest-panel panel-outline" id="ingest-panel">
      <div className="panel-corner panel-corner--tl" />
      <div className="panel-corner panel-corner--br" />
      <div className="section-eyebrow section-eyebrow--light"><span className="eyebrow-index">01</span> LOAD YOUR CODEBASE</div>
      <div className="ingest-panel__heading">
        <div>
          <h2>Put a codebase<br /><em>on the map.</em></h2>
          <p>Point Codegrok at a local repository. We’ll parse the functions, embed their meaning, and build your private search layer.</p>
        </div>
        <div className="ingest-orbit" aria-hidden="true"><div className="orbit-ring orbit-ring--one" /><div className="orbit-ring orbit-ring--two" /><span>AST<br />→<br />VECTOR</span></div>
      </div>

      <form onSubmit={onSubmit} className="ingest-form">
        <label className="field-label" htmlFor="repoPath">REPOSITORY PATH <span>LOCAL FS</span></label>
        <div className="field-shell"><FolderTree size={17} /><Input id="repoPath" value={repoPath} onChange={(event) => setRepoPath(event.target.value)} placeholder="/Users/you/projects/my-repo" disabled={isLoading} /></div>
        <label className="field-label" htmlFor="repoName">DISPLAY NAME <span>OPTIONAL HANDLE</span></label>
        <div className="field-shell"><Code2 size={17} /><Input id="repoName" value={repoName} onChange={(event) => setRepoName(event.target.value)} placeholder="my-repo" disabled={isLoading} /></div>
        <Button type="submit" className="index-button" disabled={isLoading || !repoPath.trim()}>
          {isLoading ? <><LoaderCircle className="spin" size={17} /> INDEXING REPOSITORY…</> : <><Zap size={17} /> INDEX REPOSITORY <ArrowUpRight size={16} /></>}
        </Button>
      </form>

      {isLoading && <div className="index-progress"><div className="index-progress__top"><span><span className="live-dot" /> Indexing repository…</span><span>usually 30 sec – 3 min</span></div><div className="index-progress__track"><span /></div><div className="index-progress__note">Parsing functions and methods · generating semantic embeddings · storing vectors</div></div>}
      {notice?.tone === "success" && <div className="notice notice--success"><Check size={17} /><div><strong>Repository indexed.</strong><span>{totalChunks?.toLocaleString()} semantic chunks are ready to search.</span></div></div>}
      {notice?.tone === "error" && <div className="notice notice--error"><TriangleAlert size={17} /><div><strong>Indexing paused.</strong><span>{notice.message}</span></div></div>}
    </section>
  );
}

function SearchPanel({
  query,
  setQuery,
  filter,
  setFilter,
  isIndexed,
  isSearching,
  onSubmit,
  onExample,
}: {
  query: string;
  setQuery: (value: string) => void;
  filter: AstType;
  setFilter: (value: AstType) => void;
  isIndexed: boolean;
  isSearching: boolean;
  onSubmit: (event: FormEvent) => void;
  onExample: (value: string) => void;
}) {
  const locked = !isIndexed;
  return (
    <section className={cn("search-panel", locked && "search-panel--locked")} id="search-panel">
      <div className="search-panel__backdrop" />
      <div className="section-eyebrow"><span className="eyebrow-index">02</span> ASK THE CODEBASE</div>
      <div className="search-panel__heading">
        <div>
          <h1>Find the behavior,<br /><span>not the token.</span></h1>
          <p>Describe what the code does in plain language. Codegrok finds the closest intent across your indexed functions.</p>
        </div>
        <div className="search-panel__stamp"><span>MEANING</span><span>OVER</span><span>SYNTAX</span></div>
      </div>

      <form className="search-form" onSubmit={onSubmit}>
        <div className="search-input-shell">
          <Search size={22} className="search-input-icon" />
          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="try: function that validates an email" disabled={locked || isSearching} />
          <kbd>⌘ K</kbd>
          <button type="submit" className="search-submit" disabled={locked || isSearching || !query.trim()} aria-label="Search">
            {isSearching ? <LoaderCircle className="spin" size={19} /> : <Send size={18} />}
          </button>
        </div>
      </form>

      <div className="search-controls">
        <div className="filter-label"><SlidersHorizontal size={15} /> FILTER BY AST TYPE</div>
        <div className="filter-pills" role="group" aria-label="Filter by AST type">
          {(["all", "function_declaration", "method_definition", "arrow_function"] as AstType[]).map((value) => (
            <button key={value} type="button" onClick={() => setFilter(value)} disabled={locked} className={cn("filter-pill", filter === value && "filter-pill--active")}>
              {value === "all" ? "All" : TYPE_META[value].label + "s"}
            </button>
          ))}
        </div>
        <button type="button" className="example-query" onClick={() => onExample("function that validates an email")} disabled={locked}><Sparkles size={14} /> Use an example</button>
      </div>

      {locked && <div className="search-lock"><div className="search-lock__icon"><Database size={18} /></div><div><strong>Search is waiting for a repository.</strong><span>Index your codebase above, then come back with a question.</span></div><ArrowDownRight size={18} /></div>}
    </section>
  );
}

function ResultCard({ result, query, index, canExplain }: { result: SearchResult; query: string; index: number; canExplain: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [explanationError, setExplanationError] = useState(false);
  const codeLines = result.code_text.split(/\r?\n/);
  const shouldCollapse = codeLines.length > 7;
  const displayedCode = expanded || !shouldCollapse ? result.code_text : codeLines.slice(0, 7).join("\n");
  const title = result.function_name === "anonymous" ? "anonymous function" : result.function_name;
  const pathParts = prettyPath(result.file_path);
  const scoreWidth = Math.max(8, Math.min(100, result.similarity * 100));

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(result.code_text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  const explainMatch = async () => {
    if (explanation || explanationLoading) return;
    setExplanationLoading(true);
    setExplanationError(false);
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 60_000);
    try {
      const response = await fetch(`${API_BASE}/api/explain`, {
        method: "POST",
        headers: API_HEADERS,
        signal: controller.signal,
        body: JSON.stringify({ query, code_text: result.code_text, function_name: result.function_name, similarity: result.similarity }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || typeof payload.explanation !== "string" || !payload.explanation.trim()) throw new Error("Explanation unavailable");
      setExplanation(payload.explanation.trim());
    } catch {
      setExplanationError(true);
    } finally {
      window.clearTimeout(timeout);
      setExplanationLoading(false);
    }
  };

  return (
    <article className="result-card" style={{ animationDelay: `${index * 65}ms` }}>
      <div className="result-card__meta">
        <div className="result-card__path" title={result.file_path}><FileCode2 size={16} /><span className="path-crumbs">{pathParts.map((part, partIndex) => <span key={`${part}-${partIndex}`} className={cn(partIndex === pathParts.length - 1 && "path-crumbs__file")}>{part}{partIndex < pathParts.length - 1 && <b>/</b>}</span>)}</span></div>
        <div className="result-card__meta-right"><span className="line-range"><Hash size={13} />{result.start_line}–{result.end_line}</span><TypeBadge type={result.ast_type} /></div>
      </div>
      <div className="result-card__body">
        <div className="result-card__title-row"><h3>{result.function_name === "anonymous" ? <em className="anonymous-name">{title}</em> : title}</h3><button type="button" className="copy-button" onClick={copyCode}>{copied ? <><Check size={14} /> COPIED</> : <><Clipboard size={14} /> COPY</>}</button></div>
        <div className="code-window">
          <div className="code-window__bar"><span className="code-window__dots"><i /><i /><i /></span><span className="code-window__lang">TYPESCRIPT</span><span className="code-window__id">RESULT_{String(result.id).padStart(3, "0")}</span></div>
          <pre className={cn("code-window__pre", !expanded && shouldCollapse && "code-window__pre--collapsed")}><code dangerouslySetInnerHTML={{ __html: highlightCode(displayedCode) }} /></pre>
          {shouldCollapse && <button className="expand-code" type="button" onClick={() => setExpanded((value) => !value)}>{expanded ? "COLLAPSE SNIPPET" : `EXPAND ${codeLines.length - 7} MORE LINES`} <ChevronDown size={15} className={expanded ? "rotate-180" : ""} /></button>}
        </div>
        <div className="result-card__footer">
          <div className="confidence-readout"><div className="confidence-readout__label"><span>SEMANTIC MATCH</span><strong>{formatScore(result.similarity)}</strong></div><div className="confidence-track"><span style={{ width: `${scoreWidth}%` }} /></div></div>
          <span className="confidence-note">{result.similarity >= 0.58 ? "strong signal" : result.similarity >= 0.45 ? "useful lead" : "weak signal"}</span>
          {canExplain && <button type="button" className="explain-button" onClick={explainMatch} disabled={explanationLoading || Boolean(explanation)} aria-expanded={Boolean(explanation)}>
            {explanationLoading ? <><LoaderCircle className="spin" size={13} /> EXPLAINING…</> : explanation ? "EXPLANATION SHOWN" : "EXPLAIN THIS CODE"}
          </button>}
        </div>
        {explanation && <div className="match-explanation"><span className="match-explanation__label">CODE EXPLANATION</span><p>{explanation}</p></div>}
        {explanationError && <div className="match-explanation match-explanation--error"><span>Explanation unavailable right now.</span></div>}
      </div>
    </article>
  );
}

function ResultsPanel({ results, query, hasSearched, isSearching, isIndexed, isPreview, error }: { results: SearchResult[]; query: string; hasSearched: boolean; isSearching: boolean; isIndexed: boolean; isPreview: boolean; error: string | null }) {
  if (!isIndexed) {
    return <section className="results-panel results-panel--empty"><div className="empty-grid" /><div className="empty-icon"><BrandMark small /></div><div className="section-eyebrow"><span className="eyebrow-index">03</span> RANKED RESULTS</div><h2>Your code, <em>decoded.</em></h2><p>Search results will arrive here with confidence scores, syntax-highlighted context, and the exact file path your team needs.</p><div className="empty-preview-stack"><div className="empty-preview-strip"><span><FileCode2 size={13} /> src/validators/email.ts</span><span className="empty-preview-tag">FUNCTION</span></div><div className="empty-preview-code"><span>01</span><i>export function <b>isValidEmail</b>(value: string) {'{'}</i></div><div className="empty-preview-readout"><span>SEMANTIC MATCH</span><span className="empty-preview-bar"><i /></span><strong>0.61</strong></div></div><div className="empty-rule"><span>NO INDEX / NO SIGNAL</span><span>AWAITING INPUT</span></div></section>;
  }
  return <section className="results-panel" id="results-panel"><div className="results-panel__header"><div><div className="section-eyebrow"><span className="eyebrow-index">03</span> RANKED RESULTS</div><h2>{hasSearched ? "Closest matches" : "A guided preview"}</h2></div><div className="results-panel__summary"><span className="summary-pulse" />{isSearching ? "SEARCHING…" : `${results.length} ${results.length === 1 ? "RESULT" : "RESULTS"}`}<span className="summary-sep">/</span><span>{isPreview ? "INTERFACE PREVIEW" : "VECTOR RANKED"}</span></div></div>
    {error && <div className="search-error"><TriangleAlert size={18} /><span>{error}</span></div>}
    {isSearching && <div className="results-loading"><LoaderCircle className="spin" size={20} /><span>Comparing intent against the indexed codebase…</span></div>}
    {!isSearching && results.length === 0 && <div className="no-results"><div className="no-results__mark">∅</div><h3>No strong signal yet.</h3><p>Try a broader description, or ask for the behavior rather than the implementation detail.</p></div>}
    {!isSearching && results.length > 0 && <div className="results-list">{results.map((result, index) => <ResultCard key={result.id} result={result} query={query} index={index} canExplain={index < 3} />)}</div>}
  </section>;
}

export default function Home() {
  const [activeView, setActiveView] = useState<"search" | "ingest">("ingest");
  const [menuOpen, setMenuOpen] = useState(false);
  const [repoPath, setRepoPath] = useState("");
  const [repoName, setRepoName] = useState("");
  const [ingestState, setIngestState] = useState<IngestState>("idle");
  const [ingestNotice, setIngestNotice] = useState<Notice>(null);
  const [totalChunks, setTotalChunks] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<AstType>("all");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [isPreview, setIsPreview] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);

  const isIndexed = ingestState === "success";
  const visibleResults = useMemo(() => filter === "all" ? results : results.filter((result) => result.ast_type === filter), [filter, results]);

  useEffect(() => {
    let cancelled = false;

    fetch(`${API_BASE}/api/health`)
      .then((response) => {
        if (!response.ok) throw new Error("API health check failed");
        return response.json();
      })
      .then((payload) => {
        if (!cancelled) setApiOnline(payload.status === "ok");
      })
      .catch(() => {
        if (!cancelled) setApiOnline(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const navigate = (view: "search" | "ingest") => {
    setActiveView(view);
    setMenuOpen(false);
    document.getElementById(view === "search" ? "search-panel" : "ingest-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleIngest = async (event: FormEvent) => {
    event.preventDefault();
    if (!repoPath.trim()) return;
    setIngestState("loading");
    setIngestNotice(null);
    setSearchError(null);
    try {
      const response = await fetch(`${API_BASE}/api/ingest`, { method: "POST", headers: API_HEADERS, body: JSON.stringify({ repoPath: repoPath.trim(), repoName: repoName.trim() || repoPath.split("/").filter(Boolean).pop() || "repository" }) });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "The backend could not index this repository.");
      setTotalChunks(payload.total_chunks ?? 0);
      setIngestState("success");
      setIngestNotice({ tone: "success", message: "ready" });
      setActiveView("search");
      window.setTimeout(() => document.getElementById("search-panel")?.scrollIntoView({ behavior: "smooth", block: "start" }), 180);
    } catch (error) {
      setIngestState("error");
      setIngestNotice({ tone: "error", message: error instanceof Error ? error.message : "Could not connect to the indexing service." });
    }
  };

  const handleSearch = async (event: FormEvent) => {
    event.preventDefault();
    if (!isIndexed || !query.trim()) return;
    setIsSearching(true);
    setHasSearched(true);
    setSearchError(null);
    setIsPreview(false);
    try {
      const response = await fetch(`${API_BASE}/api/search`, { method: "POST", headers: API_HEADERS, body: JSON.stringify({ query: query.trim(), astType: filter === "all" ? null : filter, limit: 10 }) });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "The semantic search request failed.");
      setResults(Array.isArray(payload) ? payload : []);
    } catch (error) {
      setResults([]);
      setSearchError(error instanceof Error ? error.message : "Could not connect to the search service.");
    } finally {
      setIsSearching(false);
      window.setTimeout(() => document.getElementById("results-panel")?.scrollIntoView({ behavior: "smooth", block: "start" }), 120);
    }
  };

  const handleExample = (value: string) => {
    setQuery(value);
    setResults(DEMO_RESULTS);
    setHasSearched(true);
    setIsPreview(true);
    window.setTimeout(() => document.getElementById("results-panel")?.scrollIntoView({ behavior: "smooth", block: "start" }), 120);
  };

  const handleSearchKey = (event: KeyboardEvent<HTMLInputElement>) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      document.querySelector<HTMLInputElement>(".search-input-shell input")?.focus();
    }
  };

  return (
    <div className="app-shell">
      <div className={cn("mobile-scrim", menuOpen && "mobile-scrim--visible")} onClick={() => setMenuOpen(false)} />
      <div className={cn("rail-wrap", menuOpen && "rail-wrap--open")}><SideRail activeView={activeView} onNavigate={navigate} isIndexed={isIndexed} /></div>
      <div className="main-wrap">
        <AppHeader onMenu={() => setMenuOpen((open) => !open)} apiOnline={apiOnline} />
        <main className="workspace">
          <div className="workspace__intro"><span className="workspace__index">WORKSPACE / 001</span><span className="workspace__rule" /><span className="workspace__hint">NATURAL LANGUAGE → SOURCE</span></div>
          <div className="workspace-grid">
            <IngestPanel repoPath={repoPath} repoName={repoName} setRepoPath={setRepoPath} setRepoName={setRepoName} ingestState={ingestState} notice={ingestNotice} totalChunks={totalChunks} onSubmit={handleIngest} />
            <SearchPanel query={query} setQuery={(value) => { setQuery(value); if (!value) setIsPreview(false); }} filter={filter} setFilter={(value) => { setFilter(value); setIsPreview(false); }} isIndexed={isIndexed} isSearching={isSearching} onSubmit={handleSearch} onExample={handleExample} />
          </div>
          <ResultsPanel results={visibleResults} query={query} hasSearched={hasSearched} isSearching={isSearching} isIndexed={isIndexed} isPreview={isPreview} error={searchError} />
          <footer className="workspace-footer"><span><span className="footer-mark">⌁</span> CODEGROK / SEMANTIC INFRASTRUCTURE</span><span>BUILT FOR THE MOMENT BEFORE YOU KNOW THE FILE NAME</span><span>LOCAL-FIRST · FASTAPI · VECTOR SEARCH</span></footer>
        </main>
      </div>
    </div>
  );
}
