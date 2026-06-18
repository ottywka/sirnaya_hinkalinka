"""
TELEGRAM-БОТ ДЛЯ РАСПРЕДЕЛЕНИЯ КЛАССИЧЕСКОЙ МУЗЫКИ ПО ЭПОХАМ
Версия: Bothost (с плейлистами Apple Music, Яндекс Музыка, Spotify)
"""

import os
import re
import logging
import urllib.parse
from datetime import datetime
from typing import Dict, Optional, Tuple, List

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

# ===================== БАЗА КОМПОЗИТОРОВ =====================

COMPOSERS_DB = {
    # ===== РАННЯЯ МУЗЫКА =====
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
    
    # ===== БАРОККО =====
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
    "альбинони": {"era": "baroque", "birth": 1671, "death": 1751},
    "томазо альбинони": {"era": "baroque", "birth": 1671, "death": 1751},
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
    "люлли": {"era": "baroque", "birth": 1632, "death": 1687},
    "жан-батист люлли": {"era": "baroque", "birth": 1632, "death": 1687},
    "куперен": {"era": "baroque", "birth": 1668, "death": 1733},
    "франсуа куперен": {"era": "baroque", "birth": 1668, "death": 1733},
    "рамо": {"era": "baroque", "birth": 1683, "death": 1764},
    "жан-филипп рамо": {"era": "baroque", "birth": 1683, "death": 1764},
    "пёрселл": {"era": "baroque", "birth": 1659, "death": 1695},
    "генри пёрселл": {"era": "baroque", "birth": 1659, "death": 1695},
    "бортнянский": {"era": "baroque", "birth": 1751, "death": 1825},
    "дмитрий бортнянский": {"era": "baroque", "birth": 1751, "death": 1825},
    
    # ===== КЛАССИЦИЗМ =====
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
    "боккерини": {"era": "classical", "birth": 1743, "death": 1805},
    "луиджи боккерини": {"era": "classical", "birth": 1743, "death": 1805},
    "клементи": {"era": "classical", "birth": 1752, "death": 1832},
    "муцио клементи": {"era": "classical", "birth": 1752, "death": 1832},
    
    # ===== РОМАНТИЗМ =====
    "шуберт": {"era": "romantic", "birth": 1797, "death": 1828},
    "франц шуберт": {"era": "romantic", "birth": 1797, "death": 1828},
    "schubert": {"era": "romantic", "birth": 1797, "death": 1828},
    "вебер": {"era": "romantic", "birth": 1786, "death": 1826},
    "мендельсон": {"era": "romantic", "birth": 1809, "death": 1847},
    "феликс мендельсон": {"era": "romantic", "birth": 1809, "death": 1847},
    "mendelssohn": {"era": "romantic", "birth": 1809, "death": 1847},
    "шопен": {"era": "romantic", "birth": 1810, "death": 1849},
    "фредерик шопен": {"era": "romantic", "birth": 1810, "death": 1849},
    "chopin": {"era": "romantic", "birth": 1810, "death": 1849},
    "шuman": {"era": "romantic", "birth": 1810, "death": 1856},
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
    
    # ===== МОДЕРН =====
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
    
    # ===== СОВРЕМЕННАЯ =====
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
    "салонен": {"era": "contemporary", "birth": 1958, "death": None},
    "эса-пекка салонен": {"era": "contemporary", "birth": 1958, "death": None},
    "salonen": {"era": "contemporary", "birth": 1958, "death": None},
    "эйнауди": {"era": "contemporary", "birth": 1955, "death": None},
    "людовико эйнауди": {"era": "contemporary", "birth": 1955, "death": None},
    "einaudi": {"era": "contemporary", "birth": 1955, "death": None},
    "рихтер": {"era": "contemporary", "birth": 1969, "death": None},
    "макс рихтер": {"era": "contemporary", "birth": 1969, "death": None},
}

# ===================== СПРАВОЧНИК ПЛЕЙЛИСТОВ =====================
# Формат: "имя_композитора_для_поиска": {"apple": "url", "yandex": "url", "spotify": "url"}
# Здесь хранятся ссылки на официальные плейлисты по композиторам

