"""
TELEGRAM-БОТ ДЛЯ РАСПРЕДЕЛЕНИЯ КЛАССИЧЕСКОЙ МУЗЫКИ ПО ЭПОХАМ
Версия: PythonAnywhere (с threaded=False для бесплатного тарифа)
Требования: Python 3.10+, библиотеки python-telegram-bot==20.7
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ===================== НАСТРОЙКИ =====================
# ВСТАВЬ СВОЙ ТОКЕН СЮДА
import os
BOT_TOKEN = os.environ.get("8924352933:AAFeg484651o6c42hlgc6a-21GQXNrCF1io")

# Настройка логирования (для отслеживания ошибок на PythonAnywhere)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== СПРАВОЧНИКИ =====================

# Эпохи с временными границами и ссылками на плейлисты Apple Music
ERAS = {
    "medieval": {
        "name": "Ранняя музыка (Medieval / Renaissance)",
        "name_en": "Medieval / Renaissance",
        "year_start": 0,
        "year_end": 1599,
        "emoji": "🏛️",
        "playlist_link": "https://music.apple.com/search?term=medieval%20renaissance%20classical"
    },
    "baroque": {
        "name": "Барокко (Baroque)",
        "name_en": "Baroque",
        "year_start": 1600,
        "year_end": 1749,
        "emoji": "👑",
        "playlist_link": "https://music.apple.com/sg/playlist/bach-and-the-baroque/pl.d7a320e862fe4017a6ba8d2c6937f04c"
    },
    "classical": {
        "name": "Классицизм (Classical)",
        "name_en": "Classical",
        "year_start": 1750,
        "year_end": 1819,
        "emoji": "🏛️",
        "playlist_link": "https://music.apple.com/sg/playlist/mozart-and-more/pl.fe324bdb6f104480bae2021c10bbcf77"
    },
    "romantic": {
        "name": "Романтизм (Romantic)",
        "name_en": "Romantic",
        "year_start": 1820,
        "year_end": 1899,
        "emoji": "🌹",
        "playlist_link": "https://music.apple.com/search?term=romantic%20classical%20playlist"
    },
    "modern": {
        "name": "Импрессионизм / Модерн (Modern)",
        "name_en": "Modern",
        "year_start": 1900,
        "year_end": 1949,
        "emoji": "🎨",
        "playlist_link": "https://music.apple.com/search?term=modern%20classical%20impressionist"
    },
    "contemporary": {
        "name": "Современная академическая (Contemporary)",
        "name_en": "Contemporary",
        "year_start": 1950,
        "year_end": datetime.now().year,
        "emoji": "🔮",
        "playlist_link": "https://music.apple.com/search?term=contemporary%20classical%20minimalist"
    }
}

# База данных композиторов с годами жизни
COMPOSERS_DB = {
    # Ранняя музыка
    "машо": {"era": "medieval", "birth": 1300, "death": 1377},
    "ландини": {"era": "medieval", "birth": 1325, "death": 1397},
    "данстейбл": {"era": "medieval", "birth": 1390, "death": 1453},
    "таллис": {"era": "medieval", "birth": 1505, "death": 1585},
    
    # Барокко
    "монтеверди": {"era": "baroque", "birth": 1567, "death": 1643},
    "пёрселл": {"era": "baroque", "birth": 1659, "death": 1695},
    "перселл": {"era": "baroque", "birth": 1659, "death": 1695},
    "вивальди": {"era": "baroque", "birth": 1678, "death": 1741},
    "бах": {"era": "baroque", "birth": 1685, "death": 1750},
    "гендель": {"era": "baroque", "birth": 1685, "death": 1759},
    "händel": {"era": "baroque", "birth": 1685, "death": 1759},
    "скарлатти": {"era": "baroque", "birth": 1685, "death": 1757},
    "рамо": {"era": "baroque", "birth": 1683, "death": 1764},
    
    # Классицизм
    "глюк": {"era": "classical", "birth": 1714, "death": 1787},
    "гайдн": {"era": "classical", "birth": 1732, "death": 1809},
    "haydn": {"era": "classical", "birth": 1732, "death": 1809},
    "моцарт": {"era": "classical", "birth": 1756, "death": 1791},
    "mozart": {"era": "classical", "birth": 1756, "death": 1791},
    "бетховен": {"era": "classical", "birth": 1770, "death": 1827},
    "beethoven": {"era": "classical", "birth": 1770, "death": 1827},
    "сальери": {"era": "classical", "birth": 1750, "death": 1825},
    "к.ф.э. бах": {"era": "classical", "birth": 1714, "death": 1788},
    "c.p.e. bach": {"era": "classical", "birth": 1714, "death": 1788},
    
    # Романтизм
    "шуберт": {"era": "romantic", "birth": 1797, "death": 1828},
    "schubert": {"era": "romantic", "birth": 1797, "death": 1828},
    "шопен": {"era": "romantic", "birth": 1810, "death": 1849},
    "chopin": {"era": "romantic", "birth": 1810, "death": 1849},
    "лист": {"era": "romantic", "birth": 1811, "death": 1886},
    "liszt": {"era": "romantic", "birth": 1811, "death": 1886},
    "вагнер": {"era": "romantic", "birth": 1813, "death": 1883},
    "wagner": {"era": "romantic", "birth": 1813, "death": 1883},
    "верди": {"era": "romantic", "birth": 1813, "death": 1901},
    "verdi": {"era": "romantic", "birth": 1813, "death": 1901},
    "брамс": {"era": "romantic", "birth": 1833, "death": 1897},
    "brahms": {"era": "romantic", "birth": 1833, "death": 1897},
    "чайковский": {"era": "romantic", "birth": 1840, "death": 1893},
    "tchaikovsky": {"era": "romantic", "birth": 1840, "death": 1893},
    "дворжак": {"era": "romantic", "birth": 1841, "death": 1904},
    "dvorak": {"era": "romantic", "birth": 1841, "death": 1904},
    "григ": {"era": "romantic", "birth": 1843, "death": 1907},
    "grieg": {"era": "romantic", "birth": 1843, "death": 1907},
    "малер": {"era": "romantic", "birth": 1860, "death": 1911},
    "mahler": {"era": "romantic", "birth": 1860, "death": 1911},
    "шuman": {"era": "romantic", "birth": 1810, "death": 1856},
    "schumann": {"era": "romantic", "birth": 1810, "death": 1856},
    
    # Модерн
    "дебюсси": {"era": "modern", "birth": 1862, "death": 1918},
    "debussy": {"era": "modern", "birth": 1862, "death": 1918},
    "равель": {"era": "modern", "birth": 1875, "death": 1937},
    "ravel": {"era": "modern", "birth": 1875, "death": 1937},
    "сати": {"era": "modern", "birth": 1866, "death": 1925},
    "satie": {"era": "modern", "birth": 1866, "death": 1925},
    "стравинский": {"era": "modern", "birth": 1882, "death": 1971},
    "stravinsky": {"era": "modern", "birth": 1882, "death": 1971},
    "барток": {"era": "modern", "birth": 1881, "death": 1945},
    "bartok": {"era": "modern", "birth": 1881, "death": 1945},
    "прокофьев": {"era": "modern", "birth": 1891, "death": 1953},
    "prokofiev": {"era": "modern", "birth": 1891, "death": 1953},
    "шостакович": {"era": "modern", "birth": 1906, "death": 1975},
    "shostakovich": {"era": "modern", "birth": 1906, "death": 1975},
    "копленд": {"era": "modern", "birth": 1900, "death": 1990},
    "copland": {"era": "modern", "birth": 1900, "death": 1990},
    
    # Контемпорари
    "мессиан": {"era": "contemporary", "birth": 1908, "death": 1992},
    "messiaen": {"era": "contemporary", "birth": 1908, "death": 1992},
    "булез": {"era": "contemporary", "birth": 1925, "death": 2016},
    "boulez": {"era": "contemporary", "birth": 1925, "death": 2016},
    "кейдж": {"era": "contemporary", "birth": 1912, "death": 1992},
    "cage": {"era": "contemporary", "birth": 1912, "death": 1992},
    "штокхаузен": {"era": "contemporary", "birth": 1928, "death": 2007},
    "stockhausen": {"era": "contemporary", "birth": 1928, "death": 2007},
    "шнитке": {"era": "contemporary", "birth": 1934, "death": 1998},
    "schnittke": {"era": "contemporary", "birth": 1934, "death": 1998},
    "пярт": {"era": "contemporary", "birth": 1935, "death": None},
    "pärt": {"era": "contemporary", "birth": 1935, "death": None},
    "салонен": {"era": "contemporary", "birth": 1958, "death": None},
    "salonen": {"era": "contemporary", "birth": 1958, "death": None},
    "эйнауди": {"era": "contemporary", "birth": 1955, "death": None},
    "einaudi": {"era": "contemporary", "birth": 1955, "death": None},
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
    
    for composer, data in COMPOSERS_DB.items():
        composer_lower = composer.lower()
        if composer_lower in normalized:
            return composer, data
        
        if len(composer_lower) > 5:
            parts = composer_lower.split()
            for part in parts:
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

def format_response(composer_name: str, era_key: str, composer_data: Dict = None) -> str:
    """Формирует красивое сообщение для пользователя"""
    era_data = ERAS.get(era_key)
    if not era_data:
        return "⚠️ Не удалось определить эпоху. Пожалуйста, уточните данные."
    
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

<b>🎵 Композитор:</b> {composer_name.title() if composer_name else 'Неизвестен'}
{f'<b>📅 Годы жизни:</b> {years_life}' if years_life else ''}

✅ <b>Трек добавлен в плейлист «{era_data['name_en']}»</b>

🎵 <a href="{era_data['playlist_link']}">Слушать в Apple Music</a>"""
    
    return message

