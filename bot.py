"""
TELEGRAM-БОТ ДЛЯ РАСПРЕДЕЛЕНИЯ КЛАССИЧЕСКОЙ МУЗЫКИ ПО ЭПОХАМ
Версия: Bothost (с универсальными ссылками на поиск по композитору)
"""

import os
import re
import logging
import urllib.parse
from datetime import datetime
from typing import Dict, Optional, Tuple

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
        "emoji": "🏛️"
    },
    "baroque": {
        "name": "Барокко (Baroque)",
        "name_en": "Baroque",
        "year_start": 1600,
        "year_end": 1749,
        "emoji": "👑"
    },
    "classical": {
        "name": "Классицизм (Classical)",
        "name_en": "Classical",
        "year_start": 1750,
        "year_end": 1819,
        "emoji": "🏛️"
    },
    "romantic": {
        "name": "Романтизм (Romantic)",
        "name_en": "Romantic",
        "year_start": 1820,
        "year_end": 1899,
        "emoji": "🌹"
    },
    "modern": {
        "name": "Импрессионизм / Модерн (Modern)",
        "name_en": "Modern",
        "year_start": 1900,
        "year_end": 1949,
        "emoji": "🎨"
    },
    "contemporary": {
        "name": "Современная академическая (Contemporary)",
        "name_en": "Contemporary",
        "year_start": 1950,
        "year_end": datetime.now().year,
        "emoji": "🔮"
    }
}

# ===================== РАСШИРЕННАЯ БАЗА КОМПОЗИТОРОВ =====================

