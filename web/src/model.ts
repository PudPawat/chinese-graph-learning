import raw from "./data/graph.json";
import type { Character, GraphFile, GraphLink, GroupId, Sense, Word } from "./types";

const data = raw as GraphFile;

export const characters: Character[] = data.characters;
export const senses: Sense[] = data.senses;
export const words: Word[] = data.words;
export const graphs = data.graphs;

export const characterByGlyph = new Map(characters.map((character) => [character.traditional, character]));
export const wordByText = new Map(words.map((word) => [word.traditional, word]));

export const GROUP_LABEL: Record<GroupId, string> = {
  sound: "Sound",
  form: "Form",
  meaning: "Meaning",
  words: "Words",
};

export const GROUPS: GroupId[] = ["sound", "form", "meaning", "words"];

export const RELATION_LABEL: Record<string, string> = {
  phonetic_of: "Sound part",
  same_phonetic: "Same sound",
  semantic_of: "Meaning part",
  radical_of: "Radical",
  component_of: "Other part",
  variant_of: "Side form",
  same_semantic: "Same part family",
  similar_meaning: "Similar meaning",
  antonym: "Opposite",
  same_topic: "Same topic",
  in_word: "In a word",
};

const GROUP_RANK: Record<GroupId, number> = {
  meaning: 0,
  sound: 1,
  words: 2,
  form: 3,
};

const KIND_RANK: Record<string, number> = {
  component: 0,
  character: 1,
  word: 2,
  topic: 3,
};

export type FocusNode = {
  id: string;
  label: string;
  kind: string;
  sector: GroupId;
  links: GraphLink[];
};

export type PlacedNode = FocusNode & { x: number; y: number };

export type MapWordLabel = {
  text: string;
  pinyin: string;
};

export type MapEdge = {
  a: string;
  b: string;
  groups: GroupId[];
  labels: MapWordLabel[];
};

export const MAP_POS: Record<string, { x: number; y: number }> = {
  青: { x: 520, y: 64 },
  晴: { x: 690, y: 46 },
  請: { x: 780, y: 130 },
  清: { x: 320, y: 128 },
  情: { x: 520, y: 196 },
  心: { x: 240, y: 210 },
  愛: { x: 120, y: 320 },
  想: { x: 270, y: 370 },
  木: { x: 110, y: 470 },
  林: { x: 290, y: 545 },
  森: { x: 90, y: 590 },
  看: { x: 430, y: 500 },
  見: { x: 580, y: 575 },
  江: { x: 830, y: 175 },
  河: { x: 990, y: 120 },
  水: { x: 900, y: 310 },
  海: { x: 700, y: 430 },
  湖: { x: 1020, y: 390 },
  大: { x: 620, y: 545 },
  小: { x: 860, y: 575 },
};

export function groupOf(relation: string): GroupId {
  if (relation === "phonetic_of" || relation === "same_phonetic") return "sound";
  if (relation === "similar_meaning" || relation === "antonym" || relation === "same_topic") return "meaning";
  if (relation === "in_word") return "words";
  return "form";
}

export function sensesFor(glyph: string): Sense[] {
  return senses.filter((sense) => sense.glyph === glyph);
}

