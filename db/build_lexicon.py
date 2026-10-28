#!/usr/bin/env python3
"""Editable source for the word lexicon.

Regenerates db/lexicon.json, web/src/data/lexicon.json, and db/lexicon.sql.
HSK levels are the old HSK 2.0 band where the word is introduced.
Null means the word is not on that list. Traditional forms follow Taiwan usage
when it differs from the mainland traditional HSK headword.
"""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB_JSON = ROOT.parent / "web" / "src" / "data" / "lexicon.json"
CEDICT_GZ = ROOT / "source" / "cedict.txt.gz"
HSK_DIR = ROOT / "source" / "hsk"

TONE_MARKS = {
    "a": "āáǎà",
    "e": "ēéěè",
    "i": "īíǐì",
    "o": "ōóǒò",
    "u": "ūúǔù",
    "ü": "ǖǘǚǜ",
}

# ICTCLAS-style tags used by the old HSK word lists.
HSK_POS = {
    "n": "noun",
    "nr": "noun",
    "ns": "noun",
    "nt": "noun",
    "nz": "noun",
    "t": "noun",
    "s": "noun",
    "v": "verb",
    "vd": "verb",
    "a": "adjective",
    "an": "adjective",
    "ad": "adjective",
    "ag": "adjective",
    "z": "adjective",
    "b": "adjective",
    "d": "adverb",
    "dg": "adverb",
    "q": "measure",
    "m": "number",
    "r": "pronoun",
    "u": "particle",
    "y": "particle",
    "c": "conjunction",
    "p": "preposition",
    "e": "interjection",
    "f": "localizer",
}

# Glyphs that already have a character-graph node in seed.sql.
GRAPH_GLYPHS = set("木林森水江河海湖心青清情請晴愛想大小看見")

POS = {
    "noun", "verb", "adjective", "adverb", "measure", "pronoun", "number",
    "particle", "conjunction", "preposition", "interjection", "localizer", "other",
}

# id, group, English, Chinese, parent id
LABELS = [
    ("daily-life", "Life", "Daily life", "日常生活", None),
    ("family", "Life", "Family", "家庭", None),
    ("house", "Life", "House", "住家", None),
    ("clothes", "Life", "Clothes", "衣服", None),
    ("body", "Life", "Body", "身體", None),
    ("health", "Life", "Health", "健康", None),
    ("food", "Food", "Food", "食物", None),
    ("vegetables", "Food", "Vegetables", "蔬菜", "food"),
    ("fruits", "Food", "Fruits", "水果", "food"),
    ("meat", "Food", "Meat", "肉類", "food"),
    ("drinks", "Food", "Drinks", "飲料", "food"),
    ("animals", "Nature", "Animals", "動物", None),
    ("nature", "Nature", "Nature", "自然", None),
    ("weather", "Nature", "Weather", "天氣", None),
    ("plants", "Nature", "Plants", "植物", None),
    ("business", "Society", "Business", "商業", None),
    ("work", "Society", "Work", "工作", None),
    ("school", "Society", "School", "學校", None),
    ("travel", "Society", "Travel", "旅行", None),
    ("transport", "Society", "Transport", "交通", None),
    ("shopping", "Society", "Shopping", "購物", None),
    ("culture", "Society", "Culture", "文化", None),
    ("time", "Time", "Time", "時間", None),
    ("numbers", "Time", "Numbers", "數字", None),
    ("emotions", "Mind", "Emotions", "情緒", None),
    ("language", "Mind", "Language", "語言", None),
    ("general", "General", "General", "一般", None),
    ("top-list", "Study", "Top list", "常用詞", None),
]

# English gloss patterns. A word may match more than one label.
# Child food labels also receive Food.
LABEL_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("vegetables", re.compile(r"\b(vegetables?|cabbages?|carrots?|cucumbers?|tomatoes?|potatoes?|spinach|onions?|garlics?|lettuces?|radishes?|eggplants?|aubergines?|broccoli|celery|leeks?|pumpkins?|squash|mushrooms?|scallions?|ginger)\b")),
    ("fruits", re.compile(r"\b(fruits?|apples?|bananas?|grapes?|oranges?|tangerines?|pears?|peaches?|melons?|berries|mangoes?|mangos?|lemons?|cherries|pineapples?|watermelons?|plums?|lychees?|litchis?|kiwis?|papayas?|coconuts?)\b")),
    ("meat", re.compile(r"\b(meats?|pork|beef|mutton|lamb|bacon|steaks?|poultry|sausages?|venison)\b")),
    ("drinks", re.compile(r"\b(teas?|coffees?|juices?|beers?|wines?|liquors?|alcohol|whisky|whiskey|milks?|beverages?|sodas?|drinks?|drinking)\b")),
    ("food", re.compile(r"\b(foods?|rice|noodles?|breads?|dumplings?|cuisines?|meals?|snacks?|soups?|cakes?|cookies?|tofu|sauces?|salts?|sugars?|spices?|candies|chocolate|breakfasts?|lunches?|dinners?|edible|flavou?rs?|restaurants?|cooking|cook)\b")),
    ("animals", re.compile(r"\b(animals?|bird species|mammals?|insects?|dogs?|cats?|horses?|cows?|oxen|ox|pigs?|sheep|goats?|tigers?|pandas?|elephants?|snakes?|dragons?|mice|mouse|rats?|rabbits?|ducks?|lions?|wolves|wolf|deer|monkeys?|whales?|bees?|ants?|fish|fishes|chickens?|foxes?|fox|bears?|turtles?|frogs?|spiders?|cattle|pets?)\b")),
    ("plants", re.compile(r"\b(plants?|trees?|flowers?|grasses?|leaves|leaf|bamboos?|pines?|roses?|seeds?|crops?|forests?|blossoms?|petals?|herbs?|bushes|shrubs?)\b")),
    ("weather", re.compile(r"\b(weathers?|rains?|raining|snows?|snowing|winds?|clouds?|storms?|sunny|thunders?|lightnings?|fogs?|frosts?|climates?|temperatures?|springs?|summers?|autumns?|winters?|typhoons?|humidity|seasons?)\b")),
    ("nature", re.compile(r"\b(rivers?|seas?|oceans?|lakes?|mountains?|islands?|skies|sky|earth|stones?|rocks?|valleys?|deserts?|sun|moon|stars?|waters?|lands?|hills?|beaches?|coasts?|nature|natural)\b")),
    ("body", re.compile(r"\b(bodies|body|hands?|heads?|feet|foot|eyes?|ears?|mouths?|noses?|hairs?|faces?|arms?|legs?|hearts?|blood|bones?|skins?|teeth|tooth|fingers?|shoulders?|necks?|stomachs?|brains?|muscles?|organs?)\b")),
    ("health", re.compile(r"\b(health|healthy|hospitals?|doctors?|medicines?|medical|illnesses?|sick|diseases?|pains?|aches?|symptoms?|surgeries|surgery|nurses?|patients?|viruses?|fevers?|injuries|injury|wounds?|clinics?|pharmacies|pharmacy|cancers?|infections?)\b")),
    ("clothes", re.compile(r"\b(clothes|clothing|shirts?|shoes?|hats?|caps?|trousers|pants|dresses?|coats?|skirts?|socks?|jackets?|uniforms?|garments?|sleeves?|collars?|fabrics?|silks?|cottons?)\b")),
    ("house", re.compile(r"\b(houses?|homes?|rooms?|doors?|windows?|beds?|chairs?|tables?|furniture|bathrooms?|walls?|floors?|roofs?|apartments?|kitchens?|toilets?|gates?|courtyards?)\b")),
    ("family", re.compile(r"\b(famil(?:y|ies)|fathers?|mothers?|parents?|sons?|daughters?|brothers?|sisters?|husbands?|wives|wife|children|child|uncles?|aunts?|grandfathers?|grandmothers?|babies|baby|marriages?|marry|relatives?)\b")),
    ("time", re.compile(r"\b(times?|today|tomorrow|yesterday|years?|months?|weeks?|hours?|minutes?|mornings?|afternoons?|evenings?|nights?|noons?|clocks?|o'clock|centur(?:y|ies)|dates?|calendars?|eras?)\b")),
    ("numbers", re.compile(r"\b(numbers?|digits?|percent(?:age)?s?|thousands?|millions?|billions?|zeros?|zeroes|quantit(?:y|ies)|dozens?|integers?|kilograms?|grams?|metres?|meters?|litres?|liters?)\b")),
    ("business", re.compile(r"\b(business(?:es)?|compan(?:y|ies)|contracts?|clients?|customers?|banks?|prices?|markets?|invest(?:ment|ing|ments)?|wages?|salar(?:y|ies)|trades?|commerce|econom(?:y|ic|ies)|profits?|managers?|financ(?:e|ial|es)|tax(?:es)?|stocks?|mone(?:y|ys)|currenc(?:y|ies)|costs?|fees?|invoices?|enterprises?|firms?)\b")),
    ("work", re.compile(r"\b(works?|jobs?|colleagues?|offices?|employees?|employers?|careers?|professions?|meetings?|e-?mails?|softwares?|computers?|bosses?|staff|duties|duty|tasks?|projects?)\b")),
    ("school", re.compile(r"\b(schools?|students?|teachers?|classes|class|classrooms?|exams?|examinations?|lessons?|stud(?:y|ying|ies)|universit(?:y|ies)|colleges?|homeworks?|grammars?|educations?|campuses|textbooks?|pupils?|professors?|academic)\b")),
    ("travel", re.compile(r"\b(travels?|tourism|tourists?|hotels?|luggages?|baggages?|passports?|visas?|trips?|sightseeing|journeys?|destinations?|tours?)\b")),
    ("transport", re.compile(r"\b(transports?|buses|bus|trains?|planes?|airplanes?|aircrafts?|cars?|taxis?|bicycles?|bikes?|subways?|metros?|boats?|ships?|roads?|airports?|stations?|vehicles?|traffics?|railways?|flights?|driv(?:e|ing))\b")),
    ("shopping", re.compile(r"\b(shops?|shopping|stores?|malls?|purchases?|buy(?:ing)?|sell(?:ing)?|cheap|expensive|retail)\b")),
    ("culture", re.compile(r"\b(cultures?|cultural|histories|history|historical|music|musical|films?|movies?|cinemas?|arts?|artists?|books?|paintings?|literatures?|poems?|poetry|songs?|dances?|museums?|traditions?|traditional|operas?|novels?|dramas?)\b")),
    ("emotions", re.compile(r"\b(loves?|loving|happ(?:y|iness)|sads?|sadness|angr(?:y|er)|anger|fears?|afraid|moods?|feelings?|emotions?|hopes?|hates?|hating|worr(?:y|ies)|joys?|cr(?:y|ies|ied)|smiles?|smiling|dislikes?|anxious|anxiety)\b")),
    ("language", re.compile(r"\b(languages?|words?|characters?|sentences?|grammars?|speaks?|speech|writ(?:e|ing|ten)|reads?|reading|meanings?|letters?|vocabular(?:y|ies)|pronunciations?|pronounce|dialects?|idioms?|slangs?|phrases?|verbs?|nouns?|adjectives?|particles?|classifiers?|variant of|abbreviations?|abbr\b)\b")),
    ("daily-life", re.compile(r"\b(people|persons?|friends?|names?|hello|thanks?|please|sorry|things?|lives?|living|sleeps?|sleeping|phones?|telephones?|televisions?|tvs?|wom[ae]n|men|girls?|boys?|males?|females?|ahead|in front|behind|inside|outside)\b")),
]

