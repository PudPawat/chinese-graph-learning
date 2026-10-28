SELECT json_build_object(
  'characters', (
    SELECT json_agg(row_to_json(card) ORDER BY card.stroke_count, card.traditional)
    FROM (
      SELECT traditional, simplified, codepoint, stroke_count, structure, tocfl_band,
             zhuyin, pinyin, tone, gloss_en, gloss_zh, part_of_speech, radical, radical_meaning
      FROM character_card
    ) card
  ),
  'senses', (
    SELECT json_agg(json_build_object(
      'glyph', traditional,
      'sort', sort_order,
      'primary', is_primary,
      'pos', part_of_speech,
      'en', gloss_en,
      'zh', gloss_zh
    ) ORDER BY traditional, sort_order)
    FROM character_senses
  ),
  'words', (
    SELECT json_agg(json_build_object(
      'traditional', w.traditional,
      'simplified', w.simplified,
      'pinyin', w.pinyin,
      'en', w.gloss_en,
      'zh', w.gloss_zh,
      'pos', w.part_of_speech,
      'chars', (
        SELECT json_agg(c.traditional ORDER BY wc.position)
        FROM word_characters wc
        JOIN characters c ON c.node_id = wc.character_id
        WHERE wc.word_id = w.node_id
      )
    ) ORDER BY w.traditional)
    FROM words w
  ),
  'graphs', (
    SELECT json_object_agg(c.traditional, (
      SELECT COALESCE(json_agg(json_build_object(
        'label', g.neighbor_label,
        'kind', g.neighbor_kind,
        'relation', g.relation,
        'detail', g.detail,
        'weight', g.weight
      ) ORDER BY g.relation, g.neighbor_label), '[]'::json)
      FROM character_graph(c.traditional) g
    ))
    FROM characters c
  )
);
