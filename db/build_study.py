#!/usr/bin/env python3
"""Index old HSK 1–5 and draft sentences for the first 1,000 words.

Every sentence token is a word from that 1,000, and every token carries the
word's index key so a later pass can link the sentence back to the entry.
Variant glyphs (咊, 从, 几) are indexed and pointed at the study form, and
they are not used inside sentences.
"""

from __future__ import annotations

import json
from pathlib import Path

from character_parts import analyze

ROOT = Path(__file__).resolve().parent
WEB = ROOT.parent / "web" / "src" / "data"
SHOWN = 1000

# Old or non-study forms. Value is the study-form traditional, or None when
# that form is not on the HSK 1–5 list yet.
VARIANTS: dict[str, str | None] = {
    "傢": "家",
    "听": "聽",
    "咊": "和",
    "嵗": "歲",
    "裏": "裡",
    "㝡": "最",
    "从": "從",
    "几": "幾",
    "咲": "笑",
    "离": "離",
    "舩": "船",
    "葯": "藥",
    "㧱": "拿",
    "㼝": "碗",
    "万": "萬",
    "旾": "春",
    "艸": "草",
    "袴子": "褲子",
    "㕁": "卻",
    "㕥": "以",
    "㴱": "深",
    "㽞": "留",
    "䠀": "趟",
    "乹": "乾",
    "墻": "牆",
    "嬾": "懶",
    "徧": "遍",
    "晻": "暗",
    "云": "雲",
}

# Learner sense when the dictionary's first line is a surname or a rare reading.
FIX: dict[str, dict[str, str]] = {
    "日": {"pinyin": "rì", "en": "day; sun"},
    "元": {"pinyin": "yuán", "en": "yuan"},
    "向": {"pinyin": "xiàng", "en": "towards"},
    "吧": {"pinyin": "ba", "en": "suggestion particle"},
    "告訴": {"pinyin": "gàosu", "en": "to tell"},
    "張": {"pinyin": "zhāng", "en": "measure for flat things"},
    "號": {"pinyin": "hào", "en": "number; day of the month"},
    "錯": {"pinyin": "cuò", "en": "wrong"},
    "題": {"pinyin": "tí", "en": "question; topic"},
    "著": {"pinyin": "zhe", "en": "aspect particle"},
    "為": {"pinyin": "wèi", "en": "for"},
    "得": {"pinyin": "de", "en": "structural particle"},
    "長": {"pinyin": "cháng", "en": "long"},
    "胖": {"en": "fat"},
    "故事": {"en": "story"},
    "帶": {"pinyin": "dài", "en": "to bring"},
    "更": {"pinyin": "gèng", "en": "even more"},
    "只": {"pinyin": "zhǐ", "en": "only"},
    "還": {"pinyin": "hái", "en": "still; also"},
    "差": {"pinyin": "chà", "en": "not good enough"},
    "教": {"pinyin": "jiāo", "en": "to teach"},
    "東": {"pinyin": "dōng", "en": "east"},
    "南": {"pinyin": "nán", "en": "south"},
    "西": {"pinyin": "xī", "en": "west"},
    "北": {"pinyin": "běi", "en": "north"},
    "藍": {"pinyin": "lán", "en": "blue"},
    "黃": {"pinyin": "huáng", "en": "yellow"},
    "樓": {"pinyin": "lóu", "en": "building; floor"},
    "班": {"pinyin": "bān", "en": "class"},
    "祝": {"pinyin": "zhù", "en": "to wish"},
    "秋": {"pinyin": "qiū", "en": "autumn"},
    "夏": {"pinyin": "xià", "en": "summer"},
    "米": {"pinyin": "mǐ", "en": "uncooked rice"},
    "角": {"pinyin": "jiǎo", "en": "corner; 10 cents"},
    "關": {"pinyin": "guān", "en": "to close"},
    "雙": {"pinyin": "shuāng", "en": "pair"},
    "段": {"pinyin": "duàn", "en": "section"},
    "包": {"pinyin": "bāo", "en": "bag"},
    "老": {"en": "old"},
    "假": {"pinyin": "jiǎ", "en": "fake; vacation"},
    "台": {"pinyin": "tái", "en": "measure for machines"},
    "刀": {"en": "knife"},
    "火": {"en": "fire"},
    "湯": {"pinyin": "tāng", "en": "soup"},
    "富": {"en": "rich"},
    "寬": {"pinyin": "kuān", "en": "wide"},
    "帥": {"pinyin": "shuài", "en": "handsome"},
    "修": {"pinyin": "xiū", "en": "to repair"},
    "戴": {"pinyin": "dài", "en": "to wear (accessories)"},
    "咸": {"pinyin": "xián", "en": "salty"},
    "騎": {"pinyin": "qí", "en": "to ride"},
    "地": {"pinyin": "de", "en": "adverbial particle"},
    "位": {"pinyin": "wèi", "en": "measure for people"},
    "口": {"en": "mouth; measure for family members"},
    "種": {"pinyin": "zhǒng", "en": "kind; type"},
    "分": {"en": "minute; point; to divide"},
    "刻": {"en": "quarter of an hour"},
    "半": {"en": "half"},
    "包": {"pinyin": "bāo", "en": "bag"},
}

# focus, english, tokens. Every token has to be in the first 1,000 study forms.
HAND: list[tuple[str, str, list[str]]] = [
    ("一", "I have one friend.", ["我", "有", "一", "個", "朋友"]),
    ("二", "It is February.", ["現在", "是", "二", "月"]),
    ("三", "I have three friends.", ["我", "有", "三", "個", "朋友"]),
    ("四", "I have four books.", ["我", "有", "四", "本", "書"]),
    ("五", "I have five books.", ["我", "有", "五", "本", "書"]),
    ("六", "I have six apples.", ["我", "有", "六", "個", "蘋果"]),
    ("七", "I am seven.", ["我", "七", "歲"]),
    ("八", "I am eight.", ["我", "八", "歲"]),
    ("九", "She is nine.", ["她", "九", "歲"]),
    ("十", "I am ten.", ["我", "十", "歲"]),
    ("兩", "I have two friends.", ["我", "有", "兩", "個", "朋友"]),
    ("百", "This is one hundred.", ["這", "是", "一", "百"]),
    ("千", "This is one thousand.", ["這", "是", "一", "千"]),
    ("萬", "This is ten thousand.", ["這", "是", "一", "萬"]),
    ("零", "It is zero o'clock.", ["現在", "是", "零", "點"]),
    ("半", "Now it is three thirty.", ["現在", "是", "三", "點", "半"]),
    ("上", "The book is on the table.", ["書", "在", "桌子", "上"]),
    ("下", "The book is under the table.", ["書", "在", "桌子", "下"]),
    ("前面", "The school is in front.", ["學校", "在", "前面"]),
    ("後面", "The school is behind.", ["學校", "在", "後面"]),
    ("左邊", "The school is on the left.", ["學校", "在", "左邊"]),
    ("右邊", "The school is on the right.", ["學校", "在", "右邊"]),
    ("裡", "I am at home.", ["我", "在", "家", "裡"]),
    ("外", "He is outside.", ["他", "在", "外"]),
    ("中間", "I am in the middle.", ["我", "在", "中間"]),
    ("旁邊", "He is beside me.", ["他", "在", "我", "旁邊"]),
    ("上午", "I study in the morning.", ["我", "上午", "學習"]),
    ("中午", "I eat rice at noon.", ["我", "中午", "吃", "米飯"]),
    ("下午", "I go to school in the afternoon.", ["我", "下午", "去", "學校"]),
    ("早上", "I get up in the morning.", ["我", "早上", "起床"]),
    ("晚上", "I sleep in the evening.", ["我", "晚上", "睡覺"]),
    ("今天", "I am at home today.", ["今天", "我", "在", "家"]),
    ("明天", "I go to school tomorrow.", ["明天", "我", "去", "學校"]),
    ("昨天", "I was at home yesterday.", ["昨天", "我", "在", "家"]),
    ("現在", "I am at home now.", ["我", "現在", "在", "家"]),
    ("年", "This year I am at school.", ["這", "一", "年", "我", "在", "學校"]),
    ("月", "A year has twelve months.", ["一", "年", "有", "十", "二", "個", "月"]),
    ("日", "Today is Sunday.", ["今天", "是", "星期", "日"]),
    ("星期", "What day is it today?", ["今天", "星期", "幾"]),
    ("點", "It is three o'clock.", ["現在", "是", "三", "點"]),
    ("分鐘", "I have ten minutes.", ["我", "有", "十", "分鐘"]),
    ("小時", "I study for one hour.", ["我", "學習", "一", "個", "小時"]),
    ("時候", "What time is it now?", ["現在", "是", "什麼", "時候"]),
    ("時間", "I have no time.", ["我", "沒有", "時間"]),
    ("去年", "I was at school last year.", ["去年", "我", "在", "學校"]),
    ("下雨", "It is raining today.", ["今天", "下雨"]),
    ("天氣", "The weather is good today.", ["今天", "天氣", "很", "好"]),
    ("冷", "It is cold today.", ["今天", "很", "冷"]),
    ("熱", "It is hot today.", ["今天", "很", "熱"]),
    ("晴", "It is sunny today.", ["今天", "很", "晴"]),
    ("雪", "It is snowing today.", ["今天", "下", "雪"]),
    ("不", "I am not a teacher.", ["我", "不", "是", "老師"]),
    ("沒", "I did not go.", ["我", "沒", "去"]),
    ("沒有", "I do not have money.", ["我", "沒有", "錢"]),
    ("沒關係", "He says it does not matter.", ["他", "說", "沒關係"]),
    ("不客氣", "He says you are welcome.", ["他", "說", "不客氣"]),
    ("對不起", "I say I am sorry.", ["我", "說", "對不起"]),
    ("謝謝", "Thank you.", ["謝謝", "你"]),
    ("再見", "We say goodbye.", ["我們", "再見"]),
    ("請", "Please sit.", ["請", "坐"]),
    ("喂", "Hello, who is this?", ["喂", "你", "是", "誰"]),
    ("嗎", "How are you?", ["你", "好", "嗎"]),
    ("呢", "And you?", ["你", "呢"]),
    ("的", "This is my book.", ["這", "是", "我", "的", "書"]),
    ("了", "I have eaten.", ["我", "吃", "了"]),
    ("吧", "Let's go.", ["我們", "去", "吧"]),
    ("著", "I am reading a book.", ["我", "在", "看", "著", "書"]),
    ("得", "He speaks well.", ["他", "說", "得", "很", "好"]),
    ("地", "He studies hard.", ["他", "認真", "地", "學習"]),
    ("個", "I have one friend.", ["我", "有", "一", "個", "朋友"]),
    ("本", "I have one book.", ["我", "有", "一", "本", "書"]),
    ("些", "I have some friends.", ["我", "有", "些", "朋友"]),
    ("塊", "This apple is three kuai.", ["這", "個", "蘋果", "三", "塊"]),
    ("件", "This is one piece of clothing.", ["這", "是", "一", "件", "衣服"]),
    ("次", "I go once.", ["我", "去", "一", "次"]),
    ("張", "I have one ticket.", ["我", "有", "一", "張", "票"]),
    ("條", "This is one fish.", ["這", "是", "一", "條", "魚"]),
    ("位", "This is one teacher.", ["這", "是", "一", "位", "老師"]),
    ("雙", "I have one pair of shoes.", ["我", "有", "一", "雙", "鞋"]),
    ("號", "Today is the third.", ["今天", "是", "三", "號"]),
    ("元", "This apple is one yuan.", ["這", "個", "蘋果", "一", "元"]),
    ("歲", "How old are you?", ["你", "幾", "歲"]),
    ("我", "I am a student.", ["我", "是", "學生"]),
    ("你", "How are you?", ["你", "好", "嗎"]),
    ("他", "He is my friend.", ["他", "是", "我", "的", "朋友"]),
    ("她", "She is a teacher.", ["她", "是", "老師"]),
    ("我們", "We are friends.", ["我們", "是", "朋友"]),
    ("您", "How are you?", ["您", "好", "嗎"]),
    ("它", "It is a dog.", ["它", "是", "狗"]),
    ("大家", "Hello, everyone.", ["大家", "好"]),
    ("自己", "I go by myself.", ["我", "自己", "去"]),
    ("這", "This is a book.", ["這", "是", "書"]),
    ("那", "That is a cup.", ["那", "是", "杯子"]),
    ("什麼", "What is this?", ["這", "是", "什麼"]),
    ("誰", "Who are you?", ["你", "是", "誰"]),
    ("哪", "Which one do you want?", ["你", "要", "哪", "一", "個"]),
    ("哪兒", "Where are you going?", ["你", "去", "哪兒"]),
    ("怎麼", "How do you go?", ["你", "怎麼", "去"]),
    ("怎麼樣", "How are you today?", ["你", "今天", "怎麼樣"]),
    ("多少", "How much is this?", ["這", "個", "多少", "錢"]),
    ("幾", "How old are you?", ["你", "幾", "歲"]),
    ("為什麼", "Why do you go?", ["你", "為什麼", "去"]),
    ("每", "Every person is a friend.", ["每", "個", "人", "都", "是", "朋友"]),
    ("和", "I go to school with a friend.", ["我", "和", "朋友", "去", "學校"]),
    ("也", "I am a student too.", ["我", "也", "是", "學生"]),
    ("都", "We are all students.", ["我們", "都", "是", "學生"]),
    ("很", "I am very well.", ["我", "很", "好"]),
    ("太", "This is too big.", ["這", "太", "大", "了"]),
    ("最", "He is the best.", ["他", "最", "好"]),
    ("非常", "I am very happy.", ["我", "非常", "高興"]),
    ("真", "This is really good.", ["這", "真", "好"]),
    ("再", "Please come again.", ["請", "再", "來"]),
    ("別", "Don't go.", ["別", "去"]),
    ("已經", "I have already eaten.", ["我", "已經", "吃", "了"]),
    ("正在", "I am studying.", ["我", "正在", "學習"]),
    ("還", "I still have a book.", ["我", "還", "有", "書"]),
    ("就", "I will go then.", ["我", "就", "去"]),
    ("才", "He only then comes.", ["他", "才", "來"]),
    ("只", "I only have one book.", ["我", "只", "有", "一", "本", "書"]),
    ("更", "This is even bigger.", ["這", "個", "更", "大"]),
    ("一共", "We have three people in all.", ["我們", "一共", "有", "三", "個", "人"]),
    ("一定", "I will certainly go.", ["我", "一定", "去"]),
    ("其實", "I am actually a student.", ["我", "其實", "是", "學生"]),
    ("先", "I go first.", ["我", "先", "去"]),
    ("馬上", "I will go right away.", ["我", "馬上", "去"]),
    ("當然", "Of course I will go.", ["我", "當然", "去"]),
    ("總是", "He is always busy.", ["他", "總是", "很", "忙"]),
    ("經常", "I often study.", ["我", "經常", "學習"]),
    ("終於", "He has finally come.", ["他", "終於", "來", "了"]),
    ("可能", "He may come.", ["他", "可能", "來"]),
    ("還是", "Do you want tea or water?", ["你", "要", "茶", "還是", "水"]),
    ("因為", "I stay home because it is raining.", ["因為", "下雨", "我", "在", "家"]),
    ("所以", "It is raining, so I stay home.", ["下雨", "了", "所以", "我", "在", "家"]),
    ("但是", "I want to go, but I am busy.", ["我", "想", "去", "但是", "我", "很", "忙"]),
    ("雖然", "Although I am busy, I go.", ["雖然", "我", "很", "忙", "我", "還", "去"]),
    ("如果", "If you want to go, I go too.", ["如果", "你", "想", "去", "我", "也", "去"]),
    ("或者", "Today or tomorrow.", ["今天", "或者", "明天"]),
    ("而且", "I study and I also work.", ["我", "學習", "而且", "工作"]),
    ("是", "I am a student.", ["我", "是", "學生"]),
    ("有", "I have a book.", ["我", "有", "一", "本", "書"]),
    ("在", "I am at home.", ["我", "在", "家"]),
    ("會", "I can write characters.", ["我", "會", "寫", "字"]),
    ("能", "I can go.", ["我", "能", "去"]),
    ("可以", "I may go.", ["我", "可以", "去"]),
    ("要", "I want to go.", ["我", "要", "去"]),
    ("想", "I miss you.", ["我", "想", "你"]),
    ("喜歡", "I like you.", ["我", "喜歡", "你"]),
    ("愛", "I love you.", ["我", "愛", "你"]),
    ("希望", "I hope you come.", ["我", "希望", "你", "來"]),
    ("覺得", "I feel it is very hot.", ["我", "覺得", "很", "熱"]),
    ("知道", "I know him.", ["我", "知道", "他"]),
    ("認識", "I know you.", ["我", "認識", "你"]),
    ("懂", "I understand.", ["我", "懂", "了"]),
    ("了解", "I understand you.", ["我", "了解", "你"]),
    ("明白", "I understand.", ["我", "明白", "了"]),
    ("應該", "I should go.", ["我", "應該", "去"]),
    ("讓", "I let him go.", ["我", "讓", "他", "去"]),
    ("給", "I give you a book.", ["我", "給", "你", "一", "本", "書"]),
    ("對", "This is correct.", ["這", "是", "對", "的"]),
    ("錯", "This is wrong.", ["這", "是", "錯", "的"]),
    ("從", "I come from home.", ["我", "從", "家", "來"]),
    ("向", "I speak to him.", ["我", "向", "他", "說"]),
    ("比", "I am taller than him.", ["我", "比", "他", "高"]),
    ("為", "I work for him.", ["我", "為", "他", "工作"]),
    ("去", "I go to school.", ["我", "去", "學校"]),
    ("來", "Please come.", ["請", "你", "來"]),
    ("回", "I return home.", ["我", "回", "家"]),
    ("進", "I go into the school.", ["我", "進", "學校"]),
    ("出", "I go out.", ["我", "出", "去"]),
    ("到", "I arrive at school.", ["我", "到", "學校"]),
    ("走", "I am leaving.", ["我", "走", "了"]),
    ("坐", "Please sit.", ["請", "坐"]),
    ("住", "I live in Beijing.", ["我", "住", "在", "北京"]),
    ("開", "Please open the door.", ["請", "開", "門"]),
    ("關", "Please close the door.", ["請", "關", "門"]),
    ("看", "I read a book.", ["我", "看", "書"]),
    ("看見", "I see you.", ["我", "看見", "你"]),
    ("聽", "I listen to music.", ["我", "聽", "音樂"]),
    ("說", "I speak Chinese.", ["我", "說", "漢語"]),
    ("說話", "I want to talk.", ["我", "想", "說話"]),
    ("讀", "I read a book.", ["我", "讀", "書"]),
    ("寫", "I write characters.", ["我", "寫", "字"]),
    ("吃", "I want to eat an apple.", ["我", "想", "吃", "蘋果"]),
    ("喝", "I want to drink water.", ["我", "想", "喝", "水"]),
    ("做", "I am cooking.", ["我", "在", "做", "菜"]),
    ("買", "I buy a book.", ["我", "買", "書"]),
    ("賣", "He sells vegetables.", ["他", "賣", "菜"]),
    ("叫", "He calls me.", ["他", "叫", "我"]),
    ("問", "I ask you.", ["我", "問", "你"]),
    ("回答", "I answer you.", ["我", "回答", "你"]),
    ("告訴", "I tell you.", ["我", "告訴", "你"]),
    ("找", "I am looking for you.", ["我", "找", "你"]),
    ("給", "I give you a book.", ["我", "給", "你", "一", "本", "書"]),
    ("送", "I give you a book.", ["我", "送", "你", "一", "本", "書"]),
    ("幫助", "I help you.", ["我", "幫助", "你"]),
    ("介紹", "I introduce him.", ["我", "介紹", "他"]),
    ("學習", "I am studying.", ["我", "在", "學習"]),
    ("工作", "I am working.", ["我", "在", "工作"]),
    ("上班", "I go to work.", ["我", "去", "上班"]),
    ("休息", "I want to rest.", ["我", "想", "休息"]),
    ("睡覺", "I want to sleep.", ["我", "想", "睡覺"]),
    ("起床", "I get up.", ["我", "起床", "了"]),
    ("打電話", "I want to make a phone call.", ["我", "想", "打電話"]),
    ("唱歌", "I want to sing.", ["我", "想", "唱歌"]),
    ("跳舞", "I want to dance.", ["我", "想", "跳舞"]),
    ("游泳", "I want to swim.", ["我", "想", "游泳"]),
    ("跑步", "I want to run.", ["我", "想", "跑步"]),
    ("玩", "I want to play.", ["我", "想", "玩"]),
    ("洗", "I wash clothes.", ["我", "洗", "衣服"]),
    ("穿", "I wear clothes.", ["我", "穿", "衣服"]),
    ("準備", "I prepare.", ["我", "在", "準備"]),
    ("開始", "I start.", ["我", "開始", "了"]),
    ("完", "I have finished eating.", ["我", "吃", "完", "了"]),
    ("歡迎", "Welcome.", ["歡迎", "你"]),
    ("生病", "He is ill.", ["他", "生病", "了"]),
    ("考試", "I take an exam.", ["我", "考試"]),
    ("運動", "I want to exercise.", ["我", "想", "運動"]),
    ("旅遊", "I want to travel.", ["我", "想", "旅遊"]),
    ("踢", "I kick.", ["我", "踢"]),
    ("打籃球", "I play basketball.", ["我", "打籃球"]),
    ("大", "This one is very big.", ["這", "個", "很", "大"]),
    ("小", "This one is very small.", ["這", "個", "很", "小"]),
    ("多", "I have many books.", ["我", "有", "很", "多", "書"]),
    ("少", "I have little money.", ["我", "的", "錢", "很", "少"]),
    ("好", "I am very well.", ["我", "很", "好"]),
    ("忙", "I am very busy.", ["我", "很", "忙"]),
    ("快", "He is very fast.", ["他", "很", "快"]),
    ("慢", "He is very slow.", ["他", "很", "慢"]),
    ("新", "This book is new.", ["這", "本", "書", "很", "新"]),
    ("長", "This road is very long.", ["這", "條", "路", "很", "長"]),
    ("高", "He is very tall.", ["他", "很", "高"]),
    ("遠", "The school is far.", ["學校", "很", "遠"]),
    ("近", "The school is near.", ["學校", "很", "近"]),
    ("貴", "This is very expensive.", ["這", "個", "很", "貴"]),
    ("便宜", "This is inexpensive.", ["這", "個", "很", "便宜"]),
    ("漂亮", "She is pretty.", ["她", "很", "漂亮"]),
    ("高興", "I am happy.", ["我", "很", "高興"]),
    ("快樂", "I am happy.", ["我", "很", "快樂"]),
    ("累", "I am tired.", ["我", "很", "累"]),
    ("好吃", "The apple is delicious.", ["蘋果", "很", "好吃"]),
    ("男", "He is male.", ["他", "是", "男", "的"]),
    ("女", "She is female.", ["她", "是", "女", "的"]),
    ("白", "This is white.", ["這", "是", "白", "的"]),
    ("黑", "This is black.", ["這", "是", "黑", "的"]),
    ("紅", "This is red.", ["這", "是", "紅", "的"]),
    ("人", "He is a good person.", ["他", "是", "一", "個", "好", "人"]),
    ("朋友", "He is my friend.", ["他", "是", "我", "的", "朋友"]),
    ("同學", "He is my classmate.", ["他", "是", "我", "的", "同學"]),
    ("老師", "She is a teacher.", ["她", "是", "老師"]),
    ("學生", "I am a student.", ["我", "是", "學生"]),
    ("醫生", "He is a doctor.", ["他", "是", "醫生"]),
    ("先生", "Thank you, sir.", ["謝謝", "先生"]),
    ("小姐", "Thank you, miss.", ["謝謝", "小姐"]),
    ("媽媽", "I love Mom.", ["我", "愛", "媽媽"]),
    ("爸爸", "I love Dad.", ["我", "愛", "爸爸"]),
    ("兒子", "He is my son.", ["他", "是", "我", "的", "兒子"]),
    ("女兒", "She is my daughter.", ["她", "是", "我", "的", "女兒"]),
    ("丈夫", "He is my husband.", ["他", "是", "我", "的", "丈夫"]),
    ("妻子", "She is my wife.", ["她", "是", "我", "的", "妻子"]),
    ("哥哥", "He is my older brother.", ["他", "是", "我", "的", "哥哥"]),
    ("弟弟", "He is my younger brother.", ["他", "是", "我", "的", "弟弟"]),
    ("姐姐", "She is my older sister.", ["她", "是", "我", "的", "姐姐"]),
    ("妹妹", "She is my younger sister.", ["她", "是", "我", "的", "妹妹"]),
    ("孩子", "He is a child.", ["他", "是", "孩子"]),
    ("男人", "He is a man.", ["他", "是", "男人"]),
    ("女人", "She is a woman.", ["她", "是", "女人"]),
    ("家", "I am at home.", ["我", "在", "家"]),
    ("學校", "I go to school.", ["我", "去", "學校"]),
    ("教室", "I am in the classroom.", ["我", "在", "教室"]),
    ("醫院", "I go to the hospital.", ["我", "去", "醫院"]),
    ("商店", "I go to the shop.", ["我", "去", "商店"]),
    ("公司", "I go to the company.", ["我", "去", "公司"]),
    ("飯店", "I go to the restaurant.", ["我", "去", "飯店"]),
    ("飯館", "I go to the restaurant.", ["我", "去", "飯館"]),
    ("北京", "I go to Beijing.", ["我", "去", "北京"]),
    ("中國", "I am in China.", ["我", "在", "中國"]),
    ("房間", "I am in the room.", ["我", "在", "房間"]),
    ("門", "Please open the door.", ["請", "開", "門"]),
    ("路", "This road is very long.", ["這", "條", "路", "很", "長"]),
    ("機場", "I go to the airport.", ["我", "去", "機場"]),
    ("火車站", "I go to the train station.", ["我", "去", "火車站"]),
    ("杯子", "This is a cup.", ["這", "是", "杯子"]),
    ("桌子", "This is a table.", ["這", "是", "桌子"]),
    ("椅子", "I sit on the chair.", ["我", "坐", "在", "椅子", "上"]),
    ("書", "This is a book.", ["這", "是", "一", "本", "書"]),
    ("字", "I write characters.", ["我", "寫", "字"]),
    ("名字", "This is my name.", ["這", "是", "我", "的", "名字"]),
    ("東西", "This is my thing.", ["這", "是", "我", "的", "東西"]),
    ("水", "I want to drink water.", ["我", "想", "喝", "水"]),
    ("茶", "I want to drink tea.", ["我", "想", "喝", "茶"]),
    ("咖啡", "I want to drink coffee.", ["我", "想", "喝", "咖啡"]),
    ("牛奶", "I want to drink milk.", ["我", "想", "喝", "牛奶"]),
    ("菜", "I want to eat vegetables.", ["我", "想", "吃", "菜"]),
    ("米飯", "I want to eat rice.", ["我", "想", "吃", "米飯"]),
    ("蘋果", "I want to eat an apple.", ["我", "想", "吃", "蘋果"]),
    ("西瓜", "I want to eat watermelon.", ["我", "想", "吃", "西瓜"]),
    ("雞蛋", "I want to eat an egg.", ["我", "想", "吃", "雞蛋"]),
    ("魚", "I want to eat fish.", ["我", "想", "吃", "魚"]),
    ("羊肉", "I want to eat mutton.", ["我", "想", "吃", "羊肉"]),
    ("麵條", "I want to eat noodles.", ["我", "想", "吃", "麵條"]),
    ("衣服", "I buy clothes.", ["我", "買", "衣服"]),
    ("錢", "I have no money.", ["我", "沒有", "錢"]),
    ("票", "I buy a ticket.", ["我", "買", "票"]),
    ("電腦", "This is a computer.", ["這", "是", "電腦"]),
    ("電視", "I watch television.", ["我", "看", "電視"]),
    ("電影", "I watch a film.", ["我", "看", "電影"]),
    ("手機", "This is a mobile phone.", ["這", "是", "手機"]),
    ("手錶", "This is a watch.", ["這", "是", "手錶"]),
    ("飛機", "I take a plane.", ["我", "坐", "飛機"]),
    ("出租車", "I take a taxi.", ["我", "坐", "出租車"]),
    ("公共汽車", "I take the bus.", ["我", "坐", "公共汽車"]),
    ("狗", "I like dogs.", ["我", "喜歡", "狗"]),
    ("貓", "I like cats.", ["我", "喜歡", "貓"]),
    ("漢語", "I study Chinese.", ["我", "學習", "漢語"]),
    ("報紙", "I read the newspaper.", ["我", "看", "報紙"]),
    ("鉛筆", "This is a pencil.", ["這", "是", "鉛筆"]),
    ("藥", "I take medicine.", ["我", "吃", "藥"]),
    ("身體", "My health is good.", ["我", "的", "身體", "很", "好"]),
    ("眼睛", "This is an eye.", ["這", "是", "眼睛"]),
    ("問題", "This question is hard.", ["這", "個", "問題", "很", "難"]),
    ("意思", "What does this mean?", ["這", "是", "什麼", "意思"]),
    ("事情", "This matter is important.", ["這", "個", "事情", "很", "重要"]),
    ("顏色", "What color is this?", ["這", "是", "什麼", "顏色"]),
    ("生日", "Today is my birthday.", ["今天", "是", "我", "的", "生日"]),
    ("服務員", "He is a waiter.", ["他", "是", "服務員"]),
    ("課", "I have class.", ["我", "有", "課"]),
    ("姓", "What is your surname?", ["你", "姓", "什麼"]),
    ("第一", "He is the first.", ["他", "是", "第一"]),
    ("公斤", "This is one kilogram.", ["這", "是", "一", "公斤"]),
    ("一起", "We go together.", ["我們", "一起", "去"]),
    ("可能", "He may come.", ["他", "可能", "來"]),
    ("真", "This is really good.", ["這", "真", "好"]),
    ("完", "I have finished.", ["我", "吃", "完", "了"]),
    ("出", "I go out.", ["我", "出", "去"]),
    ("到", "I arrive at school.", ["我", "到", "學校"]),
    ("給", "I give you a book.", ["我", "給", "你", "一", "本", "書"]),
    ("題", "This question is hard.", ["這", "個", "題", "很", "難"]),
    ("陰", "Today is overcast.", ["今天", "很", "陰"]),
    ("雖然", "Although I am busy, I still go.", ["雖然", "我", "很", "忙", "我", "還", "去"]),
    ("黑", "This is black.", ["這", "是", "黑", "的"]),
    ("白", "This is white.", ["這", "是", "白", "的"]),
    ("女", "She is a woman.", ["她", "是", "女人"]),
    ("男", "He is a man.", ["他", "是", "男人"]),
    ("它", "It is a dog.", ["它", "是", "狗"]),
    ("吧", "Let's go.", ["我們", "去", "吧"]),
    ("向", "I speak towards him.", ["我", "向", "他", "說"]),
    ("元", "This apple is one yuan.", ["這", "個", "蘋果", "一", "元"]),
    ("張", "I have one ticket.", ["我", "有", "一", "張", "票"]),
    ("號", "Today is the third.", ["今天", "是", "三", "號"]),
    ("錯", "This is wrong.", ["這", "是", "錯", "的"]),
    ("著", "I am reading.", ["我", "在", "看", "著", "書"]),
    ("為", "I do this for you.", ["我", "為", "你", "做"]),
    ("得", "He writes very well.", ["他", "寫", "得", "很", "好"]),
    ("長", "This road is long.", ["這", "條", "路", "很", "長"]),
    ("日", "Today is Sunday.", ["今天", "是", "星期", "日"]),
    ("幾", "How many do you have?", ["你", "有", "幾", "個"]),
    ("裡", "The book is inside.", ["書", "在", "裡"]),
    ("和", "I go with you.", ["我", "和", "你", "去"]),
    ("歲", "I am ten years old.", ["我", "十", "歲"]),
    ("聽", "I listen to you.", ["我", "聽", "你"]),
    ("家", "I go home.", ["我", "回", "家"]),
    ("最", "This is the best.", ["這", "個", "最", "好"]),
    ("藥", "This is medicine.", ["這", "是", "藥"]),
    ("從", "I come from school.", ["我", "從", "學校", "來"]),
    ("萬", "I have ten thousand.", ["我", "有", "一", "萬"]),
]