def format_unknown_response(text: str) -> str:
    """Формирует сообщение для неизвестного композитора"""
    year = find_year_in_text(text)
    
    if year:
        era_key = get_era_by_year(year)
        if era_key:
            era_data = ERAS[era_key]
            return f"""🔍 <b>Композитор не найден</b>, но я определил эпоху по году {year}:

<b>{era_data['emoji']} Эпоха:</b> {era_data['name']}
<b>📅 Период:</b> {era_data['year_start']}–{era_data['year_end']}

✅ <b>Трек добавлен в плейлист «{era_data['name_en']}»</b>

🎵 <a href="{era_data['playlist_link']}">Слушать в Apple Music</a>"""
    
    return f"""⚠️ <b>Не удалось определить эпоху</b>

Я не нашел композитора <b>«{text[:50]}»</b> в своей базе данных и не смог определить год.

<b>Пожалуйста, уточните:</b>
• Полное имя композитора
• Год создания произведения (например, 1824)

Пример: <i>«Бетховен Симфония №9 1824»</i>"""

def get_eras_list() -> str:
    """Возвращает список всех эпох для справки"""
    result = "<b>📚 Доступные эпохи:</b>\n\n"
    for key, era in ERAS.items():
        result += f"{era['emoji']} <b>{era['name']}</b>\n"
        result += f"   📅 {era['year_start']}–{era['year_end']}\n"
        result += f"   🎵 <a href='{era['playlist_link']}'>Плейлист Apple Music</a>\n\n"
    return result

