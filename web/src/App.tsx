import { lazy, Suspense, useEffect, useState } from "react";
import { FocusGraph } from "./FocusGraph";
import { MapGraph } from "./MapGraph";
import {
  characterByGlyph,
  characters,
  explain,
  focusNodes,
  graphs,
  GROUP_LABEL,
  GROUPS,
  groupOf,
  initialGlyph,
  matchesQuery,
  matchesWord,
  nodeTarget,
  RELATION_LABEL,
  sensesFor,
  wordByText,
  words,
} from "./model";
import type { GraphLink, GroupId } from "./types";
const WordDatabase = lazy(() => import("./WordDatabase").then((module) => ({ default: module.WordDatabase })));
const StudyList = lazy(() => import("./StudyList").then((module) => ({ default: module.StudyList })));

function packLinks(links: GraphLink[]) {
  const packed = new Map<string, { id: string; label: string; kind: string; links: GraphLink[] }>();
  for (const link of links) {
    const id = `${link.kind}:${link.label}`;
    const existing = packed.get(id);
    if (existing) existing.links.push(link);
    else packed.set(id, { id, label: link.label, kind: link.kind, links: [link] });
  }
  return [...packed.values()];
}

type Mode = "focus" | "map" | "database" | "study";

const ALL_ON: Record<GroupId, boolean> = {
  sound: true,
  form: true,
  meaning: true,
  words: true,
};

