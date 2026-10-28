import { useState } from "react";
import {
  characterByGlyph,
  FOCUS_CENTER,
  FOCUS_VIEW,
  GROUP_LABEL,
  GROUPS,
  layoutFocus,
  nodeTarget,
  readingFor,
  RELATION_LABEL,
  type FocusNode,
} from "./model";
type FocusGraphProps = {
  glyph: string;
  nodes: FocusNode[];
  onSelect: (glyph: string) => void;
};

function shorten(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  trimStart: number,
  trimEnd: number,
) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const length = Math.hypot(dx, dy) || 1;
  return {
    x1: x1 + (dx / length) * trimStart,
    y1: y1 + (dy / length) * trimStart,
    x2: x2 - (dx / length) * trimEnd,
    y2: y2 - (dy / length) * trimEnd,
  };
}

function nodeBox(kind: string, label: string, pinyin: string | null): { width: number; height: number; rx: number } {
  const readingWidth = pinyin ? pinyin.length * 7.4 + 18 : 0;
  if (kind === "word") {
    return {
      width: Math.max(92, label.length * 26 + 22, readingWidth),
      height: 64,
      rx: 32,
    };
  }
  if (!pinyin) return { width: 58, height: 48, rx: 4 };
  return { width: Math.max(72, readingWidth), height: 72, rx: kind === "component" ? 6 : 36 };
}

export function FocusGraph({ glyph, nodes, onSelect }: FocusGraphProps) {
  const [hoverId, setHoverId] = useState<string | null>(null);
  const placed = layoutFocus(nodes);
  const hover = placed.find((node) => node.id === hoverId) ?? null;
  const present = new Set(placed.map((node) => node.sector));

  return (
    <div className="graph-wrap">
      <svg
        className="graph"
        viewBox={`0 0 ${FOCUS_VIEW.width} ${FOCUS_VIEW.height}`}
        role="img"
        aria-label={`Links around ${glyph}`}
      >
        {GROUPS.filter((group) => present.has(group)).map((group) => {
          const sample = placed.find((node) => node.sector === group);
          if (!sample) return null;
          const labelY = group === "sound" || group === "form" ? 36 : FOCUS_VIEW.height - 18;
          const labelX = group === "sound" || group === "meaning" ? 230 : 750;
          return (
            <text key={group} className={`sector-label sector-${group}`} x={labelX} y={labelY} textAnchor="middle">
              {GROUP_LABEL[group]}
            </text>
          );
        })}

        {placed.map((node) => {
          const box = nodeBox(node.kind, node.label, readingFor(node.kind, node.label));
          const line = shorten(
            FOCUS_CENTER.x,
            FOCUS_CENTER.y,
            node.x,
            node.y,
            76,
            Math.max(box.width, box.height) / 2 + 8,
          );
          return (
            <line
              key={`edge-${node.id}`}
              className={`edge edge-${node.sector}`}
              x1={line.x1}
              y1={line.y1}
              x2={line.x2}
              y2={line.y2}
            />
          );
        })}

        <g className="center-node">
          <circle cx={FOCUS_CENTER.x} cy={FOCUS_CENTER.y} r="70" />
          <text x={FOCUS_CENTER.x} y={FOCUS_CENTER.y - 2} textAnchor="middle">
            {glyph}
          </text>
          <text className="reading" x={FOCUS_CENTER.x} y={FOCUS_CENTER.y + 28} textAnchor="middle">
            {characterByGlyph.get(glyph)?.pinyin}
          </text>
        </g>

        {placed.map((node) => {
          const target = nodeTarget(node);
          const pinyin = readingFor(node.kind, node.label);
          const box = nodeBox(node.kind, node.label, pinyin);
          const primary = node.links[0];
          return (
            <g
              key={node.id}
              className={`graph-node kind-${node.kind}${target ? " is-link" : ""}`}
              role={target ? "button" : "img"}
              tabIndex={target ? 0 : undefined}
              aria-label={`${node.label}${pinyin ? `, ${pinyin}` : ""}, ${node.links.map((link) => RELATION_LABEL[link.relation] ?? link.relation).join(", ")}`}
              onMouseEnter={() => setHoverId(node.id)}
              onMouseLeave={() => setHoverId((current) => (current === node.id ? null : current))}
              onFocus={() => setHoverId(node.id)}
              onBlur={() => setHoverId((current) => (current === node.id ? null : current))}
              onClick={() => {
                if (target) onSelect(target);
              }}
              onKeyDown={(event) => {
                if (!target) return;
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelect(target);
                }
              }}
            >
              <rect
                className={`node-shape sector-${node.sector}`}
                x={node.x - box.width / 2}
                y={node.y - box.height / 2}
                width={box.width}
                height={box.height}
                rx={box.rx}
              />
              <text x={node.x} y={node.y + (pinyin ? -8 : 9)} textAnchor="middle">
                {node.label}
              </text>
              {pinyin ? (
                <text className="reading" x={node.x} y={node.y + 18} textAnchor="middle">
                  {pinyin}
                </text>
              ) : null}
              {primary ? <title>{`${RELATION_LABEL[primary.relation] ?? primary.relation}`}</title> : null}
            </g>
          );
        })}
      </svg>
      <p className="hover-line">
        {hover
          ? `${hover.label}${readingFor(hover.kind, hover.label) ? ` ${readingFor(hover.kind, hover.label)}` : ""} · ${hover.links.map((link) => RELATION_LABEL[link.relation] ?? link.relation).join(" · ")}`
          : "Click a character to move. Pinyin sits under each character and word."}
      </p>
    </div>
  );
}