# traditional, simplified, pinyin, English, HSK or None, parts of speech, label ids
# The first part of speech is the primary one.
WORDS = [
    # --- HSK 1, people and grammar ---
    ("我", "我", "wǒ", "I; me", 1, ["pronoun"], ["daily-life"]),
    ("你", "你", "nǐ", "you", 1, ["pronoun"], ["daily-life"]),
    ("他", "他", "tā", "he; him", 1, ["pronoun"], ["daily-life"]),
    ("她", "她", "tā", "she; her", 1, ["pronoun"], ["daily-life"]),
    ("我們", "我们", "wǒmen", "we; us", 1, ["pronoun"], ["daily-life"]),
    ("這", "这", "zhè", "this", 1, ["pronoun"], ["daily-life"]),
    ("那", "那", "nà", "that", 1, ["pronoun"], ["daily-life"]),
    ("哪", "哪", "nǎ", "which", 1, ["pronoun"], ["daily-life"]),
    ("哪兒", "哪儿", "nǎr", "where", 1, ["pronoun"], ["daily-life"]),
    ("誰", "谁", "shéi", "who", 1, ["pronoun"], ["daily-life"]),
    ("什麼", "什么", "shénme", "what", 1, ["pronoun"], ["daily-life"]),
    ("多少", "多少", "duōshao", "how many; how much", 1, ["pronoun"], ["numbers", "daily-life"]),
    ("幾", "几", "jǐ", "how many", 1, ["pronoun"], ["numbers"]),
    ("不", "不", "bù", "not", 1, ["adverb"], ["daily-life"]),
    ("很", "很", "hěn", "very", 1, ["adverb"], ["daily-life"]),
    ("太", "太", "tài", "too; extremely", 1, ["adverb"], ["daily-life"]),
    ("都", "都", "dōu", "all; both", 1, ["adverb"], ["daily-life"]),
    ("和", "和", "hé", "and; with", 1, ["conjunction"], ["daily-life"]),
    ("的", "的", "de", "structural particle", 1, ["particle"], ["language"]),
    ("了", "了", "le", "aspect particle", 1, ["particle"], ["language"]),
    ("嗎", "吗", "ma", "question particle", 1, ["particle"], ["language"]),
    ("呢", "呢", "ne", "question particle", 1, ["particle"], ["language"]),
    ("在", "在", "zài", "at; to be at", 1, ["preposition", "verb"], ["daily-life"]),
    ("是", "是", "shì", "to be", 1, ["verb"], ["daily-life"]),
    ("有", "有", "yǒu", "to have", 1, ["verb"], ["daily-life"]),
    ("沒有", "没有", "méiyǒu", "to not have; there is not", 1, ["verb"], ["daily-life"]),
    ("做", "做", "zuò", "to do; to make", 1, ["verb"], ["daily-life"]),
    ("坐", "坐", "zuò", "to sit", 1, ["verb"], ["daily-life"]),
    ("來", "来", "lái", "to come", 1, ["verb"], ["daily-life"]),
    ("去", "去", "qù", "to go", 1, ["verb"], ["daily-life", "travel"]),
    ("回", "回", "huí", "to return", 1, ["verb"], ["daily-life"]),
    ("開", "开", "kāi", "to open; to drive", 1, ["verb"], ["daily-life"]),
    ("看", "看", "kàn", "to look at", 1, ["verb"], ["daily-life"]),
    ("看見", "看见", "kànjiàn", "to see", 1, ["verb"], ["daily-life"]),
    ("聽", "听", "tīng", "to listen", 1, ["verb"], ["daily-life"]),
    ("說", "说", "shuō", "to speak", 1, ["verb"], ["language"]),
    ("讀", "读", "dú", "to read", 1, ["verb"], ["school", "language"]),
    ("寫", "写", "xiě", "to write", 1, ["verb"], ["school", "language"]),
    ("吃", "吃", "chī", "to eat", 1, ["verb"], ["food", "daily-life"]),
    ("喝", "喝", "hē", "to drink", 1, ["verb"], ["drinks", "daily-life"]),
    ("買", "买", "mǎi", "to buy", 1, ["verb"], ["shopping"]),
    ("叫", "叫", "jiào", "to be called; to call", 1, ["verb"], ["daily-life"]),
    ("會", "会", "huì", "can; to be able to", 1, ["verb"], ["daily-life"]),
    ("能", "能", "néng", "can; to be able to", 1, ["verb"], ["daily-life"]),
    ("想", "想", "xiǎng", "to think; to want", 1, ["verb"], ["emotions"]),
    ("愛", "爱", "ài", "to love; love", 1, ["verb", "noun"], ["emotions"]),
    ("喜歡", "喜欢", "xǐhuan", "to like", 1, ["verb"], ["emotions"]),
    ("請", "请", "qǐng", "please; to invite", 1, ["verb"], ["daily-life"]),
    ("謝謝", "谢谢", "xièxie", "thank you", 1, ["verb"], ["daily-life"]),
    ("再見", "再见", "zàijiàn", "goodbye", 1, ["verb"], ["daily-life"]),
    ("認識", "认识", "rènshi", "to know (a person)", 1, ["verb"], ["daily-life"]),
    ("學習", "学习", "xuéxí", "to study; study", 1, ["verb", "noun"], ["school"]),
    ("住", "住", "zhù", "to live; to stay", 1, ["verb"], ["house"]),
    ("睡覺", "睡觉", "shuìjiào", "to sleep", 1, ["verb"], ["daily-life"]),
    ("打電話", "打电话", "dǎ diànhuà", "to make a phone call", 1, ["verb"], ["daily-life"]),
    ("下雨", "下雨", "xiàyǔ", "to rain", 1, ["verb"], ["weather"]),
    # HSK 1 description and size
    ("好", "好", "hǎo", "good", 1, ["adjective"], ["daily-life"]),
    ("大", "大", "dà", "big", 1, ["adjective"], ["daily-life"]),
    ("小", "小", "xiǎo", "small", 1, ["adjective"], ["daily-life"]),
    ("多", "多", "duō", "many; much", 1, ["adjective"], ["numbers"]),
    ("少", "少", "shǎo", "few; little", 1, ["adjective"], ["numbers"]),
    ("冷", "冷", "lěng", "cold", 1, ["adjective"], ["weather"]),
    ("熱", "热", "rè", "hot", 1, ["adjective"], ["weather"]),
    ("漂亮", "漂亮", "piàoliang", "pretty", 1, ["adjective"], ["daily-life"]),
    ("高興", "高兴", "gāoxìng", "happy", 1, ["adjective"], ["emotions"]),
    # HSK 1 numbers, time, measure
    ("一", "一", "yī", "one", 1, ["number"], ["numbers"]),
    ("二", "二", "èr", "two", 1, ["number"], ["numbers"]),
    ("三", "三", "sān", "three", 1, ["number"], ["numbers"]),
    ("四", "四", "sì", "four", 1, ["number"], ["numbers"]),
    ("五", "五", "wǔ", "five", 1, ["number"], ["numbers"]),
    ("六", "六", "liù", "six", 1, ["number"], ["numbers"]),
    ("七", "七", "qī", "seven", 1, ["number"], ["numbers"]),
    ("八", "八", "bā", "eight", 1, ["number"], ["numbers"]),
    ("九", "九", "jiǔ", "nine", 1, ["number"], ["numbers"]),
    ("十", "十", "shí", "ten", 1, ["number"], ["numbers"]),
    ("個", "个", "gè", "general measure word", 1, ["measure"], ["language"]),
    ("本", "本", "běn", "measure word for books", 1, ["measure"], ["school"]),
    ("歲", "岁", "suì", "years old", 1, ["measure"], ["time"]),
    ("點", "点", "diǎn", "o'clock; a bit", 1, ["measure", "noun"], ["time"]),
    ("分鐘", "分钟", "fēnzhōng", "minute", 1, ["measure", "noun"], ["time"]),
    ("塊", "块", "kuài", "yuan; piece", 1, ["measure"], ["shopping", "numbers"]),
    ("些", "些", "xiē", "some", 1, ["measure"], ["daily-life"]),
    ("今天", "今天", "jīntiān", "today", 1, ["noun"], ["time"]),
    ("明天", "明天", "míngtiān", "tomorrow", 1, ["noun"], ["time"]),
    ("昨天", "昨天", "zuótiān", "yesterday", 1, ["noun"], ["time"]),
    ("上午", "上午", "shàngwǔ", "morning", 1, ["noun"], ["time"]),
    ("中午", "中午", "zhōngwǔ", "noon", 1, ["noun"], ["time"]),
    ("下午", "下午", "xiàwǔ", "afternoon", 1, ["noun"], ["time"]),
    ("年", "年", "nián", "year", 1, ["noun"], ["time"]),
    ("月", "月", "yuè", "month; moon", 1, ["noun"], ["time"]),
    ("星期", "星期", "xīngqī", "week", 1, ["noun"], ["time"]),
    ("現在", "现在", "xiànzài", "now", 1, ["noun"], ["time"]),
    ("時候", "时候", "shíhou", "time; moment", 1, ["noun"], ["time"]),
    ("上", "上", "shàng", "up; to get on", 1, ["localizer", "verb"], ["daily-life"]),
    ("下", "下", "xià", "down; to get off", 1, ["localizer", "verb"], ["daily-life"]),
    ("裡", "里", "lǐ", "inside", 1, ["localizer"], ["house"]),
    ("後面", "后面", "hòumiàn", "behind", 1, ["localizer"], ["daily-life"]),
    # HSK 1 family, food, animals, places
    ("人", "人", "rén", "person", 1, ["noun"], ["daily-life"]),
    ("家", "家", "jiā", "family; home", 1, ["noun"], ["family", "house"]),
    ("爸爸", "爸爸", "bàba", "dad", 1, ["noun"], ["family"]),
    ("媽媽", "妈妈", "māma", "mom", 1, ["noun"], ["family"]),
    ("兒子", "儿子", "érzi", "son", 1, ["noun"], ["family"]),
    ("女兒", "女儿", "nǚ'ér", "daughter", 1, ["noun"], ["family"]),
    ("朋友", "朋友", "péngyou", "friend", 1, ["noun"], ["daily-life"]),
    ("老師", "老师", "lǎoshī", "teacher", 1, ["noun"], ["school"]),
    ("學生", "学生", "xuésheng", "student", 1, ["noun"], ["school"]),
    ("同學", "同学", "tóngxué", "classmate", 1, ["noun"], ["school"]),
    ("先生", "先生", "xiānsheng", "Mr.; sir", 1, ["noun"], ["daily-life"]),
    ("小姐", "小姐", "xiǎojiě", "Miss", 1, ["noun"], ["daily-life"]),
    ("醫生", "医生", "yīshēng", "doctor", 1, ["noun"], ["health"]),
    ("名字", "名字", "míngzi", "name", 1, ["noun"], ["daily-life"]),
    ("水", "水", "shuǐ", "water", 1, ["noun"], ["drinks", "nature"]),
    ("茶", "茶", "chá", "tea", 1, ["noun"], ["drinks", "food"]),
    ("米飯", "米饭", "mǐfàn", "cooked rice", 1, ["noun"], ["food"]),
    ("菜", "菜", "cài", "dish; vegetable", 1, ["noun"], ["food", "vegetables"]),
    ("蘋果", "苹果", "píngguǒ", "apple", 1, ["noun"], ["fruits", "food"]),
    ("杯子", "杯子", "bēizi", "cup", 1, ["noun"], ["house", "drinks"]),
    ("衣服", "衣服", "yīfu", "clothes", 1, ["noun"], ["clothes"]),
    ("貓", "猫", "māo", "cat", 1, ["noun"], ["animals", "daily-life"]),
    ("狗", "狗", "gǒu", "dog", 1, ["noun"], ["animals", "daily-life"]),
    ("書", "书", "shū", "book", 1, ["noun"], ["school", "culture"]),
    ("字", "字", "zì", "character; word", 1, ["noun"], ["language"]),
    ("漢語", "汉语", "Hànyǔ", "Chinese language", 1, ["noun"], ["language"]),
    ("學校", "学校", "xuéxiào", "school", 1, ["noun"], ["school"]),
    ("醫院", "医院", "yīyuàn", "hospital", 1, ["noun"], ["health"]),
    ("商店", "商店", "shāngdiàn", "shop", 1, ["noun"], ["shopping", "business"]),
    ("飯店", "饭店", "fàndiàn", "restaurant; hotel", 1, ["noun"], ["food", "travel"]),
    ("中國", "中国", "Zhōngguó", "China", 1, ["noun"], ["culture"]),
    ("北京", "北京", "Běijīng", "Beijing", 1, ["noun"], ["travel"]),
    ("天氣", "天气", "tiānqì", "weather", 1, ["noun"], ["weather"]),
    ("電影", "电影", "diànyǐng", "film", 1, ["noun"], ["culture"]),
    ("電視", "电视", "diànshì", "television", 1, ["noun"], ["daily-life", "culture"]),
    ("電腦", "电脑", "diànnǎo", "computer", 1, ["noun"], ["daily-life", "work"]),
    ("東西", "东西", "dōngxi", "thing", 1, ["noun"], ["daily-life"]),
    ("錢", "钱", "qián", "money", 1, ["noun"], ["shopping", "business"]),
    ("椅子", "椅子", "yǐzi", "chair", 1, ["noun"], ["house"]),
    ("桌子", "桌子", "zhuōzi", "table", 1, ["noun"], ["house"]),
    ("飛機", "飞机", "fēijī", "airplane", 1, ["noun"], ["transport", "travel"]),
    ("出租車", "出租车", "chūzūchē", "taxi", 1, ["noun"], ["transport"]),
    ("工作", "工作", "gōngzuò", "job; to work", 1, ["noun", "verb"], ["work", "business"]),
    ("怎麼", "怎么", "zěnme", "how", 1, ["pronoun"], ["daily-life"]),
    ("怎麼樣", "怎么样", "zěnmeyàng", "how is it", 1, ["pronoun"], ["daily-life"]),
    ("喂", "喂", "wèi", "hello (on the phone)", 1, ["interjection"], ["daily-life"]),
    ("對不起", "对不起", "duìbuqǐ", "sorry", 1, ["verb"], ["daily-life"]),
    ("不客氣", "不客气", "bú kèqi", "you're welcome", 1, ["adjective"], ["daily-life"]),
    ("沒關係", "没关系", "méi guānxi", "it doesn't matter", 1, ["verb"], ["daily-life"]),
    # --- HSK 2 ---
    ("您", "您", "nín", "you (polite)", 2, ["pronoun"], ["daily-life"]),
    ("它", "它", "tā", "it", 2, ["pronoun"], ["daily-life"]),
    ("大家", "大家", "dàjiā", "everybody", 2, ["pronoun"], ["daily-life"]),
    ("也", "也", "yě", "also", 2, ["adverb"], ["daily-life"]),
    ("還", "还", "hái", "still; also", 2, ["adverb"], ["daily-life"]),
    ("最", "最", "zuì", "most", 2, ["adverb"], ["daily-life"]),
    ("非常", "非常", "fēicháng", "extremely", 2, ["adverb"], ["daily-life"]),
    ("已經", "已经", "yǐjīng", "already", 2, ["adverb"], ["time"]),
    ("一起", "一起", "yìqǐ", "together", 2, ["adverb"], ["daily-life"]),
    ("從", "从", "cóng", "from", 2, ["preposition"], ["daily-life"]),
    ("對", "对", "duì", "toward; correct", 2, ["preposition", "adjective"], ["daily-life"]),
    ("比", "比", "bǐ", "compared with", 2, ["preposition"], ["daily-life"]),
    ("給", "给", "gěi", "to give; for", 2, ["verb", "preposition"], ["daily-life"]),
    ("讓", "让", "ràng", "to let; to allow", 2, ["verb"], ["daily-life"]),
    ("因為", "因为", "yīnwèi", "because", 2, ["conjunction"], ["language"]),
    ("所以", "所以", "suǒyǐ", "so; therefore", 2, ["conjunction"], ["language"]),
    ("雖然", "虽然", "suīrán", "although", 2, ["conjunction"], ["language"]),
    ("但是", "但是", "dànshì", "but", 2, ["conjunction"], ["language"]),
    ("別", "别", "bié", "don't", 2, ["adverb"], ["daily-life"]),
    ("可能", "可能", "kěnéng", "possible; maybe", 2, ["adverb", "adjective"], ["daily-life"]),
    ("可以", "可以", "kěyǐ", "may; can", 2, ["verb"], ["daily-life"]),
    ("要", "要", "yào", "to want; must", 2, ["verb"], ["daily-life"]),
    ("覺得", "觉得", "juéde", "to feel; to think", 2, ["verb"], ["emotions"]),
    ("知道", "知道", "zhīdào", "to know", 2, ["verb"], ["daily-life"]),
    ("希望", "希望", "xīwàng", "to hope; hope", 2, ["verb", "noun"], ["emotions"]),
    ("開始", "开始", "kāishǐ", "to start; start", 2, ["verb", "noun"], ["time"]),
    ("準備", "准备", "zhǔnbèi", "to prepare; preparation", 2, ["verb", "noun"], ["daily-life"]),
    ("介紹", "介绍", "jièshào", "to introduce", 2, ["verb"], ["daily-life"]),
    ("問", "问", "wèn", "to ask", 2, ["verb"], ["language"]),
    ("回答", "回答", "huídá", "to answer; answer", 2, ["verb", "noun"], ["language"]),
    ("賣", "卖", "mài", "to sell", 2, ["verb"], ["shopping", "business"]),
    ("穿", "穿", "chuān", "to wear", 2, ["verb"], ["clothes"]),
    ("洗", "洗", "xǐ", "to wash", 2, ["verb"], ["daily-life"]),
    ("送", "送", "sòng", "to give; to see off", 2, ["verb"], ["daily-life"]),
    ("找", "找", "zhǎo", "to look for", 2, ["verb"], ["daily-life"]),
    ("走", "走", "zǒu", "to walk; to leave", 2, ["verb"], ["transport", "daily-life"]),
    ("跑步", "跑步", "pǎobù", "to run", 2, ["verb"], ["body", "daily-life"]),
    ("游泳", "游泳", "yóuyǒng", "to swim", 2, ["verb"], ["daily-life"]),
    ("唱歌", "唱歌", "chànggē", "to sing", 2, ["verb"], ["culture"]),
    ("跳舞", "跳舞", "tiàowǔ", "to dance", 2, ["verb"], ["culture"]),
    ("休息", "休息", "xiūxi", "to rest; rest", 2, ["verb", "noun"], ["daily-life", "health"]),
    ("生病", "生病", "shēngbìng", "to fall ill", 2, ["verb"], ["health"]),
    ("起床", "起床", "qǐchuáng", "to get up", 2, ["verb"], ["daily-life"]),
    ("上班", "上班", "shàngbān", "to go to work", 2, ["verb"], ["work"]),
    ("幫助", "帮助", "bāngzhù", "to help; help", 2, ["verb", "noun"], ["daily-life"]),
    ("哥哥", "哥哥", "gēge", "older brother", 2, ["noun"], ["family"]),
    ("弟弟", "弟弟", "dìdi", "younger brother", 2, ["noun"], ["family"]),
    ("姐姐", "姐姐", "jiějie", "older sister", 2, ["noun"], ["family"]),
    ("妹妹", "妹妹", "mèimei", "younger sister", 2, ["noun"], ["family"]),
    ("孩子", "孩子", "háizi", "child", 2, ["noun"], ["family"]),
    ("丈夫", "丈夫", "zhàngfu", "husband", 2, ["noun"], ["family"]),
    ("妻子", "妻子", "qīzi", "wife", 2, ["noun"], ["family"]),
    ("男", "男", "nán", "male", 2, ["adjective"], ["body"]),
    ("女", "女", "nǚ", "female", 2, ["adjective"], ["body"]),
    ("身體", "身体", "shēntǐ", "body; health", 2, ["noun"], ["body", "health"]),
    ("眼睛", "眼睛", "yǎnjing", "eye", 2, ["noun"], ["body"]),
    ("藥", "药", "yào", "medicine", 2, ["noun"], ["health"]),
    ("公司", "公司", "gōngsī", "company", 2, ["noun"], ["business", "work"]),
    ("房間", "房间", "fángjiān", "room", 2, ["noun"], ["house"]),
    ("門", "门", "mén", "door", 2, ["noun"], ["house"]),
    ("手錶", "手表", "shǒubiǎo", "wristwatch", 2, ["noun"], ["clothes", "time"]),
    ("手機", "手机", "shǒujī", "mobile phone", 2, ["noun"], ["daily-life"]),
    ("時間", "时间", "shíjiān", "time", 2, ["noun"], ["time"]),
    ("小時", "小时", "xiǎoshí", "hour", 2, ["noun"], ["time"]),
    ("早上", "早上", "zǎoshang", "early morning", 2, ["noun"], ["time"]),
    ("晚上", "晚上", "wǎnshang", "evening", 2, ["noun"], ["time"]),
    ("生日", "生日", "shēngrì", "birthday", 2, ["noun"], ["time", "family"]),
    ("去年", "去年", "qùnián", "last year", 2, ["noun"], ["time"]),
    ("問題", "问题", "wèntí", "question; problem", 2, ["noun"], ["school", "language"]),
    ("意思", "意思", "yìsi", "meaning", 2, ["noun"], ["language"]),
    ("課", "课", "kè", "lesson; class", 2, ["noun"], ["school"]),
    ("教室", "教室", "jiàoshì", "classroom", 2, ["noun"], ["school"]),
    ("考試", "考试", "kǎoshì", "exam; to take an exam", 2, ["noun", "verb"], ["school"]),
    ("鉛筆", "铅笔", "qiānbǐ", "pencil", 2, ["noun"], ["school"]),
    ("報紙", "报纸", "bàozhǐ", "newspaper", 2, ["noun"], ["culture"]),
    ("顏色", "颜色", "yánsè", "color", 2, ["noun"], ["daily-life"]),
    ("紅", "红", "hóng", "red", 2, ["adjective"], ["daily-life"]),
    ("白", "白", "bái", "white", 2, ["adjective"], ["daily-life"]),
    ("黑", "黑", "hēi", "black", 2, ["adjective"], ["daily-life"]),
    ("新", "新", "xīn", "new", 2, ["adjective"], ["daily-life"]),
    ("高", "高", "gāo", "tall; high", 2, ["adjective"], ["body"]),
    ("長", "长", "cháng", "long", 2, ["adjective"], ["daily-life"]),
    ("忙", "忙", "máng", "busy", 2, ["adjective"], ["work"]),
    ("累", "累", "lèi", "tired", 2, ["adjective"], ["body", "health"]),
    ("快", "快", "kuài", "fast", 2, ["adjective"], ["daily-life"]),
    ("慢", "慢", "màn", "slow", 2, ["adjective"], ["daily-life"]),
    ("貴", "贵", "guì", "expensive", 2, ["adjective"], ["shopping"]),
    ("便宜", "便宜", "piányi", "inexpensive", 2, ["adjective"], ["shopping"]),
    ("好吃", "好吃", "hǎochī", "delicious", 2, ["adjective"], ["food"]),
    ("快樂", "快乐", "kuàilè", "happy", 2, ["adjective"], ["emotions"]),
    ("零", "零", "líng", "zero", 2, ["number"], ["numbers"]),
    ("百", "百", "bǎi", "hundred", 2, ["number"], ["numbers"]),
    ("千", "千", "qiān", "thousand", 2, ["number"], ["numbers"]),
    ("兩", "两", "liǎng", "two", 2, ["number"], ["numbers"]),
    ("次", "次", "cì", "time (occurrence)", 2, ["measure"], ["time"]),
    ("件", "件", "jiàn", "measure for clothes and matters", 2, ["measure"], ["clothes"]),
    ("西瓜", "西瓜", "xīguā", "watermelon", 2, ["noun"], ["fruits", "food"]),
    ("雞蛋", "鸡蛋", "jīdàn", "egg", 2, ["noun"], ["food"]),
    ("牛奶", "牛奶", "niúnǎi", "milk", 2, ["noun"], ["drinks", "food"]),
    ("咖啡", "咖啡", "kāfēi", "coffee", 2, ["noun"], ["drinks"]),
    ("麵條", "面条", "miàntiáo", "noodles", 2, ["noun"], ["food"]),
    ("魚", "鱼", "yú", "fish", 2, ["noun"], ["animals", "food"]),
    ("羊肉", "羊肉", "yángròu", "mutton", 2, ["noun"], ["meat", "food"]),
    ("雪", "雪", "xuě", "snow", 2, ["noun"], ["weather"]),
    ("晴", "晴", "qíng", "sunny", 2, ["adjective"], ["weather"]),
    ("陰", "阴", "yīn", "overcast", 2, ["adjective"], ["weather"]),
    ("機場", "机场", "jīchǎng", "airport", 2, ["noun"], ["transport", "travel"]),
    ("火車站", "火车站", "huǒchēzhàn", "train station", 2, ["noun"], ["transport", "travel"]),
    ("公共汽車", "公共汽车", "gōnggòng qìchē", "bus", 2, ["noun"], ["transport"]),
    ("旅遊", "旅游", "lǚyóu", "to travel; tourism", 2, ["verb", "noun"], ["travel"]),
    ("票", "票", "piào", "ticket", 2, ["noun"], ["travel", "shopping"]),
    ("路", "路", "lù", "road", 2, ["noun"], ["transport"]),
    ("遠", "远", "yuǎn", "far", 2, ["adjective"], ["travel"]),
    ("近", "近", "jìn", "near", 2, ["adjective"], ["daily-life"]),
    ("左邊", "左边", "zuǒbian", "left side", 2, ["localizer"], ["daily-life"]),
    ("右邊", "右边", "yòubian", "right side", 2, ["localizer"], ["daily-life"]),
    ("旁邊", "旁边", "pángbiān", "beside", 2, ["localizer"], ["daily-life"]),
    ("外", "外", "wài", "outside", 2, ["localizer"], ["daily-life"]),
    ("為什麼", "为什么", "wèishénme", "why", 2, ["pronoun"], ["language"]),
    # --- HSK 3 ---
    ("動物", "动物", "dòngwù", "animal", 3, ["noun"], ["animals"]),
    ("馬", "马", "mǎ", "horse", 3, ["noun"], ["animals"]),
    ("牛", "牛", "niú", "cow; ox", 3, ["noun"], ["animals"]),
    ("鳥", "鸟", "niǎo", "bird", 4, ["noun"], ["animals"]),
    ("花", "花", "huā", "flower", 3, ["noun"], ["plants"]),
    ("樹", "树", "shù", "tree", 4, ["noun"], ["plants", "nature"]),
    ("草", "草", "cǎo", "grass", 4, ["noun"], ["plants", "nature"]),
    ("山", "山", "shān", "mountain", 3, ["noun"], ["nature"]),
    ("河", "河", "hé", "river", 3, ["noun"], ["nature"]),
    ("海", "海", "hǎi", "sea", 3, ["noun"], ["nature"]),
    ("湖", "湖", "hú", "lake", 4, ["noun"], ["nature"]),
    ("風", "风", "fēng", "wind", 3, ["noun"], ["weather"]),
    ("雨", "雨", "yǔ", "rain", 3, ["noun"], ["weather"]),
    ("雲", "云", "yún", "cloud", 4, ["noun"], ["weather"]),
    ("春天", "春天", "chūntiān", "spring", 3, ["noun"], ["time", "weather"]),
    ("夏天", "夏天", "xiàtiān", "summer", 3, ["noun"], ["time", "weather"]),
    ("秋天", "秋天", "qiūtiān", "autumn", 4, ["noun"], ["time", "weather"]),
    ("冬天", "冬天", "dōngtiān", "winter", 3, ["noun"], ["time", "weather"]),
    ("季節", "季节", "jìjié", "season", 4, ["noun"], ["time", "weather"]),
    ("麵包", "面包", "miànbāo", "bread", 3, ["noun"], ["food"]),
    ("果汁", "果汁", "guǒzhī", "fruit juice", 4, ["noun"], ["drinks", "fruits"]),
    ("新鮮", "新鲜", "xīnxiān", "fresh", 3, ["adjective"], ["food"]),
    ("手", "手", "shǒu", "hand", 3, ["noun"], ["body"]),
    ("頭", "头", "tóu", "head", 3, ["noun"], ["body"]),
    ("腳", "脚", "jiǎo", "foot", 4, ["noun"], ["body"]),
    ("鞋", "鞋", "xié", "shoe", 3, ["noun"], ["clothes"]),
    ("帽子", "帽子", "màozi", "hat", 4, ["noun"], ["clothes"]),
    ("褲子", "裤子", "kùzi", "trousers", 4, ["noun"], ["clothes"]),
    ("床", "床", "chuáng", "bed", 3, ["noun"], ["house"]),
    ("窗", "窗", "chuāng", "window", 4, ["noun"], ["house"]),
    ("廚房", "厨房", "chúfáng", "kitchen", 4, ["noun"], ["house", "food"]),
    ("洗手間", "洗手间", "xǐshǒujiān", "restroom", 3, ["noun"], ["house"]),
    ("自行車", "自行车", "zìxíngchē", "bicycle", 3, ["noun"], ["transport"]),
    ("地鐵", "地铁", "dìtiě", "subway", 4, ["noun"], ["transport"]),
    ("船", "船", "chuán", "boat", 4, ["noun"], ["transport"]),
    ("地圖", "地图", "dìtú", "map", 4, ["noun"], ["travel"]),
    ("行李", "行李", "xíngli", "luggage", 4, ["noun"], ["travel"]),
    ("酒店", "酒店", "jiǔdiàn", "hotel", 4, ["noun"], ["travel"]),
    ("旅行", "旅行", "lǚxíng", "to travel; trip", 4, ["verb", "noun"], ["travel"]),
    ("音樂", "音乐", "yīnyuè", "music", 3, ["noun"], ["culture"]),
    ("中文", "中文", "Zhōngwén", "Chinese language", 3, ["noun"], ["language"]),
    ("句子", "句子", "jùzi", "sentence", 3, ["noun"], ["language"]),
    ("萬", "万", "wàn", "ten thousand", 3, ["number"], ["numbers"]),
    ("關心", "关心", "guānxīn", "to care about; concern", 4, ["verb", "noun"], ["emotions"]),
    ("生氣", "生气", "shēngqì", "to be angry", 4, ["verb", "adjective"], ["emotions"]),
    ("難過", "难过", "nánguò", "sad", 4, ["adjective"], ["emotions"]),
    ("害怕", "害怕", "hàipà", "to be afraid", 4, ["verb", "adjective"], ["emotions"]),
    # --- HSK 4–5 topics: food, business, health, culture ---
    ("水果", "水果", "shuǐguǒ", "fruit", 4, ["noun"], ["fruits", "food"]),
    ("蔬菜", "蔬菜", "shūcài", "vegetable", 4, ["noun"], ["vegetables", "food"]),
    ("白菜", "白菜", "báicài", "Chinese cabbage", 4, ["noun"], ["vegetables", "food"]),
    ("西紅柿", "西红柿", "xīhóngshì", "tomato", 4, ["noun"], ["vegetables", "food"]),
    ("香蕉", "香蕉", "xiāngjiāo", "banana", 4, ["noun"], ["fruits", "food"]),
    ("牛肉", "牛肉", "niúròu", "beef", 4, ["noun"], ["meat", "food"]),
    ("啤酒", "啤酒", "píjiǔ", "beer", 5, ["noun"], ["drinks"]),
    ("土豆", "土豆", "tǔdòu", "potato", 5, ["noun"], ["vegetables", "food"]),
    ("黃瓜", "黄瓜", "huángguā", "cucumber", 5, ["noun"], ["vegetables", "food"]),
    ("胡蘿蔔", "胡萝卜", "húluóbo", "carrot", 5, ["noun"], ["vegetables", "food"]),
    ("青菜", "青菜", "qīngcài", "green vegetable", None, ["noun"], ["vegetables", "food"]),
    ("葡萄", "葡萄", "pútao", "grape", 5, ["noun"], ["fruits", "food"]),
    ("草莓", "草莓", "cǎoméi", "strawberry", 5, ["noun"], ["fruits", "food"]),
    ("橘子", "橘子", "júzi", "tangerine", 5, ["noun"], ["fruits", "food"]),
    ("梨", "梨", "lí", "pear", 5, ["noun"], ["fruits", "food"]),
    ("餃子", "饺子", "jiǎozi", "dumpling", 5, ["noun"], ["food"]),
    ("雞肉", "鸡肉", "jīròu", "chicken meat", 5, ["noun"], ["meat", "food"]),
    ("豬肉", "猪肉", "zhūròu", "pork", 5, ["noun"], ["meat", "food"]),
    ("豬", "猪", "zhū", "pig", 4, ["noun"], ["animals"]),
    ("羊", "羊", "yáng", "sheep; goat", 4, ["noun"], ["animals"]),
    ("老虎", "老虎", "lǎohǔ", "tiger", 5, ["noun"], ["animals"]),
    ("熊貓", "熊猫", "xióngmāo", "panda", 5, ["noun"], ["animals"]),
    ("大象", "大象", "dàxiàng", "elephant", 5, ["noun"], ["animals"]),
    ("健康", "健康", "jiànkāng", "health; healthy", 4, ["noun", "adjective"], ["health"]),
    ("頭痛", "头痛", "tóutòng", "headache", 4, ["noun"], ["health", "body"]),
    ("襯衫", "衬衫", "chènshān", "shirt", 5, ["noun"], ["clothes"]),
    ("父母", "父母", "fùmǔ", "parents", 4, ["noun"], ["family"]),
    ("經理", "经理", "jīnglǐ", "manager", 4, ["noun"], ["business", "work"]),
    ("同事", "同事", "tóngshì", "colleague", 4, ["noun"], ["work"]),
    ("辦公室", "办公室", "bàngōngshì", "office", 4, ["noun"], ["work", "business"]),
    ("會議", "会议", "huìyì", "meeting", 4, ["noun"], ["business", "work"]),
    ("經驗", "经验", "jīngyàn", "experience", 4, ["noun"], ["work"]),
    ("專業", "专业", "zhuānyè", "major; specialty", 4, ["noun"], ["school", "work"]),
    ("市場", "市场", "shìchǎng", "market", 4, ["noun"], ["business", "shopping"]),
    ("價格", "价格", "jiàgé", "price", 4, ["noun"], ["shopping", "business"]),
    ("銀行", "银行", "yínháng", "bank", 4, ["noun"], ["business"]),
    ("老闆", "老板", "lǎobǎn", "boss", 5, ["noun"], ["work", "business"]),
    ("工資", "工资", "gōngzī", "wages", 5, ["noun"], ["work", "business"]),
    ("合同", "合同", "hétong", "contract", 5, ["noun"], ["business"]),
    ("客戶", "客户", "kèhù", "client", 5, ["noun"], ["business"]),
    ("質量", "质量", "zhìliàng", "quality", 5, ["noun"], ["business"]),
    ("談判", "谈判", "tánpàn", "to negotiate; negotiation", 5, ["verb", "noun"], ["business"]),
    ("投資", "投资", "tóuzī", "to invest; investment", 5, ["verb", "noun"], ["business"]),
    ("郵件", "邮件", "yóujiàn", "mail; email", 5, ["noun"], ["work", "business"]),
    ("護照", "护照", "hùzhào", "passport", 5, ["noun"], ["travel"]),
    ("簽證", "签证", "qiānzhèng", "visa", 5, ["noun"], ["travel"]),
    ("文化", "文化", "wénhuà", "culture", 4, ["noun"], ["culture"]),
    ("歷史", "历史", "lìshǐ", "history", 4, ["noun"], ["culture"]),
    ("畫", "画", "huà", "picture; to draw", 4, ["noun", "verb"], ["culture"]),
    ("漢字", "汉字", "Hànzì", "Chinese character", 4, ["noun"], ["language"]),
    ("語法", "语法", "yǔfǎ", "grammar", 4, ["noun"], ["language"]),
    ("資訊", "信息", "zīxùn", "information", 4, ["noun"], ["language", "business"]),
    ("網路", "网络", "wǎnglù", "network; the internet", 5, ["noun"], ["work", "daily-life"]),
    ("軟體", "软件", "ruǎntǐ", "software", 5, ["noun"], ["work"]),
    # Words already drawn in the character graph. HSK is null when the word
    # is not an HSK 2.0 headword.
    ("森林", "森林", "sēnlín", "forest", 4, ["noun"], ["plants", "nature"]),
    ("林木", "林木", "línmù", "forest trees; timber", None, ["noun"], ["plants"]),
    ("林海", "林海", "línhǎi", "a vast forest", None, ["noun"], ["plants", "nature"]),
    ("心情", "心情", "xīnqíng", "mood", 4, ["noun"], ["emotions"]),
    ("愛情", "爱情", "àiqíng", "romantic love", 4, ["noun"], ["emotions"]),
    ("情愛", "情爱", "qíng'ài", "affection", None, ["noun"], ["emotions"]),
    ("愛心", "爱心", "àixīn", "compassion", 4, ["noun"], ["emotions"]),
    ("心愛", "心爱", "xīn'ài", "beloved", None, ["adjective"], ["emotions"]),
    ("心想", "心想", "xīnxiǎng", "to think to oneself", None, ["verb"], ["emotions"]),
    ("小心", "小心", "xiǎoxīn", "be careful", 3, ["verb", "adjective"], ["daily-life"]),
    ("清心", "清心", "qīngxīn", "a pure mind", None, ["noun"], ["emotions"]),
    ("海水", "海水", "hǎishuǐ", "seawater", None, ["noun"], ["nature"]),
    ("河水", "河水", "héshuǐ", "river water", None, ["noun"], ["nature"]),
    ("江水", "江水", "jiāngshuǐ", "river water", None, ["noun"], ["nature"]),
    ("湖水", "湖水", "húshuǐ", "lake water", None, ["noun"], ["nature"]),
    ("清水", "清水", "qīngshuǐ", "clear water", None, ["noun"], ["nature"]),
    ("大水", "大水", "dàshuǐ", "flood", None, ["noun"], ["nature"]),
    ("大海", "大海", "dàhǎi", "the sea", 4, ["noun"], ["nature"]),
    ("大河", "大河", "dàhé", "a large river", None, ["noun"], ["nature"]),
    ("大江", "大江", "dàjiāng", "a great river", None, ["noun"], ["nature"]),
    ("小河", "小河", "xiǎohé", "a brook", None, ["noun"], ["nature"]),
    ("江湖", "江湖", "jiānghú", "rivers and lakes; the wider world", None, ["noun"], ["culture"]),
    ("江河", "江河", "jiānghé", "rivers", None, ["noun"], ["nature"]),
    ("大小", "大小", "dàxiǎo", "size", 3, ["noun"], ["daily-life"]),
    ("想見", "想见", "xiǎngjiàn", "to long to see", None, ["verb"], ["emotions"]),
    ("小看", "小看", "xiǎokàn", "to look down on", 5, ["verb"], ["emotions"]),
    ("請看", "请看", "qǐngkàn", "please look", None, ["verb"], ["daily-life"]),
    ("青青", "青青", "qīngqīng", "lush and green", None, ["adjective"], ["plants", "nature"]),
]


