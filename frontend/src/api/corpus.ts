// Matches app/schemas/corpus.py (issue #36).
import { apiFetch } from "./client";

export interface CorpusEntry {
  path: string;
  title: string | null;
  tags: string[];
  updated: string | null;
}

export interface CorpusFile extends CorpusEntry {
  content: string;
}

export function getCorpusEntries(): Promise<{ entries: CorpusEntry[] }> {
  return apiFetch<{ entries: CorpusEntry[] }>("/corpus");
}

export function getCorpusFile(path: string): Promise<CorpusFile> {
  return apiFetch<CorpusFile>(`/corpus/${path}`);
}

export function searchCorpus(query: string): Promise<{ entries: CorpusEntry[] }> {
  return apiFetch<{ entries: CorpusEntry[] }>(`/corpus/search?q=${encodeURIComponent(query)}`);
}