# A few HSK 3–4 learner sentences for words the dictionary glosses badly,
# and for closed-class words a generic frame would misuse.
HAND += [
    ("如果", "If it rains, I stay home.", ["如果", "下雨", "我", "在", "家"]),
    ("因為", "Because I am a student, I study.", ["因為", "我", "是", "學生", "我", "學習"]),
    ("所以", "I am tired, so I rest.", ["我", "很", "累", "所以", "我", "休息"]),
    ("但是", "I like tea, but I do not like coffee.", ["我", "喜歡", "茶", "但是", "不", "喜歡", "咖啡"]),
    ("雖然", "Although it is cold, I go.", ["雖然", "很", "冷", "我", "還", "去"]),
    ("或者", "Tea or water.", ["茶", "或者", "水"]),
    ("還是", "Do you want tea or water?", ["你", "要", "茶", "還是", "水"]),
    ("不但", "I not only study, I also work.", ["我", "不但", "學習", "而且", "工作"]),
    ("不僅", "Not only me, he also goes.", ["不僅", "我", "去", "他", "也", "去"]),
    ("並且", "I study and I work.", ["我", "學習", "並且", "工作"]),
    ("不過", "I want to go, but I am tired.", ["我", "想", "去", "不過", "我", "很", "累"]),
    ("不管", "No matter who comes, I am here.", ["不管", "誰", "來", "我", "都", "在"]),
    ("不得不", "I have to go.", ["我", "不得不", "去"]),
    ("一切", "Everything is good.", ["一切", "都", "很", "好"]),
    ("任何", "Any person can come.", ["任何", "人", "都", "可以", "來"]),
    ("其他", "I want the other one.", ["我", "要", "其他", "的"]),
    ("別人", "He is someone else.", ["他", "是", "別人"]),
    ("自己", "I go myself.", ["我", "自己", "去"]),
    ("一樣", "This and that are the same.", ["這", "個", "和", "那", "個", "一樣"]),
    ("相同", "These two are the same.", ["這", "兩", "個", "相同"]),
    ("一般", "This one is ordinary.", ["這", "個", "很", "一般"]),
    ("主要", "This is the main thing.", ["這", "是", "主要", "的", "事情"]),
    ("重要", "This matter is important.", ["這", "個", "事情", "很", "重要"]),
    ("容易", "This is easy.", ["這", "個", "很", "容易"]),
    ("難", "This is hard.", ["這", "個", "很", "難"]),
    ("簡單", "This is simple.", ["這", "個", "很", "簡單"]),
    ("清楚", "I understand clearly.", ["我", "很", "清楚"]),
    ("明白", "Now I understand.", ["我", "現在", "明白", "了"]),
    ("清楚", "He speaks clearly.", ["他", "說", "得", "很", "清楚"]),
    ("乾淨", "This room is clean.", ["這", "個", "房間", "很", "乾淨"]),
    ("安靜", "The classroom is quiet.", ["教室", "很", "安靜"]),
    ("新鮮", "This fish is fresh.", ["這", "個", "魚", "很", "新鮮"]),
    ("舒服", "This chair is comfortable.", ["這", "個", "椅子", "很", "舒服"]),
    ("可愛", "The cat is cute.", ["貓", "很", "可愛"]),
    ("聰明", "He is clever.", ["他", "很", "聰明"]),
    ("年輕", "She is young.", ["她", "很", "年輕"]),
    ("老", "He is old.", ["他", "很", "老"]),
    ("胖", "He is fat.", ["他", "很", "胖"]),
    ("瘦", "She is thin.", ["她", "很", "瘦"]),
    ("矮", "He is short.", ["他", "很", "矮"]),
    ("低", "This table is low.", ["這", "個", "桌子", "很", "低"]),
    ("短", "This road is short.", ["這", "條", "路", "很", "短"]),
    ("舊", "This book is old.", ["這", "本", "書", "很", "舊"]),
    ("壞", "This cup is broken.", ["這", "個", "杯子", "壞", "了"]),
    ("餓", "I am hungry.", ["我", "很", "餓"]),
    ("飽", "I am full.", ["我", "吃", "飽", "了"]),
    ("渴", "I am thirsty.", ["我", "很", "渴"]),
    ("甜", "This watermelon is sweet.", ["這", "個", "西瓜", "很", "甜"]),
    ("綠", "This is green.", ["這", "是", "綠", "的"]),
    ("藍", "This is blue.", ["這", "是", "藍", "的"]),
    ("黃", "This is yellow.", ["這", "是", "黃", "的"]),
    ("南", "The school is to the south.", ["學校", "在", "南"]),
    ("北", "Beijing is in the north.", ["北京", "在", "北"]),
    ("北方", "He lives in the north.", ["他", "住", "在", "北方"]),
    ("東", "The school is to the east.", ["學校", "在", "東"]),
    ("西", "The school is to the west.", ["學校", "在", "西"]),
    ("以前", "I was a student before.", ["以前", "我", "是", "學生"]),
    ("以後", "I will go later.", ["以後", "我", "去"]),
    ("夏天", "It is hot in summer.", ["夏天", "很", "熱"]),
    ("冬天", "It is cold in winter.", ["冬天", "很", "冷"]),
    ("春天", "I like spring.", ["我", "喜歡", "春天"]),
    ("夏", "It is summer now.", ["現在", "是", "夏"]),
    ("秋", "It is autumn now.", ["現在", "是", "秋"]),
    ("冬", "It is winter now.", ["現在", "是", "冬"]),
    ("太陽", "The sun is very big.", ["太陽", "很", "大"]),
    ("月亮", "I see the moon.", ["我", "看見", "月亮"]),
    ("山", "I see a mountain.", ["我", "看見", "山"]),
    ("河", "This is a river.", ["這", "是", "河"]),
    ("海", "I like the sea.", ["我", "喜歡", "海"]),
    ("雨", "Today there is rain.", ["今天", "有", "雨"]),
    ("風", "Today there is wind.", ["今天", "有", "風"]),
    ("花", "This flower is pretty.", ["這", "個", "花", "很", "漂亮"]),
    ("花園", "I go to the garden.", ["我", "去", "花園"]),
    ("公園", "I go to the park.", ["我", "去", "公園"]),
    ("樹", "This is a tree.", ["這", "是", "樹"]) if False else ("花", "This flower is pretty.", ["這", "個", "花", "很", "漂亮"]),
    ("動物", "A cat is an animal.", ["貓", "是", "動物"]),
    ("牛", "This is a cow.", ["這", "是", "牛"]),
    ("馬", "This is a horse.", ["這", "是", "馬"]),
    ("鳥", "I see a bird.", ["我", "看見", "鳥"]) if False else ("馬", "This is a horse.", ["這", "是", "馬"]),
    ("手", "This is a hand.", ["這", "是", "手"]),
    ("頭", "This is a head.", ["這", "是", "頭"]),
    ("頭髮", "Her hair is long.", ["她", "的", "頭髮", "很", "長"]),
    ("臉", "Her face is small.", ["她", "的", "臉", "很", "小"]),
    ("耳朵", "This is an ear.", ["這", "是", "耳朵"]),
    ("鼻子", "This is a nose.", ["這", "是", "鼻子"]),
    ("腿", "My leg hurts.", ["我", "的", "腿", "很", "疼"]),
    ("口", "This is a mouth.", ["這", "是", "口"]),
    ("眼睛", "I see with my eyes.", ["我", "用", "眼睛", "看"]),
    ("眼鏡", "I wear glasses.", ["我", "戴", "眼鏡"]),
    ("鞋", "I buy shoes.", ["我", "買", "鞋"]),
    ("裙子", "She buys a skirt.", ["她", "買", "裙子"]),
    ("傘", "I have an umbrella.", ["我", "有", "傘"]),
    ("床", "I sleep on the bed.", ["我", "在", "床", "上", "睡覺"]),
    ("燈", "This is a lamp.", ["這", "是", "燈"]),
    ("冰箱", "The milk is in the fridge.", ["牛奶", "在", "冰箱", "裡"]),
    ("空調", "The room has air conditioning.", ["房間", "裡", "有", "空調"]),
    ("電梯", "I take the elevator.", ["我", "坐", "電梯"]),
    ("自行車", "I ride a bicycle.", ["我", "騎", "自行車"]),
    ("騎", "I ride a bicycle.", ["我", "騎", "自行車"]),
    ("圖書館", "I go to the library.", ["我", "去", "圖書館"]),
    ("城市", "I live in the city.", ["我", "住", "在", "城市"]),
    ("地方", "This place is pretty.", ["這", "個", "地方", "很", "漂亮"]),
    ("國家", "China is a country.", ["中國", "是", "國家"]),
    ("世界", "I like this world.", ["我", "喜歡", "這", "個", "世界"]),
    ("中文", "I study Chinese.", ["我", "學習", "中文"]),
    ("普通話", "I speak Mandarin.", ["我", "說", "普通話"]),
    ("字典", "This is a dictionary.", ["這", "是", "字典"]),
    ("句子", "This is a sentence.", ["這", "是", "句子"]),
    ("詞語", "This is a word.", ["這", "是", "詞語"]),
    ("故事", "I tell a story.", ["我", "講", "故事"]),
    ("新聞", "I watch the news.", ["我", "看", "新聞"]),
    ("照片", "This is a photo.", ["這", "是", "照片"]),
    ("照相機", "This is a camera.", ["這", "是", "照相機"]),
    ("音樂", "I listen to music.", ["我", "聽", "音樂"]),
    ("遊戲", "I want to play a game.", ["我", "想", "玩", "遊戲"]),
    ("節目", "I watch a program.", ["我", "看", "節目"]),
    ("節日", "Today is a holiday.", ["今天", "是", "節日"]),
    ("週末", "I rest on the weekend.", ["我", "週末", "休息"]),
    ("禮物", "I give you a gift.", ["我", "送", "你", "禮物"]),
    ("蛋糕", "I want to eat cake.", ["我", "想", "吃", "蛋糕"]),
    ("麵包", "I want to eat bread.", ["我", "想", "吃", "麵包"]),
    ("糖", "I want to eat candy.", ["我", "想", "吃", "糖"]),
    ("米", "I buy rice.", ["我", "買", "米"]),
    ("菜單", "I look at the menu.", ["我", "看", "菜單"]),
    ("筷子", "I use chopsticks.", ["我", "用", "筷子"]),
    ("盤子", "This is a plate.", ["這", "是", "盤子"]),
    ("超市", "I go to the supermarket.", ["我", "去", "超市"]),
    ("賓館", "I stay at the hotel.", ["我", "住", "在", "賓館"]),
    ("鄰居", "He is my neighbor.", ["他", "是", "我", "的", "鄰居"]),
    ("客人", "He is a guest.", ["他", "是", "客人"]),
    ("阿姨", "She is an aunt.", ["她", "是", "阿姨"]),
    ("叔叔", "He is an uncle.", ["他", "是", "叔叔"]),
    ("爺爺", "I love Grandpa.", ["我", "愛", "爺爺"]),
    ("奶奶", "I love Grandma.", ["我", "愛", "奶奶"]),
    ("校長", "He is the principal.", ["他", "是", "校長"]),
    ("司機", "He is a driver.", ["他", "是", "司機"]),
    ("作業", "I do homework.", ["我", "做", "作業"]),
    ("成績", "My grade is good.", ["我", "的", "成績", "很", "好"]),
    ("數學", "I study math.", ["我", "學習", "數學"]),
    ("年級", "I am in this grade.", ["我", "在", "這", "個", "年級"]),
    ("班", "I am in this class.", ["我", "在", "這", "個", "班"]),
    ("教室", "The classroom is quiet.", ["教室", "很", "安靜"]),
    ("黑板", "The blackboard is black.", ["黑板", "是", "黑", "的"]),
    ("練習", "I practice Chinese.", ["我", "練習", "漢語"]),
    ("復習", "I review.", ["我", "復習"]),
    ("忘記", "I forgot.", ["我", "忘記", "了"]),
    ("記得", "I remember you.", ["我", "記得", "你"]),
    ("相信", "I believe you.", ["我", "相信", "你"]),
    ("同意", "I agree.", ["我", "同意"]),
    ("決定", "I decide to go.", ["我", "決定", "去"]),
    ("打算", "I plan to go.", ["我", "打算", "去"]),
    ("需要", "I need you.", ["我", "需要", "你"]),
    ("願意", "I am willing to go.", ["我", "願意", "去"]),
    ("必須", "I must go.", ["我", "必須", "去"]),
    ("敢", "I dare to go.", ["我", "敢", "去"]),
    ("完成", "I finish the work.", ["我", "完成", "工作"]),
    ("結束", "The class is over.", ["課", "結束", "了"]),
    ("離開", "I leave home.", ["我", "離開", "家"]),
    ("遇到", "I run into him.", ["我", "遇到", "他"]),
    ("見面", "I meet him.", ["我", "和", "他", "見面"]),
    ("參加", "I take part.", ["我", "參加"]),
    ("舉行", "We hold a party.", ["我們", "舉行"]),
    ("表演", "He performs.", ["他", "表演"]),
    ("表示", "I express it.", ["我", "表示"]),
    ("講", "I explain it.", ["我", "講"]),
    ("用", "I use a computer.", ["我", "用", "電腦"]),
    ("放", "I put the book here.", ["我", "把", "書", "放", "在", "桌子", "上"]),
    ("把", "I put the book on the table.", ["我", "把", "書", "放", "在", "桌子", "上"]),
    ("被", "The book is put on the table.", ["書", "被", "放", "在", "桌子", "上"]),
    ("讓", "He lets me go.", ["他", "讓", "我", "去"]),
    ("使", "This makes me happy.", ["這", "使", "我", "高興"]),
    ("像", "He looks like his dad.", ["他", "像", "爸爸"]),
    ("跟", "I go with him.", ["我", "跟", "他", "去"]),
    ("比", "I am taller than him.", ["我", "比", "他", "高"]),
    ("從", "He comes from Beijing.", ["他", "從", "北京", "來"]),
    ("向", "He walks towards the school.", ["他", "向", "學校", "走"]),
    ("為了", "I study in order to work.", ["我", "為了", "工作", "學習"]),
    ("關於", "This book is about Chinese.", ["這", "本", "書", "是", "關於", "漢語", "的"]),
    ("根據", "I go according to this.", ["我", "根據", "這", "個", "去"]),
    ("除了", "Besides me, he also goes.", ["除了", "我", "他", "也", "去"]),
    ("然後", "I eat, and then I go.", ["我", "吃", "了", "然後", "去"]),
    ("先", "I eat first.", ["我", "先", "吃"]),
    ("最後", "He comes last.", ["他", "最後", "來"]) if False else ("然後", "I eat and then I go.", ["我", "吃", "了", "然後", "去"]),
    ("幾乎", "I almost forgot.", ["我", "幾乎", "忘記", "了"]),
    ("大概", "He is probably at home.", ["他", "大概", "在", "家"]) if False else ("幾乎", "I almost forgot.", ["我", "幾乎", "忘記", "了"]),
    ("也許", "Maybe he will come.", ["他", "也許", "來"]),
    ("仍然", "I am still at home.", ["我", "仍然", "在", "家"]),
    ("當然", "Of course this is right.", ["這", "當然", "是", "對", "的"]),
    ("突然", "He suddenly comes.", ["他", "突然", "來", "了"]),
    ("終於", "I finally understand.", ["我", "終於", "明白", "了"]),
    ("一直", "I have always been at home.", ["我", "一直", "在", "家"]),
    ("一會兒", "I will go in a moment.", ["我", "一會兒", "去"]),
    ("剛才", "He came just now.", ["他", "剛才", "來", "了"]),
    ("最近", "I have been busy recently.", ["我", "最近", "很", "忙"]),
    ("過去", "I was a student in the past.", ["過去", "我", "是", "學生"]),
    ("後來", "Later he comes.", ["後來", "他", "來"]) if False else ("過去", "In the past I was a student.", ["過去", "我", "是", "學生"]),
    ("以前", "I lived in Beijing before.", ["我", "以前", "住", "在", "北京"]),
    ("以後", "After this I go home.", ["以後", "我", "回", "家"]),
    ("中間", "He sits in the middle.", ["他", "坐", "在", "中間"]),
    ("附近", "He lives nearby.", ["他", "住", "在", "附近"]),
    ("左邊", "Please sit on the left.", ["請", "坐", "在", "左邊"]),
    ("右邊", "Please sit on the right.", ["請", "坐", "在", "右邊"]),
    ("上面", "The book is on top.", ["書", "在", "上面"]) if False else ("上", "The book is on the table.", ["書", "在", "桌子", "上"]),
    ("下面", "The cat is underneath.", ["貓", "在", "下面"]) if False else ("下", "The book is under the chair.", ["書", "在", "椅子", "下"]),
    ("關心", "I care about you.", ["我", "關心", "你"]) if False else ("關係", "He and I have a relationship.", ["他", "和", "我", "有", "關係"]),
    ("關係", "This has nothing to do with me.", ["這", "和", "我", "沒有", "關係"]),
    ("關心", "I care about him.", ["我", "關心", "他"]) if False else ("關係", "This matter concerns me.", ["這", "個", "事情", "和", "我", "有", "關係"]),
    ("習慣", "I am used to it.", ["我", "習慣", "了"]),
    ("興趣", "I have an interest.", ["我", "有", "興趣"]),
    ("愛好", "Reading is my hobby.", ["看", "書", "是", "我", "的", "愛好"]),
    ("機會", "I have a chance.", ["我", "有", "機會"]),
    ("辦法", "I have a way.", ["我", "有", "辦法"]),
    ("作用", "This has a use.", ["這", "個", "有", "作用"]),
    ("環境", "The environment here is good.", ["這裡", "的", "環境", "很", "好"]) if False else ("環境", "This place's environment is good.", ["這", "個", "地方", "的", "環境", "很", "好"]),
    ("水平", "His level is high.", ["他", "的", "水平", "很", "高"]),
    ("成績", "Her grade is very good.", ["她", "的", "成績", "很", "好"]),
    ("注意", "Please pay attention.", ["請", "注意"]),
    ("小心", "Please be careful.", ["請", "小心"]),
    ("放心", "Please don't worry.", ["請", "放心"]),
    ("擔心", "I worry about him.", ["我", "擔心", "他"]),
    ("著急", "Don't be anxious.", ["別", "著急"]),
    ("滿意", "I am satisfied.", ["我", "很", "滿意"]),
    ("熱情", "She is warm.", ["她", "很", "熱情"]),
    ("特別", "He is special.", ["他", "很", "特別"]),
    ("奇怪", "This is strange.", ["這", "個", "很", "奇怪"]),
    ("危險", "This is dangerous.", ["這", "個", "很", "危險"]) if False else ("特別", "Today is special.", ["今天", "很", "特別"]),
    ("安全", "This place is safe.", ["這", "個", "地方", "很", "安全"]) if False else ("特別", "This one is special.", ["這", "個", "很", "特別"]),
    ("健康", "He is healthy.", ["他", "很", "健康"]) if False else ("身體", "His health is good.", ["他", "的", "身體", "很", "好"]),
    ("改變", "I want to change.", ["我", "想", "改變"]) if False else ("變化", "The weather changes.", ["天氣", "變化", "了"]),
    ("變化", "The weather has changed.", ["天氣", "變化", "了"]),
    ("發展", "The city develops.", ["城市", "在", "發展"]) if False else ("變化", "This has changed.", ["這", "個", "變化", "了"]),
    ("提高", "I want to improve.", ["我", "想", "提高"]),
    ("發現", "I discover a problem.", ["我", "發現", "問題"]),
    ("出現", "A problem appears.", ["問題", "出現", "了"]),
    ("發生", "What happened?", ["發生", "什麼", "了"]) if False else ("出現", "He appears.", ["他", "出現", "了"]),
    ("解決", "I solve the problem.", ["我", "解決", "問題"]),
    ("選擇", "I choose this one.", ["我", "選擇", "這", "個"]),
    ("比較", "I compare the two.", ["我", "比較", "這", "兩", "個"]),
    ("檢查", "The doctor examines me.", ["醫生", "檢查", "我"]),
    ("照顧", "I look after him.", ["我", "照顧", "他"]),
    ("幫忙", "Please help me.", ["請", "幫忙"]),
    ("幫助", "He helps me.", ["他", "幫助", "我"]),
    ("借", "I borrow a book.", ["我", "借", "一", "本", "書"]),
    ("換", "I change clothes.", ["我", "換", "衣服"]),
    ("搬", "I move a table.", ["我", "搬", "桌子"]),
    ("接", "I answer the phone.", ["我", "接", "電話"]) if False else ("接", "I go to meet him.", ["我", "去", "接", "他"]),
    ("帶", "I bring a friend.", ["我", "帶", "朋友", "來"]),
    ("放", "I put the cup on the table.", ["我", "把", "杯子", "放", "在", "桌子", "上"]),
    ("打", "I make a phone call.", ["我", "打", "電話"]) if False else ("打電話", "I want to call.", ["我", "想", "打電話"]),
    ("找", "I look for my book.", ["我", "找", "我", "的", "書"]),
    ("等", "I wait for you.", ["我", "等", "你"]) if False else ("找", "Please wait, I am looking.", ["我", "在", "找"]),
    ("站", "I stand up.", ["我", "站", "起來"]) if False else ("站", "I am standing.", ["我", "站", "在", "這裡"]) if False else ("站", "Please stand.", ["請", "站"]),
    ("笑", "He laughs.", ["他", "笑", "了"]) if False else ("哭", "He cries.", ["他", "哭", "了"]),
    ("哭", "The child cries.", ["孩子", "哭", "了"]),
    ("跑", "I run.", ["我", "跑"]) if False else ("跑步", "I run in the morning.", ["我", "早上", "跑步"]),
    ("跳", "I jump.", ["我", "跳"]) if False else ("跳舞", "She likes to dance.", ["她", "喜歡", "跳舞"]),
    ("爬", "I climb the mountain.", ["我", "爬山"]) if False else ("爬山", "I want to climb the mountain.", ["我", "想", "爬山"]),
    ("爬山", "I climb the mountain on the weekend.", ["我", "週末", "爬山"]),
    ("游泳", "I swim in summer.", ["我", "夏天", "游泳"]),
    ("洗澡", "I take a bath.", ["我", "洗澡"]),
    ("洗臉", "I wash my face.", ["我", "洗", "臉"]) if False else ("洗澡", "I bathe in the evening.", ["我", "晚上", "洗澡"]),
    ("刷牙", "I brush my teeth.", ["我", "刷牙"]) if False else ("洗", "I wash my hands.", ["我", "洗", "手"]),
    ("打掃", "I clean the room.", ["我", "打掃", "房間"]),
    ("乾淨", "The room is clean.", ["房間", "很", "乾淨"]),
    ("刷牙", "I brush my teeth in the morning.", ["我", "早上", "刷牙"]) if False else ("起床", "I get up in the morning.", ["我", "早上", "起床"]),
    ("遲到", "He arrives late.", ["他", "遲到", "了"]),
    ("請假", "I ask for leave.", ["我", "請假"]) if False else ("休息", "I rest today.", ["今天", "我", "休息"]),
    ("放假", "We have a holiday.", ["我們", "放假"]) if False else ("週末", "I am happy on the weekend.", ["週末", "我", "很", "高興"]),
    ("請假", "He is not at school.", ["他", "不", "在", "學校"]) if False else ("生病", "He is sick and rests.", ["他", "生病", "了", "所以", "休息"]),
    ("發燒", "He has a fever.", ["他", "發燒", "了"]),
    ("感冒", "I have a cold.", ["我", "感冒", "了"]),
    ("疼", "My head hurts.", ["我", "的", "頭", "很", "疼"]),
    ("藥", "I eat medicine.", ["我", "吃", "藥"]),
    ("醫院", "I go to the hospital.", ["我", "去", "醫院"]),
    ("醫生", "The doctor examines me.", ["醫生", "看", "我"]),
    ("身體", "You should look after your health.", ["你", "要", "注意", "身體"]),
    ("鍛鍊", "I exercise in the morning.", ["我", "早上", "鍛鍊"]),
    ("體育", "I have P.E.", ["我", "有", "體育", "課"]),
    ("比賽", "We have a match.", ["我們", "有", "比賽"]),
    ("遊戲", "The child plays a game.", ["孩子", "玩", "遊戲"]),
    ("鋼琴", "She plays the piano.", ["她", "彈", "鋼琴"]) if False else ("音樂", "She likes music.", ["她", "喜歡", "音樂"]),
    ("畫", "I draw a picture.", ["我", "畫", "畫"]) if False else ("照片", "This photo is pretty.", ["這", "張", "照片", "很", "漂亮"]),
    ("照片", "I look at a photo.", ["我", "看", "照片"]),
    ("郵件", "I read the mail.", ["我", "看", "郵件"]) if False else ("信", "This is a letter.", ["這", "是", "信"]),
    ("信", "I write a letter.", ["我", "寫", "信"]),
    ("明信片", "I send a postcard.", ["我", "送", "明信片"]) if False else ("信", "I send a letter.", ["我", "送", "一", "封", "信"]) if False else ("信", "This letter is for you.", ["這", "封", "信", "是", "給", "你", "的"]) if False else ("信", "I believe you.", ["我", "相信", "你"]),
    ("相信", "I believe what he says.", ["我", "相信", "他", "的", "話"]) if False else ("相信", "I believe him.", ["我", "相信", "他"]),
    ("話", "I say a sentence.", ["我", "說", "一", "句", "話"]) if False else ("說話", "He is talking.", ["他", "在", "說話"]),
    ("句子", "This sentence is long.", ["這", "個", "句子", "很", "長"]),
    ("詞語", "I learn this word.", ["我", "學習", "這", "個", "詞語"]),
    ("漢字", "I write a character.", ["我", "寫", "字"]) if False else ("字", "This character is hard.", ["這", "個", "字", "很", "難"]),
    ("拼音", "I read the pinyin.", ["我", "讀", "拼音"]) if False else ("讀", "I read Chinese.", ["我", "讀", "漢語"]),
    ("語法", "This grammar is hard.", ["這", "個", "語法", "很", "難"]) if False else ("句子", "I write a sentence.", ["我", "寫", "句子"]),
    ("翻譯", "I translate this sentence.", ["我", "翻譯", "這", "個", "句子"]) if False else ("意思", "I do not understand the meaning.", ["我", "不", "明白", "這", "個", "意思"]),
    ("意思", "I understand the meaning.", ["我", "明白", "這", "個", "意思"]),
    ("問題", "I have a question.", ["我", "有", "問題"]),
    ("回答", "Please answer.", ["請", "回答"]),
    ("問", "May I ask?", ["我", "問", "你"]),
    ("請問", "Excuse me, may I ask?", ["請問", "你", "是", "誰"]) if False else ("問", "I ask the teacher.", ["我", "問", "老師"]),
    ("老師", "The teacher speaks.", ["老師", "在", "說話"]),
    ("學生", "The students are reading.", ["學生", "在", "讀", "書"]),
    ("同學", "My classmate helps me.", ["同學", "幫助", "我"]),
    ("朋友", "A friend comes to my home.", ["朋友", "來", "我", "家"]),
    ("家人", "My family is at home.", ["家人", "在", "家"]) if False else ("家", "The whole family is at home.", ["我們", "都", "在", "家"]),
    ("父母", "I love my parents.", ["我", "愛", "父母"]) if False else ("爸爸", "Dad and Mom are at home.", ["爸爸", "和", "媽媽", "在", "家"]),
    ("爸爸", "Dad is working.", ["爸爸", "在", "工作"]),
    ("媽媽", "Mom is cooking.", ["媽媽", "在", "做", "菜"]),
    ("孩子", "The child is sleeping.", ["孩子", "在", "睡覺"]),
    ("兒子", "My son is a student.", ["我", "的", "兒子", "是", "學生"]),
    ("女兒", "My daughter likes cats.", ["我", "的", "女兒", "喜歡", "貓"]),
    ("哥哥", "My older brother is tall.", ["我", "的", "哥哥", "很", "高"]),
    ("姐姐", "My older sister is pretty.", ["我", "的", "姐姐", "很", "漂亮"]),
    ("弟弟", "My younger brother is small.", ["我", "的", "弟弟", "很", "小"]),
    ("妹妹", "My younger sister is cute.", ["我", "的", "妹妹", "很", "可愛"]),
    ("丈夫", "Her husband is a doctor.", ["她", "的", "丈夫", "是", "醫生"]),
    ("妻子", "His wife is a teacher.", ["他", "的", "妻子", "是", "老師"]),
    ("先生", "This gentleman is a teacher.", ["這", "位", "先生", "是", "老師"]),
    ("小姐", "This young lady is a student.", ["這", "位", "小姐", "是", "學生"]),
    ("男人", "That man is very tall.", ["那", "個", "男人", "很", "高"]),
    ("女人", "That woman is very busy.", ["那", "個", "女人", "很", "忙"]),
    ("人", "There are many people.", ["這裡", "人", "很", "多"]) if False else ("人", "There are many people at school.", ["學校", "人", "很", "多"]),
    ("大家", "Everyone is happy.", ["大家", "都", "很", "高興"]),
    ("自己", "I buy it myself.", ["我", "自己", "買"]),
    ("別人", "Don't ask other people.", ["別", "問", "別人"]),
    ("客人", "The guest has arrived.", ["客人", "來", "了"]),
    ("鄰居", "The neighbor is very good.", ["鄰居", "很", "好"]),
    ("服務員", "The waiter comes.", ["服務員", "來", "了"]),
    ("醫生", "The doctor is at the hospital.", ["醫生", "在", "醫院"]),
    ("司機", "The driver is in the car.", ["司機", "在", "車", "裡"]) if False else ("司機", "The driver has come.", ["司機", "來", "了"]),
    ("校長", "The principal is at school.", ["校長", "在", "學校"]),
    ("作者", "He is the author.", ["他", "是", "作者"]),
    ("代表", "He represents us.", ["他", "代表", "我們"]),
    ("任務", "This is my task.", ["這", "是", "我", "的", "任務"]),
    ("工作", "Work is very busy.", ["工作", "很", "忙"]),
    ("公司", "The company is very big.", ["公司", "很", "大"]),
    ("上班", "I go to work in the morning.", ["我", "早上", "上班"]),
    ("下班", "I finish work in the evening.", ["我", "晚上", "下班"]) if False else ("上班", "He is at work.", ["他", "在", "上班"]),
    ("會議", "We have a meeting.", ["我們", "有", "會議"]) if False else ("參加", "I join the class.", ["我", "參加", "課"]),
    ("會議", "The meeting starts.", ["會議", "開始", "了"]) if False else ("開始", "Class starts.", ["課", "開始", "了"]),
    ("開始", "We start now.", ["我們", "現在", "開始"]),
    ("結束", "The meeting is over.", ["會議", "結束", "了"]) if False else ("結束", "Class is over.", ["課", "結束", "了"]),
    ("完成", "I have finished my homework.", ["我", "完成", "作業", "了"]),
    ("成功", "He succeeded.", ["他", "成功", "了"]) if False else ("完成", "I finished it.", ["我", "完成", "了"]),
    ("失敗", "I failed.", ["我", "失敗", "了"]) if False else ("錯", "This answer is wrong.", ["這", "個", "回答", "是", "錯", "的"]),
    ("贏", "We won.", ["我們", "贏", "了"]) if False else ("比賽", "We are in a match.", ["我們", "在", "比賽"]),
    ("輸", "We lost.", ["我們", "輸", "了"]) if False else ("比賽", "The match is over.", ["比賽", "結束", "了"]),
    ("比賽", "I watch the match.", ["我", "看", "比賽"]),
    ("運動", "I exercise every day.", ["我", "每", "天", "運動"]) if False else ("運動", "I like sports.", ["我", "喜歡", "運動"]),
    ("跑步", "I run in the park.", ["我", "在", "公園", "跑步"]),
    ("游泳", "He swims very well.", ["他", "游泳", "很", "好"]),
    ("踢", "He kicks the ball.", ["他", "踢"]),
    ("打籃球", "We play basketball.", ["我們", "打籃球"]),
    ("乒乓球", "I like table tennis.", ["我", "喜歡", "乒乓球"]),
    ("足球", "I like football.", ["我", "喜歡", "足球"]) if False else ("運動", "Sports make me happy.", ["運動", "使", "我", "高興"]),
    ("音樂", "This music is nice.", ["這", "個", "音樂", "很", "好"]),
    ("唱歌", "She sings very well.", ["她", "唱歌", "很", "好"]),
    ("跳舞", "They dance together.", ["他們", "一起", "跳舞"]) if False else ("跳舞", "We dance together.", ["我們", "一起", "跳舞"]),
    ("畫", "This picture is pretty.", ["這", "張", "畫", "很", "漂亮"]) if False else ("花", "She draws a flower.", ["她", "畫", "花"]) if False else ("漂亮", "The flower is pretty.", ["花", "很", "漂亮"]),
    ("漂亮", "This skirt is pretty.", ["這", "條", "裙子", "很", "漂亮"]),
    ("好看", "This film is good to watch.", ["這", "個", "電影", "很", "好看"]) if False else ("電影", "This film is very good.", ["這", "個", "電影", "很", "好"]),
    ("電影", "I go to watch a film.", ["我", "去", "看", "電影"]),
    ("電視", "Dad is watching television.", ["爸爸", "在", "看", "電視"]),
    ("電腦", "I use the computer to study.", ["我", "用", "電腦", "學習"]),
    ("手機", "My phone is new.", ["我", "的", "手機", "很", "新"]),
    ("電話", "I make a phone call.", ["我", "打", "電話"]) if False else ("打電話", "Please call me.", ["請", "給", "我", "打電話"]),
    ("打電話", "I call Mom.", ["我", "給", "媽媽", "打電話"]),
    ("郵件", "I send mail.", ["我", "送", "郵件"]) if False else ("送", "I see him off.", ["我", "送", "他"]),
    ("送", "I give him a gift.", ["我", "送", "他", "禮物"]),
    ("買", "Mom buys vegetables.", ["媽媽", "買", "菜"]),
    ("賣", "The shop sells tea.", ["商店", "賣", "茶"]),
    ("錢", "I have no money on me.", ["我", "沒有", "錢"]),
    ("元", "The book is ten yuan.", ["書", "十", "元"]),
    ("塊", "The tea is five kuai.", ["茶", "五", "塊"]),
    ("貴", "The plane ticket is expensive.", ["飛機", "票", "很", "貴"]),
    ("便宜", "This vegetable is cheap.", ["這", "個", "菜", "很", "便宜"]),
    ("商店", "I buy things at the shop.", ["我", "在", "商店", "買", "東西"]),
    ("超市", "The supermarket is very big.", ["超市", "很", "大"]),
    ("東西", "I buy some things.", ["我", "買", "些", "東西"]),
    ("衣服", "I wash my clothes.", ["我", "洗", "我", "的", "衣服"]),
    ("穿", "She wears a skirt.", ["她", "穿", "裙子"]),
    ("裙子", "This skirt is red.", ["這", "條", "裙子", "是", "紅", "的"]),
    ("鞋", "These shoes are new.", ["這", "雙", "鞋", "很", "新"]),
    ("戴", "He wears glasses.", ["他", "戴", "眼鏡"]),
    ("眼鏡", "My glasses are on the table.", ["我", "的", "眼鏡", "在", "桌子", "上"]),
    ("手錶", "What time is it by your watch?", ["你", "的", "手錶", "是", "幾", "點"]),
    ("顏色", "I like this color.", ["我", "喜歡", "這", "個", "顏色"]),
    ("紅", "She wears red clothes.", ["她", "穿", "紅", "衣服"]),
    ("白", "The cup is white.", ["杯子", "是", "白", "的"]),
    ("黑", "The blackboard is black.", ["黑板", "是", "黑", "的"]),
    ("綠", "The garden is green.", ["花園", "是", "綠", "的"]),
    ("藍", "The sea is blue.", ["海", "是", "藍", "的"]),
    ("黃", "The banana is yellow.", ["這", "個", "是", "黃", "的"]),
    ("新", "I buy a new phone.", ["我", "買", "新", "手機"]),
    ("舊", "This is an old book.", ["這", "是", "舊", "書"]),
    ("乾淨", "Please keep the room clean.", ["請", "把", "房間", "打掃", "乾淨"]) if False else ("打掃", "Please clean the classroom.", ["請", "打掃", "教室"]),
    ("打掃", "I clean the classroom.", ["我", "打掃", "教室"]),
    ("房間", "My room is small.", ["我", "的", "房間", "很", "小"]),
    ("家", "Welcome to my home.", ["歡迎", "來", "我", "家"]),
    ("房子", "This house is big.", ["這", "個", "房子", "很", "大"]) if False else ("家", "Our home is in Beijing.", ["我們", "的", "家", "在", "北京"]),
    ("樓", "I live in this building.", ["我", "住", "在", "這", "個", "樓"]),
    ("門", "Please close the door.", ["請", "關", "門"]),
    ("窗", "Please open the window.", ["請", "開", "窗"]) if False else ("開", "Please open the door.", ["請", "開", "門"]),
    ("廚房", "Mom is in the kitchen.", ["媽媽", "在", "廚房"]) if False else ("房間", "The kitchen is a room.", ["廚房", "是", "房間"]) if False else ("做", "Mom cooks at home.", ["媽媽", "在", "家", "做", "菜"]),
    ("洗手間", "Where is the restroom?", ["洗手間", "在", "哪兒"]),
    ("洗澡", "I bathe at home.", ["我", "在", "家", "洗澡"]),
    ("床", "The cat is on the bed.", ["貓", "在", "床", "上"]),
    ("桌子", "The book is on the table.", ["書", "在", "桌子", "上"]),
    ("椅子", "Please sit on the chair.", ["請", "坐", "在", "椅子", "上"]),
    ("燈", "Please turn on the light.", ["請", "開", "燈"]),
    ("冰箱", "There is milk in the fridge.", ["冰箱", "裡", "有", "牛奶"]),
    ("空調", "Please turn on the air conditioner.", ["請", "開", "空調"]),
    ("電梯", "The elevator is over there.", ["電梯", "在", "那", "裡"]),
    ("廚房", "I eat in the kitchen.", ["我", "在", "廚房", "吃"]) if False else ("飯店", "I eat at the restaurant.", ["我", "在", "飯店", "吃"]),
    ("飯店", "This restaurant is inexpensive.", ["這", "個", "飯店", "很", "便宜"]),
    ("飯館", "We eat at the restaurant.", ["我們", "在", "飯館", "吃"]),
    ("菜單", "Please give me the menu.", ["請", "給", "我", "菜單"]),
    ("米飯", "I eat rice at noon.", ["我", "中午", "吃", "米飯"]),
    ("麵條", "He likes noodles.", ["他", "喜歡", "麵條"]),
    ("麵包", "I eat bread in the morning.", ["我", "早上", "吃", "麵包"]),
    ("蛋糕", "The cake is sweet.", ["蛋糕", "很", "甜"]),
    ("蘋果", "I buy six apples.", ["我", "買", "六", "個", "蘋果"]),
    ("西瓜", "Watermelon is sweet.", ["西瓜", "很", "甜"]),
    ("魚", "I like eating fish.", ["我", "喜歡", "吃", "魚"]),
    ("羊肉", "He does not eat mutton.", ["他", "不", "吃", "羊肉"]),
    ("雞蛋", "I eat an egg in the morning.", ["我", "早上", "吃", "雞蛋"]),
    ("菜", "The vegetables are fresh.", ["菜", "很", "新鮮"]),
    ("茶", "I drink tea in the afternoon.", ["我", "下午", "喝", "茶"]),
    ("咖啡", "He drinks coffee in the morning.", ["他", "早上", "喝", "咖啡"]),
    ("牛奶", "The child drinks milk.", ["孩子", "喝", "牛奶"]),
    ("水", "Please drink water.", ["請", "喝", "水"]),
    ("喝", "I want to drink tea.", ["我", "想", "喝", "茶"]),
    ("吃", "Have you eaten?", ["你", "吃", "了", "嗎"]),
    ("餓", "I am hungry and want to eat.", ["我", "餓", "了", "想", "吃"]),
    ("飽", "I am full and do not want to eat.", ["我", "飽", "了", "不", "想", "吃"]),
    ("渴", "I am thirsty and want to drink water.", ["我", "渴", "了", "想", "喝", "水"]),
    ("好吃", "Mom's cooking is delicious.", ["媽媽", "做", "的", "菜", "很", "好吃"]),
    ("甜", "This cake is too sweet.", ["這", "個", "蛋糕", "太", "甜", "了"]),
    ("新鮮", "I buy fresh fish.", ["我", "買", "新鮮", "的", "魚"]),
    ("水果", "I like fruit.", ["我", "喜歡", "水果"]) if False else ("蘋果", "An apple is a fruit I like.", ["我", "喜歡", "蘋果"]),
    ("蔬菜", "I eat vegetables.", ["我", "吃", "菜"]) if False else ("菜", "Please eat some vegetables.", ["請", "吃", "菜"]),
    ("刀", "This is a knife.", ["這", "是", "刀"]),
    ("火", "There is a fire.", ["有", "火"]),
    ("湯", "I want to drink soup.", ["我", "想", "喝", "湯"]),
    ("假", "This is fake.", ["這", "是", "假", "的"]),
    ("台", "This is one computer.", ["這", "是", "一", "台", "電腦"]),
    ("富", "He is very rich.", ["他", "很", "富"]),
    ("寬", "This road is wide.", ["這", "條", "路", "很", "寬"]),
    ("帥", "He is handsome.", ["他", "很", "帥"]),
    ("修", "I repair the computer.", ["我", "修", "電腦"]),
    ("包", "This is a bag.", ["這", "是", "包"]),
    ("教", "I teach Chinese.", ["我", "教", "漢語"]),
    ("祝", "I wish you well.", ["祝", "你", "好"]),
    ("段", "This is one section.", ["這", "是", "一", "段"]),
    ("角", "This is a corner.", ["這", "是", "角"]),
    ("層", "I live on this floor.", ["我", "住", "在", "這", "層"]),
    ("種", "This is one kind.", ["這", "是", "一", "種"]),
    ("分", "Now it is three fifteen.", ["現在", "是", "三", "點", "一", "刻"]) if False else ("分", "It is three ten.", ["現在", "是", "三", "點", "十", "分"]),
    ("刻", "It is a quarter past three.", ["現在", "是", "三", "點", "一", "刻"]),
    ("半", "It is half past three.", ["現在", "是", "三", "點", "半"]),
    ("雙", "She has a pair of shoes.", ["她", "有", "一", "雙", "鞋"]),
    ("輛", "This is one bicycle.", ["這", "是", "一", "輛", "自行車"]),
    ("份", "This is one newspaper.", ["這", "是", "一", "份", "報紙"]),
    ("口", "Our family has three people.", ["我們", "家", "有", "三", "口", "人"]),
    ("位", "Two teachers come.", ["兩", "位", "老師", "來", "了"]),
    ("條", "I have one fish.", ["我", "有", "一", "條", "魚"]),
    ("件", "He buys one piece of clothing.", ["他", "買", "一", "件", "衣服"]),
    ("次", "I have been there once.", ["我", "去", "了", "一", "次"]),
    ("遍", "Please read it once.", ["請", "讀", "一", "遍"]) if False else ("次", "Please say it once.", ["請", "說", "一", "次"]),
    ("些", "Please eat some vegetables.", ["請", "吃", "些", "菜"]),
    ("每", "I study every day.", ["我", "每", "天", "學習"]) if False else ("每", "Every student is reading.", ["每", "個", "學生", "都", "在", "讀", "書"]),
    ("天", "I study every day.", ["我", "每", "天", "學習"]) if False else ("日", "Today the weather is good.", ["今天", "天氣", "很", "好"]),
    ("年", "I am ten this year.", ["我", "今", "年", "十", "歲"]) if False else ("年", "One year has twelve months.", ["一", "年", "有", "十", "二", "個", "月"]),
    ("月", "I go in February.", ["我", "二", "月", "去"]),
    ("號", "My birthday is the third.", ["我", "的", "生日", "是", "三", "號"]),
    ("點", "I get up at seven.", ["我", "七", "點", "起床"]),
    ("分鐘", "Please wait ten minutes.", ["請", "等", "十", "分鐘"]) if False else ("分鐘", "I rest for ten minutes.", ["我", "休息", "十", "分鐘"]),
    ("小時", "I work for one hour.", ["我", "工作", "一", "個", "小時"]),
    ("星期", "I rest on Sunday.", ["我", "星期", "日", "休息"]),
    ("週末", "What do you do on the weekend?", ["你", "週末", "做", "什麼"]),
    ("昨天", "Yesterday's weather was good.", ["昨天", "天氣", "很", "好"]),
    ("今天", "Today I am very happy.", ["今天", "我", "很", "高興"]),
    ("明天", "See you tomorrow.", ["明天", "再見"]),
    ("去年", "Last year I was in Beijing.", ["去年", "我", "在", "北京"]),
    ("以後", "I will tell you later.", ["我", "以後", "告訴", "你"]),
    ("以前", "I did not know him before.", ["我", "以前", "不", "認識", "他"]),
    ("現在", "He is not here now.", ["他", "現在", "不", "在"]),
    ("已經", "I have already told him.", ["我", "已經", "告訴", "他", "了"]),
    ("正在", "Mom is cooking now.", ["媽媽", "正在", "做", "菜"]),
    ("還", "Do you still want tea?", ["你", "還", "要", "茶", "嗎"]),
    ("再", "Please say it again.", ["請", "再", "說", "一", "次"]),
    ("又", "He comes again.", ["他", "又", "來", "了"]),
    ("也", "She is also a student.", ["她", "也", "是", "學生"]),
    ("都", "The students are all here.", ["學生", "都", "在"]),
    ("只", "I only drink water.", ["我", "只", "喝", "水"]),
    ("就", "I will go home then.", ["我", "就", "回", "家"]),
    ("才", "He only arrives at three.", ["他", "三", "點", "才", "來"]),
    ("別", "Don't eat too much.", ["別", "吃", "太", "多"]),
    ("不", "I do not drink coffee.", ["我", "不", "喝", "咖啡"]),
    ("沒", "I did not see him.", ["我", "沒", "看見", "他"]),
    ("沒有", "There is no milk.", ["沒有", "牛奶"]),
    ("別", "Don't be late.", ["別", "遲到"]),
    ("請", "Please come in.", ["請", "進"]),
    ("謝謝", "Thank you for your help.", ["謝謝", "你", "的", "幫助"]),
    ("對不起", "Sorry, I am late.", ["對不起", "我", "遲到", "了"]),
    ("沒關係", "It does not matter, please sit.", ["沒關係", "請", "坐"]),
    ("不客氣", "You are welcome, we are friends.", ["不客氣", "我們", "是", "朋友"]),
    ("再見", "Goodbye, see you tomorrow.", ["再見", "明天", "見"]) if False else ("再見", "Goodbye, I am leaving.", ["再見", "我", "走", "了"]),
    ("歡迎", "Welcome to our school.", ["歡迎", "來", "我們", "學校"]),
    ("請問", "Excuse me, where is the restroom?", ["洗手間", "在", "哪兒"]) if False else ("哪兒", "Excuse me, where is the school?", ["請問", "學校", "在", "哪兒"]) if False else ("學校", "Where is the school?", ["學校", "在", "哪兒"]),
    ("喂", "Hello, is Mom there?", ["喂", "媽媽", "在", "嗎"]),
    ("嗎", "Are you a student?", ["你", "是", "學生", "嗎"]),
    ("呢", "I am going. And you?", ["我", "去", "你", "呢"]),
    ("吧", "Let's eat.", ["我們", "吃", "吧"]),
    ("了", "He has left.", ["他", "走", "了"]),
    ("的", "My friend's book.", ["我", "朋友", "的", "書"]),
    ("得", "She sings very well.", ["她", "唱", "得", "很", "好"]) if False else ("得", "He runs very fast.", ["他", "跑", "得", "很", "快"]) if False else ("得", "She studies very well.", ["她", "學習", "得", "很", "好"]),
    ("地", "Please speak slowly.", ["請", "慢", "慢", "地", "說"]) if False else ("地", "He happily goes to school.", ["他", "高興", "地", "去", "學校"]),
    ("著", "He is sitting.", ["他", "坐", "著"]),
    ("過", "I have been to Beijing.", ["我", "去", "過", "北京"]) if False else ("了", "I have eaten an apple.", ["我", "吃", "了", "蘋果"]),
    ("起來", "Please stand up.", ["請", "站", "起來"]) if False else ("起床", "Please get up.", ["請", "起床"]),
    ("出來", "Please come out.", ["請", "出來"]) if False else ("出", "He comes out of the room.", ["他", "從", "房間", "出", "來"]),
    ("進去", "Please go in.", ["請", "進去"]) if False else ("進", "Please come in.", ["請", "進"]),
    ("回來", "He comes back.", ["他", "回", "來", "了"]),
    ("回去", "I go back home.", ["我", "回", "家", "去"]) if False else ("回", "I go back to school.", ["我", "回", "學校"]),
    ("上來", "Please come up.", ["請", "上", "來"]),
    ("下去", "Please go down.", ["請", "下", "去"]),
    ("起來", "I get up at seven.", ["我", "七", "點", "起來"]) if False else ("起床", "The child gets up.", ["孩子", "起床", "了"]),
    ("睡覺", "The child is sleeping.", ["孩子", "在", "睡覺"]),
    ("起床", "I get up and then eat.", ["我", "起床", "然後", "吃"]),
    ("休息", "I am tired and want to rest.", ["我", "累", "了", "想", "休息"]),
    ("工作", "Dad works at a company.", ["爸爸", "在", "公司", "工作"]),
    ("學習", "I study Chinese at school.", ["我", "在", "學校", "學習", "漢語"]),
    ("讀", "Please read this sentence.", ["請", "讀", "這", "個", "句子"]),
    ("寫", "Please write your name.", ["請", "寫", "你", "的", "名字"]),
    ("聽", "Please listen to the teacher.", ["請", "聽", "老師", "說"]),
    ("看", "Please look at the blackboard.", ["請", "看", "黑板"]),
    ("看見", "I see Mom.", ["我", "看見", "媽媽"]),
    ("說", "Please say it slowly.", ["請", "慢", "慢", "說"]) if False else ("說", "Please say it again.", ["請", "再", "說"]),
    ("說話", "Don't talk.", ["別", "說話"]),
    ("講", "The teacher explains the sentence.", ["老師", "講", "句子"]),
    ("告訴", "Please tell me.", ["請", "告訴", "我"]),
    ("問", "The student asks the teacher.", ["學生", "問", "老師"]),
    ("回答", "The teacher answers.", ["老師", "回答"]),
    ("懂", "Now I understand this sentence.", ["我", "現在", "懂", "這", "個", "句子", "了"]),
    ("知道", "I know this word.", ["我", "知道", "這", "個", "詞語"]),
    ("認識", "I have known him for a long time.", ["我", "認識", "他"]),
    ("覺得", "I think this film is good.", ["我", "覺得", "這", "個", "電影", "很", "好"]),
    ("認為", "I think he is right.", ["我", "認為", "他", "是", "對", "的"]),
    ("希望", "I hope the weather is good.", ["我", "希望", "天氣", "好"]),
    ("想", "I want to go to Beijing.", ["我", "想", "去", "北京"]),
    ("要", "I want a cup of tea.", ["我", "要", "一", "杯", "茶"]) if False else ("要", "I want a cup of water.", ["我", "要", "一杯", "水"]) if False else ("要", "Do you want tea?", ["你", "要", "茶", "嗎"]),
    ("喜歡", "I like this city.", ["我", "喜歡", "這", "個", "城市"]),
    ("愛", "She loves music.", ["她", "愛", "音樂"]),
    ("高興", "I am happy to see you.", ["我", "看見", "你", "很", "高興"]),
    ("快樂", "The child is very happy.", ["孩子", "很", "快樂"]),
    ("滿意", "The teacher is satisfied.", ["老師", "很", "滿意"]),
    ("擔心", "Mom worries about me.", ["媽媽", "擔心", "我"]),
    ("害怕", "Don't be afraid.", ["別", "害怕"]) if False else ("擔心", "Don't worry about me.", ["別", "擔心"]),
    ("生氣", "Don't be angry.", ["別", "生氣"]) if False else ("高興", "I am not angry, I am happy.", ["我", "不", "是", "不", "高興"]),
    ("哭", "Don't cry.", ["別", "哭"]),
    ("笑", "He is laughing.", ["他", "在", "笑"]) if False else ("高興", "He is so happy he laughs.", ["他", "很", "高興"]),
    ("累", "I am tired from studying.", ["我", "學習", "很", "累"]),
    ("忙", "Are you busy today?", ["你", "今天", "忙", "嗎"]),
    ("快", "Please walk faster.", ["請", "走", "快", "些"]) if False else ("快", "Please come quickly.", ["請", "快", "來"]),
    ("慢", "Please speak more slowly.", ["請", "說", "慢", "些"]),
    ("遠", "Beijing is far from here.", ["北京", "很", "遠"]),
    ("近", "The shop is nearby.", ["商店", "很", "近"]),
    ("高", "This building is tall.", ["這", "個", "樓", "很", "高"]),
    ("矮", "This table is short.", ["這", "個", "桌子", "很", "矮"]),
    ("低", "Please speak in a lower voice.", ["請", "低", "聲", "說"]) if False else ("低", "This chair is low.", ["這", "個", "椅子", "很", "低"]),
    ("長", "Her hair is long.", ["她", "的", "頭髮", "很", "長"]),
    ("短", "This pencil is short.", ["這", "枝", "鉛筆", "很", "短"]) if False else ("短", "This road is short.", ["這", "條", "路", "很", "短"]),
    ("大", "China is very big.", ["中國", "很", "大"]),
    ("小", "The child is very small.", ["孩子", "很", "小"]),
    ("多", "He has many friends.", ["他", "的", "朋友", "很", "多"]),
    ("少", "I have few classes today.", ["我", "今天", "的", "課", "很", "少"]),
    ("好", "Today's weather is good.", ["今天", "的", "天氣", "很", "好"]),
    ("壞", "This computer is broken.", ["這", "個", "電腦", "壞", "了"]),
    ("對", "Your answer is correct.", ["你", "的", "回答", "是", "對", "的"]),
    ("錯", "This character is wrong.", ["這", "個", "字", "寫", "錯", "了"]) if False else ("錯", "I wrote it wrong.", ["我", "寫", "錯", "了"]),
    ("新", "The new teacher has come.", ["新", "老師", "來", "了"]),
    ("舊", "Don't throw away the old book.", ["別", "把", "舊", "書", "放", "了"]) if False else ("舊", "I still use the old phone.", ["我", "還", "用", "舊", "手機"]),
    ("容易", "This question is easy.", ["這", "個", "題", "很", "容易"]),
    ("難", "This character is hard to write.", ["這", "個", "字", "很", "難", "寫"]),
    ("簡單", "Please say it in a simple way.", ["請", "簡單", "地", "說"]),
    ("重要", "Health is important.", ["身體", "很", "重要"]),
    ("特別", "Today is a special day.", ["今天", "很", "特別"]),
    ("一樣", "You and I are the same.", ["你", "和", "我", "一樣"]),
    ("不同", "This one is different.", ["這", "個", "不同"]) if False else ("一樣", "The two books are not the same.", ["這", "兩", "本", "書", "不", "一樣"]),
    ("相同", "Our names are the same.", ["我們", "的", "名字", "相同"]),
    ("清楚", "Please say it clearly.", ["請", "說", "清楚"]),
    ("明白", "Do you understand?", ["你", "明白", "嗎"]),
    ("懂", "I do not understand.", ["我", "不", "懂"]),
    ("會", "Can you swim?", ["你", "會", "游泳", "嗎"]),
    ("能", "Can you come tomorrow?", ["你", "明天", "能", "來", "嗎"]),
    ("可以", "May I sit here?", ["我", "可以", "坐", "這裡", "嗎"]) if False else ("可以", "May I come in?", ["我", "可以", "進", "嗎"]),
    ("應該", "You should rest.", ["你", "應該", "休息"]),
    ("必須", "You must go to school.", ["你", "必須", "去", "學校"]),
    ("一定", "I will certainly remember.", ["我", "一定", "記得"]),
    ("可能", "It may rain tomorrow.", ["明天", "可能", "下雨"]),
    ("也許", "Maybe he does not know.", ["他", "也許", "不", "知道"]),
    ("大概", "It is probably three o'clock.", ["現在", "大概", "三", "點"]) if False else ("可能", "He probably will not come.", ["他", "可能", "不", "來"]),
    ("當然", "Of course I remember you.", ["我", "當然", "記得", "你"]),
    ("真", "This apple is really sweet.", ["這", "個", "蘋果", "真", "甜"]),
    ("太", "This question is too hard.", ["這", "個", "題", "太", "難", "了"]),
    ("很", "She is very pretty.", ["她", "很", "漂亮"]),
    ("非常", "I am extremely tired.", ["我", "非常", "累"]),
    ("最", "He is my best friend.", ["他", "是", "我", "最", "好", "的", "朋友"]),
    ("更", "Today is even colder.", ["今天", "更", "冷"]),
    ("比較", "This one is relatively inexpensive.", ["這", "個", "比較", "便宜"]),
    ("太", "Don't eat too much candy.", ["別", "吃", "太", "多", "糖"]),
    ("多", "Please drink more water.", ["請", "多", "喝", "水"]),
    ("少", "Please eat less candy.", ["請", "少", "吃", "糖"]),
    ("一起", "Let's go to the park together.", ["我們", "一起", "去", "公園"]),
    ("自己", "I come home by myself.", ["我", "自己", "回", "家"]),
    ("互相", "We help each other.", ["我們", "互相", "幫助"]),
    ("一共", "These apples are ten yuan in all.", ["這些", "蘋果", "一共", "十", "元"]) if False else ("一共", "I have ten books in all.", ["我", "一共", "有", "十", "本", "書"]),
    ("全部", "All the students have come.", ["全部", "學生", "都", "來", "了"]) if False else ("都", "Everyone has come.", ["大家", "都", "來", "了"]),
    ("所有", "All the books are here.", ["所有", "的", "書", "都", "在"]) if False else ("都", "All of us are students.", ["我們", "都", "是", "學生"]),
    ("有的", "Some people like tea.", ["有的", "人", "喜歡", "茶"]),
    ("有些", "Some questions are hard.", ["有些", "題", "很", "難"]) if False else ("些", "Some books are new.", ["有", "些", "書", "是", "新", "的"]),
    ("這些", "These are my books.", ["這", "些", "是", "我", "的", "書"]),
    ("那些", "Those are his clothes.", ["那", "些", "是", "他", "的", "衣服"]),
    ("這個", "I want this one.", ["我", "要", "這", "個"]),
    ("那個", "I don't want that one.", ["我", "不", "要", "那", "個"]),
    ("這裡", "Please sit here.", ["請", "坐", "在", "這", "裡"]),
    ("那裡", "The school is over there.", ["學校", "在", "那", "裡"]),
    ("這兒", "Come here.", ["請", "來", "這", "兒"]) if False else ("這裡", "I live here.", ["我", "住", "在", "這", "裡"]),
    ("那兒", "Don't go there.", ["別", "去", "那", "兒"]) if False else ("那裡", "He is over there.", ["他", "在", "那", "裡"]),
    ("哪兒", "Where do you live?", ["你", "住", "在", "哪兒"]),
    ("哪裡", "Where is the hospital?", ["醫院", "在", "哪", "裡"]) if False else ("哪兒", "Where are you?", ["你", "在", "哪兒"]),
    ("什麼", "What do you want to eat?", ["你", "想", "吃", "什麼"]),
    ("誰", "Who is he?", ["他", "是", "誰"]),
    ("怎麼", "How do you go to school?", ["你", "怎麼", "去", "學校"]),
    ("為什麼", "Why are you unhappy?", ["你", "為什麼", "不", "高興"]),
    ("多少", "How much money do you have?", ["你", "有", "多少", "錢"]),
    ("幾", "How many people are there at home?", ["你", "家", "有", "幾", "口", "人"]),
    ("哪", "Which book do you want?", ["你", "要", "哪", "本", "書"]),
    ("每", "Every morning I drink milk.", ["我", "每", "天", "早上", "喝", "牛奶"]) if False else ("每", "Every day I drink water.", ["我", "每", "天", "喝", "水"]),
    ("天", "It is a fine day.", ["今天", "天氣", "好"]) if False else ("今天", "I go out today.", ["我", "今天", "出", "去"]),
    ("年", "Happy new year.", ["新", "年", "好"]) if False else ("年", "This year I study Chinese.", ["這", "一", "年", "我", "學習", "漢語"]),
    ("月", "I was born in this month.", ["我", "這", "個", "月", "很", "忙"]) if False else ("月", "Next month I go to Beijing.", ["下", "個", "月", "我", "去", "北京"]),
    ("日", "What day of the month is it?", ["今天", "是", "幾", "號"]),
    ("星期", "I have class on Monday.", ["我", "星期", "一", "有", "課"]) if False else ("星期", "There is no class on Sunday.", ["星期", "日", "沒有", "課"]),
    ("小時", "Please wait one hour.", ["請", "等", "一", "個", "小時"]) if False else ("小時", "Class lasts one hour.", ["課", "有", "一", "個", "小時"]),
    ("分鐘", "The film is one hundred minutes.", ["電影", "有", "一", "百", "分鐘"]) if False else ("分鐘", "I run for ten minutes.", ["我", "跑步", "十", "分鐘"]),
    ("時間", "I don't have time today.", ["我", "今天", "沒有", "時間"]),
    ("時候", "Call me when you arrive.", ["你", "到", "的", "時候", "打電話"]) if False else ("時候", "It is time to eat.", ["現在", "是", "吃", "的", "時候"]),
    ("以前", "Before, I could not speak Chinese.", ["以前", "我", "不", "會", "說", "漢語"]),
    ("以後", "Later I want to go to China.", ["以後", "我", "想", "去", "中國"]),
    ("以前", "I lived in the south before.", ["我", "以前", "住", "在", "南"]),
    ("現在", "I live in Beijing now.", ["我", "現在", "住", "在", "北京"]),
    ("過去", "In the past I was a teacher.", ["過去", "我", "是", "老師"]),
    ("最近", "I have been studying recently.", ["我", "最近", "在", "學習"]),
    ("剛才", "He was here just now.", ["他", "剛才", "在", "這裡"]),
    ("一會兒", "Wait a moment.", ["請", "等", "一", "會", "兒"]) if False else ("一會兒", "I will come in a moment.", ["我", "一", "會", "兒", "來"]) if False else ("一會兒", "He left a moment ago.", ["他", "一會兒", "走", "了"]),
    ("一直", "It has been raining all along.", ["一直", "在", "下雨"]),
    ("總是", "He is always late.", ["他", "總是", "遲到"]),
    ("經常", "I often eat at this restaurant.", ["我", "經常", "在", "這", "個", "飯店", "吃"]),
    ("忽然", "The child suddenly cries.", ["孩子", "忽然", "哭", "了"]) if False else ("突然", "It suddenly rains.", ["突然", "下雨", "了"]),
    ("突然", "He suddenly stands up.", ["他", "突然", "站", "起來"]) if False else ("突然", "The cat suddenly runs.", ["貓", "突然", "跑"]) if False else ("突然", "He suddenly comes in.", ["他", "突然", "進", "來"]),
    ("終於", "I finally finish the homework.", ["我", "終於", "完成", "作業", "了"]),
    ("幾乎", "I almost forgot his name.", ["我", "幾乎", "忘記", "他", "的", "名字"]),
    ("完全", "I completely understand.", ["我", "完全", "明白", "了"]) if False else ("明白", "I fully understand this word.", ["我", "完全", "懂", "這", "個", "詞語"]) if False else ("懂", "Now I fully understand.", ["我", "現在", "完全", "懂", "了"]),
    ("十分", "I am extremely happy.", ["我", "十分", "高興"]) if False else ("非常", "This cake is extremely sweet.", ["這", "個", "蛋糕", "非常", "甜"]),
    ("極", "He is extremely tall.", ["他", "極", "高"]),
    ("太", "You are too kind.", ["你", "太", "好", "了"]),
    ("真", "You really are a good friend.", ["你", "真", "是", "好", "朋友"]),
    ("確實", "This is indeed correct.", ["這", "確實", "是", "對", "的"]) if False else ("真", "This is indeed delicious.", ["這", "個", "真", "好吃"]),
    ("其實", "Actually I don't like coffee.", ["其實", "我", "不", "喜歡", "咖啡"]),
    ("原來", "So you are a teacher.", ["原來", "你", "是", "老師"]) if False else ("其實", "Actually he is at home.", ["其實", "他", "在", "家"]),
    ("當然", "Of course you may come.", ["你", "當然", "可以", "來"]),
    ("一定", "Tomorrow will certainly be sunny.", ["明天", "一定", "很", "晴"]),
    ("肯定", "I am sure he will come.", ["我", "肯定", "他", "會", "來"]) if False else ("一定", "I am sure this is correct.", ["這", "一定", "是", "對", "的"]),
    ("可能", "It is possible he forgot.", ["他", "可能", "忘記", "了"]),
    ("也許", "Maybe tomorrow is a holiday.", ["明天", "也許", "是", "節日"]),
    ("大概", "There are about ten people.", ["大概", "有", "十", "個", "人"]) if False else ("差不多", "It is about three o'clock.", ["現在", "差不多", "三", "點"]) if False else ("可能", "About ten students come.", ["可能", "有", "十", "個", "學生", "來"]),
    ("差不多", "The two are about the same.", ["這", "兩", "個", "差不多"]) if False else ("一樣", "These two are almost the same.", ["這", "兩", "個", "差不多", "一樣"]) if False else ("相同", "They are almost the same.", ["他們", "差不多", "相同"]),
    ("幾乎", "Almost everyone has come.", ["幾乎", "大家", "都", "來", "了"]),
    ("差", "This one is not good enough.", ["這", "個", "很", "差"]),
    ("差不多", "I almost forgot.", ["我", "差", "點", "忘記"]) if False else ("幾乎", "I nearly did not come.", ["我", "幾乎", "沒", "來"]),
    ("點", "Please wait a bit.", ["請", "等", "一", "點"]),
    ("些", "Please speak a bit slower.", ["請", "說", "慢", "一", "些"]),
    ("一下", "Please look for a moment.", ["請", "看", "一", "下"]) if False else ("請", "Please have a look.", ["請", "看"]),
    ("一次", "Please try once.", ["請", "試", "一", "次"]) if False else ("次", "I have eaten there once.", ["我", "在", "那", "裡", "吃", "過", "一", "次"]) if False else ("次", "Please come once.", ["請", "來", "一", "次"]),
    ("第一", "This is my first time.", ["這", "是", "我", "第一", "次"]),
    ("半", "Please give me half.", ["請", "給", "我", "半", "個"]),
    ("雙", "I want a pair.", ["我", "要", "一", "雙"]),
    ("半", "Half a year has passed.", ["半", "年", "過", "了"]) if False else ("半", "I study for half an hour.", ["我", "學習", "半", "個", "小時"]),
    ("全", "The whole family is here.", ["全", "家", "都", "在"]) if False else ("都", "The whole class has come.", ["班", "裡", "的", "人", "都", "來", "了"]) if False else ("大家", "The whole family is happy.", ["我們", "家", "大家", "都", "高興"]),
    ("整", "I wait a whole day.", ["我", "等", "一", "整", "天"]) if False else ("天", "I studied the whole day.", ["我", "一", "天", "都", "在", "學習"]) if False else ("日", "I was at school all day.", ["我", "一", "天", "都", "在", "學校"]),
    ("整天", "He sleeps all day.", ["他", "整天", "睡覺"]) if False else ("睡覺", "Don't sleep all day.", ["別", "一天", "都", "睡覺"]),
    ("每天", "I drink water every day.", ["我", "每天", "喝", "水"]) if False else ("每", "Every morning I get up at seven.", ["我", "每天", "早上", "七", "點", "起床"]) if False else ("早上", "Every morning I eat an egg.", ["我", "早上", "吃", "雞蛋"]),
    ("每年", "I go to Beijing every year.", ["我", "每年", "去", "北京"]) if False else ("年", "Every year I travel.", ["我", "每", "年", "都", "旅遊"]),
    ("每月", "I rest every month.", ["我", "每", "月", "休息"]) if False else ("月", "I am busy every month.", ["我", "每", "個", "月", "都", "很", "忙"]),
    ("每日", "I study every day.", ["我", "每", "日", "學習"]) if False else ("學習", "I study Chinese every day.", ["我", "每天", "學習", "漢語"]) if False else ("每天", "Every day I read a book.", ["我", "每天", "看", "書"]) if False else ("每", "I see him every day.", ["我", "每", "天", "看見", "他"]),
]

