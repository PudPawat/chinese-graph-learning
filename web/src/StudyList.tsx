import { useEffect, useMemo, useRef, useState } from "react";
import studyFile from "./data/study.json";
import { fold } from "./model";

type Relation = {
  type: "synonym" | "antonym" | "related" | "variant";
  key: string | null;
  text: string | null;
};

type GlyphPart = {
  glyph: string;
  meaning: string;
  sound: string;
  side: string | null;
  same_sound: string[];
  same_family: string[];
};

type Entry = {
  key: string;
  traditional: string;
  simplified: string;
  pinyin: string;
  en: string;
  hsk: number;
  pos: string[];
  labels: string[];
  parts: GlyphPart[];
  relations: Relation[];
  sentences: string[];
};

type Token = { key: string; text: string; after: string };

type Sentence = { key: string; en: string; tokens: Token[] };

const study = studyFile as {
  source: string;
  list_size: number;
  shown: number;
  entries: Entry[];
  sentences: Sentence[];
};

const PAGE_SIZE = 50;
const RELATION_LABEL: Record<Relation["type"], string> = {
  antonym: "Opposite",
  synonym: "Synonym",
  related: "Related",
  variant: "Variant of",
};

const byKey = new Map(study.entries.map((entry) => [entry.key, entry]));
const sentenceByKey = new Map(study.sentences.map((sentence) => [sentence.key, sentence]));
const keyByGlyph = new Map(
  study.entries.filter((entry) => Array.from(entry.traditional).length === 1).map((entry) => [entry.traditional, entry.key]),
);
const preview = study.entries.slice(0, study.shown);

function titleCase(value: string): string {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
}

function partLine(entry: Entry, field: "meaning" | "sound"): string {
  return entry.parts.map((part) => part[field]).join(" · ");
}

function listLine(entry: Entry, field: "same_sound" | "same_family"): string {
  return entry.parts.map((part) => part[field].join("")).join(" · ");
}

function sentenceText(sentence: Sentence): string {
  return sentence.tokens.map((token) => token.text + token.after).join("");
}

function sentencesFor(entry: Entry): Sentence[] {
  return entry.sentences.flatMap((key) => {
    const sentence = sentenceByKey.get(key);
    return sentence ? [sentence] : [];
  });
}

function rank(key: string): number {
  return Number(key.slice(1));
}

function GlyphLink({
  glyph,
  currentKey,
  onOpen,
}: {
  glyph: string;
  currentKey: string;
  onOpen: (key: string) => void;
}) {
  const key = keyByGlyph.get(glyph);
  if (!key || key === currentKey) return <span className="db-glyph">{glyph}</span>;
  return (
    <button type="button" onClick={() => onOpen(key)}>
      {glyph} {key}
    </button>
  );
}

