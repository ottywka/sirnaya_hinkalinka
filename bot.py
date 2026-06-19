"""
TELEGRAM-БОТ ДЛЯ РАСПРЕДЕЛЕНИЯ КЛАССИЧЕСКОЙ МУЗЫКИ ПО ЭПОХАМ
Версия: Bothost (с полными именами, биографией и фото композиторов)
"""

import os
import re
import logging
import urllib.parse
from datetime import datetime
from typing import Dict, Optional, Tuple, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
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
        "description": "Эпоха, охватывающая григорианский хорал, музыку трубадуров и раннюю полифонию. Это время зарождения европейской музыкальной традиции."
    },
    "baroque": {
        "name": "Барокко (Baroque)",
        "name_en": "Baroque",
        "year_start": 1600,
        "year_end": 1749,
        "emoji": "👑",
        "description": "Эпоха пышности, контрастов и полифонии. Рождение оперы, развитие инструментальной музыки. Бах, Вивальди, Гендель — вершины этого периода."
    },
    "classical": {
        "name": "Классицизм (Classical)",
        "name_en": "Classical",
        "year_start": 1750,
        "year_end": 1819,
        "emoji": "🏛️",
        "description": "Эпоха гармонии, ясности и сонатной формы. Венские классики — Гайдн, Моцарт, Бетховен — создали музыкальный язык, который мы называем классическим."
    },
    "romantic": {
        "name": "Романтизм (Romantic)",
        "name_en": "Romantic",
        "year_start": 1820,
        "year_end": 1899,
        "emoji": "🌹",
        "description": "Эпоха эмоций, страстей и индивидуальности. Музыка становится программной, расширяется оркестр, рождается национальная музыкальная идентичность."
    },
    "modern": {
        "name": "Импрессионизм / Модерн (Modern)",
        "name_en": "Modern",
        "year_start": 1900,
        "year_end": 1949,
        "emoji": "🎨",
        "description": "Эпоха поиска новых звуковых красок и отказ от традиционной тональности. Дебюсси, Стравинский, Шостакович — это время музыкальных революций."
    },
    "contemporary": {
        "name": "Современная академическая (Contemporary)",
        "name_en": "Contemporary",
        "year_start": 1950,
        "year_end": datetime.now().year,
        "emoji": "🔮",
        "description": "Эпоха минимализма, алеаторики и электронной музыки. Композиторы ищут новые формы, звуки и способы взаимодействия со слушателем."
    }
}

# ===================== РАСШИРЕННАЯ БАЗА КОМПОЗИТОРОВ =====================