COMPOSERS_DB = {
    # ===== РАННЯЯ МУЗЫКА (Medieval / Renaissance) =====
    "машо": {"era": "medieval", "birth": 1300, "death": 1377},
    "ландини": {"era": "medieval", "birth": 1325, "death": 1397},
    "данстейбл": {"era": "medieval", "birth": 1390, "death": 1453},
    "таллис": {"era": "medieval", "birth": 1505, "death": 1585},
    "томас таллис": {"era": "medieval", "birth": 1505, "death": 1585},
    "палестрина": {"era": "medieval", "birth": 1525, "death": 1594},
    "джованни да палестрина": {"era": "medieval", "birth": 1525, "death": 1594},
    "виктория": {"era": "medieval", "birth": 1548, "death": 1611},
    "т. л. де виктория": {"era": "medieval", "birth": 1548, "death": 1611},
    "берд": {"era": "medieval", "birth": 1543, "death": 1623},
    "уильям берд": {"era": "medieval", "birth": 1543, "death": 1623},
    
    # ===== БАРОККО (Baroque) =====
    "монтеверди": {"era": "baroque", "birth": 1567, "death": 1643},
    "клаудио монтеверди": {"era": "baroque", "birth": 1567, "death": 1643},
    "кариссими": {"era": "baroque", "birth": 1605, "death": 1674},
    "джакомо кариссими": {"era": "baroque", "birth": 1605, "death": 1674},
    "фрескобальди": {"era": "baroque", "birth": 1583, "death": 1643},
    "джироламо фрескобальди": {"era": "baroque", "birth": 1583, "death": 1643},
    "корелли": {"era": "baroque", "birth": 1653, "death": 1713},
    "арканджело корелли": {"era": "baroque", "birth": 1653, "death": 1713},
    "вивальди": {"era": "baroque", "birth": 1678, "death": 1741},
    "антонио вивальди": {"era": "baroque", "birth": 1678, "death": 1741},
    "скарлатти": {"era": "baroque", "birth": 1685, "death": 1757},
    "доменико скарлатти": {"era": "baroque", "birth": 1685, "death": 1757},
    "алессандро скарлатти": {"era": "baroque", "birth": 1660, "death": 1725},
    "альбинони": {"era": "baroque", "birth": 1671, "death": 1751},
    "томазо альбинони": {"era": "baroque", "birth": 1671, "death": 1751},
    "локателли": {"era": "baroque", "birth": 1695, "death": 1764},
    "пьетро локателли": {"era": "baroque", "birth": 1695, "death": 1764},
    "джеминиани": {"era": "baroque", "birth": 1687, "death": 1762},
    "франческо джеминиани": {"era": "baroque", "birth": 1687, "death": 1762},
    "тартини": {"era": "baroque", "birth": 1692, "death": 1770},
    "джузеппе тартини": {"era": "baroque", "birth": 1692, "death": 1770},
    "бах": {"era": "baroque", "birth": 1685, "death": 1750},
    "иоганн себастьян бах": {"era": "baroque", "birth": 1685, "death": 1750},
    "j.s. bach": {"era": "baroque", "birth": 1685, "death": 1750},
    "гендель": {"era": "baroque", "birth": 1685, "death": 1759},
    "георг фридрих гендель": {"era": "baroque", "birth": 1685, "death": 1759},
    "händel": {"era": "baroque", "birth": 1685, "death": 1759},
    "телеман": {"era": "baroque", "birth": 1681, "death": 1767},
    "георг филипп телеман": {"era": "baroque", "birth": 1681, "death": 1767},
    "пахельбель": {"era": "baroque", "birth": 1653, "death": 1706},
    "иоганн пахельбель": {"era": "baroque", "birth": 1653, "death": 1706},
    "букстехуде": {"era": "baroque", "birth": 1637, "death": 1707},
    "дитрих букстехуде": {"era": "baroque", "birth": 1637, "death": 1707},
    "фробергер": {"era": "baroque", "birth": 1616, "death": 1667},
    "иоганн якоб фробергер": {"era": "baroque", "birth": 1616, "death": 1667},
    "шайдт": {"era": "baroque", "birth": 1587, "death": 1654},
    "самуэль шайдт": {"era": "baroque", "birth": 1587, "death": 1654},
    "люлли": {"era": "baroque", "birth": 1632, "death": 1687},
    "жан-батист люлли": {"era": "baroque", "birth": 1632, "death": 1687},
    "куперен": {"era": "baroque", "birth": 1668, "death": 1733},
    "франсуа куперен": {"era": "baroque", "birth": 1668, "death": 1733},
    "рамо": {"era": "baroque", "birth": 1683, "death": 1764},
    "жан-филипп рамо": {"era": "baroque", "birth": 1683, "death": 1764},
    "шампоньер": {"era": "baroque", "birth": 1602, "death": 1672},
    "жак шампоньер": {"era": "baroque", "birth": 1602, "death": 1672},
    "пёрселл": {"era": "baroque", "birth": 1659, "death": 1695},
    "перселл": {"era": "baroque", "birth": 1659, "death": 1695},
    "генри пёрселл": {"era": "baroque", "birth": 1659, "death": 1695},
    "бортнянский": {"era": "baroque", "birth": 1751, "death": 1825},
    "дмитрий бортнянский": {"era": "baroque", "birth": 1751, "death": 1825},
    "березовский": {"era": "baroque", "birth": 1745, "death": 1777},
    "максим березовский": {"era": "baroque", "birth": 1745, "death": 1777},
    
    # ===== КЛАССИЦИЗМ (Classical) =====
    "глюк": {"era": "classical", "birth": 1714, "death": 1787},
    "кристоф глюк": {"era": "classical", "birth": 1714, "death": 1787},
    "гайдн": {"era": "classical", "birth": 1732, "death": 1809},
    "йозеф гайдн": {"era": "classical", "birth": 1732, "death": 1809},
    "haydn": {"era": "classical", "birth": 1732, "death": 1809},
    "моцарт": {"era": "classical", "birth": 1756, "death": 1791},
    "вольфганг амадей моцарт": {"era": "classical", "birth": 1756, "death": 1791},
    "mozart": {"era": "classical", "birth": 1756, "death": 1791},
    "бетховен": {"era": "classical", "birth": 1770, "death": 1827},
    "людвиг ван бетховен": {"era": "classical", "birth": 1770, "death": 1827},
    "beethoven": {"era": "classical", "birth": 1770, "death": 1827},
    "сальери": {"era": "classical", "birth": 1750, "death": 1825},
    "антонио сальери": {"era": "classical", "birth": 1750, "death": 1825},
    "к.ф.э. бах": {"era": "classical", "birth": 1714, "death": 1788},
    "c.p.e. bach": {"era": "classical", "birth": 1714, "death": 1788},
    "иоганн христиан бах": {"era": "classical", "birth": 1735, "death": 1782},
    "j.c. bach": {"era": "classical", "birth": 1735, "death": 1782},
    "боккерини": {"era": "classical", "birth": 1743, "death": 1805},
    "луиджи боккерини": {"era": "classical", "birth": 1743, "death": 1805},
    "клементи": {"era": "classical", "birth": 1752, "death": 1832},
    "муцио клементи": {"era": "classical", "birth": 1752, "death": 1832},
    
    # ===== РОМАНТИЗМ (Romantic) =====
    "шуберт": {"era": "romantic", "birth": 1797, "death": 1828},
    "франц шуберт": {"era": "romantic", "birth": 1797, "death": 1828},
    "schubert": {"era": "romantic", "birth": 1797, "death": 1828},
    "вебер": {"era": "romantic", "birth": 1786, "death": 1826},
    "карл мария фон вебер": {"era": "romantic", "birth": 1786, "death": 1826},
    "мендельсон": {"era": "romantic", "birth": 1809, "death": 1847},
    "феликс мендельсон": {"era": "romantic", "birth": 1809, "death": 1847},
    "mendelssohn": {"era": "romantic", "birth": 1809, "death": 1847},
    "шопен": {"era": "romantic", "birth": 1810, "death": 1849},
    "фредерик шопен": {"era": "romantic", "birth": 1810, "death": 1849},
    "chopin": {"era": "romantic", "birth": 1810, "death": 1849},
    "шuman": {"era": "romantic", "birth": 1810, "death": 1856},
    "шyман": {"era": "romantic", "birth": 1810, "death": 1856},
    "роберт шуман": {"era": "romantic", "birth": 1810, "death": 1856},
    "schumann": {"era": "romantic", "birth": 1810, "death": 1856},
    "лист": {"era": "romantic", "birth": 1811, "death": 1886},
    "ференц лист": {"era": "romantic", "birth": 1811, "death": 1886},
    "liszt": {"era": "romantic", "birth": 1811, "death": 1886},
    "вагнер": {"era": "romantic", "birth": 1813, "death": 1883},
    "рихард вагнер": {"era": "romantic", "birth": 1813, "death": 1883},
    "wagner": {"era": "romantic", "birth": 1813, "death": 1883},
    "верди": {"era": "romantic", "birth": 1813, "death": 1901},
    "джузеппе верди": {"era": "romantic", "birth": 1813, "death": 1901},
    "verdi": {"era": "romantic", "birth": 1813, "death": 1901},
    "берлиоз": {"era": "romantic", "birth": 1803, "death": 1869},
    "гектор берлиоз": {"era": "romantic", "birth": 1803, "death": 1869},
    "брамс": {"era": "romantic", "birth": 1833, "death": 1897},
    "иоганнес брамс": {"era": "romantic", "birth": 1833, "death": 1897},
    "brahms": {"era": "romantic", "birth": 1833, "death": 1897},
    "бизе": {"era": "romantic", "birth": 1838, "death": 1875},
    "жорж бизе": {"era": "romantic", "birth": 1838, "death": 1875},
    "муссоргский": {"era": "romantic", "birth": 1839, "death": 1881},
    "модест муссоргский": {"era": "romantic", "birth": 1839, "death": 1881},
    "mussorgsky": {"era": "romantic", "birth": 1839, "death": 1881},
    "чайковский": {"era": "romantic", "birth": 1840, "death": 1893},
    "пётр ильич чайковский": {"era": "romantic", "birth": 1840, "death": 1893},
    "tchaikovsky": {"era": "romantic", "birth": 1840, "death": 1893},
    "дворжак": {"era": "romantic", "birth": 1841, "death": 1904},
    "антонин дворжак": {"era": "romantic", "birth": 1841, "death": 1904},
    "dvorak": {"era": "romantic", "birth": 1841, "death": 1904},
    "григ": {"era": "romantic", "birth": 1843, "death": 1907},
    "эдвард григ": {"era": "romantic", "birth": 1843, "death": 1907},
    "grieg": {"era": "romantic", "birth": 1843, "death": 1907},
    "римский-корсаков": {"era": "romantic", "birth": 1844, "death": 1908},
    "николай римский-корсаков": {"era": "romantic", "birth": 1844, "death": 1908},
    "rimsky-korsakov": {"era": "romantic", "birth": 1844, "death": 1908},
    "бородин": {"era": "romantic", "birth": 1833, "death": 1887},
    "александр бородин": {"era": "romantic", "birth": 1833, "death": 1887},
    "малер": {"era": "romantic", "birth": 1860, "death": 1911},
    "густав малер": {"era": "romantic", "birth": 1860, "death": 1911},
    "mahler": {"era": "romantic", "birth": 1860, "death": 1911},
    "штраус": {"era": "romantic", "birth": 1864, "death": 1949},
    "рихард штраус": {"era": "romantic", "birth": 1864, "death": 1949},
    "richard strauss": {"era": "romantic", "birth": 1864, "death": 1949},
    "рахманинов": {"era": "romantic", "birth": 1873, "death": 1943},
    "сергей рахманинов": {"era": "romantic", "birth": 1873, "death": 1943},
    "rachmaninoff": {"era": "romantic", "birth": 1873, "death": 1943},
    "rachmaninov": {"era": "romantic", "birth": 1873, "death": 1943},
    
    # ===== МОДЕРН (Modern) =====
    "дебюсси": {"era": "modern", "birth": 1862, "death": 1918},
    "клод дебюсси": {"era": "modern", "birth": 1862, "death": 1918},
    "debussy": {"era": "modern", "birth": 1862, "death": 1918},
    "сати": {"era": "modern", "birth": 1866, "death": 1925},
    "эрик сати": {"era": "modern", "birth": 1866, "death": 1925},
    "satie": {"era": "modern", "birth": 1866, "death": 1925},
    "равель": {"era": "modern", "birth": 1875, "death": 1937},
    "морис равель": {"era": "modern", "birth": 1875, "death": 1937},
    "ravel": {"era": "modern", "birth": 1875, "death": 1937},
    "фаля": {"era": "modern", "birth": 1876, "death": 1946},
    "мануэль де фаля": {"era": "modern", "birth": 1876, "death": 1946},
    "респиги": {"era": "modern", "birth": 1879, "death": 1936},
    "отторино респиги": {"era": "modern", "birth": 1879, "death": 1936},
    "барток": {"era": "modern", "birth": 1881, "death": 1945},
    "бела барток": {"era": "modern", "birth": 1881, "death": 1945},
    "bartok": {"era": "modern", "birth": 1881, "death": 1945},
    "стравинский": {"era": "modern", "birth": 1882, "death": 1971},
    "игорь стравинский": {"era": "modern", "birth": 1882, "death": 1971},
    "stravinsky": {"era": "modern", "birth": 1882, "death": 1971},
    "прокофьев": {"era": "modern", "birth": 1891, "death": 1953},
    "сергей прокофьев": {"era": "modern", "birth": 1891, "death": 1953},
    "prokofiev": {"era": "modern", "birth": 1891, "death": 1953},
    "копленд": {"era": "modern", "birth": 1900, "death": 1990},
    "аарон копленд": {"era": "modern", "birth": 1900, "death": 1990},
    "copland": {"era": "modern", "birth": 1900, "death": 1990},
    "веберн": {"era": "modern", "birth": 1883, "death": 1945},
    "антон веберн": {"era": "modern", "birth": 1883, "death": 1945},
    "берг": {"era": "modern", "birth": 1885, "death": 1935},
    "альбан берг": {"era": "modern", "birth": 1885, "death": 1935},
    "онигер": {"era": "modern", "birth": 1892, "death": 1955},
    "артюр онигер": {"era": "modern", "birth": 1892, "death": 1955},
    "мийо": {"era": "modern", "birth": 1892, "death": 1974},
    "дариус мийо": {"era": "modern", "birth": 1892, "death": 1974},
    "глиэр": {"era": "modern", "birth": 1875, "death": 1956},
    "рейнгольд глиэр": {"era": "modern", "birth": 1875, "death": 1956},
    "миасковский": {"era": "modern", "birth": 1881, "death": 1950},
    "николай миасковский": {"era": "modern", "birth": 1881, "death": 1950},
    "хачатурян": {"era": "modern", "birth": 1903, "death": 1978},
    "арам хачатурян": {"era": "modern", "birth": 1903, "death": 1978},
    "khachaturian": {"era": "modern", "birth": 1903, "death": 1978},
    "кабалевский": {"era": "modern", "birth": 1904, "death": 1987},
    "дмитрий кабалевский": {"era": "modern", "birth": 1904, "death": 1987},
    "шостакович": {"era": "modern", "birth": 1906, "death": 1975},
    "дмитрий шостакович": {"era": "modern", "birth": 1906, "death": 1975},
    "shostakovich": {"era": "modern", "birth": 1906, "death": 1975},
    "бриттен": {"era": "modern", "birth": 1913, "death": 1976},
    "бенджамин бриттен": {"era": "modern", "birth": 1913, "death": 1976},
    
    # ===== СОВРЕМЕННАЯ (Contemporary) =====
    "мессиан": {"era": "contemporary", "birth": 1908, "death": 1992},
    "оливье мессиан": {"era": "contemporary", "birth": 1908, "death": 1992},
    "messiaen": {"era": "contemporary", "birth": 1908, "death": 1992},
    "кейдж": {"era": "contemporary", "birth": 1912, "death": 1992},
    "джон кейдж": {"era": "contemporary", "birth": 1912, "death": 1992},
    "cage": {"era": "contemporary", "birth": 1912, "death": 1992},
    "булез": {"era": "contemporary", "birth": 1925, "death": 2016},
    "пьер булез": {"era": "contemporary", "birth": 1925, "death": 2016},
    "boulez": {"era": "contemporary", "birth": 1925, "death": 2016},
    "штокхаузен": {"era": "contemporary", "birth": 1928, "death": 2007},
    "карлхайнц штокхаузен": {"era": "contemporary", "birth": 1928, "death": 2007},
    "stockhausen": {"era": "contemporary", "birth": 1928, "death": 2007},
    "шнитке": {"era": "contemporary", "birth": 1934, "death": 1998},
    "альфред шнитке": {"era": "contemporary", "birth": 1934, "death": 1998},
    "schnittke": {"era": "contemporary", "birth": 1934, "death": 1998},
    "пярт": {"era": "contemporary", "birth": 1935, "death": None},
    "арво пярт": {"era": "contemporary", "birth": 1935, "death": None},
    "pärt": {"era": "contemporary", "birth": 1935, "death": None},
    "горецкий": {"era": "contemporary", "birth": 1933, "death": 2010},
    "генрик горецкий": {"era": "contemporary", "birth": 1933, "death": 2010},
    "лигети": {"era": "contemporary", "birth": 1923, "death": 2006},
    "дьёрдь лигети": {"era": "contemporary", "birth": 1923, "death": 2006},
    "бере": {"era": "contemporary", "birth": 1925, "death": 2016},
    "лючано берио": {"era": "contemporary", "birth": 1925, "death": 2003},
    "салонен": {"era": "contemporary", "birth": 1958, "death": None},
    "эса-пекка салонен": {"era": "contemporary", "birth": 1958, "death": None},
    "salonen": {"era": "contemporary", "birth": 1958, "death": None},
    "эйнауди": {"era": "contemporary", "birth": 1955, "death": None},
    "людовико эйнауди": {"era": "contemporary", "birth": 1955, "death": None},
    "einaudi": {"era": "contemporary", "birth": 1955, "death": None},
    "рихтер": {"era": "contemporary", "birth": 1969, "death": None},
    "макс рихтер": {"era": "contemporary", "birth": 1969, "death": None},
    "йоханнссон": {"era": "contemporary", "birth": 1969, "death": None},
    "йоуханн йоуханнссон": {"era": "contemporary", "birth": 1969, "death": 2018},
}

# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================

def normalize_text(text: str) -> str:
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

def find_composer_in_text(text: str) -> Tuple[Optional[str], Optional[Dict]]:
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

def get_composer_search_name(composer_key: str, composer_data: Dict) -> str:
    """
    Формирует имя композитора для поиска в стриминговых сервисах.
    Приоритет: английское написание (если есть) > русское
    """
    # Список английских вариантов для популярных композиторов
    english_names = {
        "чайковский": "Tchaikovsky",
        "tchaikovsky": "Tchaikovsky",
        "рахманинов": "Rachmaninoff",
        "rachmaninoff": "Rachmaninoff",
        "rachmaninov": "Rachmaninoff",
        "шопен": "Chopin",
        "chopin": "Chopin",
        "лист": "Liszt",
        "liszt": "Liszt",
        "моцарт": "Mozart",
        "mozart": "Mozart",
        "бетховен": "Beethoven",
        "beethoven": "Beethoven",
        "бах": "Bach",
        "bach": "Bach",
        "вивальди": "Vivaldi",
        "vivaldi": "Vivaldi",
        "дебюсси": "Debussy",
        "debussy": "Debussy",
        "равель": "Ravel",
        "ravel": "Ravel",
        "стравинский": "Stravinsky",
        "stravinsky": "Stravinsky",
        "прокофьев": "Prokofiev",
        "prokofiev": "Prokofiev",
        "шостакович": "Shostakovich",
        "shostakovich": "Shostakovich",
        "шуберт": "Schubert",
        "schubert": "Schubert",
        "шuman": "Schumann",
        "schumann": "Schumann",
        "мендельсон": "Mendelssohn",
        "mendelssohn": "Mendelssohn",
        "вагнер": "Wagner",
        "wagner": "Wagner",
        "верди": "Verdi",
        "verdi": "Verdi",
        "брамс": "Brahms",
        "brahms": "Brahms",
        "григ": "Grieg",
        "grieg": "Grieg",
        "дворжак": "Dvorak",
        "dvorak": "Dvorak",
        "малер": "Mahler",
        "mahler": "Mahler",
        "хачатурян": "Khachaturian",
        "khachaturian": "Khachaturian",
        "эйнaуди": "Einaudi",
        "einaudi": "Einaudi",
        "пярт": "Pärt",
        "pärt": "Pärt",
        "сати": "Satie",
        "satie": "Satie",
        "фаля": "Falla",
        "falla": "Falla",
        "респиги": "Respighi",
        "respighi": "Respighi",
        "барток": "Bartok",
        "bartok": "Bartok",
        "копленд": "Copland",
        "copland": "Copland",
        "берлиоз": "Berlioz",
        "berlioz": "Berlioz",
        "бизе": "Bizet",
        "bizet": "Bizet",
        "муссоргский": "Mussorgsky",
        "mussorgsky": "Mussorgsky",
        "римский-корсаков": "Rimsky-Korsakov",
        "rimsky-korsakov": "Rimsky-Korsakov",
        "бородин": "Borodin",
        "borodin": "Borodin",
        "штраус": "Strauss",
        "strauss": "Strauss",
        "букстехуде": "Buxtehude",
        "buxtehude": "Buxtehude",
        "пахельбель": "Pachelbel",
        "pachelbel": "Pachelbel",
        "телеман": "Telemann",
        "telemann": "Telemann",
        "гендель": "Handel",
        "handel": "Handel",
        "händel": "Handel",
        "корелли": "Corelli",
        "corelli": "Corelli",
        "тартини": "Tartini",
        "tartini": "Tartini",
        "альбинони": "Albinoni",
        "albinoni": "Albinoni",
        "скарлатти": "Scarlatti",
        "scarlatti": "Scarlatti",
        "люлли": "Lully",
        "lully": "Lully",
        "куперен": "Couperin",
        "couperin": "Couperin",
        "рамо": "Rameau",
        "rameau": "Rameau",
        "глюк": "Gluck",
        "gluck": "Gluck",
        "гайдн": "Haydn",
        "haydn": "Haydn",
        "сальери": "Salieri",
        "salieri": "Salieri",
        "боккерини": "Boccherini",
        "boccherini": "Boccherini",
        "клементи": "Clementi",
        "clementi": "Clementi",
        "вебер": "Weber",
        "weber": "Weber",
        "мессиан": "Messiaen",
        "messiaen": "Messiaen",
        "кейдж": "Cage",
        "cage": "Cage",
        "булез": "Boulez",
        "boulez": "Boulez",
        "штокхаузен": "Stockhausen",
        "stockhausen": "Stockhausen",
        "шнитке": "Schnittke",
        "schnittke": "Schnittke",
        "салонен": "Salonen",
        "salonen": "Salonen",
        "рихтер": "Richter",
        "richter": "Richter",
        "горецкий": "Gorecki",
        "gorecki": "Gorecki",
        "лигети": "Ligeti",
        "ligeti": "Ligeti",
        "берио": "Berio",
        "berio": "Berio",
        "бриттен": "Britten",
        "britten": "Britten",
        "палестрина": "Palestrina",
        "palestrina": "Palestrina",
        "виктория": "Victoria",
        "victoria": "Victoria",
        "берд": "Byrd",
        "byrd": "Byrd",
        "бортнянский": "Bortnyansky",
        "bortnyansky": "Bortnyansky",
        "березовский": "Berezovsky",
        "berezovsky": "Berezovsky",
        "глиэр": "Gliere",
        "gliere": "Gliere",
        "миасковский": "Myaskovsky",
        "myaskovsky": "Myaskovsky",
        "кабалевский": "Kabalevsky",
        "kabalevsky": "Kabalevsky",
    }
    
    # Проверяем, есть ли английский вариант
    composer_lower = composer_key.lower()
    if composer_lower in english_names:
        return english_names[composer_lower]
    
    # Проверяем, может быть в english_names есть ключ с другим написанием
    for key, value in english_names.items():
        if key in composer_lower or composer_lower in key:
            return value
    
    # Если английского нет, возвращаем русское имя
    return composer_key