def apply_tone(syllable: str, tone: int) -> str:
    if tone < 1 or tone > 4:
        return syllable
    chars = list(syllable)
    text = "".join(chars)

    def mark(index: int) -> str:
        base = chars[index]
        chars[index] = TONE_MARKS[base][tone - 1]
        return "".join(chars)

    if "a" in text:
        return mark(text.index("a"))
    if "e" in text:
        return mark(text.index("e"))
    if "ou" in text:
        return mark(text.index("ou"))
    for index in range(len(chars) - 1, -1, -1):
        if chars[index] in TONE_MARKS:
            return mark(index)
    return syllable


def convert_syllable(token: str) -> str:
    token = token.strip()
    if not token:
        return token
    tone = 5
    if token[-1].isdigit():
        tone = int(token[-1])
        token = token[:-1]
    token = token.replace("u:", "ü").replace("v", "ü")
    return apply_tone(token, tone)


def convert_pinyin(raw: str) -> str:
    pieces = []
    for token in raw.split():
        if "'" in token:
            pieces.append("'".join(convert_syllable(part) for part in token.split("'")))
        else:
            pieces.append(convert_syllable(token))
    return " ".join(pieces)


def map_pos(codes: list[str]) -> list[str]:
    mapped: list[str] = []
    for code in codes:
        base = code.split("-")[0]
        if base == "vn":
            for item in ("verb", "noun"):
                if item not in mapped:
                    mapped.append(item)
            continue
        name = HSK_POS.get(base) or HSK_POS.get(base[:1])
        if name and name not in mapped and name in POS:
            mapped.append(name)
    return mapped or ["other"]