COMPOSERS_DB = {
    # ===== РАННЯЯ МУЗЫКА =====
    "машо": {
        "era": "medieval",
        "birth": 1300,
        "death": 1377,
        "full_name": "Гильом де Машо",
        "bio": "Французский поэт и композитор эпохи Средневековья. Ключевая фигура Ars Nova, автор одной из первых полных месс в истории.",
        "wiki": "https://ru.wikipedia.org/wiki/Машо,_Гильом_де",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Machaut.jpg/220px-Machaut.jpg"
    },
    "ландини": {
        "era": "medieval",
        "birth": 1325,
        "death": 1397,
        "full_name": "Франческо Ландини",
        "bio": "Итальянский композитор, органист и поэт эпохи Треченто. Один из крупнейших композиторов итальянского Ars Nova.",
        "wiki": "https://ru.wikipedia.org/wiki/Ландини,_Франческо",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Landini.jpg/220px-Landini.jpg"
    },
    "таллис": {
        "era": "medieval",
        "birth": 1505,
        "death": 1585,
        "full_name": "Томас Таллис",
        "bio": "Английский композитор эпохи Ренессанса. Гениальный полифонист, работавший при дворах четырёх английских монархов.",
        "wiki": "https://ru.wikipedia.org/wiki/Таллис,_Томас",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Thomas_Tallis.jpg/220px-Thomas_Tallis.jpg"
    },
    "палестрина": {
        "era": "medieval",
        "birth": 1525,
        "death": 1594,
        "full_name": "Джованни Пьерлуиджи да Палестрина",
        "bio": "Итальянский композитор эпохи Ренессанса. Его мессы и мотеты стали эталоном церковной полифонии.",
        "wiki": "https://ru.wikipedia.org/wiki/Палестрина,_Джованни_Пьерлуиджи_да",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/Palestrina.jpg/220px-Palestrina.jpg"
    },
    
    # ===== БАРОККО =====
    "вивальди": {
        "era": "baroque",
        "birth": 1678,
        "death": 1741,
        "full_name": "Антонио Лучо Вивальди",
        "bio": "Итальянский композитор, скрипач-виртуоз, педагог и священник. Один из величайших представителей венецианской школы. Автор более 500 концертов.",
        "wiki": "https://ru.wikipedia.org/wiki/Вивальди,_Антонио",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Antonio_Vivaldi.jpg/220px-Antonio_Vivaldi.jpg"
    },
    "бах": {
        "era": "baroque",
        "birth": 1685,
        "death": 1750,
        "full_name": "Иоганн Себастьян Бах",
        "bio": "Великий немецкий композитор, органист, капельмейстер. Его творчество — вершина полифонии и всей барочной музыки. Автор «Хорошо темперированного клавира», мессы си-минор, Страстей по Матфею.",
        "wiki": "https://ru.wikipedia.org/wiki/Бах,_Иоганн_Себастьян",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Johann_Sebastian_Bach.jpg/220px-Johann_Sebastian_Bach.jpg"
    },
    "гендель": {
        "era": "baroque",
        "birth": 1685,
        "death": 1759,
        "full_name": "Георг Фридрих Гендель",
        "bio": "Немецкий и английский композитор эпохи барокко. Мастер ораториального жанра, автор знаменитой оратории «Мессия».",
        "wiki": "https://ru.wikipedia.org/wiki/Гендель,_Георг_Фридрих",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Georg_Friedrich_Händel.jpg/220px-Georg_Friedrich_Händel.jpg"
    },
    "монтеверди": {
        "era": "baroque",
        "birth": 1567,
        "death": 1643,
        "full_name": "Клаудио Монтеверди",
        "bio": "Итальянский композитор, основоположник оперного жанра. Его опера «Орфей» считается первой великой оперой в истории музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Монтеверди,_Клаудио",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Monteverdi.jpg/220px-Monteverdi.jpg"
    },
    "корелли": {
        "era": "baroque",
        "birth": 1653,
        "death": 1713,
        "full_name": "Арканджело Корелли",
        "bio": "Итальянский скрипач и композитор, основоположник римской скрипичной школы. Его сонаты и концерты стали эталоном для современников.",
        "wiki": "https://ru.wikipedia.org/wiki/Корелли,_Арканджело",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Arcangelo_Corelli.jpg/220px-Arcangelo_Corelli.jpg"
    },
    "пёрселл": {
        "era": "baroque",
        "birth": 1659,
        "death": 1695,
        "full_name": "Генри Пёрселл",
        "bio": "Английский композитор, крупнейший представитель английской барочной музыки. Автор оперы «Дидона и Эней».",
        "wiki": "https://ru.wikipedia.org/wiki/Пёрселл,_Генри",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Henry_Purcell.jpg/220px-Henry_Purcell.jpg"
    },
    "рамо": {
        "era": "baroque",
        "birth": 1683,
        "death": 1764,
        "full_name": "Жан-Филипп Рамо",
        "bio": "Французский композитор и теоретик музыки. Реформировал французскую оперу, создал трактат «Трактат о гармонии».",
        "wiki": "https://ru.wikipedia.org/wiki/Рамо,_Жан-Филипп",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Jean-Philippe_Rameau.jpg/220px-Jean-Philippe_Rameau.jpg"
    },
    "пахельбель": {
        "era": "baroque",
        "birth": 1653,
        "death": 1706,
        "full_name": "Иоганн Пахельбель",
        "bio": "Немецкий органист и композитор. Его знаменитый «Канон ре-мажор» — одно из самых узнаваемых произведений классической музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Пахельбель,_Иоганн",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Pachelbel.jpg/220px-Pachelbel.jpg"
    },
    "телеман": {
        "era": "baroque",
        "birth": 1681,
        "death": 1767,
        "full_name": "Георг Филипп Телеман",
        "bio": "Немецкий композитор, органист и капельмейстер. Один из самых плодовитых композиторов в истории музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Телеман,_Георг_Филипп",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Telemann.jpg/220px-Telemann.jpg"
    },
    "альбинони": {
        "era": "baroque",
        "birth": 1671,
        "death": 1751,
        "full_name": "Томазо Джованни Альбинони",
        "bio": "Итальянский композитор эпохи барокко. Его «Адажио соль-минор» — одно из самых популярных произведений классической музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Альбинони,_Томазо",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Tomaso_Albinoni.jpg/220px-Tomaso_Albinoni.jpg"
    },
    "тартини": {
        "era": "baroque",
        "birth": 1692,
        "death": 1770,
        "full_name": "Джузеппе Тартини",
        "bio": "Итальянский скрипач и композитор. Автор знаменитой сонаты для скрипки «Дьявольские трели».",
        "wiki": "https://ru.wikipedia.org/wiki/Тартини,_Джузеппе",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Tartini.jpg/220px-Tartini.jpg"
    },
    
    # ===== КЛАССИЦИЗМ =====
    "моцарт": {
        "era": "classical",
        "birth": 1756,
        "death": 1791,
        "full_name": "Вольфганг Амадей Моцарт",
        "bio": "Великий австрийский композитор, представитель венской классической школы. Его творчество — вершина классического стиля. Автор более 600 произведений, включая оперы «Свадьба Фигаро», «Дон Жуан», «Волшебная флейта».",
        "wiki": "https://ru.wikipedia.org/wiki/Моцарт,_Вольфганг_Амадей",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Wolfgang_Amadeus_Mozart_2.jpg/220px-Wolfgang_Amadeus_Mozart_2.jpg"
    },
    "бетховен": {
        "era": "classical",
        "birth": 1770,
        "death": 1827,
        "full_name": "Людвиг ван Бетховен",
        "bio": "Великий немецкий композитор, последний представитель венской классической школы. Его музыка стала мостом между классицизмом и романтизмом. Автор 9 симфоний, «Лунной сонаты» и «Аппассионаты».",
        "wiki": "https://ru.wikipedia.org/wiki/Бетховен,_Людвиг_ван",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Beethoven.jpg/220px-Beethoven.jpg"
    },
    "гайдн": {
        "era": "classical",
        "birth": 1732,
        "death": 1809,
        "full_name": "Йозеф Гайдн",
        "bio": "Австрийский композитор, основоположник венской классической школы, «отец симфонии» и «отец струнного квартета». Автор 104 симфоний.",
        "wiki": "https://ru.wikipedia.org/wiki/Гайдн,_Йозеф",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Joseph_Haydn.jpg/220px-Joseph_Haydn.jpg"
    },
    "глюк": {
        "era": "classical",
        "birth": 1714,
        "death": 1787,
        "full_name": "Кристоф Виллибальд Глюк",
        "bio": "Немецкий композитор, реформатор оперного жанра. Его оперы «Орфей и Эвридика» и «Альцеста» стали манифестом нового оперного стиля.",
        "wiki": "https://ru.wikipedia.org/wiki/Глюк,_Кристоф_Виллибальд",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Gluck.jpg/220px-Gluck.jpg"
    },
    "сальери": {
        "era": "classical",
        "birth": 1750,
        "death": 1825,
        "full_name": "Антонио Сальери",
        "bio": "Итальянский и австрийский композитор, педагог. Придворный капельмейстер в Вене. Учитель Бетховена, Шуберта и Листа.",
        "wiki": "https://ru.wikipedia.org/wiki/Сальери,_Антонио",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Salieri.jpg/220px-Salieri.jpg"
    },
    "клементи": {
        "era": "classical",
        "birth": 1752,
        "death": 1832,
        "full_name": "Муцио Клементи",
        "bio": "Итальянский композитор и пианист, основатель лондонской фортепианной школы. Его этюды до сих пор входят в репертуар пианистов.",
        "wiki": "https://ru.wikipedia.org/wiki/Клементи,_Муцио",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Muzio_Clementi.jpg/220px-Muzio_Clementi.jpg"
    },
    
    # ===== РОМАНТИЗМ =====
    "шуберт": {
        "era": "romantic",
        "birth": 1797,
        "death": 1828,
        "full_name": "Франц Петер Шуберт",
        "bio": "Австрийский композитор, основоположник романтизма в музыке. Создатель вокального цикла «Прекрасная мельничиха». Автор более 600 песен.",
        "wiki": "https://ru.wikipedia.org/wiki/Шуберт,_Франц",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Schubert.jpg/220px-Schubert.jpg"
    },
    "шопен": {
        "era": "romantic",
        "birth": 1810,
        "death": 1849,
        "full_name": "Фредерик Шопен",
        "bio": "Великий польский композитор, пианист-виртуоз. Его музыка — поэзия фортепиано. Автор мазурок, полонезов, этюдов и ноктюрнов.",
        "wiki": "https://ru.wikipedia.org/wiki/Шопен,_Фредерик",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Frederic_Chopin.jpg/220px-Frederic_Chopin.jpg"
    },
    "лист": {
        "era": "romantic",
        "birth": 1811,
        "death": 1886,
        "full_name": "Ференц Лист",
        "bio": "Венгерский композитор, пианист-виртуоз, дирижёр. Крупнейший представитель музыкального романтизма, создатель жанра симфонической поэмы.",
        "wiki": "https://ru.wikipedia.org/wiki/Лист,_Ференц",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Liszt.jpg/220px-Liszt.jpg"
    },
    "вагнер": {
        "era": "romantic",
        "birth": 1813,
        "death": 1883,
        "full_name": "Рихард Вагнер",
        "bio": "Немецкий композитор, дирижёр, теоретик искусства. Реформатор оперного жанра, создатель концепции «музыкальной драмы». Автор тетралогии «Кольцо нибелунга».",
        "wiki": "https://ru.wikipedia.org/wiki/Вагнер,_Рихард",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Richard_Wagner.jpg/220px-Richard_Wagner.jpg"
    },
    "верди": {
        "era": "romantic",
        "birth": 1813,
        "death": 1901,
        "full_name": "Джузеппе Верди",
        "bio": "Великий итальянский композитор, вершина оперного жанра. Автор «Травиаты», «Аиды», «Риголетто» и других шедевров.",
        "wiki": "https://ru.wikipedia.org/wiki/Верди,_Джузеппе",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Giuseppe_Verdi.jpg/220px-Giuseppe_Verdi.jpg"
    },
    "брамс": {
        "era": "romantic",
        "birth": 1833,
        "death": 1897,
        "full_name": "Иоганнес Брамс",
        "bio": "Немецкий композитор, один из главных представителей романтизма. Его симфонии, концерты и камерная музыка — вершина романтического стиля.",
        "wiki": "https://ru.wikipedia.org/wiki/Брамс,_Иоганнес",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Brahms.jpg/220px-Brahms.jpg"
    },
    "бизе": {
        "era": "romantic",
        "birth": 1838,
        "death": 1875,
        "full_name": "Жорж Бизе",
        "bio": "Французский композитор, автор всемирно известной оперы «Кармен». Его музыка — синтез французского лиризма и испанских ритмов.",
        "wiki": "https://ru.wikipedia.org/wiki/Бизе,_Жорж",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Georges_Bizet.jpg/220px-Georges_Bizet.jpg"
    },
    "муссоргский": {
        "era": "romantic",
        "birth": 1839,
        "death": 1881,
        "full_name": "Модест Петрович Мусоргский",
        "bio": "Русский композитор, член «Могучей кучки». Его оперы «Борис Годунов» и «Хованщина» — вершины русской оперной классики.",
        "wiki": "https://ru.wikipedia.org/wiki/Мусоргский,_Модест_Петрович",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Musorgsky.jpg/220px-Musorgsky.jpg"
    },
    "чайковский": {
        "era": "romantic",
        "birth": 1840,
        "death": 1893,
        "full_name": "Пётр Ильич Чайковский",
        "bio": "Великий русский композитор, педагог, дирижёр. Его балеты «Лебединое озеро», «Щелкунчик», «Спящая красавица» — мировая классика. Автор 6 симфоний, опер, концертов.",
        "wiki": "https://ru.wikipedia.org/wiki/Чайковский,_Пётр_Ильич",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Tchaikovsky.jpg/220px-Tchaikovsky.jpg"
    },
    "дворжак": {
        "era": "romantic",
        "birth": 1841,
        "death": 1904,
        "full_name": "Антонин Леопольд Дворжак",
        "bio": "Чешский композитор, один из крупнейших представителей европейского романтизма. Его «Славянские танцы» и симфонии известны во всём мире.",
        "wiki": "https://ru.wikipedia.org/wiki/Дворжак,_Антонин",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Dvorak.jpg/220px-Dvorak.jpg"
    },
    "григ": {
        "era": "romantic",
        "birth": 1843,
        "death": 1907,
        "full_name": "Эдвард Хагеруп Григ",
        "bio": "Норвежский композитор, пианист и дирижёр. Его музыка для драмы Ибсена «Пер Гюнт» стала символом норвежской музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Григ,_Эдвард",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Edvard_Grieg.jpg/220px-Edvard_Grieg.jpg"
    },
    "римский-корсаков": {
        "era": "romantic",
        "birth": 1844,
        "death": 1908,
        "full_name": "Николай Андреевич Римский-Корсаков",
        "bio": "Русский композитор, педагог, дирижёр. Мастер оркестровой палитры. Автор опер «Садко», «Снегурочка», «Золотой петушок». Основоположник русской оркестровой школы.",
        "wiki": "https://ru.wikipedia.org/wiki/Римский-Корсаков,_Николай_Андреевич",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Rimsky-Korsakov.jpg/220px-Rimsky-Korsakov.jpg"
    },
    "бородин": {
        "era": "romantic",
        "birth": 1833,
        "death": 1887,
        "full_name": "Александр Порфирьевич Бородин",
        "bio": "Русский композитор и учёный-химик. Его опера «Князь Игорь» — шедевр русской эпической оперы. Автор романсов и симфоний.",
        "wiki": "https://ru.wikipedia.org/wiki/Бородин,_Александр_Порфирьевич",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Alexander_Borodin.jpg/220px-Alexander_Borodin.jpg"
    },
    "малер": {
        "era": "romantic",
        "birth": 1860,
        "death": 1911,
        "full_name": "Густав Малер",
        "bio": "Австрийский композитор и дирижёр, один из крупнейших представителей позднего романтизма. Его 9 симфоний — вершины симфонического жанра.",
        "wiki": "https://ru.wikipedia.org/wiki/Малер,_Густав",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Gustav_Mahler.jpg/220px-Gustav_Mahler.jpg"
    },
    "рахманинов": {
        "era": "romantic",
        "birth": 1873,
        "death": 1943,
        "full_name": "Сергей Васильевич Рахманинов",
        "bio": "Великий русский композитор, пианист и дирижёр. Его Второй и Третий фортепианные концерты — одни из самых исполняемых в мире. Символ русской музыкальной эмиграции.",
        "wiki": "https://ru.wikipedia.org/wiki/Рахманинов,_Сергей_Васильевич",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Rachmaninoff.jpg/220px-Rachmaninoff.jpg"
    },
    "берлиоз": {
        "era": "romantic",
        "birth": 1803,
        "death": 1869,
        "full_name": "Гектор Берлиоз",
        "bio": "Французский композитор, дирижёр. Крупнейший представитель французского романтизма. Автор «Фантастической симфонии» и «Траурно-триумфальной симфонии».",
        "wiki": "https://ru.wikipedia.org/wiki/Берлиоз,_Гектор",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Berlioz.jpg/220px-Berlioz.jpg"
    },
    "мендельсон": {
        "era": "romantic",
        "birth": 1809,
        "death": 1847,
        "full_name": "Якоб Людвиг Феликс Мендельсон-Бартольди",
        "bio": "Немецкий композитор и дирижёр. Возродил музыку Баха, создал знаменитый «Свадебный марш» из музыки к «Сну в летнюю ночь».",
        "wiki": "https://ru.wikipedia.org/wiki/Мендельсон,_Феликс",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Mendelssohn.jpg/220px-Mendelssohn.jpg"
    },
    "шuman": {
        "era": "romantic",
        "birth": 1810,
        "death": 1856,
        "full_name": "Роберт Шуман",
        "bio": "Немецкий композитор, пианист, музыкальный критик. Его фортепианные циклы «Бабочки», «Карнавал», «Детские сцены» — шедевры романтизма.",
        "wiki": "https://ru.wikipedia.org/wiki/Шуман,_Роберт",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Robert_Schumann.jpg/220px-Robert_Schumann.jpg"
    },
    "штраус": {
        "era": "romantic",
        "birth": 1864,
        "death": 1949,
        "full_name": "Рихард Штраус",
        "bio": "Немецкий композитор и дирижёр позднего романтизма. Его симфонические поэмы «Так говорил Заратустра» и «Дон Жуан» — вершины программного симфонизма.",
        "wiki": "https://ru.wikipedia.org/wiki/Штраус,_Рихард",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Richard_Strauss.jpg/220px-Richard_Strauss.jpg"
    },
    
    # ===== МОДЕРН =====
    "дебюсси": {
        "era": "modern",
        "birth": 1862,
        "death": 1918,
        "full_name": "Клод Ашиль Дебюсси",
        "bio": "Французский композитор, основоположник музыкального импрессионизма. Его прелюдии, «Лунный свет» и опера «Пеллеас и Мелизанда» изменили музыкальный язык XX века.",
        "wiki": "https://ru.wikipedia.org/wiki/Дебюсси,_Клод",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Debussy.jpg/220px-Debussy.jpg"
    },
    "сати": {
        "era": "modern",
        "birth": 1866,
        "death": 1925,
        "full_name": "Эрик Альфред Лесли Сати",
        "bio": "Французский композитор, пианист. Предшественник музыкального минимализма. Его «Гимнопедии» и «Гносьенны» — уникальный звуковой мир.",
        "wiki": "https://ru.wikipedia.org/wiki/Сати,_Эрик",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Satie.jpg/220px-Satie.jpg"
    },
    "равель": {
        "era": "modern",
        "birth": 1875,
        "death": 1937,
        "full_name": "Морис Равель",
        "bio": "Французский композитор-импрессионист. Его «Болеро» — одно из самых популярных произведений классической музыки. Виртуоз оркестровки.",
        "wiki": "https://ru.wikipedia.org/wiki/Равель,_Морис",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Ravel.jpg/220px-Ravel.jpg"
    },
    "стравинский": {
        "era": "modern",
        "birth": 1882,
        "death": 1971,
        "full_name": "Игорь Фёдорович Стравинский",
        "bio": "Великий русский композитор, один из главных новаторов XX века. Его балеты «Весна священная», «Жар-птица» и «Петрушка» перевернули музыкальный мир.",
        "wiki": "https://ru.wikipedia.org/wiki/Стравинский,_Игорь_Фёдорович",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Stravinsky.jpg/220px-Stravinsky.jpg"
    },
    "прокофьев": {
        "era": "modern",
        "birth": 1891,
        "death": 1953,
        "full_name": "Сергей Сергеевич Прокофьев",
        "bio": "Великий русский композитор, пианист, дирижёр. Его «Ромео и Джульетта», «Петя и волк», «Монтекки и Капулетти» — классика XX века.",
        "wiki": "https://ru.wikipedia.org/wiki/Прокофьев,_Сергей_Сергеевич",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Prokofiev.jpg/220px-Prokofiev.jpg"
    },
    "шостакович": {
        "era": "modern",
        "birth": 1906,
        "death": 1975,
        "full_name": "Дмитрий Дмитриевич Шостакович",
        "bio": "Великий русский композитор, пианист и педагог. Его 15 симфоний, 15 струнных квартетов, опера «Леди Макбет Мценского уезда» — музыкальная летопись XX века.",
        "wiki": "https://ru.wikipedia.org/wiki/Шостакович,_Дмитрий_Дмитриевич",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Shostakovich.jpg/220px-Shostakovich.jpg"
    },
    "барток": {
        "era": "modern",
        "birth": 1881,
        "death": 1945,
        "full_name": "Бела Барток",
        "bio": "Венгерский композитор, пианист и этномузыколог. Создатель уникального музыкального языка, основанного на народной музыке Восточной Европы.",
        "wiki": "https://ru.wikipedia.org/wiki/Барток,_Бела",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Bartok.jpg/220px-Bartok.jpg"
    },
    "копленд": {
        "era": "modern",
        "birth": 1900,
        "death": 1990,
        "full_name": "Аарон Копленд",
        "bio": "Американский композитор, создатель «американского звучания». Его балеты «Аппалачская весна» и «Парень Билли» стали символами американской музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Копленд,_Аарон",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Copland.jpg/220px-Copland.jpg"
    },
    "хачатурян": {
        "era": "modern",
        "birth": 1903,
        "death": 1978,
        "full_name": "Арам Ильич Хачатурян",
        "bio": "Армянский советский композитор, дирижёр. Его «Танец с саблями» из балета «Гаяне» стал одним из самых узнаваемых произведений советской музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Хачатурян,_Арам_Ильич",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Khachaturian.jpg/220px-Khachaturian.jpg"
    },
    
    # ===== СОВРЕМЕННАЯ =====
    "мессиан": {
        "era": "contemporary",
        "birth": 1908,
        "death": 1992,
        "full_name": "Оливье Эжен Проспер Шарль Мессиан",
        "bio": "Французский композитор, органист, орнитолог. Его музыка — синтез религиозного мистицизма и звуков природы. Грандиозное сочинение «Турангалила».",
        "wiki": "https://ru.wikipedia.org/wiki/Мессиан,_Оливье",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Messiaen.jpg/220px-Messiaen.jpg"
    },
    "кейдж": {
        "era": "contemporary",
        "birth": 1912,
        "death": 1992,
        "full_name": "Джон Милтон Кейдж-младший",
        "bio": "Американский композитор, философ музыки. Его знаменитая пьеса «4'33\"» — манифест концептуального искусства и тишины как музыки.",
        "wiki": "https://ru.wikipedia.org/wiki/Кейдж,_Джон",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Cage.jpg/220px-Cage.jpg"
    },
    "шнитке": {
        "era": "contemporary",
        "birth": 1934,
        "death": 1998,
        "full_name": "Альфред Гарриевич Шнитке",
        "bio": "Русский композитор, пианист, музыковед. Создатель стиля «полистилистика». Его произведения сочетают разные эпохи и жанры.",
        "wiki": "https://ru.wikipedia.org/wiki/Шнитке,_Альфред_Гарриевич",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/Schnittke.jpg/220px-Schnittke.jpg"
    },
    "пярт": {
        "era": "contemporary",
        "birth": 1935,
        "death": None,
        "full_name": "Арво Пярт",
        "bio": "Эстонский композитор, создатель стиля «колокольного звона» (tintinnabuli). Его музыка — медитация, возвращение к истокам христианской традиции.",
        "wiki": "https://ru.wikipedia.org/wiki/Пярт,_Арво",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Arvo_Pärt.jpg/220px-Arvo_Pärt.jpg"
    },
    "эйнауди": {
        "era": "contemporary",
        "birth": 1955,
        "death": None,
        "full_name": "Людовико Эйнауди",
        "bio": "Итальянский композитор и пианист. Его минималистическая музыка для кино и театра делает его одним из самых исполняемых современных композиторов в мире.",
        "wiki": "https://ru.wikipedia.org/wiki/Эйнауди,_Людовико",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/Einaudi.jpg/220px-Einaudi.jpg"
    },
    "лигети": {
        "era": "contemporary",
        "birth": 1923,
        "death": 2006,
        "full_name": "Дьёрдь Шандор Лигети",
        "bio": "Венгерский и австрийский композитор. Его музыка использована в фильме Стэнли Кубрика «Космическая одиссея 2001 года».",
        "wiki": "https://ru.wikipedia.org/wiki/Лигети,_Дьёрдь",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Ligeti.jpg/220px-Ligeti.jpg"
    },
}

# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================

def normalize_text(text: str) -> str:
    """Очищает текст от лишних символов и приводит к нижнему регистру"""
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

def find_composer_in_text(text: str) -> Tuple[Optional[str], Optional[Dict]]:
    """Ищет композитора в тексте по базе данных"""
    normalized = normalize_text(text)
    words = normalized.split()
    
    # Сначала проверяем точные совпадения (полные имена)
    for composer, data in COMPOSERS_DB.items():
        composer_lower = composer.lower()
        if composer_lower in normalized:
            return composer, data
    
    # Затем проверяем слова (для длинных фамилий)
    for composer, data in COMPOSERS_DB.items():
        composer_lower = composer.lower()
        if len(composer_lower) > 5:
            for part in composer_lower.split():
                if len(part) > 3 and part in words:
                    return composer, data
    
    return None, None

def find_year_in_text(text: str) -> Optional[int]:
    """Ищет четырехзначное число (год) в тексте"""
    pattern = r'\b(1[0-9]{3}|2[0-9]{3})\b'
    matches = re.findall(pattern, text)
    if matches:
        return int(matches[0])
    return None

def get_era_by_year(year: int) -> Optional[str]:
    """Определяет эпоху по году"""
    for era_key, era_data in ERAS.items():
        if era_data["year_start"] <= year <= era_data["year_end"]:
            return era_key
    return None