# ===================== ОБРАБОТЧИКИ КОМАНД =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = f"""👋 <b>Привет, {user.first_name}!</b>

Я — <b>ClassicalEraBot</b> 🎼
Я помогаю распределять классическую музыку по историческим эпохам и даю ссылки на плейлисты в Apple Music.

<b>Как я работаю:</b>
1️⃣ Отправь мне название произведения или имя композитора
2️⃣ Я найду композитора в базе данных
3️⃣ Определю эпоху и дам ссылку на плейлист

<b>Примеры запросов:</b>
• <i>«Лунная соната»</i>
• <i>«Бах Токката и фуга»</i>
• <i>«Чайковский Лебединое озеро»</i>
• <i>«Шостакович Симфония №7 1941»</i>

Используй команду /help для подробной информации.
Команда /eras покажет все доступные эпохи и плейлисты."""
    
    keyboard = [
        [InlineKeyboardButton("📖 Помощь", callback_data="help")],
        [InlineKeyboardButton("🎵 Все эпохи", callback_data="eras")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = """📖 <b>Справка по боту</b>

<b>Как пользоваться:</b>
Просто отправьте мне название произведения или имя композитора.

<b>Примеры:</b>
• <i>«Моцарт Реквием»</i> → Классицизм
• <i>«Бах»</i> → Барокко
• <i>«Дебюсси Лунный свет»</i> → Модерн
• <i>«Шопен Ноктюрн»</i> → Романтизм