export function fold(value: string): string {
  return value.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

export function readingFor(kind: string, label: string): string | null {
  if (kind === "word") return wordByText.get(label)?.pinyin ?? null;
  return characterByGlyph.get(label)?.pinyin ?? null;
}

export function matchesWord(word: Word, query: string): boolean {
  const needle = fold(query.trim());
  if (!needle) return true;
  return fold(`${word.traditional} ${word.simplified} ${word.pinyin} ${word.en} ${word.zh}`).includes(needle);
}

export function matchesQuery(character: Character, query: string): boolean {
  const needle = fold(query.trim());
  if (!needle) return true;
  const senseText = sensesFor(character.traditional)
    .map((sense) => `${sense.en} ${sense.zh}`)
    .join(" ");
  const relatedWords = words
    .filter((word) => word.chars.includes(character.traditional))
    .map((word) => `${word.traditional} ${word.pinyin} ${word.en} ${word.zh}`)
    .join(" ");
  const haystack = fold(
    [
      character.traditional,
      character.simplified,
      character.pinyin,
      character.zhuyin,
      character.gloss_en,
      character.gloss_zh,
      senseText,
      relatedWords,
    ].join(" "),
  );
  return haystack.includes(needle);
}

function place(detail: string): string {
  const times = detail.match(/^(\d+)/);
  if (detail.includes("repeat") && times) return `written ${times[1]} times`;
  if (detail === "left") return "on the left";
  if (detail === "right") return "on the right";
  if (detail === "top") return "on the top";
  if (detail === "bottom") return "on the bottom";
  return detail;
}

export function explain(link: GraphLink): string {
  switch (link.relation) {
    case "phonetic_of":
      return `Sound part ${place(link.detail)}`;
    case "semantic_of":
      return `Meaning part ${place(link.detail)}`;
    case "radical_of":
      return "Radical";
    case "component_of":
      return `Other part ${place(link.detail)}`;
    case "variant_of":
      return link.detail;
    case "same_phonetic":
      return `Same sound, through ${link.detail}`;
    case "same_semantic":
      return `Same part family ${link.detail}`;
    case "same_topic":
      return `Topic ${link.detail}`;
    case "in_word": {
      const position = link.detail.match(/\d+/)?.[0];
      return position ? `Character ${position} in the word` : link.detail;
    }
    default:
      return link.detail;
  }
}

export function focusNodes(glyph: string, enabled: Record<GroupId, boolean>): FocusNode[] {
  const merged = new Map<string, FocusNode>();
  for (const link of graphs[glyph] ?? []) {
    const id = `${link.kind}:${link.label}`;
    const existing = merged.get(id);
    if (existing) {
      existing.links.push(link);
      continue;
    }
    merged.set(id, {
      id,
      label: link.label,
      kind: link.kind,
      sector: "form",
      links: [link],
    });
  }

  const nodes: FocusNode[] = [];
  for (const node of merged.values()) {
    const groups = [...new Set(node.links.map((link) => groupOf(link.relation)))];
    const sector = GROUPS.slice().sort((a, b) => GROUP_RANK[a] - GROUP_RANK[b]).find(
      (group) => groups.includes(group) && enabled[group],
    );
    if (!sector) continue;
    node.sector = sector;
    nodes.push(node);
  }

  nodes.sort((a, b) => {
    const byKind = (KIND_RANK[a.kind] ?? 9) - (KIND_RANK[b.kind] ?? 9);
    if (byKind !== 0) return byKind;
    return a.label.localeCompare(b.label, "zh-Hant");
  });
  return nodes;
}

const QUADRANT: Record<GroupId, { x: number; y: number }> = {
  sound: { x: 220, y: 118 },
  form: { x: 760, y: 118 },
  meaning: { x: 220, y: 530 },
  words: { x: 760, y: 530 },
};

export const FOCUS_CENTER = { x: 490, y: 340 };
export const FOCUS_VIEW = { width: 980, height: 800 };

export function layoutFocus(nodes: FocusNode[]): PlacedNode[] {
  const buckets = new Map<GroupId, FocusNode[]>();
  for (const node of nodes) {
    const list = buckets.get(node.sector);
    if (list) list.push(node);
    else buckets.set(node.sector, [node]);
  }

  const placed: PlacedNode[] = [];
  for (const [sector, list] of buckets) {
    const origin = QUADRANT[sector];
    const perRow = sector === "words" ? Math.min(3, list.length) : Math.min(4, list.length);
    const colGap = sector === "words" ? 136 : 96;
    const rowGap = 118;
    list.forEach((node, index) => {
      const row = Math.floor(index / perRow);
      const col = index % perRow;
      const rowCount = Math.min(perRow, list.length - row * perRow);
      const rowWidth = (rowCount - 1) * colGap;
      placed.push({
        ...node,
        x: origin.x - rowWidth / 2 + col * colGap,
        y: origin.y + row * rowGap,
      });
    });
  }
  return placed;
}

export function nodeTarget(node: FocusNode): string | null {
  if (node.kind === "word") return null;
  return characterByGlyph.has(node.label) ? node.label : null;
}

function edgeKey(a: string, b: string): string {
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}

function addGroup(edge: MapEdge, group: GroupId, label?: MapWordLabel) {
  if (!edge.groups.includes(group)) edge.groups.push(group);
  if (label && !edge.labels.some((item) => item.text === label.text)) edge.labels.push(label);
}

export const mapEdges: MapEdge[] = buildMapEdges();

function buildMapEdges(): MapEdge[] {
  const edges = new Map<string, MapEdge>();
  const touch = (a: string, b: string, group: GroupId, label?: MapWordLabel) => {
    if (!a || !b || a === b || !MAP_POS[a] || !MAP_POS[b]) return;
    const key = edgeKey(a, b);
    const existing = edges.get(key);
    if (existing) {
      addGroup(existing, group, label);
      return;
    }
    const created: MapEdge = { a, b, groups: [group], labels: [] };
    if (label) created.labels.push(label);
    edges.set(key, created);
  };

  for (const word of words) {
    const [first, second] = word.chars;
    if (word.chars.length === 2 && first && second) {
      touch(first, second, "words", { text: word.traditional, pinyin: word.pinyin });
    }
  }

  for (const [glyph, links] of Object.entries(graphs)) {
    for (const link of links) {
      if (link.kind !== "character") continue;
      if (link.relation === "same_phonetic") {
        const hub = characterByGlyph.has(link.detail) ? link.detail : null;
        if (hub && hub !== glyph) touch(glyph, hub, "sound");
        else if (glyph === link.detail) touch(glyph, link.label, "sound");
        continue;
      }
      if (link.relation === "same_semantic") {
        const hub = link.detail.split(" · ").find((part) => characterByGlyph.has(part));
        if (hub) touch(glyph, hub, "form");
        continue;
      }
      if (link.relation === "similar_meaning" || link.relation === "antonym") {
        touch(glyph, link.label, "meaning");
      }
    }
  }

  return [...edges.values()];
}

export function visibleMapGroup(edge: MapEdge, enabled: Record<GroupId, boolean>): GroupId | null {
  const ranked = edge.groups.slice().sort((a, b) => GROUP_RANK[a] - GROUP_RANK[b]);
  return ranked.find((group) => enabled[group]) ?? null;
}

export function initialGlyph(): string {
  const fromHash = decodeURIComponent(window.location.hash.replace(/^#/, ""));
  if (characterByGlyph.has(fromHash)) return fromHash;
  return "情";
}