export function StudyList() {
  const [hsk, setHsk] = useState("all");
  const [link, setLink] = useState("all");
  const [query, setQuery] = useState("");
  const initialIndex = preview.findIndex((entry) => entry.key === "w0089");
  const [page, setPage] = useState(initialIndex >= 0 ? Math.floor(initialIndex / PAGE_SIZE) : 0);
  const [selected, setSelected] = useState("w0089");
  const skipPageReset = useRef(true);

  const visible = useMemo(() => {
    const needle = fold(query.trim());
    return preview.filter((entry) => {
      if (hsk !== "all" && entry.hsk !== Number(hsk)) return false;
      if (link === "sentence" && entry.sentences.length === 0) return false;
      if (link === "variant" && !entry.relations.some((row) => row.type === "variant")) return false;
      if (link !== "all" && link !== "sentence" && link !== "variant" && !entry.relations.some((row) => row.type === link)) {
        return false;
      }
      if (!needle) return true;
      const related = entry.relations.map((row) => `${row.text ?? ""} ${row.key ?? ""}`).join(" ");
      const samples = sentencesFor(entry).map((sentence) => sentenceText(sentence)).join(" ");
      const parts = entry.parts
        .map((part) => `${part.glyph} ${part.meaning} ${part.sound} ${part.side ?? ""} ${part.same_sound.join("")} ${part.same_family.join("")}`)
        .join(" ");
      const haystack = `${entry.key} ${entry.traditional} ${entry.simplified} ${entry.pinyin} ${entry.en} ${entry.pos.join(" ")} ${entry.labels.join(" ")} ${parts} ${related} ${samples}`;
      return fold(haystack).includes(needle);
    });
  }, [hsk, link, query]);

  useEffect(() => {
    if (skipPageReset.current) {
      skipPageReset.current = false;
      return;
    }
    setPage(0);
  }, [hsk, link, query]);

  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const pageRows = visible.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);
  const current = byKey.get(selected) ?? visible[0];
  const samples = current ? sentencesFor(current) : [];

  function openWord(key: string) {
    setSelected(key);
    const index = visible.findIndex((entry) => entry.key === key);
    if (index >= 0) setPage(Math.floor(index / PAGE_SIZE));
  }

  return (
    <div className="db">
      <div className="db-bar">
        <p className="db-source">{study.source}</p>
        <div className="db-filters">
          <label>
            HSK
            <select value={hsk} onChange={(event) => setHsk(event.target.value)}>
              <option value="all">1–4 in this 1,000</option>
              {[1, 2, 3, 4].map((level) => (
                <option key={level} value={level}>
                  HSK {level}
                </option>
              ))}
            </select>
          </label>
          <label>
            Link
            <select value={link} onChange={(event) => setLink(event.target.value)}>
              <option value="all">All words</option>
              <option value="antonym">Has an opposite</option>
              <option value="synonym">Has a synonym</option>
              <option value="related">Has a related word</option>
              <option value="variant">Variant form</option>
              <option value="sentence">Has a sentence</option>
            </select>
          </label>
          <label className="db-search">
            Find
            <input
              value={query}
              placeholder="key, word, pinyin, or sentence"
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
        </div>
        <p className="index-count">
          {visible.length.toLocaleString()} of {study.shown.toLocaleString()} shown. {study.list_size.toLocaleString()} HSK 1–5 words have keys.
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
                <th>Key</th>
                <th>HSK</th>
                <th>Word</th>
                <th>Simplified</th>
                <th>Pinyin</th>
                <th>English</th>
                <th>Part of speech</th>
                <th>Categories</th>
                <th>Meaning part</th>
                <th>Sound part</th>
                <th>Same sound</th>
                <th>Same part family</th>
                <th>Links</th>
                <th>Samples</th>
                <th>Sentence</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.map((entry) => {
                const rowSentences = sentencesFor(entry);
                return (
                  <tr
                    key={entry.key}
                    className={current?.key === entry.key ? "is-selected" : ""}
                    onClick={() => setSelected(entry.key)}
                  >
                    <td>{entry.key}</td>
                    <td>{entry.hsk}</td>
                    <td className="db-glyph">{entry.traditional}</td>
                    <td className="db-glyph">{entry.simplified}</td>
                    <td>{entry.pinyin}</td>
                    <td className="db-en">{entry.en}</td>
                    <td>{entry.pos.map(titleCase).join(", ")}</td>
                    <td>{entry.labels.join(", ")}</td>
                    <td className="db-glyph">{partLine(entry, "meaning")}</td>
                    <td className="db-glyph">{partLine(entry, "sound")}</td>
                    <td className="db-glyph">{listLine(entry, "same_sound")}</td>
                    <td className="db-glyph">{listLine(entry, "same_family")}</td>
                    <td>{entry.relations.map((row) => row.text).filter(Boolean).join("、") || "None in this set"}</td>
                    <td>{rowSentences.length}</td>
                    <td>
                      {rowSentences[0]
                        ? sentenceText(rowSentences[0])
                        : entry.relations.some((row) => row.type === "variant")
                          ? "Variant form"
                          : "No sentence yet"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {visible.length === 0 ? <p className="empty">No word matches these filters.</p> : null}
        </div>
        {current ? (
          <aside className="db-raw">
            <p className="panel-kicker">{current.key}</p>
            <h2>
              {current.traditional} <span className="db-pinyin">{current.pinyin}</span>
            </h2>
            <p>{current.en}</p>
            <dl>
              <dt>Simplified</dt>
              <dd className="db-glyph">{current.simplified}</dd>
              <dt>Part of speech</dt>
              <dd>{current.pos.map(titleCase).join(", ")}</dd>
              <dt>Categories</dt>
              <dd>{current.labels.join(", ")}</dd>
              <dt>HSK</dt>
              <dd>
                {current.hsk}
                {rank(current.key) > study.shown ? " · past the first 1,000, so no sentence yet" : ""}
              </dd>
              <dt>Character parts</dt>
              <dd>
                {current.parts.map((part) => (
                  <div key={`${current.key}-${part.glyph}`} className="study-block">
                    <p className="db-glyph">{part.glyph}</p>
                    <p>
                      <span className="study-kicker">Meaning part</span>
                      <span className="db-glyph">{part.meaning}</span>
                      {part.side ? <span className="study-kicker"> side form {part.side}</span> : null}
                    </p>
                    <p>
                      <span className="study-kicker">Sound part</span>
                      <GlyphLink glyph={part.sound} currentKey={current.key} onOpen={openWord} />
                    </p>
                    <p>
                      <span className="study-kicker">Same sound</span>
                      {part.same_sound.map((glyph) => (
                        <GlyphLink key={`${part.glyph}-sound-${glyph}`} glyph={glyph} currentKey={current.key} onOpen={openWord} />
                      ))}
                    </p>
                    <p>
                      <span className="study-kicker">Same part family</span>
                      {part.same_family.map((glyph) => (
                        <GlyphLink key={`${part.glyph}-family-${glyph}`} glyph={glyph} currentKey={current.key} onOpen={openWord} />
                      ))}
                    </p>
                  </div>
                ))}
              </dd>
              <dt>Links</dt>
              <dd>
                {current.relations.length === 0 ? <span>None in this set</span> : null}
                {current.relations.map((row) => (
                  <span key={`${row.type}-${row.key}-${row.text}`} className="db-tag">
                    {RELATION_LABEL[row.type]}{" "}
                    {row.key ? (
                      <button type="button" onClick={() => openWord(row.key as string)}>
                        {row.text} {row.key}
                      </button>
                    ) : (
                      <span>{row.text ? `${row.text} is not on HSK 1–5 yet` : "standard form is not on HSK 1–5 yet"}</span>
                    )}
                  </span>
                ))}
              </dd>
              <dt>{samples.length ? `Sentences · ${samples.length}` : "Sentence"}</dt>
              <dd>
                {samples.length > 0 ? (
                  samples.map((sentence) => (
                    <div key={sentence.key} className="study-block">
                      <div className="study-sentence">
                        {sentence.tokens.map((token, index) => (
                          <span key={`${sentence.key}-${token.key}-${index}`} className="study-token-wrap">
                            <button
                              type="button"
                              className={token.key === current.key ? "study-token is-focus" : "study-token"}
                              onClick={() => openWord(token.key)}
                            >
                              <span className="db-glyph">{token.text}</span>
                              <small>{token.key}</small>
                            </button>
                            {token.after ? <span className="study-punct">{token.after}</span> : null}
                          </span>
                        ))}
                      </div>
                      <p>{sentence.en}</p>
                      <p className="study-index">
                        {sentence.key} = {sentence.tokens.map((token) => token.key).join(" ")}
                      </p>
                    </div>
                  ))
                ) : rank(current.key) > study.shown ? (
                  <span>This word has a key. Sentences in this view are only for the first 1,000.</span>
                ) : (
                  <span>No sentence. This entry is a variant, and the sentence stays on the study form.</span>
                )}
              </dd>
            </dl>
          </aside>
        ) : null}
      </div>
    </div>
  );
}