def get_music_links(composer_name: str, search_query: str = None) -> Dict[str, str]:
    """
    Формирует ссылки для поиска в стриминговых сервисах
    """
    # Если search_query не передан, используем имя композитора
    query = search_query or composer_name
    
    # Кодируем запрос для URL
    encoded_query = urllib.parse.quote(query)
    encoded_query_ru = urllib.parse.quote(composer_name)
    
    # Формируем ссылки на поиск
    links = {
        "apple": f"https://music.apple.com/search?term={encoded_query}",
        "yandex": f"https://music.yandex.ru/search?text={encoded_query}",
        "spotify": f"https://open.spotify.com/search/{encoded_query}/tracks"
    }
    
    # Для русских имен также добавляем поиск по английскому варианту
    # Но оставляем основной запрос как есть
    
    return links

# ===================== ОСНОВНЫЕ ФУНКЦИИ =====================

def format_response(composer_key: str, era_key: str, composer_data: Dict = None, user_text: str = None) -> Tuple[str, Dict[str, str]]:
    """Формирует сообщение и ссылки для пользователя"""
    era_data = ERAS.get(era_key)
    if not era_data:
        return "⚠️ Не удалось определить эпоху. Пожалуйста, уточните данные.", {}
    
    # Получаем имя композитора для поиска
    search_name = get_composer_search_name(composer_key, composer_data)
    
    # Формируем ссылки на музыкальные сервисы
    links = get_music_links(search_name, composer_key)
    
    years_life = ""
    if composer_data:
        birth = composer_data.get("birth")
        death = composer_data.get("death")
        if birth:
            years_life = f"{birth}"
            if death:
                years_life += f"–{death}"
            else:
                years_life += "–н.в."
    
    message = f"""<b>{era_data['emoji']} Эпоха:</b> {era_data['name']}
<b>📅 Период:</b> {era_data['year_start']}–{era_data['year_end']}

<b>🎵 Композитор:</b> {composer_key.title()}
{f'<b>📅 Годы жизни:</b> {years_life}' if years_life else ''}

<b>🔍 Ссылки на поиск музыки:</b>"""
    
    return message, links