def get_music_links(composer_key: str, search_query: str = None) -> Dict[str, str]:
    """
    Формирует ссылки для ПОИСКА в стриминговых сервисах.
    Использует полное имя композитора для более точного поиска.
    """
    # Получаем полное имя композитора для поиска
    composer_data = COMPOSERS_DB.get(composer_key.lower())
    if composer_data:
        full_name = composer_data.get("full_name", composer_key)
        query = full_name
    else:
        query = search_query or composer_key
    
    encoded_query = urllib.parse.quote(query)
    
    links = {
        "apple": f"https://music.apple.com/search?term={encoded_query}",
        "yandex": f"https://music.yandex.ru/search?text={encoded_query}",
        "spotify": f"https://open.spotify.com/search/{encoded_query}"
    }
    return links

def get_composer_info(composer_key: str) -> Optional[Dict]:
    """Возвращает полную информацию о композиторе"""
    return COMPOSERS_DB.get(composer_key.lower())

def format_years_life(composer_data: Dict) -> str:
    """Форматирует годы жизни композитора"""
    birth = composer_data.get("birth")
    death = composer_data.get("death")
    if birth:
        if death:
            return f"{birth} – {death}"
        else:
            return f"{birth} – н.в."
    return ""

def format_composer_response(composer_key: str, composer_data: Dict, user_text: str = None) -> Tuple[str, str, str, Dict[str, str]]:
    """Формирует ответ о композиторе"""
    era_key = composer_data.get("era")
    era_data = ERAS.get(era_key)
    
    full_name = composer_data.get("full_name", composer_key.title())
    years_life = format_years_life(composer_data)
    bio = composer_data.get("bio", "Информация о композиторе уточняется.")
    wiki_link = composer_data.get("wiki", "#")
    image_url = composer_data.get("image")
    
    message = f"""<b>{era_data['emoji']} Эпоха:</b> {era_data['name']}
<b>📅 Период:</b> {era_data['year_start']}–{era_data['year_end']}

<b>🎵 Композитор:</b> {full_name}
<b>📅 Годы жизни:</b> {years_life}

<b>📖 Краткая биография:</b>
{bio}

<b>📚 Подробнее:</b> <a href="{wiki_link}">Читать на Википедии</a>

<b>📌 Эпоха:</b> {era_data['description']}

<b>🔍 Поиск музыки по имени композитора:</b>"""
    
    links = get_music_links(composer_key, full_name)
    
    return message, image_url, wiki_link, links

