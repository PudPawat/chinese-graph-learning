-- Traditional Chinese character graph
-- Requires PostgreSQL 14 or newer.
--
-- The traditional glyph is the identity of a character. Simplified form,
-- Zhuyin, and pinyin are attributes. They are not separate nodes.
--
-- Connections are a property graph stored in PostgreSQL:
--   nodes   one row for a character, word, sense, component, or topic
--   links   a typed edge between two nodes
--
-- Two kinds of connection stay separate on purpose:
--   graphic   shared part, shared sound (聲旁), shared radical (形旁)
--   meaning   one sense of a character, not the glyph as a whole
-- A character such as 行 can mean "walk" or "row". Meaning links attach
-- to a sense so those ideas do not get mixed together.
--
-- Word membership is ordered in word_characters. It is not copied into links.
-- Decomposition is stored in character_components. rebuild_derived_links()
-- turns that structure into graphic edges the visualizer can walk.
--
-- The word list is a lexicon, separate from the character drawing.
-- Three filters stay separate so they do not collapse into one tag soup:
--   hsk_level       one band, the old HSK 2.0 level where the word is introduced
--   part of speech  one or more, on word_pos (noun is not a topic)
--   labels          many topics, on word_labels (daily life, vegetables, business)
-- A word may name glyphs that are not character-graph nodes yet.
-- Those glyphs live in word_glyphs. word_characters is filled only when
-- the glyph already exists in characters.

CREATE TABLE nodes (
  id    text PRIMARY KEY,
  kind  text NOT NULL CHECK (kind IN ('character', 'word', 'sense', 'component', 'topic')),
  label text NOT NULL
);

CREATE TABLE components (
  node_id       text PRIMARY KEY REFERENCES nodes (id) ON DELETE CASCADE,
  glyph         text NOT NULL CHECK (char_length(glyph) >= 1),
  kind          text NOT NULL CHECK (kind IN ('radical', 'form', 'phonetic')),
  kangxi_index  smallint CHECK (kangxi_index BETWEEN 1 AND 214),
  meaning_en    text NOT NULL,
  meaning_zh    text NOT NULL,
  stroke_count  smallint NOT NULL CHECK (stroke_count > 0)
);

-- 氵 is the left-side form of 水, 忄 of 心, 訁 of 言.
CREATE TABLE component_variants (
  variant_id    text PRIMARY KEY REFERENCES components (node_id) ON DELETE CASCADE,
  canonical_id  text NOT NULL REFERENCES components (node_id),
  form_label    text NOT NULL,
  CHECK (variant_id <> canonical_id)
);

CREATE TABLE characters (
  node_id       text PRIMARY KEY REFERENCES nodes (id) ON DELETE CASCADE,
  traditional   text NOT NULL UNIQUE CHECK (char_length(traditional) = 1),
  simplified    text NOT NULL CHECK (char_length(simplified) = 1),
  codepoint     text NOT NULL,
  stroke_count  smallint NOT NULL CHECK (stroke_count > 0),
  structure     text NOT NULL CHECK (structure IN ('獨體', '左右', '上下', '包圍', '品字', '其他')),
  radical_id    text NOT NULL REFERENCES components (node_id),
  tocfl_band    text CHECK (tocfl_band IN ('準備級', '入門級', '基礎級', '進階級', '高階級', '流利級')),
  note          text
);

CREATE TABLE readings (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  character_id  text NOT NULL REFERENCES characters (node_id) ON DELETE CASCADE,
  zhuyin        text NOT NULL,
  pinyin        text NOT NULL,
  tone          smallint NOT NULL CHECK (tone BETWEEN 1 AND 5),
  is_primary    boolean NOT NULL DEFAULT false,
  UNIQUE (character_id, zhuyin)
);

CREATE UNIQUE INDEX readings_one_primary
  ON readings (character_id)
  WHERE is_primary;