PLAYLISTS = {
    # Apple Music плейлисты (официальные)
    "bach": {
        "apple": "https://music.apple.com/ru/playlist/pl.9a6c98b486ed4bfa970918a0fd47b43c",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX4sWSpwq3LiO",  # This Is Bach
    },
    "beethoven": {
        "apple": "https://music.apple.com/ru/playlist/pl.70ed5f9f3f50411d9d35605b3df8e559",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX3YSRoTd8Bm6",  # This Is Beethoven
    },
    "mozart": {
        "apple": "https://music.apple.com/ru/playlist/pl.fd4a201bef5f487a92b192d2351f7838",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX1dJnFdIx1P3",  # This Is Mozart
    },
    "tchaikovsky": {
        "apple": "https://music.apple.com/ru/playlist/pl.32513146314b4b4b9dab75bfad573b94",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWTAlXLF2C01E",  # This Is Tchaikovsky
    },
    "rachmaninoff": {
        "apple": "https://music.apple.com/ru/playlist/pl.4837ce8c3b5244edba580d962143b733",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWWp8EeOJJlpN",  # This Is Rachmaninoff
    },
    "chopin": {
        "apple": "https://music.apple.com/ru/playlist/pl.a349afa03abe43d685571f632192b570",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX41K7tDhtLsl",  # This Is Chopin
    },
    "vivaldi": {
        "apple": "https://music.apple.com/ru/playlist/pl.fec7c813a8c249b88102e56db5a79f8c",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWX1bKbL5bZ4n",  # This Is Vivaldi
    },
    "debussy": {
        "apple": "https://music.apple.com/ru/playlist/pl.c2f7dce0a13548189e200a716af43c8f",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWWVxqyN2fBzD",  # This Is Debussy
    },
    "ravel": {
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWVZkP3IZ6xHj",  # This Is Ravel
    },
    "shostakovich": {
        "apple": "https://music.apple.com/ru/playlist/pl.f9a2b8d6f1b04178b5921bc98b7400e5",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX9vk2dUsQnIQ",  # This Is Shostakovich
    },
    "stravinsky": {
        "apple": "https://music.apple.com/ru/playlist/pl.bc8846a16fb84748993275a62126b303",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWTbpTEaZ6bFc",  # This Is Stravinsky
    },
    "prokofiev": {
        "apple": "https://music.apple.com/ru/playlist/pl.92593dee2b3f4295afce4ddf994d5cfc",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWSwLt1UrcHfM",  # This Is Prokofiev
    },
    "handel": {
        "apple": "https://music.apple.com/ru/playlist/pl.0d4fcc70129d4a14865ba65895213d9d",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWXgrteGHYk8J",  # This Is Handel
    },
    "schubert": {
        "apple": "https://music.apple.com/ru/playlist/pl.bcd558114bd748a7a5f0fa458560027f",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DXdG2HfMjlC1I",  # This Is Schubert
    },
    "schumann": {
        "apple": "https://music.apple.com/ru/playlist/pl.e134abbf0621464daf57cf59c87632a1",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWSMGFmnmZ7VZ",  # This Is Schumann
    },
    "brahms": {
        "apple": "https://music.apple.com/ru/playlist/pl.163f926792274a63b69399db0f01841d",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWZ5qKtLZkHpN",  # This Is Brahms
    },
    "mahler": {
        "apple": "https://music.apple.com/ru/playlist/pl.afa1734df46f42709b6a6ed600b6223a",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX9K2lHcl5wQ1",  # This Is Mahler
    },
    "wagner": {
        "apple": "https://music.apple.com/ru/playlist/pl.41b8493720e34baeb23ce707b012ef2f",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX1S8fQOKYf6v",  # This Is Wagner
    },
    "liszt": {
        "apple": "https://music.apple.com/ru/playlist/pl.07a5c0ab0cb34abcb9973db03c7e8c6f",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWVjRsUC2ng2V",  # This Is Liszt
    },
    "grieg": {
        "apple": "https://music.apple.com/ru/playlist/pl.8750949e2a9548bf80f248b3dc47e255",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWTNxUQZQ0z1T",  # This Is Grieg
    },
    "dvorak": {
        "apple": "https://music.apple.com/ru/playlist/pl.9d28c83c6ecb48b68a135d1a3950b07b",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWSk6qNta4vrg",  # This Is Dvořák
    },
    "mussorgsky": {
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWWFc9dtd9SoH",  # This Is Mussorgsky
    },
    "rimsky-korsakov": {
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX5gjAfk5uJhD",  # This Is Rimsky-Korsakov
    },
    "verdi": {
        "apple": "https://music.apple.com/ru/playlist/pl.62dcc82ae6f5452e8f5afc5b1126b783",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWWiE1lB1eWfI",  # This Is Verdi
    },
    "bizet": {
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX3X9Bk0mnpeK",  # This Is Bizet
    },
    "prokofiev": {
        "apple": "https://music.apple.com/ru/playlist/pl.92593dee2b3f4295afce4ddf994d5cfc",
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWSwLt1UrcHfM",  # This Is Prokofiev
    },
    "satie": {
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX7WmwHbk60Lf",  # This Is Satie
    },
    "cage": {
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWT9gHMN0G23M",  # This Is Cage
    },
    "einaudi": {
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWWwTQHcQ7pPo",  # This Is Einaudi
    },
    "pärt": {
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWWWjP4Nefgnr",  # This Is Pärt
    },
    "cage": {
        "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWT9gHMN0G23M",  # This Is Cage
    },
}

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