export function App() {
  const [glyph, setGlyph] = useState(initialGlyph);
  const [mode, setMode] = useState<Mode>("focus");
  const [query, setQuery] = useState("");
  const [enabled, setEnabled] = useState(ALL_ON);

  const character = characterByGlyph.get(glyph) ?? characters[0];
  const visibleCharacters = characters.filter((item) => matchesQuery(item, query));
  const visibleWords = words.filter((word) => matchesWord(word, query));
  const nodes = focusNodes(character.traditional, enabled);
  const senses = sensesFor(character.traditional);
  const links = (graphs[character.traditional] ?? []).filter((link) => enabled[groupOf(link.relation)]);

  useEffect(() => {
    document.title = mode === "database" ? "詞庫 · 字網" : mode === "study" ? "前一千詞 · 字網" : `${character.traditional} · 字網`;
  }, [character.traditional, mode]);

  useEffect(() => {
    const onPop = () => setGlyph(initialGlyph());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  function selectGlyph(next: string) {
    if (!characterByGlyph.has(next)) return;
    setGlyph(next);
    const hash = `#${encodeURIComponent(next)}`;
    if (window.location.hash !== hash) history.pushState(null, "", hash);
  }

  function toggleGroup(group: GroupId) {
    setEnabled((current) => ({ ...current, [group]: !current[group] }));
  }

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <span className="seal">字</span>
          <div>
            <h1>字網</h1>
            <p>
              {mode === "database"
                ? "Word list. HSK level, part of speech, and category are separate."
                : mode === "study"
                  ? "First 1,000 words of HSK 1–5. Every word has a meaning part, a sound part, and the same-sound set."
                  : "Traditional characters, joined by sound, form, and meaning."}
            </p>
          </div>
        </div>
        <div className="modes" role="group" aria-label="View">
          <button type="button" aria-pressed={mode === "focus"} onClick={() => setMode("focus")}>
            This character
          </button>
          <button type="button" aria-pressed={mode === "map"} onClick={() => setMode("map")}>
            Whole map
          </button>
          <button type="button" aria-pressed={mode === "database"} onClick={() => setMode("database")}>
            Word list
          </button>
          <button type="button" aria-pressed={mode === "study"} onClick={() => setMode("study")}>
            First 1,000
          </button>
        </div>
        {mode !== "database" && mode !== "study" ? <div className="filters" role="group" aria-label="Link types">
          {GROUPS.map((group) => (
            <button
              key={group}
              type="button"
              className={`filter filter-${group}`}
              aria-pressed={enabled[group]}
              onClick={() => toggleGroup(group)}
            >
              {GROUP_LABEL[group]}
            </button>
          ))}
        </div> : null}
      </header>

      {mode === "database" ? (
        <Suspense fallback={<p className="empty">Loading the word list.</p>}>
          <WordDatabase
            onOpenGlyph={(next) => {
              setMode("focus");
              selectGlyph(next);
            }}
          />
        </Suspense>
      ) : mode === "study" ? (
        <Suspense fallback={<p className="empty">Loading the first 1,000 words.</p>}>
          <StudyList />
        </Suspense>
      ) : (
      <div className="workspace">
        <nav className="index" aria-label="Characters">
          <label className="search-label" htmlFor="character-search">
            Find
          </label>
          <input
            id="character-search"
            className="search"
            value={query}
            placeholder="字, pinyin, or word"
            onChange={(event) => setQuery(event.target.value)}
          />
          <p className="index-count">
            {visibleCharacters.length} of {characters.length}
          </p>
          <ul>
            {visibleCharacters.map((item) => (
              <li key={item.traditional}>
                <button
                  type="button"
                  className="index-item"
                  aria-current={item.traditional === character.traditional ? "true" : undefined}
                  onClick={() => selectGlyph(item.traditional)}
                >
                  <span className="index-glyph">{item.traditional}</span>
                  <span className="index-copy">
                    <span className="index-reading">{item.pinyin}</span>
                    <span className="index-gloss">{item.gloss_en}</span>
                  </span>
                  <span className="index-strokes">{item.stroke_count}</span>
                </button>
              </li>
            ))}
          </ul>
          {visibleCharacters.length === 0 ? <p className="empty">No character matches.</p> : null}
          <h2 className="index-heading">Words</h2>
          <p className="index-count">
            {visibleWords.length} of {words.length}
          </p>
          <ul>
            {visibleWords.map((word) => (
              <li key={word.traditional}>
                <button type="button" className="index-item" onClick={() => selectGlyph(word.chars[0] ?? "")}>
                  <span className="index-glyph">{word.traditional}</span>
                  <span className="index-copy">
                    <span className="index-reading">{word.pinyin}</span>
                    <span className="index-gloss">{word.en}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {visibleWords.length === 0 ? <p className="empty">No word matches.</p> : null}
        </nav>

        <main className="stage">
          <h2 className="sr-only">
            {mode === "focus" ? `Neighborhood of ${character.traditional}` : "Map of the seed"}
          </h2>
          {mode === "focus" ? (
            nodes.length > 0 ? (
              <FocusGraph glyph={character.traditional} nodes={nodes} onSelect={selectGlyph} />
            ) : (
              <p className="empty stage-empty">Turn a link type back on to draw this character.</p>
            )
          ) : (
            <MapGraph glyph={character.traditional} enabled={enabled} onSelect={selectGlyph} />
          )}
        </main>

        <aside className="panel" aria-label="Character">
          <p className="panel-kicker">{character.codepoint}</p>
          <div className="hero-row">
            <p className="hero-glyph">{character.traditional}</p>
            <div>
              <p className="pinyin">{character.pinyin}</p>
              <p className="zhuyin">{character.zhuyin}</p>
              {character.simplified !== character.traditional ? (
                <p className="simplified">Simplified {character.simplified}</p>
              ) : null}
            </div>
          </div>
          <ul className="facts">
            <li>{character.stroke_count} strokes</li>
            <li>{character.structure}</li>
            <li>
              Radical {character.radical}
              <span className="fact-note">{character.radical_meaning}</span>
            </li>
            {character.tocfl_band ? <li>{character.tocfl_band}</li> : null}
          </ul>

          <h3>Meanings</h3>
          <ul className="senses">
            {senses.map((sense) => (
              <li key={`${sense.glyph}-${sense.sort}`}>
                <span className="sense-zh">{sense.zh}</span>
                <span className="sense-en">{sense.en}</span>
                <span className="sense-pos">{sense.pos}</span>
                {sense.primary ? null : <span className="unlinked">No link yet</span>}
              </li>
            ))}
          </ul>

          <h3>Links</h3>
          {GROUPS.map((group) => {
            const rows = packLinks(links.filter((link) => groupOf(link.relation) === group));
            if (rows.length === 0) return null;
            return (
              <section key={group} className="link-group">
                <h4 className={`group-title title-${group}`}>{GROUP_LABEL[group]}</h4>
                <ul>
                  {rows.map((row) => {
                    const target = nodeTarget({
                      id: row.id,
                      label: row.label,
                      kind: row.kind,
                      sector: group,
                      links: row.links,
                    });
                    const word = row.kind === "word" ? wordByText.get(row.label) : undefined;
                    const body = (
                      <>
                        <span className="link-glyph">{row.label}</span>
                        <span className="link-copy">
                          <span className="link-relation">
                            {row.links.map((link) => RELATION_LABEL[link.relation] ?? link.relation).join(" · ")}
                          </span>
                          <span className="link-detail">
                            {word ? `${word.pinyin} · ${word.en}` : row.links.map((link) => explain(link)).join(" · ")}
                          </span>
                        </span>
                      </>
                    );
                    return (
                      <li key={row.id}>
                        {target ? (
                          <button type="button" className="link-row" onClick={() => selectGlyph(target)}>
                            {body}
                          </button>
                        ) : (
                          <div className="link-row is-static">{body}</div>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
          {links.length === 0 ? <p className="empty">No links of the selected types.</p> : null}
        </aside>
      </div>
      )}
    </div>
  );
}