def clean_gloss(gloss: str) -> str:
    parts = [part.strip() for part in gloss.split("/") if part.strip()]
    text = "; ".join(parts[:4])
    if len(text) > 220:
        return text[:217] + "..."
    return text


def skip_cedict(gloss: str) -> bool:
    parts = [part.strip() for part in gloss.split("/") if part.strip()]
    if not parts:
        return True

    def boring(part: str) -> bool:
        lowered = part.lower()
        return (
            lowered.startswith("surname ")
            or lowered.startswith("variant of")
            or lowered.startswith("old variant")
            or lowered.startswith("see ")
            or lowered.startswith("also written")
        )

    return all(boring(part) for part in parts)


def cedict_pos(gloss: str) -> list[str]:
    first = gloss.split("/")[0].strip().lower()
    if first.startswith("to ") or first.startswith("(verb)"):
        return ["verb"]
    if first.startswith("(noun)") or first.startswith("a ") or first.startswith("the "):
        return ["noun"]
    return ["other"]


def load_hsk() -> dict[str, dict]:
    by_trad: dict[str, dict] = {}
    by_simp: dict[str, dict] = {}
    for level in range(1, 7):
        path = HSK_DIR / f"{level}.json"
        if not path.exists():
            raise SystemExit(f"missing {path}")
        for item in json.loads(path.read_text(encoding="utf-8")):
            forms = item.get("forms") or []
            if not forms:
                continue
            form = forms[0]
            trad = form.get("traditional") or ""
            simp = item.get("simplified") or ""
            pinyin = (form.get("transcriptions") or {}).get("pinyin") or ""
            meanings = form.get("meanings") or []
            if not trad or not simp or not pinyin or len(trad) != len(simp):
                continue
            if any(char.isascii() for char in trad):
                continue
            record = {
                "traditional": trad,
                "simplified": simp,
                "pinyin": pinyin,
                "en": clean_gloss("/".join(meanings)),
                "hsk": level,
                "pos": map_pos(item.get("pos") or []),
            }
            by_trad.setdefault(trad, record)
            by_simp.setdefault(simp, record)
    return {"trad": by_trad, "simp": by_simp}