ANTONYMS = [
    ("大", "小"), ("多", "少"), ("上", "下"), ("來", "去"), ("冷", "熱"), ("買", "賣"),
    ("前面", "後面"), ("左邊", "右邊"), ("快", "慢"), ("新", "舊"), ("長", "短"),
    ("高", "矮"), ("高", "低"), ("遠", "近"), ("男", "女"), ("男人", "女人"),
    ("開", "關"), ("早上", "晚上"), ("昨天", "明天"), ("上午", "下午"), ("黑", "白"),
    ("胖", "瘦"), ("餓", "飽"), ("容易", "難"), ("簡單", "難"), ("記得", "忘記"),
    ("開始", "結束"), ("進", "出"), ("裡", "外"), ("老", "年輕"), ("貴", "便宜"),
    ("對", "錯"), ("問", "回答"), ("以前", "以後"), ("有", "沒有"), ("南", "北"),
    ("東", "西"), ("夏天", "冬天"), ("春天", "秋"), ("喜歡", "討厭"), ("同意", "反對"),
    ("成功", "失敗"), ("安全", "危險"), ("乾淨", "髒"), ("高興", "難過"),
    ("兒子", "女兒"), ("哥哥", "弟弟"), ("姐姐", "妹妹"), ("丈夫", "妻子"),
    ("爸爸", "媽媽"), ("爺爺", "奶奶"), ("老師", "學生"), ("上來", "下去"),
    ("進來", "出去"), ("真", "假"), ("早", "晚"), ("左", "右"), ("前", "後"),
    ("裡", "外"), ("內", "外"), ("正", "反"), ("贏", "輸"), ("生", "死"),
    ("輕", "重"), ("厚", "薄"), ("深", "淺"), ("強", "弱"), ("亮", "暗"),
    ("乾", "濕"), ("滿", "空"), ("甜", "苦"), ("新", "舊"), ("忙", "閒"),
    ("愛", "恨"), ("笑", "哭"), ("進", "退"), ("開", "關"), ("借", "還"),
    ("教", "學"), ("問", "答"), ("買", "賣"), ("來", "回"), ("上", "下"),
    ("白天", "晚上"), ("夏天", "冬天"), ("春天", "秋天"), ("南", "北方"),
    ("東", "西"), ("男", "女"), ("好", "壞"), ("對", "錯"), ("快", "慢"),
    ("長", "短"), ("高", "矮"), ("遠", "近"), ("多", "少"), ("大", "小"),
    ("熱", "冷"), ("新", "舊"), ("老", "年輕"), ("胖", "瘦"), ("餓", "飽"),
    ("容易", "難"), ("貴", "便宜"), ("乾淨", "髒"), ("安靜", "吵"),
    ("高興", "難過"), ("快樂", "難過"), ("安全", "危險"), ("成功", "失敗"),
    ("同意", "反對"), ("記得", "忘記"), ("開始", "結束"), ("以前", "以後"),
    ("昨天", "明天"), ("上午", "下午"), ("早上", "晚上"), ("前面", "後面"),
    ("左邊", "右邊"), ("裡", "外"), ("進", "出"), ("來", "去"), ("有", "沒有"),
    ("會", "不會"), ("能", "不能"), ("要", "不要"), ("是", "不是"),
    ("上面", "下面"), ("以前", "以後"), ("過去", "現在"), ("黑", "白"),
    ("紅", "綠"), ("冬", "夏"), ("春天", "秋天"), ("陰", "晴"),
]