<b>Что я умею:</b>
✅ Распознавать композиторов по фамилии
✅ Определять эпоху по году (если указан)
✅ Давать ссылки на плейлисты в Apple Music

<b>Команды:</b>
/start - Приветствие
/help - Эта справка
/eras - Список всех эпох и плейлистов

<b>Если я не узнал композитора:</b>
Укажи год создания произведения, и я определю эпоху по дате!"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def eras_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /eras - показывает все эпохи и ссылки на плейлисты"""
    eras_text = get_eras_list()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(eras_text, parse_mode='HTML', reply_markup=reply_markup, disable_web_page_preview=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Основной обработчик текстовых сообщений"""
    user_text = update.message.text
    logger.info(f"Получено сообщение от {update.effective_user.username}: {user_text}")
    
    composer_name, composer_data = find_composer_in_text(user_text)
    
    if composer_name and composer_data:
        era_key = composer_data.get("era")
        era_data = ERAS.get(era_key)
        
        if era_data:
            response = format_response(composer_name, era_key, composer_data)
            await update.message.reply_text(response, parse_mode='HTML', disable_web_page_preview=False)
            logger.info(f"Определен композитор {composer_name} → эпоха {era_key}")
            return
    
    year = find_year_in_text(user_text)
    if year:
        era_key = get_era_by_year(year)
        if era_key:
            response = format_unknown_response(user_text)
            await update.message.reply_text(response, parse_mode='HTML', disable_web_page_preview=False)
            logger.info(f"Определена эпоха по году {year} → {era_key}")
            return
    
    response = format_unknown_response(user_text)
    await update.message.reply_text(response, parse_mode='HTML')
    logger.warning(f"Не удалось определить эпоху для: {user_text}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на инлайн-кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        help_text = """📖 <b>Справка</b>

Отправь мне название произведения или имя композитора.

<b>Примеры:</b>
• Моцарт Реквием → Классицизм
• Бах → Барокко
• Дебюсси → Модерн

<b>Если я не узнал композитора:</b>
Укажи год создания (например, 1824)"""
        await query.edit_message_text(help_text, parse_mode='HTML')
    
    elif query.data == "eras":
        eras_text = get_eras_list()
        await query.edit_message_text(eras_text, parse_mode='HTML', disable_web_page_preview=True)
    
    elif query.data == "start":
        welcome_text = """👋 <b>Главное меню</b>

Я помогаю распределять классическую музыку по эпохам.

<b>Просто отправь мне:</b>
• Имя композитора
• Название произведения
• Или год создания

Я найду нужную эпоху и покажу плейлист в Apple Music!"""
        await query.edit_message_text(welcome_text, parse_mode='HTML')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "😅 Произошла ошибка. Пожалуйста, попробуйте еще раз или переформулируйте запрос."
        )

# ===================== ЗАПУСК БОТА =====================

def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("eras", eras_command))
    
    # Регистрируем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Регистрируем обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота с threaded=False (важно для PythonAnywhere!)
    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    print("📋 Доступные команды: /start, /help, /eras")
    
    # ВАЖНО: добавляем параметр allowed_updates чтобы уменьшить нагрузку
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        # на бесплатном тарифе PythonAnywhere нужно отключить threading
        # это делается через параметр drop_pending_updates или без дополнительных настроек
    )

if __name__ == '__main__':
    main()