-- Sample reads for the learning graph. Load schema.sql then seed.sql first.

-- Empty result means every character has one primary reading and one primary sense.
SELECT c.traditional
FROM characters c
LEFT JOIN readings r ON r.character_id = c.node_id AND r.is_primary
LEFT JOIN senses s ON s.owner_id = c.node_id AND s.owner_kind = 'character' AND s.is_primary
WHERE r.id IS NULL OR s.node_id IS NULL;

-- Card for one character: reading, primary meaning, radical.
SELECT traditional, zhuyin, pinyin, gloss_en, gloss_zh, radical, stroke_count, structure
FROM character_card
WHERE traditional = '情';

-- Both meanings of 情. Only "feeling" participates in meaning links.
SELECT traditional, sort_order, is_primary, gloss_en, gloss_zh
FROM character_senses
WHERE traditional = '情'
ORDER BY sort_order;

-- Everything connected to 情: sound part 青, heart part 忄, siblings, words.
SELECT neighbor_label, neighbor_kind, relation, detail, weight
FROM character_graph('情')
ORDER BY relation, neighbor_label;

-- 青 is the sound hub. This should list 清, 情, 請, 晴.
SELECT neighbor_label, relation, detail
FROM character_graph('青')
WHERE relation = 'same_phonetic'
ORDER BY neighbor_label;

-- 木 grows into 林 and 森 by repetition, and into the word 森林.
SELECT neighbor_label, neighbor_kind, relation, detail
FROM character_graph('木')
ORDER BY relation, neighbor_label;

-- 大 links to 小 by meaning (antonym) and to the word 大小.
SELECT neighbor_label, neighbor_kind, relation, detail
FROM character_graph('大')
ORDER BY relation, neighbor_label;

-- Lexicon after lexicon.sql. One row is the raw word record.
SELECT traditional, simplified, pinyin, hsk_level, parts_of_speech, labels, glyphs, gloss_en
FROM lexicon_card
WHERE traditional = '蘋果';

-- Food includes words tagged food and words tagged a child of food.
SELECT w.traditional, w.hsk_level, l.name_en
FROM words w
JOIN word_labels wl ON wl.word_id = w.node_id
JOIN labels l ON l.id = wl.label_id
WHERE l.id = 'food' OR l.parent_id = 'food'
ORDER BY w.hsk_level NULLS LAST, w.traditional;
