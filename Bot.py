import telebot
from telebot import types
import sqlite3
import re
import time

# ============================================================
# 1. BOT SOZLAMALARI
# ============================================================

# BOTFATHERDAN OLINGAN TOKENNI SHU YERGA YOZING
BOT_TOKEN = "8846630020:AAHoPoqx7PvWqfwiT40NgRPMLwXLzHLYcho"

# Sizning Telegram ID'ingiz
ADMIN_ID = 8673768534

# Kino kanali
MOVIE_CHANNEL = "@kanalk12"

# Majburiy obuna kanali
REQUIRED_CHANNEL = {
    "chat_id": "@treylaeral",
    "name": "Treylerlar",
    "link": "https://t.me/treylaeral"
}

# Treylerlar kanali
TRAILER_CHANNEL = {
    "name": "Treylerlar",
    "link": "https://t.me/treylaeral"
}

# Ma'lumotlar bazasi
DATABASE = "kino_bot.db"


# ============================================================
# 2. BOTNI ISHGA TUSHIRISH
# ============================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# ============================================================
# 3. DATABASE
# ============================================================

def database():
    return sqlite3.connect(DATABASE)


def create_database():

    conn = database()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            channel TEXT NOT NULL,
            message_id INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()


def add_user(user_id):

    conn = database()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()
    conn.close()


def save_movie(code, channel, message_id):

    conn = database()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO movies
        (code, channel, message_id)
        VALUES (?, ?, ?)
    """, (
        code,
        channel,
        message_id
    ))

    conn.commit()
    conn.close()


def get_movie(code):

    conn = database()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT channel, message_id
        FROM movies
        WHERE code = ?
    """, (code,))

    result = cursor.fetchone()

    conn.close()

    return result


def movie_count():

    conn = database()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM movies"
    )

    result = cursor.fetchone()[0]

    conn.close()

    return result


def user_count():

    conn = database()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    result = cursor.fetchone()[0]

    conn.close()

    return result


# ============================================================
# 4. ASOSIY MENYU
# ============================================================

def main_menu():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "🎞 Treylerlar",
        "👤 Admin"
    )

    return keyboard


# ============================================================
# 5. MAJBURIY OBUNANI TEKSHIRISH
# ============================================================

def check_subscription(user_id):

    try:

        member = bot.get_chat_member(
            REQUIRED_CHANNEL["chat_id"],
            user_id
        )

        # A'zo bo'lgan holatlar
        if member.status in [
            "member",
            "administrator",
            "creator"
        ]:
            return True

        # Restricted holatida ham is_member bo'lishi mumkin
        if member.status == "restricted":
            return member.is_member

        return False

    except Exception as error:

        print(
            "Obuna tekshirishda xato:",
            error
        )

        return False


# ============================================================
# 6. OBUNA TUGMALARI
# ============================================================

def subscription_keyboard():

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "📢 Treylerlar kanaliga obuna bo‘lish",
            url=REQUIRED_CHANNEL["link"]
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Tekshirish",
            callback_data="check_subscription"
        )
    )

    return keyboard


def ask_subscription(chat_id):

    text = (
        "🔒 <b>Botdan foydalanish uchun obuna bo‘ling!</b>\n\n"
        "Avval quyidagi kanalga obuna bo‘ling:\n\n"
        "📢 <b>Treylerlar</b>\n\n"
        "Obuna bo‘lgach, "
        "<b>✅ Tekshirish</b> tugmasini bosing."
    )

    bot.send_message(
        chat_id,
        text,
        reply_markup=subscription_keyboard()
    )


# ============================================================
# 7. START
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.from_user.id

    add_user(user_id)

    if not check_subscription(user_id):

        ask_subscription(
            message.chat.id
        )

        return

    bot.send_message(
        message.chat.id,
        "✅ <b>Obuna tasdiqlandi!</b>\n\n"
        "🎬 Kino kodini yuboring.\n\n"
        "Masalan: <code>34</code>",
        reply_markup=main_menu()
    )


# ============================================================
# 8. OBUNANI QAYTA TEKSHIRISH
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "check_subscription"
)
def check_subscription_button(call):

    user_id = call.from_user.id

    if not check_subscription(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Siz hali kanalga obuna bo‘lmagansiz!",
            show_alert=True
        )

        try:

            bot.edit_message_text(
                "❌ <b>Obuna hali tasdiqlanmadi.</b>\n\n"
                "Quyidagi kanalga obuna bo‘ling:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=subscription_keyboard()
            )

        except Exception as error:

            print(error)

        return

    bot.answer_callback_query(
        call.id,
        "✅ Obuna tasdiqlandi!"
    )

    try:

        bot.edit_message_text(
            "✅ <b>Obuna tasdiqlandi!</b>\n\n"
            "🎬 Endi kino kodini yuboring.\n\n"
            "Masalan: <code>34</code>",
            call.message.chat.id,
            call.message.message_id
        )

    except Exception as error:

        print(error)

    bot.send_message(
        call.message.chat.id,
        "👇 <b>Asosiy menyu</b>",
        reply_markup=main_menu()
    )


# ============================================================
# 9. KINO KANALINI KUZATISH
# ============================================================