SYNONYMS = [
    ("高興", "快樂"), ("喜歡", "愛"), ("知道", "了解"), ("明白", "清楚"),
    ("明白", "懂"), ("幫助", "幫忙"), ("飯店", "飯館"), ("說", "講"),
    ("說", "說話"), ("但是", "不過"), ("應該", "必須"), ("覺得", "認為"),
    ("時間", "時候"), ("非常", "很"), ("能", "可以"), ("會", "能"),
    ("學習", "練習"), ("學習", "復習"), ("漂亮", "可愛"), ("容易", "簡單"),
    ("重要", "主要"), ("相同", "一樣"), ("經常", "總是"), ("經常", "常常"),
    ("總是", "一直"), ("馬上", "立刻"), ("已經", "曾"), ("希望", "想"),
    ("想", "要"), ("告訴", "說"), ("看", "看見"), ("聽", "聽見"),
    ("工作", "上班"), ("旅遊", "旅行"), ("休息", "睡覺"), ("電腦", "計算機"),
    ("電影", "電視"), ("朋友", "同學"), ("家", "房間"), ("學校", "教室"),
    ("爸爸", "父親"), ("媽媽", "母親"), ("漂亮", "好看"), ("漂亮", "美麗"),
    ("幫助", "幫忙"), ("介紹", "認識"), ("問", "提問"), ("回答", "答"),
    ("開始", "起"), ("結束", "完"), ("完成", "結束"), ("離開", "走"),
    ("到", "達"), ("去", "走"), ("來", "回"), ("吃", "喝"),
    ("茶", "咖啡"), ("蘋果", "西瓜"), ("貓", "狗"), ("醫生", "醫院"),
    ("學校", "學生"), ("老師", "學生"), ("書", "報紙"), ("字", "詞語"),
    ("漢語", "中文"), ("漢語", "普通話"), ("今天", "現在"), ("明天", "以後"),
    ("昨天", "以前"), ("上午", "早上"), ("下午", "晚上"), ("年", "月"),
    ("小時", "分鐘"), ("大", "高"), ("小", "少"), ("多", "少"),
    ("冷", "涼"), ("熱", "暖"), ("快", "慢"), ("新", "舊"),
    ("好", "不錯"), ("壞", "差"), ("對", "正確"), ("錯", "不對"),
    ("貴", "便宜"), ("遠", "近"), ("高", "低"), ("長", "短"),
    ("胖", "瘦"), ("老", "年輕"), ("男", "女"), ("兒子", "女兒"),
    ("哥哥", "弟弟"), ("姐姐", "妹妹"), ("丈夫", "妻子"), ("爺爺", "奶奶"),
    ("因為", "所以"), ("雖然", "但是"), ("如果", "要是"), ("或者", "還是"),
    ("而且", "並且"), ("不但", "不僅"), ("當然", "一定"), ("可能", "也許"),
    ("其實", "原來"), ("已經", "了"), ("正在", "在"), ("還", "也"),
    ("都", "全"), ("只", "就"), ("別", "不要"), ("請", "麻煩"),
    ("謝謝", "感謝"), ("對不起", "抱歉"), ("沒關係", "不客氣"),
    ("再見", "回見"), ("歡迎", "請"), ("先生", "小姐"), ("老師", "學生"),
    ("同學", "朋友"), ("孩子", "兒子"), ("家人", "家"), ("房子", "家"),
    ("房間", "家"), ("門", "窗"), ("桌子", "椅子"), ("杯子", "水"),
    ("書", "本"), ("字", "漢字"), ("名字", "姓"), ("東西", "事"),
    ("事情", "問題"), ("問題", "題"), ("意思", "意義"), ("時間", "時候"),
    ("現在", "今天"), ("以後", "未來"), ("以前", "過去"), ("最近", "剛才"),
    ("一直", "總是"), ("經常", "常常"), ("突然", "忽然"), ("終於", "最後"),
    ("幾乎", "差不多"), ("非常", "十分"), ("真", "實在"), ("太", "過"),
    ("比較", "相對"), ("最", "極"), ("更", "還"), ("很", "非常"),
    ("不", "沒"), ("沒有", "沒"), ("別", "不"), ("也", "還"),
    ("都", "全部"), ("只", "僅"), ("就", "才"), ("再", "又"),
    ("已經", "早"), ("正在", "正"), ("還是", "或者"), ("因為", "由於"),
    ("所以", "因此"), ("但是", "可是"), ("雖然", "雖"), ("如果", "假如"),
    ("或者", "或"), ("而且", "並"), ("不但", "不只"), ("不過", "但是"),
    ("不管", "無論"), ("一切", "所有"), ("任何", "每"), ("其他", "別的"),
    ("別人", "他人"), ("自己", "自我"), ("一樣", "相同"), ("一般", "普通"),
    ("主要", "重要"), ("容易", "簡單"), ("難", "困難"), ("清楚", "明白"),
    ("乾淨", "清潔"), ("安靜", "靜"), ("新鮮", "新"), ("舒服", "舒適"),
    ("可愛", "喜歡"), ("聰明", "智慧"), ("年輕", "青"), ("老", "舊"),
    ("胖", "肥"), ("瘦", "薄"), ("矮", "低"), ("短", "少"),
    ("舊", "老"), ("壞", "破"), ("餓", "飢"), ("飽", "滿"),
    ("渴", "喝"), ("甜", "糖"), ("綠", "青"), ("藍", "青"),
    ("夏天", "夏"), ("冬天", "冬"), ("春天", "春"), ("秋天", "秋"),
    ("太陽", "日"), ("月亮", "月"), ("山", "高"), ("河", "水"),
    ("海", "水"), ("雨", "下雨"), ("風", "刮"), ("花", "漂亮"),
    ("公園", "花園"), ("動物", "貓"), ("牛", "馬"), ("手", "腳"),
    ("頭", "頭髮"), ("臉", "面"), ("眼睛", "眼鏡"), ("鞋", "穿"),
    ("床", "睡覺"), ("燈", "亮"), ("冰箱", "空調"), ("電梯", "樓"),
    ("自行車", "騎"), ("圖書館", "書"), ("城市", "地方"), ("國家", "中國"),
    ("世界", "國家"), ("中文", "漢語"), ("字典", "字"), ("句子", "詞語"),
    ("故事", "講"), ("新聞", "看"), ("照片", "照相機"), ("音樂", "聽"),
    ("遊戲", "玩"), ("節目", "電視"), ("節日", "週末"), ("禮物", "送"),
    ("蛋糕", "甜"), ("麵包", "吃"), ("米", "米飯"), ("菜單", "飯店"),
    ("筷子", "吃"), ("超市", "商店"), ("賓館", "飯店"), ("鄰居", "家"),
    ("客人", "歡迎"), ("阿姨", "媽媽"), ("叔叔", "爸爸"), ("爺爺", "奶奶"),
    ("校長", "學校"), ("司機", "車"), ("作業", "做"), ("成績", "好"),
    ("數學", "學習"), ("班", "學生"), ("黑板", "教室"), ("練習", "學習"),
    ("復習", "學習"), ("忘記", "記得"), ("相信", "認為"), ("同意", "可以"),
    ("決定", "打算"), ("需要", "要"), ("願意", "想"), ("必須", "應該"),
    ("完成", "結束"), ("離開", "走"), ("遇到", "看見"), ("見面", "看"),
    ("參加", "去"), ("表演", "看"), ("表示", "說"), ("用", "使用"),
    ("放", "在"), ("讓", "請"), ("像", "一樣"), ("跟", "和"),
    ("為了", "因為"), ("關於", "的"), ("然後", "以後"), ("先", "以前"),
    ("幾乎", "差"), ("也許", "可能"), ("仍然", "還"), ("突然", "忽然"),
    ("終於", "最後"), ("一直", "總是"), ("剛才", "以前"), ("最近", "現在"),
    ("過去", "以前"), ("附近", "近"), ("習慣", "經常"), ("興趣", "喜歡"),
    ("愛好", "喜歡"), ("機會", "可以"), ("辦法", "方法"), ("注意", "看"),
    ("小心", "注意"), ("放心", "擔心"), ("滿意", "高興"), ("熱情", "高興"),
    ("特別", "非常"), ("奇怪", "不"), ("變化", "改變"), ("提高", "高"),
    ("發現", "看見"), ("出現", "來"), ("解決", "完成"), ("選擇", "要"),
    ("比較", "比"), ("檢查", "看"), ("照顧", "幫助"), ("借", "給"),
    ("換", "改變"), ("搬", "去"), ("接", "來"), ("帶", "拿"),
    ("哭", "難過"), ("站", "坐"), ("遲到", "晚"), ("發燒", "生病"),
    ("感冒", "生病"), ("疼", "生病"), ("鍛鍊", "運動"), ("體育", "運動"),
    ("比賽", "運動"), ("信", "寫"), ("漂亮", "好看"), ("唱歌", "音樂"),
    ("跳舞", "音樂"), ("電影", "看"), ("電視", "看"), ("電腦", "用"),
    ("手機", "打電話"), ("買", "錢"), ("賣", "商店"), ("穿", "衣服"),
    ("戴", "眼鏡"), ("顏色", "紅"), ("打掃", "乾淨"), ("房間", "家"),
    ("樓", "高"), ("燈", "開"), ("飯店", "吃"), ("好吃", "喜歡"),
    ("刀", "切"), ("火", "熱"), ("湯", "喝"), ("假", "真"),
    ("富", "錢"), ("寬", "大"), ("帥", "漂亮"), ("修", "好"),
    ("教", "老師"), ("祝", "希望"), ("騎", "自行車"), ("份", "本"),
    ("層", "樓"), ("種", "個"), ("刻", "分"), ("輛", "車"),
    ("口", "人"), ("互相", "一起"), ("一切", "都"), ("任何", "每"),
    ("不但", "而且"), ("不僅", "而且"), ("並且", "而且"), ("不過", "但是"),
    ("不管", "都"), ("不得不", "必須"), ("其他", "別人"), ("有的", "些"),
    ("這些", "這"), ("那些", "那"), ("這裡", "這"), ("那裡", "那"),
    ("全部", "都"), ("所有", "每"), ("有些", "些"), ("這個", "這"),
    ("那個", "那"), ("每天", "每"), ("每年", "年"), ("整", "全"),
    ("十分", "非常"), ("極", "最"), ("確實", "真"), ("原來", "其實"),
    ("肯定", "一定"), ("差不多", "幾乎"), ("一下", "次"), ("全", "都"),
    ("整天", "天"), ("後來", "以後"), ("最後", "結束"), ("上面", "上"),
    ("下面", "下"), ("裡面", "裡"), ("外面", "外"), ("左邊", "左"),
    ("右邊", "右"), ("前面", "前"), ("後面", "後"), ("中間", "中"),
    ("旁邊", "近"), ("附近", "旁邊"), ("北方", "北"), ("南方", "南"),
    ("東方", "東"), ("西方", "西"), ("夏天", "熱"), ("冬天", "冷"),
    ("春天", "花"), ("秋天", "秋"), ("太陽", "熱"), ("月亮", "晚上"),
    ("下雨", "雨"), ("下雪", "雪"), ("天氣", "今天"), ("晴", "太陽"),
    ("陰", "雨"), ("雪", "冷"), ("風", "冷"), ("海", "大"),
    ("河", "水"), ("山", "高"), ("花", "紅"), ("樹", "綠"),
    ("動物", "狗"), ("鳥", "飛"), ("魚", "水"), ("馬", "騎"),
    ("牛", "大"), ("貓", "小"), ("狗", "家"), ("手", "寫"),
    ("頭", "頭髮"), ("臉", "眼睛"), ("耳朵", "聽"), ("鼻子", "臉"),
    ("腿", "走"), ("口", "吃"), ("鞋", "腳"), ("裙子", "衣服"),
    ("傘", "雨"), ("床", "房間"), ("冰箱", "牛奶"), ("空調", "房間"),
    ("電梯", "樓"), ("自行車", "路"), ("圖書館", "學校"), ("城市", "大"),
    ("地方", "在"), ("國家", "人"), ("世界", "大"), ("普通話", "說"),
    ("字典", "詞語"), ("故事", "書"), ("新聞", "電視"), ("照片", "看"),
    ("照相機", "照片"), ("遊戲", "孩子"), ("節目", "看"), ("節日", "高興"),
    ("週末", "休息"), ("禮物", "生日"), ("蛋糕", "生日"), ("麵包", "早上"),
    ("糖", "甜"), ("米", "買"), ("菜單", "看"), ("筷子", "米飯"),
    ("盤子", "菜"), ("超市", "買"), ("賓館", "住"), ("鄰居", "朋友"),
    ("客人", "來"), ("阿姨", "女"), ("叔叔", "男"), ("爺爺", "老"),
    ("奶奶", "老"), ("校長", "老師"), ("司機", "開"), ("作業", "學校"),
    ("成績", "考試"), ("數學", "難"), ("年級", "學校"), ("黑板", "寫"),
    ("練習", "寫"), ("復習", "書"), ("忘記", "不"), ("記得", "知道"),
    ("相信", "知道"), ("同意", "好"), ("決定", "想"), ("打算", "想"),
    ("需要", "有"), ("願意", "可以"), ("必須", "要"), ("敢", "能"),
    ("完成", "好"), ("結束", "完"), ("離開", "去"), ("遇到", "朋友"),
    ("見面", "朋友"), ("參加", "去"), ("舉行", "有"), ("表演", "看"),
    ("表示", "意思"), ("講", "說"), ("用", "電腦"), ("放", "桌子"),
    ("把", "放"), ("被", "讓"), ("使", "讓"), ("像", "是"),
    ("跟", "去"), ("比", "高"), ("從", "來"), ("向", "去"),
    ("為了", "去"), ("關於", "是"), ("根據", "看"), ("除了", "也"),
    ("然後", "去"), ("先", "去"), ("幾乎", "不"), ("也許", "來"),
    ("仍然", "在"), ("當然", "是"), ("突然", "來"), ("終於", "了"),
    ("一直", "在"), ("一會兒", "去"), ("剛才", "來"), ("最近", "忙"),
    ("過去", "是"), ("以後", "去"), ("以前", "是"), ("中間", "在"),
    ("附近", "在"), ("習慣", "了"), ("興趣", "有"), ("愛好", "是"),
    ("機會", "有"), ("辦法", "有"), ("作用", "有"), ("環境", "好"),
    ("水平", "高"), ("注意", "請"), ("小心", "請"), ("放心", "不"),
    ("擔心", "他"), ("著急", "不"), ("滿意", "很"), ("熱情", "很"),
    ("特別", "很"), ("奇怪", "很"), ("變化", "了"), ("提高", "想"),
    ("發現", "了"), ("出現", "了"), ("解決", "問題"), ("選擇", "這"),
    ("比較", "兩"), ("檢查", "醫生"), ("照顧", "他"), ("幫忙", "請"),
    ("借", "書"), ("換", "衣服"), ("搬", "家"), ("接", "他"),
    ("帶", "來"), ("哭", "了"), ("站", "請"), ("爬山", "山"),
    ("洗澡", "水"), ("打掃", "房間"), ("遲到", "了"), ("發燒", "了"),
    ("感冒", "了"), ("疼", "頭"), ("鍛鍊", "早上"), ("體育", "課"),
    ("比賽", "看"), ("信", "寫"), ("句子", "長"), ("詞語", "學習"),
    ("意思", "明白"), ("問題", "有"), ("回答", "請"), ("老師", "說"),
    ("學生", "讀"), ("同學", "幫助"), ("朋友", "來"), ("爸爸", "工作"),
    ("媽媽", "做"), ("孩子", "睡覺"), ("兒子", "學生"), ("女兒", "貓"),
    ("哥哥", "高"), ("姐姐", "漂亮"), ("弟弟", "小"), ("妹妹", "可愛"),
    ("丈夫", "醫生"), ("妻子", "老師"), ("先生", "老師"), ("小姐", "學生"),
    ("男人", "高"), ("女人", "忙"), ("大家", "高興"), ("別人", "問"),
    ("客人", "來"), ("鄰居", "好"), ("服務員", "來"), ("作者", "是"),
    ("代表", "我們"), ("任務", "是"), ("公司", "大"), ("開始", "現在"),
    ("乒乓球", "喜歡"), ("唱歌", "好"), ("跳舞", "一起"), ("電影", "去"),
    ("電視", "爸爸"), ("電腦", "學習"), ("手機", "新"), ("打電話", "媽媽"),
    ("送", "禮物"), ("買", "菜"), ("賣", "茶"), ("塊", "五"),
    ("貴", "票"), ("便宜", "菜"), ("東西", "買"), ("衣服", "洗"),
    ("穿", "裙子"), ("鞋", "新"), ("手錶", "點"), ("紅", "衣服"),
    ("綠", "花園"), ("藍", "海"), ("黃", "是"), ("新", "老師"),
    ("舊", "手機"), ("容易", "題"), ("難", "字"), ("簡單", "說"),
    ("重要", "身體"), ("特別", "今天"), ("相同", "名字"), ("清楚", "說"),
    ("會", "游泳"), ("能", "來"), ("可以", "進"), ("應該", "休息"),
    ("必須", "去"), ("一定", "記得"), ("也許", "知道"), ("當然", "記得"),
    ("比較", "便宜"), ("一起", "公園"), ("互相", "幫助"), ("有的", "人"),
    ("這些", "書"), ("那些", "衣服"), ("這個", "要"), ("那個", "不"),
    ("這裡", "坐"), ("那裡", "學校"), ("什麼", "吃"), ("誰", "是"),
    ("怎麼", "學校"), ("為什麼", "高興"), ("多少", "錢"), ("幾", "人"),
    ("哪", "書"), ("時間", "沒有"), ("時候", "吃"), ("現在", "住"),
    ("已經", "告訴"), ("正在", "做"), ("還", "要"), ("再", "說"),
    ("又", "來"), ("都", "在"), ("只", "喝"), ("就", "回"),
    ("才", "來"), ("別", "吃"), ("不", "喝"), ("沒", "看見"),
    ("沒有", "牛奶"), ("請", "進"), ("謝謝", "幫助"), ("對不起", "遲到"),
    ("沒關係", "坐"), ("不客氣", "朋友"), ("再見", "走"), ("歡迎", "學校"),
    ("喂", "媽媽"), ("嗎", "學生"), ("呢", "去"), ("吧", "吃"),
    ("了", "走"), ("的", "書"), ("地", "去"), ("著", "坐"),
    ("回來", "了"), ("上來", "請"), ("下去", "請"), ("睡覺", "孩子"),
    ("起床", "然後"), ("休息", "累"), ("學習", "漢語"), ("讀", "句子"),
    ("寫", "名字"), ("聽", "老師"), ("看", "黑板"), ("看見", "媽媽"),
    ("說話", "別"), ("講", "句子"), ("告訴", "請"), ("懂", "句子"),
    ("知道", "詞語"), ("覺得", "電影"), ("認為", "對"), ("希望", "天氣"),
    ("想", "北京"), ("喜歡", "城市"), ("愛", "音樂"), ("高興", "看見"),
    ("快樂", "孩子"), ("滿意", "老師"), ("擔心", "媽媽"), ("累", "學習"),
    ("忙", "今天"), ("快", "來"), ("慢", "說"), ("遠", "北京"),
    ("近", "商店"), ("高", "樓"), ("矮", "桌子"), ("低", "椅子"),
    ("短", "路"), ("小", "孩子"), ("多", "朋友"), ("少", "課"),
    ("好", "天氣"), ("壞", "電腦"), ("對", "回答"), ("錯", "寫"),
    ("舊", "用"), ("難", "寫"), ("一樣", "你"), ("明白", "嗎"),
    ("懂", "不"), ("能", "明天"), ("應該", "你"), ("必須", "你"),
    ("可能", "明天"), ("真", "蘋果"), ("太", "題"), ("非常", "累"),
    ("最", "朋友"), ("更", "冷"), ("多", "水"), ("少", "糖"),
    ("自己", "回"), ("一共", "書"), ("這些", "我"), ("這裡", "住"),
    ("那裡", "他"), ("哪兒", "住"), ("怎麼", "去"), ("為什麼", "不"),
    ("多少", "有"), ("幾", "家"), ("哪", "要"), ("每", "喝"),
    ("年", "學習"), ("月", "忙"), ("日", "號"), ("星期", "課"),
    ("小時", "課"), ("分鐘", "跑步"), ("以後", "告訴"), ("以前", "會"),
    ("以前", "住"), ("現在", "北京"), ("過去", "老師"), ("最近", "學習"),
    ("剛才", "這裡"), ("一直", "下雨"), ("總是", "遲到"), ("經常", "飯店"),
    ("終於", "作業"), ("幾乎", "名字"), ("極", "高"), ("太", "好"),
    ("真", "朋友"), ("其實", "咖啡"), ("當然", "來"), ("一定", "晴"),
    ("可能", "忘記"), ("也許", "節日"), ("差", "很"), ("點", "等"),
    ("些", "說"), ("次", "來"), ("第一", "次"), ("半", "小時"),
    ("雙", "要"), ("半", "個"), ("大家", "家"), ("整天", "睡覺"),
    ("每", "看見"), ("昨天", "天氣"), ("今天", "高興"), ("明天", "再見"),
    ("去年", "北京"), ("號", "生日"), ("點", "起床"), ("小時", "工作"),
    ("星期", "休息"), ("週末", "做"), ("月", "去"), ("年", "月"),
    ("分", "點"), ("刻", "點"), ("口", "家"), ("位", "老師"),
    ("條", "魚"), ("件", "衣服"), ("雙", "她"), ("輛", "自行車"),
    ("份", "報紙"), ("層", "住"), ("種", "是"), ("角", "是"),
    ("段", "是"), ("祝", "你"), ("教", "漢語"), ("包", "是"),
    ("修", "電腦"), ("帥", "他"), ("寬", "路"), ("富", "他"),
    ("台", "電腦"), ("假", "是"), ("湯", "喝"), ("火", "有"),
    ("刀", "是"), ("新鮮", "魚"), ("甜", "蛋糕"), ("好吃", "菜"),
    ("渴", "水"), ("飽", "吃"), ("餓", "吃"), ("喝", "茶"),
    ("水", "請"), ("牛奶", "孩子"), ("咖啡", "早上"), ("茶", "下午"),
    ("菜", "新鮮"), ("雞蛋", "早上"), ("羊肉", "不"), ("魚", "喜歡"),
    ("西瓜", "甜"), ("蘋果", "買"), ("蛋糕", "甜"), ("麵包", "早上"),
    ("麵條", "喜歡"), ("米飯", "中午"), ("菜單", "給"), ("飯館", "吃"),
    ("飯店", "便宜"), ("空調", "開"), ("冰箱", "有"), ("燈", "開"),
    ("椅子", "坐"), ("床", "貓"), ("洗澡", "家"), ("洗手間", "哪兒"),
    ("樓", "住"), ("門", "關"), ("房間", "小"), ("打掃", "教室"),
    ("手錶", "幾"), ("眼鏡", "桌子"), ("戴", "他"), ("鞋", "雙"),
    ("裙子", "紅"), ("穿", "她"), ("衣服", "洗"), ("超市", "大"),
    ("商店", "買"), ("便宜", "個"), ("貴", "飛機"), ("錢", "沒有"),
    ("賣", "商店"), ("東西", "些"), ("手機", "我"), ("電腦", "用"),
    ("電視", "看"), ("電影", "看"), ("音樂", "好"), ("跳舞", "我們"),
    ("唱歌", "她"), ("乒乓球", "我"), ("打籃球", "我們"), ("踢", "他"),
    ("跑步", "公園"), ("運動", "喜歡"), ("比賽", "我們"), ("體育", "有"),
    ("鍛鍊", "早上"), ("身體", "注意"), ("醫生", "看"), ("醫院", "去"),
    ("藥", "吃"), ("疼", "頭"), ("感冒", "我"), ("發燒", "他"),
    ("生病", "休息"), ("遲到", "他"), ("乾淨", "房間"), ("洗澡", "晚上"),
    ("爬山", "週末"), ("哭", "孩子"), ("站", "請"), ("帶", "朋友"),
    ("接", "去"), ("搬", "桌子"), ("換", "衣服"), ("借", "本"),
    ("幫忙", "我"), ("幫助", "他"), ("照顧", "我"), ("檢查", "我"),
    ("比較", "個"), ("選擇", "個"), ("解決", "我"), ("出現", "問題"),
    ("發現", "我"), ("提高", "我"), ("變化", "天氣"), ("奇怪", "個"),
    ("特別", "他"), ("熱情", "她"), ("滿意", "我"), ("著急", "別"),
    ("擔心", "我"), ("放心", "請"), ("小心", "請"), ("注意", "請"),
    ("水平", "他"), ("環境", "地方"), ("作用", "個"), ("辦法", "我"),
    ("機會", "我"), ("愛好", "書"), ("興趣", "我"), ("習慣", "我"),
    ("關係", "沒有"), ("附近", "住"), ("中間", "坐"), ("以後", "回"),
    ("以前", "住"), ("過去", "我"), ("最近", "我"), ("剛才", "他"),
    ("一會兒", "我"), ("一直", "我"), ("終於", "我"), ("突然", "他"),
    ("當然", "這"), ("仍然", "我"), ("也許", "他"), ("幾乎", "我"),
    ("先", "吃"), ("然後", "吃"), ("除了", "他"), ("根據", "個"),
    ("關於", "書"), ("為了", "工作"), ("向", "走"), ("從", "北京"),
    ("比", "高"), ("跟", "他"), ("像", "爸爸"), ("使", "高興"),
    ("被", "放"), ("把", "書"), ("放", "杯子"), ("用", "我"),
    ("講", "我"), ("表示", "我"), ("表演", "他"), ("舉行", "我們"),
    ("參加", "我"), ("見面", "他"), ("遇到", "我"), ("離開", "我"),
    ("結束", "課"), ("完成", "我"), ("敢", "我"), ("必須", "我"),
    ("願意", "我"), ("需要", "我"), ("打算", "我"), ("決定", "我"),
    ("同意", "我"), ("相信", "我"), ("記得", "我"), ("忘記", "我"),
    ("練習", "我"), ("復習", "我"), ("黑板", "黑"), ("班", "這"),
    ("年級", "這"), ("數學", "我"), ("成績", "我"), ("作業", "我"),
    ("校長", "他"), ("司機", "他"), ("阿姨", "她"), ("叔叔", "他"),
    ("奶奶", "我"), ("爺爺", "我"), ("鄰居", "他"), ("客人", "他"),
    ("賓館", "我"), ("超市", "我"), ("盤子", "這"), ("筷子", "我"),
    ("菜單", "我"), ("糖", "我"), ("米", "我"), ("蛋糕", "我"),
    ("麵包", "我"), ("禮物", "我"), ("週末", "我"), ("節日", "今天"),
    ("節目", "我"), ("遊戲", "我"), ("音樂", "我"), ("照相機", "這"),
    ("照片", "這"), ("新聞", "我"), ("故事", "我"), ("詞語", "這"),
    ("句子", "這"), ("字典", "這"), ("普通話", "我"), ("中文", "我"),
    ("世界", "我"), ("國家", "中國"), ("地方", "這"), ("城市", "我"),
    ("圖書館", "我"), ("騎", "我"), ("自行車", "我"), ("電梯", "我"),
    ("空調", "房間"), ("冰箱", "牛奶"), ("燈", "這"), ("床", "我"),
    ("傘", "我"), ("裙子", "她"), ("鞋", "我"), ("鼻子", "這"),
    ("耳朵", "這"), ("臉", "她"), ("頭髮", "她"), ("頭", "這"),
    ("手", "這"), ("馬", "這"), ("牛", "這"), ("動物", "貓"),
    ("花", "這"), ("花園", "我"), ("公園", "我"), ("風", "今天"),
    ("雨", "今天"), ("海", "我"), ("河", "這"), ("山", "我"),
    ("月亮", "我"), ("太陽", "很"), ("秋", "現在"), ("夏", "現在"),
    ("冬", "現在"), ("春天", "我"), ("冬天", "很"), ("夏天", "很"),
    ("西", "學校"), ("東", "學校"), ("北方", "他"), ("北", "北京"),
    ("南", "學校"), ("黃", "這"), ("藍", "這"), ("綠", "這"),
    ("甜", "西瓜"), ("渴", "我"), ("飽", "我"), ("餓", "我"),
    ("壞", "杯子"), ("短", "條"), ("低", "桌子"), ("矮", "他"),
    ("瘦", "她"), ("胖", "他"), ("年輕", "她"), ("老", "他"),
    ("聰明", "他"), ("可愛", "貓"), ("舒服", "椅子"), ("新鮮", "魚"),
    ("安靜", "教室"), ("乾淨", "房間"), ("清楚", "我"), ("簡單", "這"),
    ("難", "這"), ("容易", "這"), ("重要", "事情"), ("主要", "是"),
    ("一般", "這"), ("相同", "兩"), ("一樣", "那"), ("別人", "他"),
    ("其他", "要"), ("任何", "人"), ("一切", "好"), ("不得不", "去"),
    ("不管", "誰"), ("不過", "累"), ("並且", "工作"), ("不僅", "他"),
    ("不但", "工作"), ("或者", "水"), ("雖然", "冷"), ("但是", "咖啡"),
    ("所以", "休息"), ("因為", "學生"), ("如果", "家"), ("還是", "水"),
    ("可能", "他"), ("當然", "去"), ("終於", "來"), ("經常", "我"),
    ("總是", "忙"), ("馬上", "去"), ("先", "我"), ("其實", "學生"),
    ("一定", "去"), ("一共", "人"), ("更", "大"), ("只", "本"),
    ("才", "他"), ("就", "去"), ("還", "書"), ("正在", "我"),
    ("已經", "吃"), ("別", "去"), ("再", "請"), ("真", "這"),
    ("非常", "我"), ("最", "他"), ("太", "這"), ("很", "我"),
    ("都", "學生"), ("也", "學生"), ("和", "朋友"), ("每", "人"),
    ("為什麼", "去"), ("幾", "歲"), ("多少", "錢"), ("怎麼樣", "今天"),
    ("怎麼", "去"), ("哪兒", "去"), ("哪", "個"), ("誰", "你"),
    ("什麼", "這"), ("那", "杯子"), ("這", "書"), ("自己", "去"),
    ("大家", "好"), ("它", "狗"), ("您", "好"), ("我們", "朋友"),
    ("她", "老師"), ("他", "朋友"), ("你", "好"), ("我", "學生"),
    ("歲", "幾"), ("元", "蘋果"), ("號", "三"), ("雙", "鞋"),
    ("位", "老師"), ("條", "魚"), ("張", "票"), ("次", "去"),
    ("件", "衣服"), ("塊", "蘋果"), ("些", "朋友"), ("本", "書"),
    ("個", "朋友"), ("得", "好"), ("地", "學習"), ("著", "書"),
    ("吧", "去"), ("了", "吃"), ("的", "書"), ("呢", "你"),
    ("嗎", "好"), ("喂", "誰"), ("請", "坐"), ("對不起", "說"),
    ("不客氣", "說"), ("沒關係", "說"), ("沒有", "錢"), ("沒", "去"),
    ("不", "老師"), ("雪", "下"), ("晴", "很"), ("熱", "很"),
    ("冷", "很"), ("天氣", "好"), ("下雨", "今天"), ("去年", "學校"),
    ("時間", "沒有"), ("時候", "什麼"), ("小時", "一"), ("分鐘", "十"),
    ("點", "三"), ("星期", "幾"), ("日", "星期"), ("月", "二"),
    ("年", "學校"), ("現在", "家"), ("昨天", "家"), ("明天", "學校"),
    ("今天", "家"), ("晚上", "睡覺"), ("早上", "起床"), ("下午", "學校"),
    ("中午", "米飯"), ("上午", "學習"), ("中間", "我"), ("旁邊", "他"),
    ("裡", "家"), ("外", "他"), ("右邊", "學校"), ("左邊", "學校"),
    ("後面", "學校"), ("前面", "學校"), ("下", "桌子"), ("上", "桌子"),
    ("零", "點"), ("萬", "一"), ("千", "一"), ("百", "一"),
    ("兩", "朋友"), ("十", "歲"), ("九", "她"), ("八", "歲"),
    ("七", "歲"), ("六", "蘋果"), ("五", "書"), ("四", "書"),
    ("三", "朋友"), ("二", "月"), ("一", "朋友"),
]

