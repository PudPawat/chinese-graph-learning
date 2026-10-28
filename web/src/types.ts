export type GroupId = "sound" | "form" | "meaning" | "words";

export type Character = {
  traditional: string;
  simplified: string;
  codepoint: string;
  stroke_count: number;
  structure: string;
  tocfl_band: string | null;
  zhuyin: string;
  pinyin: string;
  tone: number;
  gloss_en: string;
  gloss_zh: string;
  part_of_speech: string;
  radical: string;
  radical_meaning: string;
};

export type Sense = {
  glyph: string;
  sort: number;
  primary: boolean;
  pos: string;
  en: string;
  zh: string;
};

export type Word = {
  traditional: string;
  simplified: string;
  pinyin: string;
  en: string;
  zh: string;
  pos: string;
  chars: string[];
};

export type GraphLink = {
  label: string;
  kind: string;
  relation: string;
  detail: string;
  weight: number;
};

export type GraphFile = {
  characters: Character[];
  senses: Sense[];
  words: Word[];
  graphs: Record<string, GraphLink[]>;
};
