// Browse and copy corpus (#35) sections while an application form is open
// in the next tab — reading/copying, not editing (issue #37).
import { marked } from "marked";
import { useEffect, useState } from "react";
import { getCorpusEntries, getCorpusFile, searchCorpus, type CorpusEntry, type CorpusFile } from "../api/corpus";
import { splitIntoSections, stripHtmlComments } from "../lib/markdown";

function groupByDirectory(entries: CorpusEntry[]): Record<string, CorpusEntry[]> {
  const groups: Record<string, CorpusEntry[]> = {};
  for (const entry of entries) {
    const slash = entry.path.indexOf("/");
    const key = slash === -1 ? "(root)" : entry.path.slice(0, slash);
    (groups[key] ??= []).push(entry);
  }
  return groups;
}

function renderHtml(markdown: string): string {
  return marked.parse(stripHtmlComments(markdown), { async: false });
}

async function copySection(raw: string) {
  await navigator.clipboard.writeText(raw);
}

export function CorpusPage() {
  const [entries, setEntries] = useState<CorpusEntry[] | null>(null);
  const [treeError, setTreeError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<CorpusEntry[] | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [file, setFile] = useState<CorpusFile | null>(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  useEffect(() => {
    getCorpusEntries()
      .then((result) => setEntries(result.entries))
      .catch((err: unknown) => setTreeError(err instanceof Error ? err.message : String(err)));
  }, []);

  function selectFile(path: string) {
    setSelectedPath(path);
    setFile(null);
    setFileError(null);
    setFileLoading(true);
    getCorpusFile(path)
      .then(setFile)
      .catch((err: unknown) => setFileError(err instanceof Error ? err.message : String(err)))
      .finally(() => setFileLoading(false));
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    setSearchError(null);
    searchCorpus(query.trim())
      .then((result) => setSearchResults(result.entries))
      .catch((err: unknown) => setSearchError(err instanceof Error ? err.message : String(err)));
  }

  function clearSearch() {
    setQuery("");
    setSearchResults(null);
    setSearchError(null);
  }

  const groups = entries ? groupByDirectory(entries) : {};

  return (
    <div>
      <h1>Corpus</h1>
      <div style={{ display: "flex", gap: "2rem" }}>
        <div>
          <form onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Search corpus"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button type="submit">Search</button>
            {searchResults && (
              <button type="button" onClick={clearSearch}>
                Back to tree
              </button>
            )}
          </form>

          {searchError && <p role="alert">Search failed: {searchError}</p>}

          {searchResults ? (
            <section>
              <h2>Search results</h2>
              {searchResults.length === 0 ? (
                <p>No matches.</p>
              ) : (
                <ul>
                  {searchResults.map((entry) => (
                    <li key={entry.path}>
                      <button type="button" onClick={() => selectFile(entry.path)}>
                        {entry.title || entry.path}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ) : (
            <>
              {treeError && <p role="alert">Could not load the corpus tree: {treeError}</p>}
              {!treeError && !entries && <p>Loading…</p>}
              {Object.keys(groups)
                .sort()
                .map((dir) => (
                  <section key={dir}>
                    <h2>{dir}</h2>
                    <ul>
                      {groups[dir].map((entry) => {
                        const slash = entry.path.indexOf("/");
                        const displayName = entry.title || (slash === -1 ? entry.path : entry.path.slice(slash + 1));
                        return (
                          <li key={entry.path}>
                            <button type="button" onClick={() => selectFile(entry.path)}>
                              {displayName}
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  </section>
                ))}
            </>
          )}
        </div>

        <div style={{ flex: 1 }}>
          {!selectedPath && <p>Select a file to view it.</p>}
          {fileLoading && <p>Loading…</p>}
          {fileError && <p role="alert">Could not load this file: {fileError}</p>}
          {file && <FileView file={file} />}
        </div>
      </div>
    </div>
  );
}

function FileView({ file }: { file: CorpusFile }) {
  const lines = file.content.split("\n");
  const headingRe = /^#{1,6}\s+.+$/;
  const firstHeadingIndex = lines.findIndex((line) => headingRe.test(line));
  const preamble =
    firstHeadingIndex === 0
      ? ""
      : firstHeadingIndex === -1
        ? file.content
        : lines.slice(0, firstHeadingIndex).join("\n");
  const sections = splitIntoSections(file.content);

  return (
    <article>
      <h2>{file.title || file.path}</h2>
      {file.tags.length > 0 && <p>Tags: {file.tags.join(", ")}</p>}
      {file.updated && <p>Updated: {file.updated}</p>}

      {preamble && <div dangerouslySetInnerHTML={{ __html: renderHtml(preamble) }} />}

      {sections.map((section, i) => (
        <section key={`${i}-${section.heading}`}>
          <div dangerouslySetInnerHTML={{ __html: renderHtml(section.raw) }} />
          <button type="button" onClick={() => copySection(section.raw)}>
            Copy section
          </button>
        </section>
      ))}
    </article>
  );
}