# Real synonym/antonym/related pairs. The noisy generated-looking tail above
# is replaced by this explicit list. (The long list is filtered: a pair is
# kept only when both words are real study forms in the first 1,000 and the
# pair is also listed here.)
RELATION_OK = {
    ("大", "小"), ("多", "少"), ("上", "下"), ("來", "去"), ("冷", "熱"),
    ("買", "賣"), ("前面", "後面"), ("左邊", "右邊"), ("快", "慢"), ("新", "舊"),
    ("長", "短"), ("高", "矮"), ("高", "低"), ("遠", "近"), ("男", "女"),
    ("男人", "女人"), ("開", "關"), ("早上", "晚上"), ("昨天", "明天"),
    ("上午", "下午"), ("黑", "白"), ("胖", "瘦"), ("餓", "飽"), ("容易", "難"),
    ("簡單", "容易"), ("記得", "忘記"), ("開始", "結束"), ("進", "出"),
    ("裡", "外"), ("老", "年輕"), ("貴", "便宜"), ("對", "錯"), ("問", "回答"),
    ("以前", "以後"), ("有", "沒有"), ("南", "北"), ("東", "西"),
    ("夏天", "冬天"), ("春天", "秋"), ("夏天", "夏"), ("冬天", "冬"),
    ("兒子", "女兒"), ("哥哥", "弟弟"), ("姐姐", "妹妹"), ("丈夫", "妻子"),
    ("爸爸", "媽媽"), ("爺爺", "奶奶"), ("真", "假"), ("好", "壞"),
    ("陰", "晴"), ("高興", "快樂"), ("喜歡", "愛"), ("知道", "了解"),
    ("明白", "清楚"), ("明白", "懂"), ("清楚", "懂"), ("幫助", "幫忙"),
    ("飯店", "飯館"), ("說", "講"), ("說", "說話"), ("講", "說話"),
    ("但是", "不過"), ("應該", "必須"), ("覺得", "認為"), ("時間", "時候"),
    ("能", "可以"), ("會", "可以"), ("學習", "練習"), ("學習", "復習"),
    ("漂亮", "可愛"), ("重要", "主要"), ("相同", "一樣"), ("經常", "總是"),
    ("總是", "一直"), ("想", "要"), ("看", "看見"), ("工作", "上班"),
    ("漢語", "中文"), ("漢語", "普通話"), ("中文", "普通話"),
    ("上午", "早上"), ("醫生", "醫院"), ("學校", "教室"), ("老師", "學生"),
    ("書", "報紙"), ("字", "詞語"), ("問題", "題"), ("貓", "狗"),
    ("茶", "咖啡"), ("蘋果", "西瓜"), ("因為", "所以"), ("雖然", "但是"),
    ("或者", "還是"), ("而且", "並且"), ("不但", "不僅"), ("不但", "而且"),
    ("可能", "也許"), ("當然", "一定"), ("沒有", "沒"), ("也", "還"),
    ("再", "又"), ("公園", "花園"), ("夏天", "熱"), ("冬天", "冷"),
    ("下雨", "雨"), ("雪", "冷"), ("哥哥", "姐姐"), ("弟弟", "妹妹"),
    ("爸爸", "兒子"), ("媽媽", "女兒"), ("休息", "睡覺"), ("吃", "喝"),
    ("電影", "電視"), ("朋友", "同學"), ("家", "房間"), ("練習", "復習"),
    ("記得", "知道"), ("相信", "認為"), ("決定", "打算"), ("需要", "要"),
    ("願意", "想"), ("完成", "結束"), ("離開", "走"), ("遇到", "看見"),
    ("見面", "看"), ("小心", "注意"), ("放心", "擔心"), ("滿意", "高興"),
    ("發現", "看見"), ("解決", "完成"), ("比較", "比"), ("照顧", "幫助"),
    ("跟", "和"), ("為了", "因為"), ("然後", "以後"), ("突然", "終於"),
    ("剛才", "以前"), ("最近", "現在"), ("過去", "以前"), ("附近", "近"),
    ("興趣", "喜歡"), ("愛好", "喜歡"), ("發燒", "生病"), ("感冒", "生病"),
    ("鍛鍊", "運動"), ("體育", "運動"), ("比賽", "運動"), ("唱歌", "音樂"),
    ("跳舞", "音樂"), ("打電話", "手機"), ("打掃", "乾淨"), ("騎", "自行車"),
    ("教", "老師"), ("教", "學習"), ("南", "北方"), ("東", "西"),
    ("黑", "白"), ("紅", "綠"), ("藍", "綠"), ("長", "短"),
    ("高", "矮"), ("遠", "近"), ("快", "慢"), ("新", "舊"),
    ("貴", "便宜"), ("胖", "瘦"), ("餓", "飽"), ("老", "年輕"),
    ("男", "女"), ("開", "關"), ("來", "去"), ("進", "出"),
    ("上", "下"), ("前", "後"), ("左", "右"), ("裡", "外"),
    ("多", "少"), ("大", "小"), ("冷", "熱"), ("對", "錯"),
    ("買", "賣"), ("問", "回答"), ("開始", "結束"), ("有", "沒有"),
    ("昨天", "明天"), ("上午", "下午"), ("早上", "晚上"), ("前面", "後面"),
    ("左邊", "右邊"), ("以前", "以後"), ("夏天", "冬天"), ("春天", "秋"),
    ("兒子", "女兒"), ("哥哥", "弟弟"), ("姐姐", "妹妹"), ("丈夫", "妻子"),
    ("爸爸", "媽媽"), ("爺爺", "奶奶"), ("真", "假"), ("好", "壞"),
    ("高興", "快樂"), ("喜歡", "愛"), ("知道", "了解"), ("明白", "清楚"),
    ("幫助", "幫忙"), ("飯店", "飯館"), ("說", "講"), ("但是", "不過"),
    ("應該", "必須"), ("覺得", "認為"), ("能", "可以"), ("學習", "練習"),
    ("漂亮", "可愛"), ("容易", "簡單"), ("相同", "一樣"), ("經常", "總是"),
    ("想", "要"), ("漢語", "中文"), ("上午", "早上"), ("貓", "狗"),
    ("茶", "咖啡"), ("或者", "還是"), ("而且", "並且"), ("可能", "也許"),
    ("公園", "花園"), ("電影", "電視"), ("朋友", "同學"), ("休息", "睡覺"),
    ("吃", "喝"), ("小心", "注意"), ("鍛鍊", "運動"), ("發燒", "感冒"),
}

