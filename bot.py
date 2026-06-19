"""
TELEGRAM-БОТ ДЛЯ РАСПРЕДЕЛЕНИЯ КЛАССИЧЕСКОЙ МУЗЫКИ ПО ЭПОХАМ
Версия: Bothost (с улучшенной загрузкой фото через Wikipedia API)
"""

import os
import re
import logging
import urllib.parse
from datetime import datetime
from typing import Dict, Optional, Tuple, List
import aiohttp
import io

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ===================== НАСТРОЙКИ =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "❌ Токен не найден! Установите переменную окружения BOT_TOKEN\n"
        "В панели Bothost добавьте переменную окружения BOT_TOKEN с вашим токеном от @BotFather"
    )

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== СПРАВОЧНИКИ =====================

ERAS = {
    "medieval": {
        "name": "Ранняя музыка (Medieval / Renaissance)",
        "name_en": "Medieval / Renaissance",
        "year_start": 0,
        "year_end": 1599,
        "emoji": "🏛️",
        "description": "Эпоха, охватывающая григорианский хорал, музыку трубадуров и раннюю полифонию."
    },
    "baroque": {
        "name": "Барокко (Baroque)",
        "name_en": "Baroque",
        "year_start": 1600,
        "year_end": 1749,
        "emoji": "👑",
        "description": "Эпоха пышности, контрастов и полифонии. Рождение оперы, расцвет инструментальной музыки."
    },
    "classical": {
        "name": "Классицизм (Classical)",
        "name_en": "Classical",
        "year_start": 1750,
        "year_end": 1819,
        "emoji": "🏛️",
        "description": "Эпоха гармонии, ясности и сонатной формы. Венские классики — Гайдн, Моцарт, Бетховен."
    },
    "romantic": {
        "name": "Романтизм (Romantic)",
        "name_en": "Romantic",
        "year_start": 1820,
        "year_end": 1899,
        "emoji": "🌹",
        "description": "Эпоха эмоций, страстей и индивидуальности. Расцвет программной музыки."
    },
    "modern": {
        "name": "Импрессионизм / Модерн (Modern)",
        "name_en": "Modern",
        "year_start": 1900,
        "year_end": 1949,
        "emoji": "🎨",
        "description": "Эпоха поиска новых звуковых красок и отказ от традиционной тональности."
    },
    "contemporary": {
        "name": "Современная академическая (Contemporary)",
        "name_en": "Contemporary",
        "year_start": 1950,
        "year_end": datetime.now().year,
        "emoji": "🔮",
        "description": "Эпоха минимализма, алеаторики и электронной музыки."
    }
}

# ===================== БАЗА КОМПОЗИТОРОВ =====================