def get_composer_search_key(composer_key: str) -> str:
    """
    Возвращает ключ для поиска плейлиста в PLAYLISTS
    """
    # Маппинг русских имен на английские ключи
    mapping = {
        "бах": "bach",
        "бетховен": "beethoven",
        "моцарт": "mozart",
        "чайковский": "tchaikovsky",
        "рахманинов": "rachmaninoff",
        "rachmaninoff": "rachmaninoff",
        "rachmaninov": "rachmaninoff",
        "шопен": "chopin",
        "chopin": "chopin",
        "вивальди": "vivaldi",
        "vivaldi": "vivaldi",
        "дебюсси": "debussy",
        "debussy": "debussy",
        "равель": "ravel",
        "ravel": "ravel",
        "шостакович": "shostakovich",
        "shostakovich": "shostakovich",
        "стравинский": "stravinsky",
        "stravinsky": "stravinsky",
        "прокофьев": "prokofiev",
        "prokofiev": "prokofiev",
        "гендель": "handel",
        "handel": "handel",
        "händel": "handel",
        "шуберт": "schubert",
        "schubert": "schubert",
        "шuman": "schumann",
        "schumann": "schumann",
        "брамс": "brahms",
        "brahms": "brahms",
        "малер": "mahler",
        "mahler": "mahler",
        "вагнер": "wagner",
        "wagner": "wagner",
        "лист": "liszt",
        "liszt": "liszt",
        "григ": "grieg",
        "grieg": "grieg",
        "дворжак": "dvorak",
        "dvorak": "dvorak",
        "муссоргский": "mussorgsky",
        "mussorgsky": "mussorgsky",
        "римский-корсаков": "rimsky-korsakov",
        "rimsky-korsakov": "rimsky-korsakov",
        "верди": "verdi",
        "verdi": "verdi",
        "бизе": "bizet",
        "bizet": "bizet",
        "сати": "satie",
        "satie": "satie",
        "кейдж": "cage",
        "cage": "cage",
        "эйнауди": "einaudi",
        "einaudi": "einaudi",
        "пярт": "pärt",
        "pärt": "pärt",
        "барток": "bartok",
        "bartok": "bartok",
        "копленд": "copland",
        "copland": "copland",
    }
    
    composer_lower = composer_key.lower()
    if composer_lower in mapping:
        return mapping[composer_lower]
    
    # Проверяем частичные совпадения
    for key, value in mapping.items():
        if key in composer_lower or composer_lower in key:
            return value
    
    # Если не найдено, возвращаем английский вариант или оригинал
    return composer_key.lower().replace(" ", "-")

def get_playlist_links(composer_key: str) -> Dict[str, str]:
    """
    Возвращает ссылки на плейлисты для композитора.
    Если плейлиста нет - возвращает ссылку на поиск.
    """
    search_key = get_composer_search_key(composer_key)
    
    # Базовый поисковый запрос
    search_name = composer_key.title()
    encoded_search = urllib.parse.quote(search_name)
    
    # Стандартные ссылки на поиск
    default_links = {
        "apple": f"https://music.apple.com/search?term={encoded_search}",
        "yandex": f"https://music.yandex.ru/search?text={encoded_search}",
        "spotify": f"https://open.spotify.com/search/{encoded_search}"
    }
    
    # Ищем плейлист в справочнике
    if search_key in PLAYLISTS:
        playlist = PLAYLISTS[search_key]
        # Заменяем только те ссылки, которые есть в справочнике
        if "apple" in playlist:
            default_links["apple"] = playlist["apple"]
        if "spotify" in playlist:
            default_links["spotify"] = playlist["spotify"]
        if "yandex" in playlist:
            default_links["yandex"] = playlist["yandex"]
    
    return default_links