def format_unknown_response(text: str) -> Tuple[str, Dict[str, str]]:
    """Формирует сообщение для неизвестного композитора"""
    year = find_year_in_text(text)
    if year:
        era_key = get_era_by_year(year)
        if era_key:
            era_data = ERAS[era_key]
            links = get_music_links(text[:50], text[:50])
            
            message = f"""🔍 <b>Композитор не найден</b>, но я определил эпоху по году {year}:

<b>{era_data['emoji']} Эпоха:</b> {era_data['name']}
<b>📅 Период:</b> {era_data['year_start']}–{era_data['year_end']}

<b>📌 Эпоха:</b> {era_data['description']}

<b>🔍 Поиск по вашему запросу:</b> «{text[:50]}»

Выберите музыкальный сервис:"""
            return message, links
    
    links = get_music_links(text[:50], text[:50])
    
    message = f"""⚠️ <b>Не удалось определить эпоху</b>

Я не нашел композитора <b>«{text[:50]}»</b> в своей базе данных и не смог определить год.

<b>Пожалуйста, уточните:</b>
• Полное имя композитора
• Год создания произведения (например, 1824)

Пример: <i>«Бетховен Симфония №9 1824»</i>

<b>🔍 Поиск по вашему запросу:</b> «{text[:50]}»

Выберите музыкальный сервис:"""
    
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