COMPOSERS_DB = {
    # ============================================================
    # РАННЯЯ МУЗЫКА (Medieval / Renaissance)
    # ============================================================
    "машо": {
        "era": "medieval",
        "birth": 1300,
        "death": 1377,
        "full_name": "Гильом де Машо",
        "bio": "Французский поэт и композитор эпохи Средневековья. Ключевая фигура Ars Nova.",
        "wiki": "https://ru.wikipedia.org/wiki/Машо,_Гильом_де",
        "wiki_title": "Машо, Гильом де"
    },
    "ландини": {
        "era": "medieval",
        "birth": 1325,
        "death": 1397,
        "full_name": "Франческо Ландини",
        "bio": "Итальянский композитор, органист и поэт эпохи Треченто.",
        "wiki": "https://ru.wikipedia.org/wiki/Ландини,_Франческо",
        "wiki_title": "Ландини, Франческо"
    },
    "таллис": {
        "era": "medieval",
        "birth": 1505,
        "death": 1585,
        "full_name": "Томас Таллис",
        "bio": "Английский композитор эпохи Ренессанса. Гениальный полифонист.",
        "wiki": "https://ru.wikipedia.org/wiki/Таллис,_Томас",
        "wiki_title": "Таллис, Томас"
    },
    "палестрина": {
        "era": "medieval",
        "birth": 1525,
        "death": 1594,
        "full_name": "Джованни Пьерлуиджи да Палестрина",
        "bio": "Итальянский композитор эпохи Ренессанса. Эталон церковной полифонии.",
        "wiki": "https://ru.wikipedia.org/wiki/Палестрина,_Джованни_Пьерлуиджи_да",
        "wiki_title": "Палестрина, Джованни Пьерлуиджи да"
    },
    
    # ============================================================
    # БАРОККО (Baroque)
    # ============================================================
    "вивальди": {
        "era": "baroque",
        "birth": 1678,
        "death": 1741,
        "full_name": "Антонио Лучо Вивальди",
        "bio": "Итальянский композитор, скрипач-виртуоз. Автор более 500 концертов.",
        "wiki": "https://ru.wikipedia.org/wiki/Вивальди,_Антонио",
        "wiki_title": "Вивальди, Антонио"
    },
    "бах": {
        "era": "baroque",
        "birth": 1685,
        "death": 1750,
        "full_name": "Иоганн Себастьян Бах",
        "bio": "Великий немецкий композитор, вершина полифонии и барочной музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Бах,_Иоганн_Себастьян",
        "wiki_title": "Бах, Иоганн Себастьян"
    },
    "гендель": {
        "era": "baroque",
        "birth": 1685,
        "death": 1759,
        "full_name": "Георг Фридрих Гендель",
        "bio": "Немецкий и английский композитор эпохи барокко. Мастер ораторий.",
        "wiki": "https://ru.wikipedia.org/wiki/Гендель,_Георг_Фридрих",
        "wiki_title": "Гендель, Георг Фридрих"
    },
    "монтеверdi": {
        "era": "baroque",
        "birth": 1567,
        "death": 1643,
        "full_name": "Клаудио Монтеверди",
        "bio": "Итальянский композитор, основоположник оперного жанра.",
        "wiki": "https://ru.wikipedia.org/wiki/Монтеверди,_Клаудио",
        "wiki_title": "Монтеверди, Клаудио"
    },
    "корелли": {
        "era": "baroque",
        "birth": 1653,
        "death": 1713,
        "full_name": "Арканджело Корелли",
        "bio": "Итальянский скрипач и композитор, основоположник римской скрипичной школы.",
        "wiki": "https://ru.wikipedia.org/wiki/Корелли,_Арканджело",
        "wiki_title": "Корелли, Арканджело"
    },
    "пёрселл": {
        "era": "baroque",
        "birth": 1659,
        "death": 1695,
        "full_name": "Генри Пёрселл",
        "bio": "Английский композитор, крупнейший представитель английской барочной музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Пёрселл,_Генри",
        "wiki_title": "Пёрселл, Генри"
    },
    "рамо": {
        "era": "baroque",
        "birth": 1683,
        "death": 1764,
        "full_name": "Жан-Филипп Рамо",
        "bio": "Французский композитор и теоретик музыки. Реформатор французской оперы.",
        "wiki": "https://ru.wikipedia.org/wiki/Рамо,_Жан-Филипп",
        "wiki_title": "Рамо, Жан-Филипп"
    },
    "пахельбель": {
        "era": "baroque",
        "birth": 1653,
        "death": 1706,
        "full_name": "Иоганн Пахельбель",
        "bio": "Немецкий органист и композитор. Автор знаменитого «Канона ре-мажор».",
        "wiki": "https://ru.wikipedia.org/wiki/Пахельбель,_Иоганн",
        "wiki_title": "Пахельбель, Иоганн"
    },
    "альбинони": {
        "era": "baroque",
        "birth": 1671,
        "death": 1751,
        "full_name": "Томазо Джованни Альбинони",
        "bio": "Итальянский композитор эпохи барокко.",
        "wiki": "https://ru.wikipedia.org/wiki/Альбинони,_Томазо",
        "wiki_title": "Альбинони, Томазо"
    },
    "тартини": {
        "era": "baroque",
        "birth": 1692,
        "death": 1770,
        "full_name": "Джузеппе Тартини",
        "bio": "Итальянский скрипач и композитор. Автор «Дьявольских трелей».",
        "wiki": "https://ru.wikipedia.org/wiki/Тартини,_Джузеппе",
        "wiki_title": "Тартини, Джузеппе"
    },
    "скарлатти": {
        "era": "baroque",
        "birth": 1685,
        "death": 1757,
        "full_name": "Доменико Скарлатти",
        "bio": "Итальянский композитор и клавесинист. Автор более 550 сонат.",
        "wiki": "https://ru.wikipedia.org/wiki/Скарлатти,_Доменико",
        "wiki_title": "Скарлатти, Доменико"
    },
    "телеман": {
        "era": "baroque",
        "birth": 1681,
        "death": 1767,
        "full_name": "Георг Филипп Телеман",
        "bio": "Немецкий композитор, один из самых плодовитых в истории музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Телеман,_Георг_Филипп",
        "wiki_title": "Телеман, Георг Филипп"
    },
    
    # ============================================================
    # КЛАССИЦИЗМ (Classical)
    # ============================================================
    "моцарт": {
        "era": "classical",
        "birth": 1756,
        "death": 1791,
        "full_name": "Вольфганг Амадей Моцарт",
        "bio": "Великий австрийский композитор, представитель венской классической школы.",
        "wiki": "https://ru.wikipedia.org/wiki/Моцарт,_Вольфганг_Амадей",
        "wiki_title": "Моцарт, Вольфганг Амадей"
    },
    "бетховен": {
        "era": "classical",
        "birth": 1770,
        "death": 1827,
        "full_name": "Людвиг ван Бетховен",
        "bio": "Великий немецкий композитор, последний представитель венской классической школы.",
        "wiki": "https://ru.wikipedia.org/wiki/Бетховен,_Людвиг_ван",
        "wiki_title": "Бетховен, Людвиг ван"
    },
    "гайдн": {
        "era": "classical",
        "birth": 1732,
        "death": 1809,
        "full_name": "Йозеф Гайдн",
        "bio": "Австрийский композитор, основоположник венской классической школы.",
        "wiki": "https://ru.wikipedia.org/wiki/Гайдн,_Йозеф",
        "wiki_title": "Гайдн, Йозеф"
    },
    "глюк": {
        "era": "classical",
        "birth": 1714,
        "death": 1787,
        "full_name": "Кристоф Виллибальд Глюк",
        "bio": "Немецкий композитор, реформатор оперного жанра.",
        "wiki": "https://ru.wikipedia.org/wiki/Глюк,_Кристоф_Виллибальд",
        "wiki_title": "Глюк, Кристоф Виллибальд"
    },
    "сальери": {
        "era": "classical",
        "birth": 1750,
        "death": 1825,
        "full_name": "Антонио Сальери",
        "bio": "Итальянский и австрийский композитор, педагог. Учитель Бетховена и Шуберта.",
        "wiki": "https://ru.wikipedia.org/wiki/Сальери,_Антонио",
        "wiki_title": "Сальери, Антонио"
    },
    
    # ============================================================
    # РОМАНТИЗМ (Romantic)
    # ============================================================
    "шуберт": {
        "era": "romantic",
        "birth": 1797,
        "death": 1828,
        "full_name": "Франц Петер Шуберт",
        "bio": "Австрийский композитор, основоположник романтизма в музыке.",
        "wiki": "https://ru.wikipedia.org/wiki/Шуберт,_Франц",
        "wiki_title": "Шуберт, Франц"
    },
    "глинка": {
        "era": "romantic",
        "birth": 1804,
        "death": 1857,
        "full_name": "Михаил Иванович Глинка",
        "bio": "Великий русский композитор, основоположник русской классической музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Глинка,_Михаил_Иванович",
        "wiki_title": "Глинка, Михаил Иванович"
    },
    "шопен": {
        "era": "romantic",
        "birth": 1810,
        "death": 1849,
        "full_name": "Фредерик Шопен",
        "bio": "Великий польский композитор, пианист-виртуоз. Поэзия фортепиано.",
        "wiki": "https://ru.wikipedia.org/wiki/Шопен,_Фредерик",
        "wiki_title": "Шопен, Фредерик"
    },
    "шuman": {
        "era": "romantic",
        "birth": 1810,
        "death": 1856,
        "full_name": "Роберт Шуман",
        "bio": "Немецкий композитор, пианист, музыкальный критик.",
        "wiki": "https://ru.wikipedia.org/wiki/Шуман,_Роберт",
        "wiki_title": "Шуман, Роберт"
    },
    "лист": {
        "era": "romantic",
        "birth": 1811,
        "death": 1886,
        "full_name": "Ференц Лист",
        "bio": "Венгерский композитор, пианист-виртуоз. Создатель жанра симфонической поэмы.",
        "wiki": "https://ru.wikipedia.org/wiki/Лист,_Ференц",
        "wiki_title": "Лист, Ференц"
    },
    "вагнер": {
        "era": "romantic",
        "birth": 1813,
        "death": 1883,
        "full_name": "Рихард Вагнер",
        "bio": "Немецкий композитор, реформатор оперного жанра.",
        "wiki": "https://ru.wikipedia.org/wiki/Вагнер,_Рихард",
        "wiki_title": "Вагнер, Рихард"
    },
    "верди": {
        "era": "romantic",
        "birth": 1813,
        "death": 1901,
        "full_name": "Джузеппе Верди",
        "bio": "Великий итальянский композитор, вершина оперного жанра.",
        "wiki": "https://ru.wikipedia.org/wiki/Верди,_Джузеппе",
        "wiki_title": "Верди, Джузеппе"
    },
    "берлиоз": {
        "era": "romantic",
        "birth": 1803,
        "death": 1869,
        "full_name": "Гектор Берлиоз",
        "bio": "Французский композитор, дирижёр. Крупнейший представитель французского романтизма.",
        "wiki": "https://ru.wikipedia.org/wiki/Берлиоз,_Гектор",
        "wiki_title": "Берлиоз, Гектор"
    },
    "мендельсон": {
        "era": "romantic",
        "birth": 1809,
        "death": 1847,
        "full_name": "Феликс Мендельсон-Бартольди",
        "bio": "Немецкий композитор и дирижёр. Возродил музыку Баха.",
        "wiki": "https://ru.wikipedia.org/wiki/Мендельсон,_Феликс",
        "wiki_title": "Мендельсон, Феликс"
    },
    "брамс": {
        "era": "romantic",
        "birth": 1833,
        "death": 1897,
        "full_name": "Иоганнес Брамс",
        "bio": "Немецкий композитор, один из главных представителей романтизма.",
        "wiki": "https://ru.wikipedia.org/wiki/Брамс,_Иоганнес",
        "wiki_title": "Брамс, Иоганнес"
    },
    "бизе": {
        "era": "romantic",
        "birth": 1838,
        "death": 1875,
        "full_name": "Жорж Бизе",
        "bio": "Французский композитор, автор оперы «Кармен».",
        "wiki": "https://ru.wikipedia.org/wiki/Бизе,_Жорж",
        "wiki_title": "Бизе, Жорж"
    },
    "муссоргский": {
        "era": "romantic",
        "birth": 1839,
        "death": 1881,
        "full_name": "Модест Петрович Мусоргский",
        "bio": "Русский композитор, член «Могучей кучки».",
        "wiki": "https://ru.wikipedia.org/wiki/Мусоргский,_Модест_Петрович",
        "wiki_title": "Мусоргский, Модест Петрович"
    },
    "чайковский": {
        "era": "romantic",
        "birth": 1840,
        "death": 1893,
        "full_name": "Пётр Ильич Чайковский",
        "bio": "Великий русский композитор. Балеты «Лебединое озеро», «Щелкунчик».",
        "wiki": "https://ru.wikipedia.org/wiki/Чайковский,_Пётр_Ильич",
        "wiki_title": "Чайковский, Пётр Ильич"
    },
    "дворжак": {
        "era": "romantic",
        "birth": 1841,
        "death": 1904,
        "full_name": "Антонин Леопольд Дворжак",
        "bio": "Чешский композитор, один из крупнейших представителей романтизма.",
        "wiki": "https://ru.wikipedia.org/wiki/Дворжак,_Антонин",
        "wiki_title": "Дворжак, Антонин"
    },
    "григ": {
        "era": "romantic",
        "birth": 1843,
        "death": 1907,
        "full_name": "Эдвард Хагеруп Григ",
        "bio": "Норвежский композитор. Музыка к драме «Пер Гюнт».",
        "wiki": "https://ru.wikipedia.org/wiki/Григ,_Эдвард",
        "wiki_title": "Григ, Эдвард"
    },
    "римский-корсаков": {
        "era": "romantic",
        "birth": 1844,
        "death": 1908,
        "full_name": "Николай Андреевич Римский-Корсаков",
        "bio": "Русский композитор, педагог, дирижёр. Мастер оркестровой палитры.",
        "wiki": "https://ru.wikipedia.org/wiki/Римский-Корсаков,_Николай_Андреевич",
        "wiki_title": "Римский-Корсаков, Николай Андреевич"
    },
    "бородин": {
        "era": "romantic",
        "birth": 1833,
        "death": 1887,
        "full_name": "Александр Порфирьевич Бородин",
        "bio": "Русский композитор и учёный-химик. Опера «Князь Игорь».",
        "wiki": "https://ru.wikipedia.org/wiki/Бородин,_Александр_Порфирьевич",
        "wiki_title": "Бородин, Александр Порфирьевич"
    },
    "малер": {
        "era": "romantic",
        "birth": 1860,
        "death": 1911,
        "full_name": "Густав Малер",
        "bio": "Австрийский композитор, один из крупнейших представителей позднего романтизма.",
        "wiki": "https://ru.wikipedia.org/wiki/Малер,_Густав",
        "wiki_title": "Малер, Густав"
    },
    "рахманинов": {
        "era": "romantic",
        "birth": 1873,
        "death": 1943,
        "full_name": "Сергей Васильевич Рахманинов",
        "bio": "Великий русский композитор, пианист и дирижёр.",
        "wiki": "https://ru.wikipedia.org/wiki/Рахманинов,_Сергей_Васильевич",
        "wiki_title": "Рахманинов, Сергей Васильевич"
    },
    "скрябин": {
        "era": "romantic",
        "birth": 1872,
        "death": 1915,
        "full_name": "Александр Николаевич Скрябин",
        "bio": "Русский композитор и пианист. Уникальный синтез романтизма и символизма.",
        "wiki": "https://ru.wikipedia.org/wiki/Скрябин,_Александр_Николаевич",
        "wiki_title": "Скрябин, Александр Николаевич"
    },
    "сибелиус": {
        "era": "romantic",
        "birth": 1865,
        "death": 1957,
        "full_name": "Ян Сибелиус",
        "bio": "Финский композитор. Символ финской национальной музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Сибелиус,_Ян",
        "wiki_title": "Сибелиус, Ян"
    },
    "пучини": {
        "era": "romantic",
        "birth": 1858,
        "death": 1924,
        "full_name": "Джакомо Пуччини",
        "bio": "Итальянский оперный композитор. «Богема», «Тоска», «Мадам Баттерфляй».",
        "wiki": "https://ru.wikipedia.org/wiki/Пуччини,_Джакомо",
        "wiki_title": "Пуччини, Джакомо"
    },
    "штраус": {
        "era": "romantic",
        "birth": 1864,
        "death": 1949,
        "full_name": "Рихард Штраус",
        "bio": "Немецкий композитор и дирижёр позднего романтизма.",
        "wiki": "https://ru.wikipedia.org/wiki/Штраус,_Рихард",
        "wiki_title": "Штраус, Рихард"
    },
    
    # ============================================================
    # МОДЕРН (Modern)
    # ============================================================
    "дебюсси": {
        "era": "modern",
        "birth": 1862,
        "death": 1918,
        "full_name": "Клод Ашиль Дебюсси",
        "bio": "Французский композитор, основоположник музыкального импрессионизма.",
        "wiki": "https://ru.wikipedia.org/wiki/Дебюсси,_Клод",
        "wiki_title": "Дебюсси, Клод"
    },
    "сати": {
        "era": "modern",
        "birth": 1866,
        "death": 1925,
        "full_name": "Эрик Альфред Лесли Сати",
        "bio": "Французский композитор, предшественник музыкального минимализма.",
        "wiki": "https://ru.wikipedia.org/wiki/Сати,_Эрик",
        "wiki_title": "Сати, Эрик"
    },
    "равель": {
        "era": "modern",
        "birth": 1875,
        "death": 1937,
        "full_name": "Морис Равель",
        "bio": "Французский композитор-импрессионист. Его «Болеро» — мировое признание.",
        "wiki": "https://ru.wikipedia.org/wiki/Равель,_Морис",
        "wiki_title": "Равель, Морис"
    },
    "барток": {
        "era": "modern",
        "birth": 1881,
        "death": 1945,
        "full_name": "Бела Барток",
        "bio": "Венгерский композитор, пианист и этномузыколог.",
        "wiki": "https://ru.wikipedia.org/wiki/Барток,_Бела",
        "wiki_title": "Барток, Бела"
    },
    "стравинский": {
        "era": "modern",
        "birth": 1882,
        "death": 1971,
        "full_name": "Игорь Фёдорович Стравинский",
        "bio": "Великий русский композитор, один из главных новаторов XX века.",
        "wiki": "https://ru.wikipedia.org/wiki/Стравинский,_Игорь_Фёдорович",
        "wiki_title": "Стравинский, Игорь Фёдорович"
    },
    "прокофьев": {
        "era": "modern",
        "birth": 1891,
        "death": 1953,
        "full_name": "Сергей Сергеевич Прокофьев",
        "bio": "Великий русский композитор. «Ромео и Джульетта», «Петя и волк».",
        "wiki": "https://ru.wikipedia.org/wiki/Прокофьев,_Сергей_Сергеевич",
        "wiki_title": "Прокофьев, Сергей Сергеевич"
    },
    "копленд": {
        "era": "modern",
        "birth": 1900,
        "death": 1990,
        "full_name": "Аарон Копленд",
        "bio": "Американский композитор, создатель «американского звучания».",
        "wiki": "https://ru.wikipedia.org/wiki/Копленд,_Аарон",
        "wiki_title": "Копленд, Аарон"
    },
    "хачатурян": {
        "era": "modern",
        "birth": 1903,
        "death": 1978,
        "full_name": "Арам Ильич Хачатурян",
        "bio": "Армянский советский композитор. «Танец с саблями».",
        "wiki": "https://ru.wikipedia.org/wiki/Хачатурян,_Арам_Ильич",
        "wiki_title": "Хачатурян, Арам Ильич"
    },
    "шостакович": {
        "era": "modern",
        "birth": 1906,
        "death": 1975,
        "full_name": "Дмитрий Дмитриевич Шостакович",
        "bio": "Великий русский композитор. 15 симфоний — музыкальная летопись XX века.",
        "wiki": "https://ru.wikipedia.org/wiki/Шостакович,_Дмитрий_Дмитриевич",
        "wiki_title": "Шостакович, Дмитрий Дмитриевич"
    },
    
    # ============================================================
    # СОВРЕМЕННАЯ (Contemporary)
    # ============================================================
    "мессиан": {
        "era": "contemporary",
        "birth": 1908,
        "death": 1992,
        "full_name": "Оливье Мессиан",
        "bio": "Французский композитор, органист, орнитолог.",
        "wiki": "https://ru.wikipedia.org/wiki/Мессиан,_Оливье",
        "wiki_title": "Мессиан, Оливье"
    },
    "кейдж": {
        "era": "contemporary",
        "birth": 1912,
        "death": 1992,
        "full_name": "Джон Милтон Кейдж",
        "bio": "Американский композитор, философ музыки. Пьеса «4'33\"».",
        "wiki": "https://ru.wikipedia.org/wiki/Кейдж,_Джон",
        "wiki_title": "Кейдж, Джон"
    },
    "шнитке": {
        "era": "contemporary",
        "birth": 1934,
        "death": 1998,
        "full_name": "Альфред Гарриевич Шнитке",
        "bio": "Русский композитор, создатель стиля «полистилистика».",
        "wiki": "https://ru.wikipedia.org/wiki/Шнитке,_Альфред_Гарриевич",
        "wiki_title": "Шнитке, Альфред Гарриевич"
    },
    "пярт": {
        "era": "contemporary",
        "birth": 1935,
        "death": None,
        "full_name": "Арво Пярт",
        "bio": "Эстонский композитор, создатель стиля «колокольного звона».",
        "wiki": "https://ru.wikipedia.org/wiki/Пярт,_Арво",
        "wiki_title": "Пярт, Арво"
    },
    "эйнауди": {
        "era": "contemporary",
        "birth": 1955,
        "death": None,
        "full_name": "Людовико Эйнауди",
        "bio": "Итальянский композитор и пианист. Один из самых исполняемых современных композиторов.",
        "wiki": "https://ru.wikipedia.org/wiki/Эйнауди,_Людовико",
        "wiki_title": "Эйнауди, Людовико"
    },
}