def get_search_links(query: str) -> Dict[str, str]:
    """Возвращает ссылки на поиск по запросу"""
    encoded_query = urllib.parse.quote(query)
    return {
        "apple": f"https://music.apple.com/search?term={encoded_query}",
        "yandex": f"https://music.yandex.ru/search?text={encoded_query}",
        "spotify": f"https://open.spotify.com/search/{encoded_query}"
    }

# ===================== ОСНОВНЫЕ ФУНКЦИИ =====================

def format_response(composer_key: str, era_key: str, composer_data: Dict = None, user_text: str = None) -> Tuple[str, Dict[str, str]]:
    """Формирует сообщение и ссылки для пользователя"""
    era_data = ERAS.get(era_key)
    if not era_data:
        return "⚠️ Не удалось определить эпоху. Пожалуйста, уточните данные.", {}
    
    # Получаем ссылки на плейлисты или поиск
    links = get_playlist_links(composer_key)
    
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
    
    # Определяем, есть ли плейлисты
    has_playlist = False
    playlist_names = []
    
    if links["apple"] and "playlist" in links["apple"]:
        has_playlist = True
        playlist_names.append("Apple Music")
    if links["spotify"] and "playlist" in links["spotify"]:
        has_playlist = True
        playlist_names.append("Spotify")
    if links["yandex"] and "playlist" in links["yandex"]:
        has_playlist = True
        playlist_names.append("Яндекс Музыка")
    
    # Формируем сообщение
    playlist_text = ""
    if has_playlist:
        playlist_text = f"🎵 <b>Плейлист «{composer_key.title()}»</b> в {'/'.join(playlist_names)}"
    else:
        playlist_text = "🔍 <b>Поиск по имени композитора</b>"
    
    message = f"""<b>{era_data['emoji']} Эпоха:</b> {era_data['name']}
<b>📅 Период:</b> {era_data['year_start']}–{era_data['year_end']}

<b>🎵 Композитор:</b> {composer_key.title()}
{f'<b>📅 Годы жизни:</b> {years_life}' if years_life else ''}

{playlist_text}

Выберите музыкальный сервис:"""
    
    return message, links

def format_unknown_response(text: str) -> Tuple[str, Dict[str, str]]:
    """Формирует сообщение для неизвестного композитора"""
    year = find_year_in_text(text)
    if year:
        era_key = get_era_by_year(year)
        if era_key:
            era_data = ERAS[era_key]
            links = get_search_links(text[:50])
            
            message = f"""🔍 <b>Композитор не найден</b>, но я определил эпоху по году {year}:

<b>{era_data['emoji']} Эпоха:</b> {era_data['name']}
<b>📅 Период:</b> {era_data['year_start']}–{era_data['year_end']}

<b>🔍 Поиск по вашему запросу:</b> «{text[:50]}»

Выберите музыкальный сервис:"""
            return message, links
    
    links = get_search_links(text[:50])
    
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
Я помогаю распределять классическую музыку по историческим эпохам и даю ссылки на плейлисты в Apple Music, Яндекс Музыке и Spotify.

<b>Как я работаю:</b>
1️⃣ Отправь мне название произведения или имя композитора
2️⃣ Я найду композитора в базе данных (более 150 композиторов!)
3️⃣ Определю эпоху и покажу ссылки

<b>Что я умею:</b>
• 🎵 Показываю официальные плейлисты (если есть)
• 🔍 Или ссылки на поиск по имени композитора

<b>Примеры запросов:</b>
• <i>«Бах»</i> → покажет плейлист This Is Bach
• <i>«Рахманинов»</i> → покажет плейлист This Is Rachmaninoff
• <i>«Моцарт Реквием»</i> → найдёт Моцарта
• <i>«Чайковский Лебединое озеро»</i> → найдёт Чайковского

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
• <i>«Бах»</i> → Барокко (плейлист This Is Bach)
• <i>«Дебюсси Лунный свет»</i> → Модерн
• <i>«Рахманинов»</i> → Романтизм (плейлист This Is Rachmaninoff)

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
    
    composer_key, composer_data = find_composer_in_text(user_text)
    
    if composer_key and composer_data:
        era_key = composer_data.get("era")
        if era_key and ERAS.get(era_key):
            message, links = format_response(composer_key, era_key, composer_data, user_text)
            
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
• Бах → Барокко (плейлист This Is Bach)
• Дебюсси → Модерн
• Рахманинов → Романтизм (плейлист This Is Rachmaninoff)

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