-- A sense is one meaning. Character 情 has "feeling" and "situation"
-- as two senses. Only "feeling" links to 愛.
CREATE TABLE senses (
  node_id        text PRIMARY KEY REFERENCES nodes (id) ON DELETE CASCADE,
  owner_kind     text NOT NULL CHECK (owner_kind IN ('character', 'word')),
  owner_id       text NOT NULL REFERENCES nodes (id),
  gloss_en       text NOT NULL,
  gloss_zh       text NOT NULL,
  part_of_speech text NOT NULL CHECK (part_of_speech IN (
    'noun', 'verb', 'adjective', 'adverb', 'measure', 'pronoun', 'number',
    'particle', 'conjunction', 'preposition', 'interjection', 'localizer', 'other'
  )),
  is_primary     boolean NOT NULL DEFAULT false,
  sort_order     smallint NOT NULL DEFAULT 0,
  CHECK (owner_id <> node_id)
);

CREATE UNIQUE INDEX senses_one_primary
  ON senses (owner_id)
  WHERE is_primary;

CREATE TABLE words (
  node_id        text PRIMARY KEY REFERENCES nodes (id) ON DELETE CASCADE,
  traditional    text NOT NULL UNIQUE CHECK (char_length(traditional) >= 1),
  simplified     text NOT NULL CHECK (char_length(simplified) >= 1),
  pinyin         text NOT NULL,
  gloss_en       text NOT NULL,
  gloss_zh       text NOT NULL,
  part_of_speech text NOT NULL CHECK (part_of_speech IN (
    'noun', 'verb', 'adjective', 'adverb', 'measure', 'pronoun', 'number',
    'particle', 'conjunction', 'preposition', 'interjection', 'localizer', 'other'
  )),
  hsk_level      smallint CHECK (hsk_level BETWEEN 1 AND 6),
  tocfl_band     text CHECK (tocfl_band IN ('準備級', '入門級', '基礎級', '進階級', '高階級', '流利級'))
);

CREATE INDEX words_by_hsk ON words (hsk_level);

-- Ordered glyphs of a word, whether or not that character is in the graph yet.
CREATE TABLE word_glyphs (
  word_id   text NOT NULL REFERENCES words (node_id) ON DELETE CASCADE,
  position  smallint NOT NULL CHECK (position >= 1),
  glyph     text NOT NULL CHECK (char_length(glyph) = 1),
  PRIMARY KEY (word_id, position)
);

-- Topic labels. parent_id groups a specific label under a broader one
-- (vegetables → food). The parent is not copied onto the word.
CREATE TABLE labels (
  id         text PRIMARY KEY,
  group_name text NOT NULL,
  name_en    text NOT NULL,
  name_zh    text NOT NULL,
  parent_id  text REFERENCES labels (id),
  CHECK (parent_id IS NULL OR parent_id <> id)
);

CREATE TABLE word_labels (
  word_id   text NOT NULL REFERENCES words (node_id) ON DELETE CASCADE,
  label_id  text NOT NULL REFERENCES labels (id),
  PRIMARY KEY (word_id, label_id)
);

CREATE INDEX word_labels_by_label ON word_labels (label_id);

-- A word such as 工作 is both a noun and a verb. One row is primary.
CREATE TABLE word_pos (
  word_id        text NOT NULL REFERENCES words (node_id) ON DELETE CASCADE,
  part_of_speech text NOT NULL CHECK (part_of_speech IN (
    'noun', 'verb', 'adjective', 'adverb', 'measure', 'pronoun', 'number',
    'particle', 'conjunction', 'preposition', 'interjection', 'localizer', 'other'
  )),
  is_primary     boolean NOT NULL DEFAULT false,
  PRIMARY KEY (word_id, part_of_speech)
);

CREATE UNIQUE INDEX word_pos_one_primary
  ON word_pos (word_id)
  WHERE is_primary;

CREATE TABLE word_characters (
  word_id       text NOT NULL REFERENCES words (node_id) ON DELETE CASCADE,
  character_id  text NOT NULL REFERENCES characters (node_id),
  position      smallint NOT NULL CHECK (position >= 1),
  PRIMARY KEY (word_id, position)
);

CREATE INDEX word_characters_by_character
  ON word_characters (character_id);