# ===================== ФУНКЦИИ ДЛЯ РАБОТЫ С ФОТОГРАФИЯМИ =====================

async def get_wikipedia_image(wiki_title: str) -> Optional[str]:
    """
    Получает URL изображения композитора через Wikipedia API
    """
    if not wiki_title:
        return None
    
    encoded_title = urllib.parse.quote(wiki_title)
    
    # Первый запрос: получаем информацию о странице и изображении
    api_url = f"https://ru.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&pithumbsize=300&titles={encoded_title}"
    
    try:
        headers = {
            'User-Agent': 'ClassicalEraBot/1.0 (https://t.me/your_bot; your_email@example.com)'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page_id, page_data in pages.items():
                        if "thumbnail" in page_data:
                            image_url = page_data["thumbnail"].get("source")
                            if image_url:
                                # Меняем размер на больший
                                image_url = image_url.replace("/300px-", "/400px-")
                                return image_url
                    return None
                else:
                    logger.warning(f"Ошибка Wikipedia API: {response.status}")
                    return None
    except Exception as e:
        logger.warning(f"Ошибка при получении изображения: {e}")
        return None

async def download_image_as_bytes(image_url: str) -> Optional[bytes]:
    """
    Скачивает изображение и возвращает его как bytes
    """
    if not image_url:
        return None
    
    try:
        headers = {
            'User-Agent': 'ClassicalEraBot/1.0 (https://t.me/your_bot; your_email@example.com)'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.warning(f"Не удалось скачать изображение: {response.status}")
                    return None
    except Exception as e:
        logger.warning(f"Ошибка при скачивании изображения: {e}")
        return None

# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================

def normalize_text(text: str) -> str:
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

def find_composer_in_text(text: str) -> Tuple[Optional[str], Optional[Dict]]:
    normalized = normalize_text(text)
    words = normalized.split()
    
    for composer, data in COMPOSERS_DB.items():
        composer_lower = composer.lower()
        if composer_lower in normalized:
            return composer, data
        if len(composer_lower) > 5:
            for part in composer_lower.split():
                if len(part) > 3 and part in words:
                    return composer, data
    return None, None

def find_year_in_text(text: str) -> Optional[int]:
    pattern = r'\b(1[0-9]{3}|2[0-9]{3})\b'
    matches = re.findall(pattern, text)
    if matches:
        return int(matches[0])
    return None

def get_era_by_year(year: int) -> Optional[str]:
    for era_key, era_data in ERAS.items():
        if era_data["year_start"] <= year <= era_data["year_end"]:
            return era_key
    return None

def get_music_links(composer_data: Dict, search_query: str = None) -> Dict[str, str]:
    if composer_data:
        full_name = composer_data.get("full_name", "")
        query = full_name
    else:
        query = search_query or ""
    
    encoded_query = urllib.parse.quote(query)
    
    return {
        "apple": f"https://music.apple.com/search?term={encoded_query}",
        "yandex": f"https://music.yandex.ru/search?text={encoded_query}",
        "spotify": f"https://open.spotify.com/search/{encoded_query}"
    }

def format_years_life(composer_data: Dict) -> str:
    birth = composer_data.get("birth")
    death = composer_data.get("death")
    if birth:
        if death:
            return f"{birth} – {death}"
        else:
            return f"{birth} – н.в."
    return ""

def format_composer_response(composer_key: str, composer_data: Dict, image_url: str = None) -> Tuple[str, str, Dict[str, str]]:
    era_key = composer_data.get("era")
    era_data = ERAS.get(era_key)
    
    full_name = composer_data.get("full_name", composer_key.title())
    years_life = format_years_life(composer_data)
    bio = composer_data.get("bio", "Информация о композиторе уточняется.")
    wiki_link = composer_data.get("wiki", "#")
    
    message = f"""<b>{era_data['emoji']} Эпоха:</b> {era_data['name']}
<b>📅 Период:</b> {era_data['year_start']}–{era_data['year_end']}

<b>🎵 Композитор:</b> {full_name}
<b>📅 Годы жизни:</b> {years_life}

<b>📖 Краткая биография:</b>
{bio}

<b>📌 Эпоха:</b> {era_data['description']}

<b>🔍 Поиск музыки по имени композитора:</b>"""
    
    links = get_music_links(composer_data, full_name)
    
    return message, image_url, wiki_link, links

def format_unknown_response(text: str) -> Tuple[str, Dict[str, str]]:
    year = find_year_in_text(text)
    if year:
        era_key = get_era_by_year(year)
        if era_key:
            era_data = ERAS[era_key]
            links = get_music_links(None, text[:50])
            
            message = f"""🔍 <b>Композитор не найден</b>, но я определил эпоху по году {year}:

<b>{era_data['emoji']} Эпоха:</b> {era_data['name']}
<b>📅 Период:</b> {era_data['year_start']}–{era_data['year_end']}

<b>📌 Эпоха:</b> {era_data['description']}

<b>🔍 Поиск по вашему запросу:</b> «{text[:50]}»"""
            return message, links
    
    links = get_music_links(None, text[:50])
    
    message = f"""⚠️ <b>Не удалось определить эпоху</b>

Я не нашел композитора <b>«{text[:50]}»</b> в своей базе данных и не смог определить год.

<b>Пожалуйста, уточните:</b>
• Полное имя композитора
• Год создания произведения (например, 1824)

<b>🔍 Поиск по вашему запросу:</b> «{text[:50]}»"""
    
    return message, links

# ===================== ОБРАБОТЧИКИ КОМАНД =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_text = f"""👋 <b>Привет, {user.first_name}!</b>

Я — <b>ClassicalEraBot</b> 🎼
Я помогаю изучать классическую музыку и её композиторов!

<b>Что я умею:</b>
• 📚 Определяю эпоху по имени композитора или году
• 👤 Показываю полное имя, годы жизни и биографию
• 🖼️ Присылаю фотографию композитора
• 🔍 Даю ссылки на поиск в Apple Music, Яндекс Музыке и Spotify

<b>В базе более 60 композиторов!</b>

<b>Примеры запросов:</b>
• <i>«Бах»</i> → Иоганн Себастьян Бах
• <i>«Рахманинов»</i> → Сергей Васильевич Рахманинов
• <i>«Глинка»</i> → Михаил Иванович Глинка

<b>Команды:</b>
/start - Приветствие
/help - Справка
/eras - Список эпох
/composers - Список композиторов"""
    
    keyboard = [
        [InlineKeyboardButton("📖 Помощь", callback_data="help")],
        [InlineKeyboardButton("🎵 Все эпохи", callback_data="eras")],
        [InlineKeyboardButton("🎼 Список композиторов", callback_data="composers")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """📖 <b>Справка по боту</b>

<b>Как пользоваться:</b>
Просто отправьте мне имя композитора или название произведения.

<b>Примеры:</b>
• <i>«Моцарт»</i> → покажу Вольфганга Амадея Моцарта
• <i>«Бах»</i> → покажу Иоганна Себастьяна Баха
• <i>«Глинка»</i> → покажу Михаила Ивановича Глинку
• <i>«1824»</i> → определю эпоху по году

<b>Команды:</b>
/start - Приветствие
/help - Эта справка
/eras - Список всех эпох
/composers - Все композиторы в базе

<b>В базе более 60 композиторов!</b>

<b>Что вы получите в ответе:</b>
• 🖼️ Фото композитора
• 👤 Полное имя
• 📅 Годы жизни
• 📖 Краткая биография
• 📚 Ссылка на Википедию
• 🔍 Ссылки на музыкальные сервисы"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def eras_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    eras_text = "<b>📚 Доступные эпохи:</b>\n\n"
    for key, era in ERAS.items():
        eras_text += f"{era['emoji']} <b>{era['name']}</b>\n"
        eras_text += f"   📅 {era['year_start']}–{era['year_end']}\n"
        eras_text += f"   📌 {era['description']}\n\n"
    
    await update.message.reply_text(eras_text, parse_mode='HTML')

async def composers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    composers_by_era = {}
    for key, data in COMPOSERS_DB.items():
        era = data.get("era", "unknown")
        if era not in composers_by_era:
            composers_by_era[era] = []
        composers_by_era[era].append(data.get("full_name", key.title()))
    
    sorted_eras = [e for e in ERAS.keys() if e in composers_by_era]
    
    text = "<b>🎼 Все композиторы в базе:</b>\n\n"
    for era_key in sorted_eras:
        era_data = ERAS.get(era_key)
        if era_data and era_key in composers_by_era:
            names = sorted(composers_by_era[era_key])
            text += f"{era_data['emoji']} <b>{era_data['name']}</b>\n"
            for name in names:
                text += f"   • {name}\n"
            text += "\n"
    
    if len(text) > 4096:
        await update.message.reply_document(
            document=text.encode('utf-8'),
            filename="composers.txt",
            caption="📋 Полный список композиторов"
        )
    else:
        await update.message.reply_text(text, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    logger.info(f"Получено сообщение: {user_text}")
    
    composer_key, composer_data = find_composer_in_text(user_text)
    
    if composer_key and composer_data:
        era_key = composer_data.get("era")
        if era_key and ERAS.get(era_key):
            status_message = await update.message.reply_text("🔄 Ищу информацию о композиторе...")
            
            # Пытаемся получить фото через Wikipedia API
            image_url = None
            wiki_title = composer_data.get("wiki_title")
            if wiki_title:
                image_url = await get_wikipedia_image(wiki_title)
                logger.info(f"Получено фото для {composer_key}: {image_url}")
            
            message, image_url, wiki_link, links = format_composer_response(
                composer_key, composer_data, image_url
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🍎 Apple Music", url=links["apple"]),
                    InlineKeyboardButton("🎵 Яндекс Музыка", url=links["yandex"])
                ],
                [
                    InlineKeyboardButton("🎧 Spotify", url=links["spotify"])
                ],
                [
                    InlineKeyboardButton("📖 Википедия", url=wiki_link)
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_message.delete()
            
            if image_url:
                try:
                    # Скачиваем изображение и отправляем как файл
                    image_bytes = await download_image_as_bytes(image_url)
                    if image_bytes:
                        await update.message.reply_photo(
                            photo=image_bytes,
                            caption=message,
                            parse_mode='HTML',
                            reply_markup=reply_markup
                        )
                    else:
                        await update.message.reply_text(
                            message,
                            parse_mode='HTML',
                            reply_markup=reply_markup,
                            disable_web_page_preview=True
                        )
                except Exception as e:
                    logger.warning(f"Не удалось отправить фото: {e}")
                    await update.message.reply_text(
                        message,
                        parse_mode='HTML',
                        reply_markup=reply_markup,
                        disable_web_page_preview=True
                    )
            else:
                await update.message.reply_text(
                    message,
                    parse_mode='HTML',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            
            logger.info(f"Определен композитор {composer_key} → {era_key}")
            return
    
    year = find_year_in_text(user_text)
    if year:
        era_key = get_era_by_year(year)
        if era_key:
            message, links = format_unknown_response(user_text)
            
            keyboard = [
                [
                    InlineKeyboardButton("🍎 Apple Music", url=links["apple"]),
                    InlineKeyboardButton("🎵 Яндекс Музыка", url=links["yandex"])
                ],
                [
                    InlineKeyboardButton("🎧 Spotify", url=links["spotify"])
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode='HTML',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            logger.info(f"Определена эпоха по году {year} → {era_key}")
            return
    
    message, links = format_unknown_response(user_text)
    
    keyboard = [
        [
            InlineKeyboardButton("🍎 Apple Music", url=links["apple"]),
            InlineKeyboardButton("🎵 Яндекс Музыка", url=links["yandex"])
        ],
        [
            InlineKeyboardButton("🎧 Spotify", url=links["spotify"])
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    logger.warning(f"Не удалось определить эпоху для: {user_text}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await query.edit_message_text(
            """📖 <b>Справка</b>

Отправь мне имя композитора или название произведения.

<b>Примеры:</b>
• Моцарт → Вольфганг Амадей Моцарт
• Бах → Иоганн Себастьян Бах
• Глинка → Михаил Иванович Глинка
• 1824 → определю эпоху по году

<b>В ответе вы получите:</b>
• 🖼️ Фото композитора
• 👤 Полное имя
• 📅 Годы жизни
• 📖 Краткая биография
• 📚 Ссылка на Википедию
• 🔍 Ссылки на музыкальные сервисы""",
            parse_mode='HTML'
        )
    elif query.data == "eras":
        eras_text = "<b>📚 Доступные эпохи:</b>\n\n"
        for key, era in ERAS.items():
            eras_text += f"{era['emoji']} <b>{era['name']}</b>\n"
            eras_text += f"   📅 {era['year_start']}–{era['year_end']}\n"
            eras_text += f"   📌 {era['description']}\n\n"
        await query.edit_message_text(eras_text, parse_mode='HTML')
    elif query.data == "composers":
        await query.edit_message_text(
            "🎼 Используйте команду /composers, чтобы увидеть полный список композиторов в базе.",
            parse_mode='HTML'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Ошибка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "😅 Произошла ошибка. Пожалуйста, попробуйте еще раз."
        )

# ===================== ЗАПУСК БОТА =====================

def main() -> None:
    logger.info("🚀 Бот запускается...")
    logger.info(f"📋 Токен: {BOT_TOKEN[:10]}... (скрыто для безопасности)")
    logger.info(f"📊 Загружено композиторов: {len(COMPOSERS_DB)}")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("eras", eras_command))
    application.add_handler(CommandHandler("composers", composers_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот успешно инициализирован, запускаем polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()