import { useState } from "react";
import { characterByGlyph, GROUP_LABEL, MAP_POS, mapEdges, visibleMapGroup, words } from "./model";
import type { GroupId } from "./types";

type MapGraphProps = {
  glyph: string;
  enabled: Record<GroupId, boolean>;
  onSelect: (glyph: string) => void;
};

const VIEW = { width: 1080, height: 700 };

type Box = { x: number; y: number; w: number; h: number };

function overlaps(a: Box, b: Box): boolean {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function placeWordLabels(
  edges: { a: string; b: string; labels: { text: string; pinyin: string }[] }[],
): { key: string; text: string; x: number; y: number }[] {
  const occupied: Box[] = Object.values(MAP_POS).map((point) => ({
    x: point.x - 58,
    y: point.y - 40,
    w: 116,
    h: 108,
  }));
  const placed: { key: string; text: string; x: number; y: number }[] = [];
  for (const edge of edges) {
    const from = MAP_POS[edge.a];
    const to = MAP_POS[edge.b];
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const length = Math.hypot(dx, dy) || 1;
    edge.labels.forEach((label, index) => {
      const caption = `${label.text} ${label.pinyin}`;
      const width = label.text.length * 18 + label.pinyin.length * 8 + 16;
      const height = 18;
      let chosen: { x: number; y: number } | null = null;
      for (let step = 0; step < 24; step++) {
        const shift = Math.floor(step / 2) * 22 * (step % 2 === 0 ? 1 : -1);
        const along = index * 20;
        const x = (from.x + to.x) / 2 + (-dy / length) * (18 + shift);
        const y = (from.y + to.y) / 2 + (dx / length) * (18 + shift) + along;
        const box = { x: x - width / 2, y: y - 14, w: width, h: height };
        if (x < 36 || x > VIEW.width - 36 || y < 24 || y > VIEW.height - 16) continue;
        if (!occupied.some((item) => overlaps(box, item))) {
          chosen = { x, y };
          occupied.push(box);
          break;
        }
      }
      if (chosen) {
        placed.push({ key: `${edge.a}-${edge.b}-${label.text}`, text: caption, x: chosen.x, y: chosen.y });
      }
    });
  }
  return placed;
}

export function MapGraph({ glyph, enabled, onSelect }: MapGraphProps) {
  const [hover, setHover] = useState<string | null>(null);
  const visible = mapEdges
    .map((edge) => ({ edge, group: visibleMapGroup(edge, enabled) }))
    .filter((item): item is { edge: (typeof mapEdges)[number]; group: GroupId } => item.group !== null);

  const hoverCharacter = hover ? characterByGlyph.get(hover) : undefined;
  const wordLabels = enabled.words ? placeWordLabels(visible.map(({ edge }) => edge)) : [];

  return (
    <div className="graph-wrap">
      <svg className="graph" viewBox={`0 0 ${VIEW.width} ${VIEW.height}`} role="img" aria-label="Map of the seed characters">
        {visible.map(({ edge, group }) => {
          const from = MAP_POS[edge.a];
          const to = MAP_POS[edge.b];
          return (
            <line
              key={`${edge.a}-${edge.b}`}
              className={`edge edge-${group}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
            />
          );
        })}
        {wordLabels.map((label) => (
          <text key={label.key} className="word-label" x={label.x} y={label.y} textAnchor="middle">
            {label.text}
          </text>
        ))}

        {Object.entries(MAP_POS).map(([label, point]) => {
          const selected = label === glyph;
          const character = characterByGlyph.get(label);
          return (
            <g
              key={label}
              className={`graph-node is-link${selected ? " is-selected" : ""}`}
              role="button"
              tabIndex={0}
              aria-label={character ? `${label}, ${character.pinyin}, ${character.gloss_en}` : label}
              aria-current={selected ? "true" : undefined}
              onMouseEnter={() => setHover(label)}
              onMouseLeave={() => setHover((current) => (current === label ? null : current))}
              onFocus={() => setHover(label)}
              onBlur={() => setHover((current) => (current === label ? null : current))}
              onClick={() => onSelect(label)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelect(label);
                }
              }}
            >
              <circle className="node-shape" cx={point.x} cy={point.y} r={selected ? 28 : 24} />
              <text x={point.x} y={point.y + 6} textAnchor="middle">
                {label}
              </text>
              {character ? (
                <text className="node-reading" x={point.x} y={point.y + 42} textAnchor="middle">
                  {character.pinyin}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
      <p className="hover-line">
        {hoverCharacter
          ? `${hoverCharacter.traditional} ${hoverCharacter.pinyin} · ${hoverCharacter.gloss_en}${
              words.some((word) => word.chars.includes(hoverCharacter.traditional))
                ? ` · ${words
                    .filter((word) => word.chars.includes(hoverCharacter.traditional))
                    .map((word) => `${word.traditional} ${word.pinyin}`)
                    .join(" · ")}`
                : ""
            }`
          : "Lines join a shared sound, a shared part, a shared meaning, or a word. Click a character to read it."}
      </p>
      <p className="map-key">
        {(["sound", "form", "meaning", "words"] as GroupId[]).map((group) => (
          <span key={group} className={`key-item key-${group}`}>
            {GROUP_LABEL[group]}
          </span>
        ))}
        <span className="key-note">Hover a character for its words and their pinyin.</span>
      </p>
    </div>
  );
}