@bot.channel_post_handler(
    content_types=[
        "video",
        "document",
        "animation",
        "photo",
        "audio"
    ]
)
def movie_channel_media(message):

    try:

        movie_chat = bot.get_chat(
            MOVIE_CHANNEL
        )

        # Faqat @kanalk12 kanalini kuzatamiz
        if message.chat.id != movie_chat.id:
            return

    except Exception as error:

        print(
            "Kanalni aniqlashda xato:",
            error
        )

        return

    # Captionni olamiz
    caption = message.caption or ""

    print(
        "Kanalga yangi media keldi."
    )

    print(
        "Caption:",
        caption
    )

    # Caption ichidan raqamlarni topamiz
    codes = re.findall(
        r"(?<!\d)(\d{1,10})(?!\d)",
        caption
    )

    if not codes:

        print(
            "⚠️ Caption ichida kod topilmadi."
        )

        return

    # Har bir topilgan kodni shu videoga bog'laymiz
    for code in codes:

        save_movie(
            code,
            MOVIE_CHANNEL,
            message.message_id
        )

        print(
            f"✅ Kino saqlandi: "
            f"{code} -> "
            f"{message.message_id}"
        )


# ============================================================
# 10. KOD ORQALI KINO QIDIRISH
# ============================================================

@bot.message_handler(
    func=lambda message:
        message.text is not None
        and re.fullmatch(
            r"\d{1,10}",
            message.text.strip()
        ) is not None
)
def find_movie(message):

    user_id = message.from_user.id

    add_user(user_id)

    # Obunani tekshirish
    if not check_subscription(user_id):

        ask_subscription(
            message.chat.id
        )

        return

    code = message.text.strip()

    print(
        f"Foydalanuvchi {code} kodini yubordi."
    )

    movie = get_movie(code)

    # Kino topilmadi
    if movie is None:

        bot.send_message(
            message.chat.id,
            "❌ <b>Bunday kodli kino topilmadi.</b>\n\n"
            "🔎 Kodni tekshirib, qaytadan yuboring."
        )

        return

    channel, message_id = movie

    try:

        # Kanal postini foydalanuvchiga nusxalab yuboramiz
        bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=channel,
            message_id=message_id
        )

        print(
            f"✅ {code} kodi bo‘yicha kino yuborildi."
        )

    except Exception as error:

        print(
            "❌ Kino yuborishda xato:",
            error
        )

        bot.send_message(
            message.chat.id,
            "⚠️ <b>Kinoni yuborishda xatolik yuz berdi.</b>\n\n"
            "Administratorga murojaat qiling."
        )


# ============================================================
# 11. TREYLERLAR
# ============================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🎞 Treylerlar"
)
def trailers(message):

    user_id = message.from_user.id

    if not check_subscription(user_id):

        ask_subscription(
            message.chat.id
        )

        return

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "🎞 Treylerlar kanalini ochish",
            url=TRAILER_CHANNEL["link"]
        )
    )

    bot.send_message(
        message.chat.id,
        "🎞 <b>Treylerlar</b>\n\n"
        "Yangi treylerlarni quyidagi kanaldan "
        "ko‘rishingiz mumkin:",
        reply_markup=keyboard
    )


# ============================================================
# 12. ADMIN MENYUSI
# ============================================================

@bot.message_handler(
    func=lambda message:
        message.text == "👤 Admin"
)
def admin_menu(message):

    if message.from_user.id != ADMIN_ID:

        bot.send_message(
            message.chat.id,
            "⛔ <b>Bu bo‘lim faqat administrator uchun.</b>"
        )

        return

    keyboard = types.InlineKeyboardMarkup(
        row_width=1
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📊 Statistika",
            callback_data="statistics"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🎬 Kino bazasi",
            callback_data="movie_database"
        )
    )

    bot.send_message(
        message.chat.id,
        "👤 <b>Administrator paneli</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=keyboard
    )


# ============================================================
# 13. ADMIN STATISTIKA
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "statistics"
)
def statistics(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "⛔ Ruxsat yo‘q!",
            show_alert=True
        )

        return

    bot.answer_callback_query(
        call.id
    )

    movies = movie_count()
    users = user_count()

    bot.send_message(
        call.message.chat.id,
        "📊 <b>BOT STATISTIKASI</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"🎬 Kinolar: <b>{movies}</b>"
    )


# ============================================================
# 14. ADMIN KINO BAZASI
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "movie_database"
)
def movie_database(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "⛔ Ruxsat yo‘q!",
            show_alert=True
        )

        return

    bot.answer_callback_query(
        call.id
    )

    count = movie_count()

    bot.send_message(
        call.message.chat.id,
        "🎬 <b>Kino bazasi</b>\n\n"
        f"Jami saqlangan kodlar: <b>{count}</b>\n\n"
        "Kinolarni @kanalk12 kanaliga video + "
        "caption orqali joylashtiring.\n\n"
        "Masalan:\n"
        "<code>34</code>"
    )


# ============================================================
# 15. BOSHQA XABARLAR
# ============================================================

@bot.message_handler(
    func=lambda message:
        message.text is not None
)
def other_messages(message):

    user_id = message.from_user.id

    add_user(user_id)

    if not check_subscription(user_id):

        ask_subscription(
            message.chat.id
        )

        return

    bot.send_message(
        message.chat.id,
        "🎬 <b>Kino kodini yuboring.</b>\n\n"
        "Masalan: <code>34</code>",
        reply_markup=main_menu()
    )


# ============================================================
# 16. BOTNI ISHGA TUSHIRISH
# ============================================================

if __name__ == "__main__":

    create_database()

    print()
    print("========================================")
    print("       🎬 KINO BOT ISHGA TUSHDI")
    print("========================================")
    print("Kino kanali:", MOVIE_CHANNEL)
    print("Obuna kanali:", REQUIRED_CHANNEL["chat_id"])
    print("Admin ID:", ADMIN_ID)
    print("========================================")
    print()

    while True:

        try:

            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                skip_pending=True
            )

        except Exception as error:

            print()
            print("⚠️ BOTDA XATO:")
            print(error)
            print()
            print("5 soniyadan keyin qayta ulanadi...")

            time.sleep(5)