def format_unknown_response(text: str) -> Tuple[str, Dict[str, str]]:
    """Формирует сообщение для неизвестного композитора"""
    year = find_year_in_text(text)
    if year:
        era_key = get_era_by_year(year)
        if era_key:
            era_data = ERAS[era_key]
            
            # Формируем поисковый запрос из текста пользователя
            encoded_query = urllib.parse.quote(text[:50])
            links = {
                "apple": f"https://music.apple.com/search?term={encoded_query}",
                "yandex": f"https://music.yandex.ru/search?text={encoded_query}",
                "spotify": f"https://open.spotify.com/search/{encoded_query}/tracks"
            }
            
            message = f"""🔍 <b>Композитор не найден</b>, но я определил эпоху по году {year}:

<b>{era_data['emoji']} Эпоха:</b> {era_data['name']}
<b>📅 Период:</b> {era_data['year_start']}–{era_data['year_end']}

<b>🔍 Поиск по вашему запросу:</b> «{text[:50]}»"""
            return message, links
    
    # Если ничего не найдено
    encoded_query = urllib.parse.quote(text[:50])
    links = {
        "apple": f"https://music.apple.com/search?term={encoded_query}",
        "yandex": f"https://music.yandex.ru/search?text={encoded_query}",
        "spotify": f"https://open.spotify.com/search/{encoded_query}/tracks"
    }
    
    message = f"""⚠️ <b>Не удалось определить эпоху</b>

Я не нашел композитора <b>«{text[:50]}»</b> в своей базе данных и не смог определить год.

<b>Пожалуйста, уточните:</b>
• Полное имя композитора
• Год создания произведения (например, 1824)

Пример: <i>«Бетховен Симфония №9 1824»</i>

<b>🔍 Поиск по вашему запросу:</b> «{text[:50]}»"""
    
    return message, links

