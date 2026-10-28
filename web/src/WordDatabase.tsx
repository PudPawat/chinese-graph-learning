import { useEffect, useMemo, useState } from "react";
import lexiconFile from "./data/lexicon.json";
import { fold } from "./model";

type Label = {
  id: string;
  group: string;
  en: string;
  zh: string;
  parent: string | null;
};

type LexiconWord = {
  traditional: string;
  simplified: string;
  pinyin: string;
  en: string;
  zh: string;
  hsk: number | null;
  pos: string[];
  labels: string[];
  glyphs: string[];
  in_graph: boolean[];
};

const lexicon = lexiconFile as {
  source: string;
  hsk_target: number;
  labels: Label[];
  words: LexiconWord[];
};

const PAGE_SIZE = 100;

const labelById = new Map(lexicon.labels.map((label) => [label.id, label]));
const groups = [...new Set(lexicon.labels.map((label) => label.group))];
const parts = [...new Set(lexicon.words.flatMap((word) => word.pos))].sort();

function hasLabel(word: LexiconWord, labelId: string): boolean {
  if (word.labels.includes(labelId)) return true;
  return word.labels.some((id) => labelById.get(id)?.parent === labelId);
}

function graphState(word: LexiconWord): string {
  const linked = word.in_graph.filter(Boolean).length;
  if (linked === 0) return "not in the character graph";
  if (linked === word.glyphs.length) return "every character is in the graph";
  return `${linked} of ${word.glyphs.length} characters in the graph`;
}

export function WordDatabase({ onOpenGlyph }: { onOpenGlyph: (glyph: string) => void }) {
  const [hsk, setHsk] = useState("all");
  const [labelId, setLabelId] = useState("all");
  const [pos, setPos] = useState("all");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState("蘋果");

  const visible = useMemo(() => {
    const needle = fold(query.trim());
    return lexicon.words.filter((word) => {
      if (hsk === "none" && word.hsk !== null) return false;
      if (hsk !== "all" && hsk !== "none" && word.hsk !== Number(hsk)) return false;
      if (labelId !== "all" && !hasLabel(word, labelId)) return false;
      if (pos !== "all" && !word.pos.includes(pos)) return false;
      if (!needle) return true;
      const labelText = word.labels.map((id) => `${labelById.get(id)?.en} ${labelById.get(id)?.zh}`).join(" ");
      return fold(`${word.traditional} ${word.simplified} ${word.pinyin} ${word.en} ${word.pos.join(" ")} ${labelText}`).includes(needle);
    });
  }, [hsk, labelId, pos, query]);

  useEffect(() => {
    setPage(0);
  }, [hsk, labelId, pos, query]);

  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const pageRows = visible.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);
  const current = visible.find((word) => word.traditional === selected) ?? visible[0];

  return (
    <div className="db">
      <div className="db-bar">
        <p className="db-source">{lexicon.source}</p>
        <div className="db-filters">
          <label>
            HSK
            <select value={hsk} onChange={(event) => setHsk(event.target.value)}>
              <option value="all">All levels</option>
              {[1, 2, 3, 4, 5, 6].map((level) => (
                <option key={level} value={level}>
                  HSK {level}
                </option>
              ))}
              <option value="none">Not on the HSK list</option>
            </select>
          </label>
          <label>
            Category
            <select value={labelId} onChange={(event) => setLabelId(event.target.value)}>
              <option value="all">All categories</option>
              {groups.map((group) => (
                <optgroup key={group} label={group}>
                  {lexicon.labels
                    .filter((label) => label.group === group)
                    .map((label) => (
                      <option key={label.id} value={label.id}>
                        {label.parent ? `${label.en}` : label.en}
                      </option>
                    ))}
                </optgroup>
              ))}
            </select>
          </label>
          <label>
            Part of speech
            <select value={pos} onChange={(event) => setPos(event.target.value)}>
              <option value="all">All parts of speech</option>
              {parts.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="db-search">
            Find
            <input
              value={query}
              placeholder="word, pinyin, or English"
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
        </div>
        <p className="index-count">
          {visible.length.toLocaleString()} of {lexicon.words.length.toLocaleString()} words.
          {visible.length > 0
            ? ` Showing ${safePage * PAGE_SIZE + 1}–${Math.min(visible.length, safePage * PAGE_SIZE + PAGE_SIZE)}.`
            : ""}
        </p>
        <div className="db-pager">
          <button type="button" disabled={safePage === 0} onClick={() => setPage(safePage - 1)}>
            Previous
          </button>
          <span>
            Page {safePage + 1} of {pageCount.toLocaleString()}
          </span>
          <button type="button" disabled={safePage >= pageCount - 1} onClick={() => setPage(safePage + 1)}>
            Next
          </button>
        </div>
      </div>
      <div className="db-body">
        <div className="db-table-wrap">
          <table className="db-table">
            <thead>
              <tr>
                <th>Traditional</th>
                <th>Simplified</th>
                <th>Pinyin</th>
                <th>HSK</th>
                <th>Part of speech</th>
                <th>Categories</th>
                <th>English</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.map((word) => (
                <tr
                  key={word.traditional}
                  className={current?.traditional === word.traditional ? "is-selected" : ""}
                  onClick={() => setSelected(word.traditional)}
                >
                  <td className="db-glyph">{word.traditional}</td>
                  <td>{word.simplified}</td>
                  <td>{word.pinyin}</td>
                  <td>{word.hsk ?? "—"}</td>
                  <td>{word.pos.join(", ")}</td>
                  <td>
                    {word.labels.map((id) => labelById.get(id)?.en).join(", ")}
                  </td>
                  <td>{word.en}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {visible.length === 0 ? <p className="empty">No word matches these filters.</p> : null}
        </div>
        {current ? (
          <aside className="db-raw">
            <p className="panel-kicker">Raw row</p>
            <h2>
              {current.traditional} <span className="db-pinyin">{current.pinyin}</span>
            </h2>
            <dl>
              <dt>simplified</dt>
              <dd>{current.simplified}</dd>
              <dt>hsk_level</dt>
              <dd>{current.hsk ?? "null"}</dd>
              <dt>part_of_speech</dt>
              <dd>{current.pos.join(", ")}</dd>
              <dt>labels</dt>
              <dd>
                {current.labels.map((id) => {
                  const label = labelById.get(id);
                  const parent = label?.parent ? labelById.get(label.parent) : undefined;
                  return (
                    <span key={id} className="db-tag">
                      {label?.zh} {label?.en}
                      {parent ? ` · under ${parent.en}` : ""}
                    </span>
                  );
                })}
              </dd>
              <dt>gloss_en</dt>
              <dd>{current.en}</dd>
              <dt>glyphs</dt>
              <dd>
                {current.glyphs.map((glyph, index) => (
                  <span key={`${glyph}-${index}`} className="db-glyph-row">
                    <span className="db-glyph">{glyph}</span>
                    {current.in_graph[index] ? (
                      <button type="button" onClick={() => onOpenGlyph(glyph)}>
                        in the character graph
                      </button>
                    ) : (
                      <span>not a graph character yet</span>
                    )}
                  </span>
                ))}
              </dd>
              <dt>graph</dt>
              <dd>{graphState(current)}</dd>
            </dl>
          </aside>
        ) : null}
      </div>
    </div>
  );
}