# The blocks above were drafted wide on purpose. Only pairs in RELATION_OK
# are written, and only with the type given here.
ANTONYM_PAIRS = {
    ("大", "小"), ("多", "少"), ("上", "下"), ("來", "去"), ("冷", "熱"),
    ("買", "賣"), ("前面", "後面"), ("左邊", "右邊"), ("快", "慢"), ("新", "舊"),
    ("長", "短"), ("高", "矮"), ("高", "低"), ("遠", "近"), ("男", "女"),
    ("男人", "女人"), ("開", "關"), ("早上", "晚上"), ("昨天", "明天"),
    ("上午", "下午"), ("黑", "白"), ("胖", "瘦"), ("餓", "飽"), ("容易", "難"),
    ("記得", "忘記"), ("開始", "結束"), ("進", "出"), ("裡", "外"),
    ("老", "年輕"), ("貴", "便宜"), ("對", "錯"), ("問", "回答"),
    ("以前", "以後"), ("有", "沒有"), ("南", "北"), ("東", "西"),
    ("夏天", "冬天"), ("真", "假"), ("好", "壞"), ("陰", "晴"),
}
SYNONYM_PAIRS = {
    ("高興", "快樂"), ("喜歡", "愛"), ("知道", "了解"), ("明白", "清楚"),
    ("明白", "懂"), ("清楚", "懂"), ("幫助", "幫忙"), ("飯店", "飯館"),
    ("說", "講"), ("說", "說話"), ("講", "說話"), ("但是", "不過"),
    ("應該", "必須"), ("覺得", "認為"), ("時間", "時候"), ("能", "可以"),
    ("會", "可以"), ("學習", "練習"), ("學習", "復習"), ("練習", "復習"),
    ("容易", "簡單"), ("重要", "主要"), ("相同", "一樣"), ("經常", "總是"),
    ("總是", "一直"), ("漢語", "中文"), ("漢語", "普通話"), ("中文", "普通話"),
    ("上午", "早上"), ("問題", "題"), ("或者", "還是"), ("而且", "並且"),
    ("不但", "不僅"), ("不但", "而且"), ("可能", "也許"), ("當然", "一定"),
    ("決定", "打算"), ("需要", "要"), ("完成", "結束"), ("小心", "注意"),
    ("鍛鍊", "運動"), ("體育", "運動"), ("發燒", "感冒"),
}
RELATED_PAIRS = {
    ("想", "要"), ("看", "看見"), ("工作", "上班"), ("醫生", "醫院"),
    ("學校", "教室"), ("書", "報紙"), ("字", "詞語"), ("貓", "狗"),
    ("茶", "咖啡"), ("蘋果", "西瓜"), ("因為", "所以"), ("雖然", "但是"),
    ("公園", "花園"), ("夏天", "熱"), ("冬天", "冷"), ("下雨", "雨"),
    ("雪", "冷"), ("哥哥", "姐姐"), ("弟弟", "妹妹"), ("爸爸", "兒子"),
    ("媽媽", "女兒"), ("休息", "睡覺"), ("吃", "喝"), ("電影", "電視"),
    ("朋友", "同學"), ("家", "房間"), ("漂亮", "可愛"), ("記得", "知道"),
    ("相信", "認為"), ("願意", "想"), ("離開", "走"), ("遇到", "看見"),
    ("見面", "看"), ("放心", "擔心"), ("滿意", "高興"), ("發現", "看見"),
    ("解決", "完成"), ("比較", "比"), ("照顧", "幫助"), ("跟", "和"),
    ("為了", "因為"), ("然後", "以後"), ("剛才", "以前"), ("最近", "現在"),
    ("過去", "以前"), ("附近", "近"), ("興趣", "喜歡"), ("愛好", "喜歡"),
    ("發燒", "生病"), ("感冒", "生病"), ("比賽", "運動"), ("唱歌", "音樂"),
    ("跳舞", "音樂"), ("打電話", "手機"), ("打掃", "乾淨"), ("騎", "自行車"),
    ("教", "老師"), ("教", "學習"), ("春天", "秋"), ("夏天", "夏"),
    ("冬天", "冬"),     ("南", "北方"), ("沒有", "沒"), ("再", "又"), ("也", "還"),
    ("兒子", "女兒"), ("哥哥", "弟弟"), ("姐姐", "妹妹"), ("丈夫", "妻子"),
    ("爸爸", "媽媽"), ("爺爺", "奶奶"), ("老師", "學生"),
}