# ===================== ОБРАБОТЧИКИ КОМАНД =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_text = f"""👋 <b>Привет, {user.first_name}!</b>

Я — <b>ClassicalEraBot</b> 🎼
Я помогаю распределять классическую музыку по историческим эпохам и даю ссылки на поиск в Apple Music, Яндекс Музыке и Spotify.

<b>Как я работаю:</b>
1️⃣ Отправь мне название произведения или имя композитора
2️⃣ Я найду композитора в базе данных (более 150 композиторов!)
3️⃣ Определю эпоху и дам ссылки для поиска

<b>Примеры запросов:</b>
• <i>«Лунная соната»</i> → найдёт Бетховена
• <i>«Бах Токката и фуга»</i> → найдёт Баха
• <i>«Чайковский Лебединое озеро»</i> → найдёт Чайковского
• <i>«Рахманинов Концерт №2»</i> → найдёт Рахманинова
• <i>«Шостакович Симфония №7 1941»</i> → найдёт Шостаковича

Используй команду /help для подробной информации."""
    
    keyboard = [
        [InlineKeyboardButton("📖 Помощь", callback_data="help")],
        [InlineKeyboardButton("🎵 Все эпохи", callback_data="eras")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """📖 <b>Справка по боту</b>

<b>Как пользоваться:</b>
Просто отправьте мне название произведения или имя композитора.

