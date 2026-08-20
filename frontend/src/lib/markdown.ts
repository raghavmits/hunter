// Splits raw markdown into flat, per-heading sections for the corpus
// page's per-section copy buttons (issue #37). Flat, not nested — every
// heading (any level) starts a new section that runs to the next heading
// of any level, since #35's templates are flat heading lists with no
// subheadings that would need a same-or-higher-level split rule.

export interface MarkdownSection {
  heading: string;
  raw: string;
}

const HEADING_RE = /^#{1,6}\s+.+$/;

export function splitIntoSections(markdown: string): MarkdownSection[] {
  const lines = markdown.split("\n");
  const headingIndexes: number[] = [];
  lines.forEach((line, i) => {
    if (HEADING_RE.test(line)) headingIndexes.push(i);
  });

  return headingIndexes.map((start, i) => {
    const end = i + 1 < headingIndexes.length ? headingIndexes[i + 1] : lines.length;
    const sectionLines = lines.slice(start, end);
    return {
      heading: lines[start].replace(/^#{1,6}\s+/, ""),
      raw: sectionLines.join("\n").trimEnd(),
    };
  });
}

export function stripHtmlComments(markdown: string): string {
  return markdown.replace(/<!--[\s\S]*?-->/g, "");
}