<b>Примеры запросов:</b>
• <i>«Бах»</i> → покажу Иоганна Себастьяна Баха
• <i>«Рахманинов»</i> → покажу Сергея Васильевича Рахманинова
• <i>«Моцарт Реквием»</i> → найду Моцарта
• <i>«Чайковский Лебединое озеро»</i> → найду Чайковского

<b>Команды:</b>
/start - Приветствие
/help - Справка
/eras - Список эпох
/composers - Список композиторов в базе"""
    
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
• <i>«Дебюсси Лунный свет»</i> → найду Клода Дебюсси
• <i>«Рахманинов Концерт №2»</i> → найду Сергея Рахманинова
• <i>«1824»</i> → определю эпоху по году

<b>Команды:</b>
/start - Приветствие
/help - Эта справка
/eras - Список всех эпох
/composers - Все композиторы в базе

<b>Что вы получите в ответе:</b>
• 🖼️ Фото композитора (если есть)
• 👤 Полное имя
• 📅 Годы жизни
• 📖 Краткая биография
• 📚 Ссылка на Википедию
• 🔍 Ссылки на поиск в музыкальных сервисах

<b>В базе более 50 композиторов!</b>"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def eras_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    eras_text = "<b>📚 Доступные эпохи:</b>\n\n"
    for key, era in ERAS.items():
        eras_text += f"{era['emoji']} <b>{era['name']}</b>\n"
        eras_text += f"   📅 {era['year_start']}–{era['year_end']}\n"
        eras_text += f"   📌 {era['description']}\n\n"
    
    await update.message.reply_text(eras_text, parse_mode='HTML')

async def composers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список всех композиторов в базе"""
    # Группируем композиторов по эпохам
    composers_by_era = {}
    for key, data in COMPOSERS_DB.items():
        era = data.get("era", "unknown")
        if era not in composers_by_era:
            composers_by_era[era] = []
        composers_by_era[era].append(data.get("full_name", key.title()))
    
    # Сортируем эпохи в порядке ERAS
    sorted_eras = [e for e in ERAS.keys() if e in composers_by_era]
    
    text = "<b>🎼 Все композиторы в базе:</b>\n\n"
    for era_key in sorted_eras:
        era_data = ERAS.get(era_key)
        if era_data and era_key in composers_by_era:
            text += f"{era_data['emoji']} <b>{era_data['name']}</b>\n"
            # Сортируем композиторов по алфавиту
            names = sorted(composers_by_era[era_key])
            for name in names:
                text += f"   • {name}\n"
            text += "\n"
    
    if len(text) > 4096:
        # Если список слишком длинный, отправляем файлом
        await update.message.reply_document(
            document=text.encode('utf-8'),
            filename="composers.txt",
            caption="📋 Полный список композиторов"
        )
    else:
        await update.message.reply_text(text, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Основной обработчик текстовых сообщений"""
    user_text = update.message.text
    logger.info(f"Получено сообщение: {user_text}")
    
    composer_key, composer_data = find_composer_in_text(user_text)
    
    if composer_key and composer_data:
        era_key = composer_data.get("era")
        if era_key and ERAS.get(era_key):
            message, image_url, wiki_link, links = format_composer_response(
                composer_key, composer_data, user_text
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
            
            # Отправляем фото с подписью (если есть)
            if image_url:
                try:
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=message,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logger.warning(f"Не удалось отправить фото: {e}")
                    # Если фото не загрузилось, отправляем только текст
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
    
    # Если композитор не найден, ищем год
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
    
    # Ничего не найдено
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
• Моцарт → покажу Вольфганга Амадея Моцарта
• Бах → покажу Иоганна Себастьяна Баха
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
    logger.info(f"📊 Доступно эпох: {len(ERAS)}")
    
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