-- How a glyph is built. role is the job of that part inside this character.
-- repeat_count covers 林 (木 twice) and 森 (木 three times).
CREATE TABLE character_components (
  character_id  text NOT NULL REFERENCES characters (node_id) ON DELETE CASCADE,
  component_id  text NOT NULL REFERENCES components (node_id),
  role          text NOT NULL CHECK (role IN ('semantic', 'phonetic', 'residual')),
  position      text NOT NULL CHECK (position IN (
    'left', 'right', 'top', 'bottom', 'outer', 'inner', 'repeat', 'whole'
  )),
  repeat_count  smallint NOT NULL DEFAULT 1 CHECK (repeat_count >= 1),
  PRIMARY KEY (character_id, component_id, role, position)
);

CREATE TABLE topics (
  node_id   text PRIMARY KEY REFERENCES nodes (id) ON DELETE CASCADE,
  name_zh   text NOT NULL,
  name_en   text NOT NULL,
  summary   text NOT NULL
);

CREATE TABLE links (
  id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  src_id    text NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
  dst_id    text NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
  relation  text NOT NULL CHECK (relation IN (
    'phonetic_of',       -- sound part → character that uses it (青 → 情)
    'semantic_of',       -- meaning part → character (忄 → 情)
    'radical_of',        -- Kangxi radical → character
    'component_of',      -- any other part → character
    'variant_of',        -- alternate form → canonical form (忄 → 心)
    'similar_meaning',   -- sense ↔ sense
    'antonym',           -- sense ↔ sense
    'confusable_with',   -- character ↔ character (己 / 已 / 巳)
    'in_topic'           -- sense → topic
  )),
  weight    numeric(3, 2) NOT NULL DEFAULT 1.00 CHECK (weight > 0 AND weight <= 1),
  origin    text NOT NULL CHECK (origin IN ('derived', 'curated')),
  note      text,
  CHECK (src_id <> dst_id),
  UNIQUE (src_id, dst_id, relation)
);

CREATE INDEX links_by_src ON links (src_id);
CREATE INDEX links_by_dst ON links (dst_id);
CREATE INDEX links_by_relation ON links (relation);

CREATE OR REPLACE FUNCTION enforce_sense_owner()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM nodes
    WHERE id = NEW.owner_id
      AND kind = NEW.owner_kind
  ) THEN
    RAISE EXCEPTION 'sense % owner % is not a % node', NEW.node_id, NEW.owner_id, NEW.owner_kind;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER senses_owner_kind
  BEFORE INSERT OR UPDATE ON senses
  FOR EACH ROW
  EXECUTE FUNCTION enforce_sense_owner();

-- Rebuild graphic edges from decomposition. Curated meaning edges stay.
CREATE OR REPLACE FUNCTION rebuild_derived_links()
RETURNS void
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
  DELETE FROM links WHERE origin = 'derived';

  INSERT INTO links (src_id, dst_id, relation, weight, origin, note)
  SELECT
    component_id,
    character_id,
    CASE role
      WHEN 'phonetic' THEN 'phonetic_of'
      WHEN 'semantic' THEN 'semantic_of'
      ELSE 'component_of'
    END,
    1.00,
    'derived',
    CASE
      WHEN repeat_count > 1 THEN repeat_count::text || ' × ' || position
      ELSE position
    END
  FROM character_components;

  INSERT INTO links (src_id, dst_id, relation, weight, origin, note)
  SELECT radical_id, node_id, 'radical_of', 1.00, 'derived', 'Kangxi radical'
  FROM characters
  ON CONFLICT (src_id, dst_id, relation) DO NOTHING;

  INSERT INTO links (src_id, dst_id, relation, weight, origin, note)
  SELECT variant_id, canonical_id, 'variant_of', 1.00, 'derived', form_label
  FROM component_variants;
END;
$$;