def load_cedict(seen: set[str]) -> list[dict]:
    if not CEDICT_GZ.exists():
        raise SystemExit(f"missing {CEDICT_GZ}")
    added = []
    pattern = re.compile(r"(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)/$")
    with gzip.open(CEDICT_GZ, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line or line.startswith("#"):
                continue
            match = pattern.match(line.strip())
            if not match:
                continue
            trad, simp, pinyin, gloss = match.groups()
            if trad in seen or not 2 <= len(trad) <= 4 or len(trad) != len(simp):
                continue
            if any(char.isascii() for char in trad):
                continue
            if skip_cedict(gloss):
                continue
            seen.add(trad)
            added.append({
                "traditional": trad,
                "simplified": simp,
                "pinyin": convert_pinyin(pinyin),
                "en": clean_gloss(gloss),
                "zh": trad,
                "hsk": None,
                "pos": cedict_pos(gloss),
                "labels": infer_labels(clean_gloss(gloss)),
                "glyphs": list(trad),
                "in_graph": [glyph in GRAPH_GLYPHS for glyph in trad],
            })
    return added


FOOD_CHILDREN = {"vegetables", "fruits", "meat", "drinks"}


def infer_labels(english: str) -> list[str]:
    text = english.lower()
    found: list[str] = []
    for label, pattern in LABEL_RULES:
        if pattern.search(text):
            found.append(label)
    if any(label in FOOD_CHILDREN for label in found) and "food" not in found:
        found.append("food")
    return found or ["general"]


def word_record(trad: str, simp: str, pinyin: str, en: str, hsk, pos: list[str], labels: list[str]) -> dict:
    return {
        "traditional": trad,
        "simplified": simp,
        "pinyin": pinyin,
        "en": en,
        "zh": trad,
        "hsk": hsk,
        "pos": pos,
        "labels": labels,
        "glyphs": list(trad),
        "in_graph": [glyph in GRAPH_GLYPHS for glyph in trad],
    }


def main() -> None:
    assert convert_pinyin("ni3 hao3") == "nǐ hǎo"
    assert convert_pinyin("nu:3 er2") == "nǚ ér"
    assert convert_pinyin("ping2 guo3") == "píng guǒ"
    assert convert_pinyin("liu2") == "liú"
    assert convert_pinyin("lv4") == "lǜ"

    label_ids = {row[0] for row in LABELS}
    for _label_id, _group, _en, _zh, parent in LABELS:
        if parent is not None and parent not in label_ids:
            raise SystemExit(f"missing parent {parent}")

    hsk = load_hsk()
    words = []
    seen: set[str] = set()
    for trad, simp, pinyin, en, level, pos, labels in WORDS:
        if trad in seen:
            raise SystemExit(f"duplicate curated word {trad}")
        if any(item not in POS for item in pos) or any(item not in label_ids for item in labels):
            raise SystemExit(f"bad curated row {trad}")
        listed = hsk["trad"].get(trad) or hsk["simp"].get(simp)
        if level is None and listed is not None:
            level = listed["hsk"]
        seen.add(trad)
        words.append(word_record(trad, simp, pinyin, en, level, pos, labels))

    for record in hsk["trad"].values():
        if record["traditional"] in seen:
            continue
        seen.add(record["traditional"])
        words.append(word_record(
            record["traditional"],
            record["simplified"],
            record["pinyin"],
            record["en"],
            record["hsk"],
            record["pos"],
            infer_labels(record["en"]),
        ))

    words.extend(load_cedict(seen))
    if len(words) < 10000:
        raise SystemExit(f"only {len(words)} words; expected at least 10000")
    missing = [word["traditional"] for word in words if not word["labels"]]
    if missing:
        raise SystemExit(f"{len(missing)} words have no labels, for example {missing[:5]}")
    # Old HSK 2.0 levels 1–6 are the study core, a little over 5,000 headwords.
    for word in words:
        if word["hsk"] is not None and "top-list" not in word["labels"]:
            word["labels"].append("top-list")
    top_count = sum(1 for word in words if "top-list" in word["labels"])
    if top_count < 5000:
        raise SystemExit(f"top list has only {top_count} words")

    words.sort(key=lambda word: (word["hsk"] is None, word["hsk"] or 0, word["traditional"]))
    payload = {
        "source": (
            "CC-CEDICT headwords of 2–4 characters, plus every old HSK 2.0 word. "
            "CC-CEDICT is © the CC-CEDICT project, used under CC BY-SA 4.0. "
            "Top list is the old HSK 1–6 headwords, a little over 5,000 words. "
            "Every word has at least one category label. "
            "Curated words keep their hand-checked labels. "
            "The other labels are read from the English gloss, and General is used when no category matches. "
            "HSK level is the old HSK 2.0 level when the headword is on that list."
        ),
        "license": "CC-CEDICT: Creative Commons Attribution-ShareAlike 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "hsk_target": 5000,
        "labels": [
            {"id": item[0], "group": item[1], "en": item[2], "zh": item[3], "parent": item[4]}
            for item in LABELS
        ],
        "words": words,
    }
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    (ROOT / "lexicon.json").write_text(text, encoding="utf-8")
    WEB_JSON.write_text(text, encoding="utf-8")
    (ROOT / "lexicon.sql").write_text(render_sql(words), encoding="utf-8")
    by_hsk: dict[str, int] = {}
    for word in words:
        key = str(word["hsk"]) if word["hsk"] else "none"
        by_hsk[key] = by_hsk.get(key, 0) + 1
    print(f"words {len(words)} labels {len(LABELS)} hsk {by_hsk}")


def q(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def chunked_insert(statement: str, rows: list[str], suffix: str = "") -> list[str]:
    lines = []
    for start in range(0, len(rows), 500):
        block = rows[start:start + 500]
        lines.append(statement)
        lines.append(",\n".join(block))
        lines.append(suffix + ";")
        lines.append("")
    return lines


def render_sql(words: list[dict]) -> str:
    lines = [
        "-- Word lexicon. Run after schema.sql and seed.sql.",
        "-- Dictionary text from CC-CEDICT, CC BY-SA 4.0.",
        "-- https://creativecommons.org/licenses/by-sa/4.0/",
        "BEGIN;",
        "",
        "INSERT INTO labels (id, group_name, name_en, name_zh, parent_id) VALUES",
    ]
    label_rows = []
    for item in LABELS:
        parent = "NULL" if item[4] is None else q(item[4])
        label_rows.append(f"  ({q(item[0])}, {q(item[1])}, {q(item[2])}, {q(item[3])}, {parent})")
    lines.append(",\n".join(label_rows))
    lines.append("ON CONFLICT (id) DO UPDATE SET")
    lines.append("  group_name = EXCLUDED.group_name,")
    lines.append("  name_en = EXCLUDED.name_en,")
    lines.append("  name_zh = EXCLUDED.name_zh,")
    lines.append("  parent_id = EXCLUDED.parent_id;")
    lines.append("")
    node_rows = [
        f"  ({q('w:' + word['traditional'])}, 'word', {q(word['traditional'])})"
        for word in words
    ]
    lines.extend(chunked_insert(
        "INSERT INTO nodes (id, kind, label) VALUES",
        node_rows,
        "ON CONFLICT (id) DO NOTHING",
    ))
    value_rows = []
    glyph_rows = []
    pos_rows = []
    label_link_rows = []
    character_rows = []
    for word in words:
        word_id = "w:" + word["traditional"]
        hsk = "NULL" if word["hsk"] is None else str(word["hsk"])
        value_rows.append(
            "  ("
            + ", ".join([
                q(word_id),
                q(word["traditional"]),
                q(word["simplified"]),
                q(word["pinyin"]),
                q(word["en"]),
                q(word["zh"]),
                q(word["pos"][0]),
                hsk,
            ])
            + ")"
        )
        for index, glyph in enumerate(word["glyphs"], start=1):
            glyph_rows.append(f"  ({q(word_id)}, {index}, {q(glyph)})")
            if glyph in GRAPH_GLYPHS:
                character_rows.append(f"  ({q(word_id)}, {q('c:' + glyph)}, {index})")
        for index, pos in enumerate(word["pos"]):
            primary = "true" if index == 0 else "false"
            pos_rows.append(f"  ({q(word_id)}, {q(pos)}, {primary})")
        for label in word["labels"]:
            label_link_rows.append(f"  ({q(word_id)}, {q(label)})")
    lines.extend(chunked_insert(
        "INSERT INTO words (node_id, traditional, simplified, pinyin, gloss_en, gloss_zh, part_of_speech, hsk_level) VALUES",
        value_rows,
        "ON CONFLICT (traditional) DO UPDATE SET simplified = EXCLUDED.simplified, pinyin = EXCLUDED.pinyin, gloss_en = EXCLUDED.gloss_en, gloss_zh = EXCLUDED.gloss_zh, part_of_speech = EXCLUDED.part_of_speech, hsk_level = EXCLUDED.hsk_level",
    ))
    lines.append("DELETE FROM word_labels;")
    lines.append("DELETE FROM word_pos;")
    lines.append("DELETE FROM word_glyphs;")
    lines.append("")
    lines.extend(chunked_insert("INSERT INTO word_glyphs (word_id, position, glyph) VALUES", glyph_rows))
    lines.extend(chunked_insert("INSERT INTO word_pos (word_id, part_of_speech, is_primary) VALUES", pos_rows))
    if label_link_rows:
        lines.extend(chunked_insert("INSERT INTO word_labels (word_id, label_id) VALUES", label_link_rows))
    if character_rows:
        lines.extend(chunked_insert(
            "INSERT INTO word_characters (word_id, character_id, position) VALUES",
            character_rows,
            "ON CONFLICT (word_id, position) DO NOTHING",
        ))
    lines.append("COMMIT;")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