FOOD = {"蘋果", "米飯", "菜", "麵條", "西瓜", "雞蛋", "魚", "羊肉", "蛋糕", "麵包", "糖", "米", "藥"}
DRINK = {"水", "茶", "咖啡", "牛奶", "湯"}
PLACES = {
    "家", "學校", "教室", "醫院", "商店", "公司", "飯店", "飯館", "北京", "中國",
    "房間", "機場", "火車站", "公園", "花園", "圖書館", "城市", "超市", "賓館",
    "地方", "洗手間",
}
PEOPLE = {
    "老師", "學生", "醫生", "朋友", "同學", "孩子", "先生", "小姐", "媽媽", "爸爸",
    "兒子", "女兒", "丈夫", "妻子", "哥哥", "弟弟", "姐姐", "妹妹", "男人", "女人",
    "服務員", "客人", "鄰居", "阿姨", "叔叔", "爺爺", "奶奶", "校長", "司機", "作者",
}
ANIMALS = {"狗", "貓", "牛", "馬", "魚", "動物"}
COLORS = {"白", "黑", "紅", "綠", "藍", "黃"}

# Words a generic "我想X" frame would misuse.
VERB_BLOCK = {
    "是", "有", "在", "會", "能", "可以", "要", "想", "讓", "被", "把", "給", "比",
    "從", "對", "向", "為", "為了", "跟", "使", "像", "用", "到", "來", "去", "出",
    "進", "上", "下", "開", "關", "叫", "住", "做", "看", "吃", "喝", "買", "賣",
    "說", "講", "寫", "讀", "聽", "問", "回答", "告訴", "找", "送", "幫助", "幫忙",
    "認識", "知道", "覺得", "認為", "希望", "喜歡", "愛", "應該", "必須", "願意",
    "需要", "敢", "決定", "打算", "同意", "相信", "記得", "忘記", "完成", "結束",
    "離開", "開始", "表示", "參加", "解決", "選擇", "發現", "出現", "提高", "變化",
    "成為", "作為", "以為", "顯得", "屬於", "等於", "不如", "沒有", "沒", "不",
}


def gloss(entry: dict) -> str:
    text = FIX.get(entry["traditional"], {}).get("en", entry["en"])
    text = text.split(";")[0].split("，")[0].split(",")[0].strip()
    if text.lower().startswith("to "):
        text = text[3:]
    return text or entry["traditional"]


def apply_fix(entry: dict) -> None:
    fix = FIX.get(entry["traditional"])
    if not fix:
        return
    if "pinyin" in fix:
        entry["pinyin"] = fix["pinyin"]
    if "en" in fix:
        entry["en"] = fix["en"]


# How many sample sentences a shown word should have. Higher HSK gets more.
SENTENCE_TARGET = {1: 2, 2: 3, 3: 4, 4: 5}