-- One place the future visualizer calls. Graphic links, meaning links,
-- words, and topic peers come back as rows around a single glyph.
CREATE OR REPLACE FUNCTION character_graph(p_glyph text)
RETURNS TABLE (
  neighbor_label text,
  neighbor_kind  text,
  relation       text,
  detail         text,
  weight         numeric
)
LANGUAGE sql
STABLE
SET search_path = public
AS $$
  WITH me AS (
    SELECT node_id
    FROM characters
    WHERE traditional = p_glyph
  ),
  parts AS (
    SELECT
      n.label                          AS neighbor_label,
      n.kind                           AS neighbor_kind,
      l.relation,
      COALESCE(l.note, '')             AS detail,
      l.weight
    FROM links l
    JOIN me ON l.dst_id = me.node_id
    JOIN nodes n ON n.id = l.src_id
    WHERE l.relation IN ('phonetic_of', 'semantic_of', 'radical_of', 'component_of')
  ),
  -- 忄 on the left of 情 is the side form of 心. Surface that alias.
  part_forms AS (
    SELECT
      canonical.label                  AS neighbor_label,
      canonical.kind                   AS neighbor_kind,
      'variant_of'::text               AS relation,
      variant.label || ' is the ' || l.note || ' form' AS detail,
      l.weight
    FROM links mine
    JOIN me ON mine.dst_id = me.node_id
    JOIN links l
      ON l.src_id = mine.src_id
     AND l.relation = 'variant_of'
    JOIN nodes variant ON variant.id = l.src_id
    JOIN nodes canonical ON canonical.id = l.dst_id
    WHERE mine.relation IN ('phonetic_of', 'semantic_of', 'radical_of', 'component_of')
  ),
  phonetic_siblings AS (
    SELECT DISTINCT
      c.traditional,
      'character'::text,
      'same_phonetic'::text,
      src.label,
      0.85::numeric
    FROM links mine
    JOIN me ON mine.dst_id = me.node_id AND mine.relation = 'phonetic_of'
    JOIN links other
      ON other.src_id = mine.src_id
     AND other.relation = 'phonetic_of'
     AND other.dst_id <> me.node_id
    JOIN characters c ON c.node_id = other.dst_id
    JOIN nodes src ON src.id = mine.src_id
  ),
  -- Opening the sound part itself (青) should list characters that use it.
  phonetic_hub AS (
    SELECT DISTINCT
      c.traditional,
      'character'::text,
      'same_phonetic'::text,
      self.traditional,
      0.85::numeric
    FROM characters self
    JOIN me ON self.node_id = me.node_id
    JOIN components part ON part.glyph = self.traditional
    JOIN links edge
      ON edge.src_id = part.node_id
     AND edge.relation = 'phonetic_of'
    JOIN characters c ON c.node_id = edge.dst_id
  ),
  semantic_family AS (
    SELECT mine.src_id AS comp_id
    FROM links mine
    JOIN me ON mine.dst_id = me.node_id
    WHERE mine.relation IN ('semantic_of', 'radical_of')
    UNION
    SELECT cv.canonical_id
    FROM links mine
    JOIN me ON mine.dst_id = me.node_id
     AND mine.relation IN ('semantic_of', 'radical_of')
    JOIN component_variants cv ON cv.variant_id = mine.src_id
    UNION
    SELECT cv.variant_id
    FROM links mine
    JOIN me ON mine.dst_id = me.node_id
     AND mine.relation IN ('semantic_of', 'radical_of')
    JOIN component_variants cv ON cv.canonical_id = mine.src_id
  ),
  same_semantic AS (
    SELECT
      c.traditional,
      'character'::text,
      'same_semantic'::text,
      string_agg(DISTINCT n.label, ' · ' ORDER BY n.label),
      0.75::numeric
    FROM semantic_family fam
    JOIN links edge
      ON edge.src_id = fam.comp_id
     AND edge.relation IN ('semantic_of', 'radical_of')
    JOIN characters c ON c.node_id = edge.dst_id
    JOIN nodes n ON n.id = fam.comp_id
    WHERE c.traditional <> p_glyph
    GROUP BY c.traditional
  ),
  word_hits AS (
    SELECT
      w.traditional,
      'word'::text,
      'in_word'::text,
      'position ' || wc.position::text,
      0.90::numeric
    FROM word_characters wc
    JOIN me ON wc.character_id = me.node_id
    JOIN words w ON w.node_id = wc.word_id
  ),
  sense_links AS (
    SELECT
      c2.traditional,
      'character'::text,
      l.relation,
      s1.gloss_en || ' · ' || s2.gloss_en,
      l.weight
    FROM senses s1
    JOIN me ON s1.owner_id = me.node_id AND s1.owner_kind = 'character'
    JOIN links l
      ON l.relation IN ('similar_meaning', 'antonym')
     AND (l.src_id = s1.node_id OR l.dst_id = s1.node_id)
    JOIN senses s2
      ON s2.node_id = CASE
        WHEN l.src_id = s1.node_id THEN l.dst_id
        ELSE l.src_id
      END
     AND s2.owner_kind = 'character'
    JOIN characters c2 ON c2.node_id = s2.owner_id
  ),
  topic_peers AS (
    SELECT DISTINCT
      c2.traditional,
      'character'::text,
      'same_topic'::text,
      t.name_zh,
      0.60::numeric
    FROM senses s1
    JOIN me ON s1.owner_id = me.node_id AND s1.owner_kind = 'character'
    JOIN links l ON l.src_id = s1.node_id AND l.relation = 'in_topic'
    JOIN topics t ON t.node_id = l.dst_id
    JOIN links other
      ON other.dst_id = l.dst_id
     AND other.relation = 'in_topic'
     AND other.src_id <> s1.node_id
    JOIN senses s2 ON s2.node_id = other.src_id AND s2.owner_kind = 'character'
    JOIN characters c2 ON c2.node_id = s2.owner_id
    WHERE c2.traditional <> p_glyph
  )
  SELECT * FROM parts
  UNION ALL SELECT * FROM part_forms
  UNION ALL SELECT * FROM phonetic_siblings
  UNION ALL SELECT * FROM phonetic_hub
  UNION ALL SELECT * FROM same_semantic
  UNION ALL SELECT * FROM word_hits
  UNION ALL SELECT * FROM sense_links
  UNION ALL SELECT * FROM topic_peers