<b>Примеры:</b>
• <i>«Моцарт Реквием»</i> → Классицизм
• <i>«Бах»</i> → Барокко
• <i>«Дебюсси Лунный свет»</i> → Модерн
• <i>«Шопен Ноктюрн»</i> → Романтизм
• <i>«Рахманинов»</i> → Романтизм

<b>Команды:</b>
/start - Приветствие
/help - Эта справка
/eras - Список всех эпох

<b>Если я не узнал композитора:</b>
Укажи год создания произведения, и я определю эпоху по дате!"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def eras_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    eras_text = "<b>📚 Доступные эпохи:</b>\n\n"
    for key, era in ERAS.items():
        eras_text += f"{era['emoji']} <b>{era['name']}</b>\n"
        eras_text += f"   📅 {era['year_start']}–{era['year_end']}\n\n"
    
    await update.message.reply_text(eras_text, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    logger.info(f"Получено сообщение: {user_text}")
    
    context.user_data['last_query'] = user_text
    
    # Ищем композитора
    composer_key, composer_data = find_composer_in_text(user_text)
    
    if composer_key and composer_data:
        era_key = composer_data.get("era")
        if era_key and ERAS.get(era_key):
            message, links = format_response(composer_key, era_key, composer_data, user_text)
            
            # Создаем кнопки с ссылками
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
            
            await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup, disable_web_page_preview=True)
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
            
            await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup, disable_web_page_preview=True)
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
    
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup, disable_web_page_preview=True)
    logger.warning(f"Не удалось определить эпоху для: {user_text}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await query.edit_message_text(
            """📖 <b>Справка</b>

Отправь мне название произведения или имя композитора.

<b>Примеры:</b>
• Моцарт Реквием → Классицизм
• Бах → Барокко
• Дебюсси → Модерн
• Рахманинов → Романтизм

<b>Если я не узнал композитора:</b>
Укажи год создания (например, 1824)""",
            parse_mode='HTML'
        )
    elif query.data == "eras":
        eras_text = "<b>📚 Доступные эпохи:</b>\n\n"
        for key, era in ERAS.items():
            eras_text += f"{era['emoji']} <b>{era['name']}</b>\n"
            eras_text += f"   📅 {era['year_start']}–{era['year_end']}\n\n"
        await query.edit_message_text(eras_text, parse_mode='HTML')

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
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("eras", eras_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот успешно инициализирован, запускаем polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()