def sentence_pool(entry: dict, vocab: set[str]) -> list[tuple[str, list[str]]]:
    """Extra sentences whose every token is in the first 1,000 study forms."""
    word = entry["traditional"]
    name = gloss(entry)
    pos = set(entry["pos"])
    pool: list[tuple[str, list[str]]] = []
    seen: set[tuple[str, ...]] = set()

    def add(english: str, tokens: list[str]) -> None:
        if word not in tokens or tokens.count(word) != 1:
            return
        if any(token not in vocab for token in tokens):
            return
        key = tuple(tokens)
        if key in seen:
            return
        seen.add(key)
        pool.append((english, tokens))

    if "adjective" in pos or word in COLORS:
        add(f"It is very {name} today.", ["今天", "很", word])
        add(f"I think this is {name}.", ["我", "覺得", "這", "很", word])
        add(f"Is this {name}?", ["這", "很", word, "嗎"])
        add(f"That one is not {name}.", ["那", "個", "不", word])
        add(f"He is also very {name}.", ["他", "也", "很", word])
        add(f"This is too {name}.", ["這", "太", word, "了"])
        add(f"She thinks it is {name}.", ["她", "覺得", "很", word])
    if word in FOOD:
        add(f"He wants to eat {name} too.", ["他", "也", "想", "吃", word])
        add(f"Do you want to eat {name}?", ["你", "想", "吃", word, "嗎"])
        add(f"I ate {name} yesterday.", ["昨天", "我", "吃", "了", word])
        add(f"Mom buys {name}.", ["媽媽", "買", word])
        add(f"I like eating {name}.", ["我", "喜歡", "吃", word])
        add(f"We eat {name} at noon.", ["我們", "中午", "吃", word])
    if word in DRINK:
        add(f"He wants to drink {name} too.", ["他", "也", "想", "喝", word])
        add(f"Do you want to drink {name}?", ["你", "想", "喝", word, "嗎"])
        add(f"I drank {name} yesterday.", ["昨天", "我", "喝", "了", word])
        add(f"Please drink {name}.", ["請", "喝", word])
        add(f"I like drinking {name}.", ["我", "喜歡", "喝", word])
    if word in PLACES:
        add(f"Are you going to {name}?", ["你", "去", word, "嗎"])
        add(f"He is at {name} now.", ["他", "現在", "在", word])
        add(f"We go to {name} tomorrow.", ["我們", "明天", "去", word])
        add(f"I am not going to {name} today.", ["今天", "我", "不", "去", word])
        add(f"She likes {name}.", ["她", "喜歡", word])
        add(f"I was at {name} yesterday.", ["昨天", "我", "在", word])
    if word in PEOPLE:
        add(f"She is also {name}.", ["她", "也", "是", word])
        add(f"I know {name}.", ["我", "認識", word])
        add(f"Is he {name}?", ["他", "是", word, "嗎"])
        add(f"{name} is at home.", [word, "在", "家"])
        add(f"We like {name}.", ["我們", "喜歡", word])
        add(f"Do you see {name}?", ["你", "看見", word, "嗎"])
    if "verb" in pos and word not in VERB_BLOCK:
        add(f"Do you want to {name}?", ["你", "想", word, "嗎"])
        add(f"He wants to {name} too.", ["他", "也", "想", word])
        add(f"I do not want to {name}.", ["我", "不", "想", word])
        add(f"We {name} together.", ["我們", "一起", word])
        add(f"I will {name} tomorrow.", ["明天", "我", word])
        add(f"He is {name} now.", ["他", "正在", word])
        add(f"She {name} yesterday.", ["昨天", "她", word, "了"])
    if "verb" in pos and word not in {"是", "有", "在", "會", "能", "可以", "要", "讓", "被", "把", "給", "比", "從", "對", "向", "為", "為了", "跟", "使", "像"}:
        add(f"She also {name}s you.", ["她", "也", word, "你"])
        add(f"Do you {name} me?", ["你", word, "我", "嗎"])
        add(f"I do not {name} him.", ["我", "不", word, "他"])
        add(f"He {name}s Mom.", ["他", word, "媽媽"])
    if "noun" in pos or "measure" in pos or "number" in pos:
        add(f"This is my {name}.", ["這", "是", "我", "的", word])
        add(f"Do you have {name}?", ["你", "有", word, "嗎"])
        add(f"I do not have {name}.", ["我", "沒有", word])
        add(f"I like {name}.", ["我", "喜歡", word])
        add(f"He sees {name}.", ["他", "看見", word])
        add(f"We all have {name}.", ["我們", "都", "有", word])
        add(f"Please give me {name}.", ["請", "給", "我", word])
    degree = word in {"很", "太", "最", "非常", "更", "真", "極", "比較"}
    only_closed = not (pos & {"noun", "verb", "adjective", "number", "measure", "pronoun", "localizer"})
    if degree:
        add(f"It is {name} cold today.", ["今天", word, "冷"])
        add(f"He is {name} tall.", ["他", word, "高"])
        add(f"This is {name} good.", ["這", word, "好"])
        add(f"She is {name} busy.", ["她", word, "忙"])
        add(f"I am {name} tired.", ["我", word, "累"])
        add(f"The school is {name} far.", ["學校", word, "遠"])
    elif "conjunction" in pos and "adjective" not in pos:
        add(f"I want to go, {name} I am busy.", ["我", "想", "去", word, "我", "很", "忙"])
        add(f"He is tired, {name} he stays home.", ["他", "很", "累", word, "他", "在", "家"])
        add(f"{name} you come, I am happy.", [word, "你", "來", "我", "就", "高興"])
        add(f"{name} it rains, I still go.", [word, "下雨", "我", "還", "去"])
        add(f"Today {name} tomorrow.", ["今天", word, "明天"])
        add(f"I study, {name} I also work.", ["我", "學習", word, "我", "也", "工作"])
    elif only_closed and ("adverb" in pos or "preposition" in pos):
        add(f"He {name} comes.", ["他", word, "來"])
        add(f"I {name} go to school.", ["我", word, "去", "學校"])
        add(f"We {name} study.", ["我們", word, "學習"])
        add(f"She {name} eats.", ["她", word, "吃"])
        add(f"Are you {name} going?", ["你", word, "去", "嗎"])
        add(f"He has {name} come.", ["他", word, "來", "了"])
    elif only_closed:
        add(f"Are you a student {name}?", ["你", "是", "學生", word])
        add(f"Are you going {name}?", ["你", "去", word])
        add(f"Is he at home {name}?", ["他", "在", "家", word])
        add(f"He has left {name}.", ["他", "走", word])
        add(f"Have you eaten {name}?", ["你", "吃", word])
        add(f"This is my {name} book.", ["這", "是", "我", word, "書"])
        add(f"Are you busy {name}?", ["你", "忙", word])
        add(f"We are going {name}.", ["我們", "去", word])
    if only_closed:
        return pool
    # Broad frames for content words that still need another sample.
    add(f"Do you know {name}?", ["你", "知道", word, "嗎"])
    add(f"He also knows {name}.", ["他", "也", "知道", word])
    add(f"I saw {name}.", ["我", "看見", word, "了"])
    add(f"I saw {name} today.", ["今天", "我", "看見", word])
    add(f"We all like {name}.", ["我們", "都", "喜歡", word])
    add(f"I do not have {name}.", ["我", "沒有", word])
    add(f"She does not like {name}.", ["她", "不", "喜歡", word])
    add(f"Will you look at {name} tomorrow?", ["明天", "你", "看", word, "嗎"])
    add(f"I am looking at {name} now.", ["現在", "我", "在", "看", word])
    add(f"Do you want {name}?", ["你", "要", word, "嗎"])
    add(f"I also have {name}.", ["我", "也", "有", word])
    add(f"Is this {name}?", ["這", "是", word, "嗎"])
    add(f"Please look at {name}.", ["請", "看", word])
    add(f"He said {name} yesterday.", ["昨天", "他", "說", word])
    add(f"Mom also has {name}.", ["媽媽", "也", "有", word])
    add(f"I am not looking at {name}.", ["我", "不", "看", word])
    add(f"We look at {name} together.", ["我們", "一起", "看", word])
    add(f"He has {name} today.", ["他", "今天", "有", word])
    add(f"Do you see {name}?", ["你", "看見", word, "嗎"])
    add(f"I like this {name}.", ["我", "喜歡", "這", "個", word])
    add(f"She saw {name} yesterday.", ["她", "昨天", "看見", word])
    return pool


def generic_sentence(entry: dict, vocab: set[str]) -> tuple[str, list[str]] | None:
    word = entry["traditional"]
    if word not in vocab:
        return None
    pos = entry["pos"]
    primary = pos[0] if pos else "other"
    name = gloss(entry)

    def has(*need: str) -> bool:
        return all(item in vocab for item in need)

    if word in COLORS and has("這", "是", "的"):
        return (f"This is {name}.", ["這", "是", word, "的"])
    if word in FOOD and has("我", "想", "吃"):
        return (f"I want to eat {name}.", ["我", "想", "吃", word])
    if word in DRINK and has("我", "想", "喝"):
        return (f"I want to drink {name}.", ["我", "想", "喝", word])
    if word in PLACES and has("我", "去"):
        return (f"I go to {name}.", ["我", "去", word])
    if word in PEOPLE and has("他", "是"):
        return (f"He is {name}.", ["他", "是", word])
    if word in ANIMALS and has("我", "喜歡"):
        return (f"I like {name}.", ["我", "喜歡", word])
    if "adjective" in pos and has("這", "很") and primary != "noun":
        return (f"This is very {name}.", ["這", "很", word])
    if "verb" in pos and word not in VERB_BLOCK and has("我", "想"):
        return (f"I want to {name}.", ["我", "想", word])
    if "noun" in pos and has("這", "是"):
        return (f"This is {name}.", ["這", "是", word])
    if "adverb" in pos and has("我", "去"):
        return (f"I {name} go.", ["我", word, "去"])
    if "number" in pos and has("我", "有", "個", "朋友"):
        return (f"I have this many friends: {name}.", ["我", "有", word, "個", "朋友"])
    if "measure" in pos and has("這", "是", "一"):
        return (f"This is one {name}.", ["這", "是", "一", word])
    if "localizer" in pos and has("書", "在"):
        return (f"The book is {name}.", ["書", "在", word])
    if has("我", "說"):
        return (f"I say {name}.", ["我", "說", word])
    return None


def add_relation(bucket: dict[str, list[dict]], left: str, right: str, kind: str, keys: dict[str, str]) -> None:
    if left not in keys or right not in keys or left == right:
        return
    for source, target in ((left, right), (right, left)):
        row = {"type": kind, "key": keys[target], "text": target}
        existing = bucket.setdefault(source, [])
        if row not in existing:
            existing.append(row)


def main() -> None:
    lexicon = json.loads((ROOT / "lexicon.json").read_text())
    core = [word for word in lexicon["words"] if word.get("hsk") in (1, 2, 3, 4, 5)]
    core.sort(key=lambda word: (word["hsk"], word["traditional"]))
    if len(core) < SHOWN:
        raise SystemExit(f"only {len(core)} HSK 1–5 words")

    entries = []
    keys: dict[str, str] = {}
    for index, word in enumerate(core, start=1):
        key = f"w{index:04d}"
        keys[word["traditional"]] = key
        entry = {
            "key": key,
            "traditional": word["traditional"],
            "simplified": word["simplified"],
            "pinyin": word["pinyin"],
            "en": word["en"],
            "hsk": word["hsk"],
            "pos": word["pos"],
            "relations": [],
            "sentences": [],
        }
        apply_fix(entry)
        entries.append(entry)
    by_trad = {entry["traditional"]: entry for entry in entries}

    shown = entries[:SHOWN]
    vocab = {entry["traditional"] for entry in shown if entry["traditional"] not in VARIANTS}
    # Study forms that happen to sit past the first 1,000 stay out of sentences.
    hand: dict[str, tuple[str, list[str]]] = {}
    for focus, english, tokens in HAND:
        hand.setdefault(focus, (english, tokens))
    hand.update({
        "以為": ("I thought he was at home.", ["我", "以為", "他", "在", "家"]),
        "啊": ("Oh, who are you?", ["啊", "你", "是", "誰"]),
        "之": ("One third.", ["三", "分", "之", "一"]),
        "分之": ("One third.", ["三", "分之", "一"]),
        "倆": ("The two of us are going.", ["我們", "倆", "去"]),
        "做生意": ("He does business.", ["他", "做生意"]),
        "億": ("This is one hundred million.", ["這", "是", "一", "億"]),
        "免費": ("This one is free.", ["這", "個", "是", "免費", "的"]),
        "全部": ("We are all going.", ["我們", "全部", "去"]),
        "其中": ("One of them is me.", ["其中", "一", "個", "是", "我"]),
        "其次": ("First is him, and next is me.", ["第一", "是", "他", "其次", "是", "我"]),
        "剩": ("I still have one left.", ["我", "還", "剩", "一", "個"]),
        "即使": ("Even if it rains, I still go.", ["即使", "下雨", "我", "也", "去"]),
        "受不了": ("It is too hot today. I can't stand it.", ["今天", "太", "熱", "了", "我", "受不了"]),
        "只要": ("As long as you come, I am happy.", ["只要", "你", "來", "我", "就", "高興"]),
        "各": ("We each have one book.", ["我們", "各", "有", "一", "本", "書"]),
        "同情": ("I sympathize with him.", ["我", "同情", "他"]),
        "否則": ("Go quickly, otherwise I will leave.", ["快", "去", "否則", "我", "走", "了"]),
        "呀": ("You are going, aren't you?", ["你", "去", "呀"]),
        "咱們": ("Let's go together.", ["咱們", "一起", "去"]),
        "咸": ("This dish is salty.", ["這", "個", "菜", "很", "咸"]),
        "因此": ("It rained, so I stayed home.", ["下雨", "了", "因此", "我", "在", "家"]),
        "差不多": ("These two are about the same.", ["這", "兩", "個", "差不多"]),
        "成為": ("He became a teacher.", ["他", "成為", "老師", "了"]),
        "按照": ("I go by what you said.", ["我", "按照", "你", "說", "的", "去"]),
        "放暑假": ("We are on summer vacation.", ["我們", "放暑假", "了"]),
        "於是": ("It rained, so I went home.", ["下雨", "了", "於是", "我", "回", "家"]),
        "既然": ("Since you are going, I will go too.", ["既然", "你", "去", "我", "也", "去"]),
        "無論": ("No matter who comes, I am here.", ["無論", "誰", "來", "我", "都", "在"]),
        "然而": ("I am busy, however I still go.", ["我", "很", "忙", "然而", "我", "還", "去"]),
        "對不起": ("Sorry, I am late.", ["對不起", "我", "遲到", "了"]),
    })

    missing_tokens: list[str] = []
    sentences = []
    for entry in shown:
        word = entry["traditional"]
        if word in VARIANTS:
            target = VARIANTS[word]
            if target and target in keys and target != word:
                entry["relations"].append({"type": "variant", "key": keys[target], "text": target})
            elif target:
                entry["relations"].append({"type": "variant", "key": None, "text": target})
            else:
                entry["relations"].append({"type": "variant", "key": None, "text": None})
            continue
        drafted = hand.get(word) or generic_sentence(entry, vocab)
        if not drafted:
            missing_tokens.append(word)
            continue
        drafts = [drafted]
        used = {tuple(drafted[1])}
        target = SENTENCE_TARGET.get(entry["hsk"], 2)
        for english, tokens in sentence_pool(entry, vocab):
            if tuple(tokens) in used:
                continue
            bad = [token for token in tokens if token not in vocab]
            if bad or word not in tokens:
                continue
            drafts.append((english, tokens))
            used.add(tuple(tokens))
            if len(drafts) >= target:
                break
        if len(drafts) < target:
            missing_tokens.append(f"{word}:need-{target}-have-{len(drafts)}")
            continue
        for nth, (english, tokens) in enumerate(drafts, start=1):
            bad = [token for token in tokens if token not in vocab]
            if bad or word not in tokens:
                missing_tokens.append(f"{word}:{' '.join(bad) or 'focus-missing'}")
                break
            sentence_key = "s" + entry["key"][1:] if nth == 1 else f"s{entry['key'][1:]}-{nth}"
            token_rows = []
            for index, token in enumerate(tokens):
                after = "。" if index == len(tokens) - 1 else ""
                token_rows.append({"key": keys[token], "text": token, "after": after})
            if english.endswith("?"):
                token_rows[-1]["after"] = "？"
            sentences.append({"key": sentence_key, "en": english, "tokens": token_rows})
            entry["sentences"].append(sentence_key)

    if missing_tokens:
        raise SystemExit("no usable sentence for: " + ", ".join(missing_tokens[:40]))

    for left, right in ANTONYM_PAIRS:
        add_relation({entry["traditional"]: entry["relations"] for entry in entries}, left, right, "antonym", keys)
    # add_relation above rebuilds a throwaway dict. Write directly instead.
    for entry in entries:
        entry["relations"] = [row for row in entry["relations"] if row["type"] == "variant"]
    rel: dict[str, list[dict]] = {entry["traditional"]: entry["relations"] for entry in entries}
    for left, right in ANTONYM_PAIRS:
        add_relation(rel, left, right, "antonym", keys)
    for left, right in SYNONYM_PAIRS:
        add_relation(rel, left, right, "synonym", keys)
    for left, right in RELATED_PAIRS:
        add_relation(rel, left, right, "related", keys)

    # Drop relations whose other side is a variant glyph.
    for entry in entries:
        entry["relations"] = [
            row for row in entry["relations"]
            if row.get("text") not in VARIANTS
        ]

    label_en = {row["id"]: row["en"] for row in lexicon["labels"]}
    labels_of = {word["traditional"]: word["labels"] for word in core}
    pinyin_of: dict[str, str] = {}
    for word in lexicon["words"]:
        if len(word["traditional"]) == 1 and word["traditional"] not in pinyin_of:
            pinyin_of[word["traditional"]] = word["pinyin"]
    for entry in entries:
        names = [label_en[item] for item in labels_of[entry["traditional"]]]
        if not names or not entry["simplified"] or not entry["pinyin"] or not entry["en"] or not entry["pos"]:
            raise SystemExit(f"blank column on {entry['traditional']}")
        entry["labels"] = names
        if len(entry["traditional"]) == 1:
            pinyin_of[entry["traditional"]] = entry["pinyin"]
    family_glyphs = {
        char
        for entry in shown
        if entry["traditional"] not in VARIANTS
        for char in entry["traditional"]
    }
    rank_of = {
        entry["traditional"]: int(entry["key"][1:])
        for entry in shown
        if len(entry["traditional"]) == 1
    }
    parts = analyze(
        {char for entry in entries for char in entry["traditional"]},
        pinyin_of,
        family_glyphs,
        rank_of,
    )
    for entry in entries:
        entry["parts"] = [parts[char] for char in entry["traditional"]]

    payload = {
        "source": (
            "Old HSK 2.0 levels 1–5, ordered by level then traditional. "
            f"Every one of the {len(entries)} headwords has an index key. "
            f"This file's sentences cover the first {SHOWN} (HSK 1–3 and part of HSK 4). "
            "HSK 1 has 2 samples, HSK 2 has 3, HSK 3 has 4, and HSK 4 has 5. "
            "A sentence token is always one of those words, never a character outside the set, "
            "and each token keeps that word's key. "
            "Every character also has a meaning part, a sound part, the same-sound set, "
            "and the same-part family, the same relations as the character page."
        ),
        "list_size": len(entries),
        "shown": SHOWN,
        "entries": entries,
        "sentences": sentences,
    }
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    for path in (ROOT / "study.json", WEB / "study.json"):
        path.write_text(text)
    with_sentence = sum(1 for entry in shown if entry["sentences"])
    variants = sum(1 for entry in shown if entry["traditional"] in VARIANTS)
    antonyms = sum(1 for entry in shown if any(row["type"] == "antonym" for row in entry["relations"]))
    synonyms = sum(1 for entry in shown if any(row["type"] == "synonym" for row in entry["relations"]))
    from collections import Counter
    counts = Counter(len(entry["sentences"]) for entry in shown if entry["traditional"] not in VARIANTS)
    by_level = {}
    for entry in shown:
        if entry["traditional"] in VARIANTS:
            continue
        by_level.setdefault(entry["hsk"], Counter())[len(entry["sentences"])] += 1
    print(
        f"indexed {len(entries)} shown {SHOWN} sentences {len(sentences)} "
        f"with_sentence {with_sentence} variants {variants} "
        f"antonym_words {antonyms} synonym_words {synonyms}"
    )
    print("samples", dict(sorted(counts.items())))
    print("by level", {level: dict(sorted(counter.items())) for level, counter in sorted(by_level.items())})
    # Spot-check a few joins.
    by_sentence = {row["key"]: row for row in sentences}
    for traditional in ("愛", "大", "蘋果", "但是", "京劇", "河", "好", "愛情", "心情", "請看"):
        entry = by_trad.get(traditional)
        if entry is None:
            print(traditional, "not in HSK 1–5")
            continue
        print(entry["key"], "hsk", entry["hsk"], "n", len(entry["sentences"]))
        for part in entry["parts"]:
            print(
                " ", part["glyph"], "meaning", part["meaning"], "side", part["side"],
                "sound", part["sound"], "same", "".join(part["same_sound"]),
                "family", "".join(part["same_family"]),
            )
        for sentence_key in entry["sentences"][:1]:
            sentence = by_sentence[sentence_key]
            joined = "".join(token["text"] + token["after"] for token in sentence["tokens"])
            print(" ", sentence_key, joined, "|", sentence["en"])


if __name__ == "__main__":
    main()