$$;

CREATE VIEW character_card AS
SELECT
  c.traditional,
  c.simplified,
  c.codepoint,
  c.stroke_count,
  c.structure,
  c.tocfl_band,
  r.zhuyin,
  r.pinyin,
  r.tone,
  s.gloss_en,
  s.gloss_zh,
  s.part_of_speech,
  rad.glyph AS radical,
  rad.meaning_en AS radical_meaning
FROM characters c
LEFT JOIN readings r
  ON r.character_id = c.node_id
 AND r.is_primary
LEFT JOIN senses s
  ON s.owner_id = c.node_id
 AND s.owner_kind = 'character'
 AND s.is_primary
LEFT JOIN components rad
  ON rad.node_id = c.radical_id;

CREATE VIEW character_senses AS
SELECT
  c.traditional,
  s.sort_order,
  s.is_primary,
  s.part_of_speech,
  s.gloss_en,
  s.gloss_zh
FROM senses s
JOIN characters c
  ON c.node_id = s.owner_id
 AND s.owner_kind = 'character';

COMMENT ON TABLE nodes IS 'Graph nodes. Every character, word, sense, component, and topic has one.';
COMMENT ON TABLE links IS 'Typed edges. Derived edges are rebuilt from structure; curated edges are meaning, opposites, and topics.';
COMMENT ON TABLE senses IS 'One meaning of a character or word. Meaning edges attach here, not to the glyph.';
COMMENT ON FUNCTION character_graph IS 'Neighborhood of one traditional character for the learning graph.';
COMMENT ON TABLE labels IS 'Topic labels. A word may have many. Part of speech and HSK level are not labels.';
COMMENT ON COLUMN words.hsk_level IS 'Old HSK 2.0 level where this word is introduced. Null means it is not on that list.';

-- One row per word for reading the lexicon without joining by hand.
CREATE VIEW lexicon_card AS
SELECT
  w.traditional,
  w.simplified,
  w.pinyin,
  w.hsk_level,
  w.part_of_speech AS primary_pos,
  w.gloss_en,
  w.gloss_zh,
  (
    SELECT string_agg(wp.part_of_speech, ', ' ORDER BY wp.is_primary DESC, wp.part_of_speech)
    FROM word_pos wp
    WHERE wp.word_id = w.node_id
  ) AS parts_of_speech,
  (
    SELECT string_agg(l.name_en, ', ' ORDER BY l.group_name, l.name_en)
    FROM word_labels wl
    JOIN labels l ON l.id = wl.label_id
    WHERE wl.word_id = w.node_id
  ) AS labels,
  (
    SELECT string_agg(g.glyph, '' ORDER BY g.position)
    FROM word_glyphs g
    WHERE g.word_id = w.node_id
  ) AS glyphs
FROM words w;
