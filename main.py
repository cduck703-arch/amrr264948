import os
import time
import hashlib
import random
from datetime import datetime

import telebot
from telebot import types


# ==================================================
# CONFIG
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN غير موجود في Environment Variables في Railway"
    )

ADMIN_ID = 8855682617
DEV = "@z_0_y2"

VERSION = "⤷ ᴠ𝟼.𝟶"
AUTHOR = "⤷ @z_0_y2"


# ==================================================
# USERS / CODES
# ==================================================

AUTHORIZED_USERS = {
    ADMIN_ID
}

user_codes = {}
pending_codes = {}

stop_flags = {}


# ==================================================
# BOT
# ==================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# ==================================================
# AUTH
# ==================================================

def is_authorized(user_id):

    # الأدمن دائمًا لديه صلاحية
    if user_id == ADMIN_ID:
        return True

    if user_id not in user_codes:
        return False

    expiry = user_codes[user_id]["expiry"]

    if expiry <= time.time():
        user_codes.pop(user_id, None)
        return False

    return True


def generate_user_code(expiry_days):

    random_part = f"{time.time()}-{random.random()}"

    code = hashlib.md5(
        random_part.encode()
    ).hexdigest()[:12].upper()

    pending_codes[code] = {
        "expiry": time.time() + (expiry_days * 86400),
        "created_by": ADMIN_ID
    }

    return code


def activate_user_code(user_id, code):

    code = code.strip().upper()

    if code not in pending_codes:
        return False

    data = pending_codes[code]

    if data["expiry"] <= time.time():
        pending_codes.pop(code, None)
        return False

    user_codes[user_id] = {
        "expiry": data["expiry"]
    }

    pending_codes.pop(code, None)

    return True


def get_user_expiry(user_id):

    if user_id == ADMIN_ID:
        return "ADMIN"

    if user_id not in user_codes:
        return "غير مسجل"

    expiry = user_codes[user_id]["expiry"]

    if expiry <= time.time():
        user_codes.pop(user_id, None)
        return "منتهي"

    return datetime.fromtimestamp(
        expiry
    ).strftime("%Y-%m-%d %H:%M:%S")


# ==================================================
# START
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.from_user.id

    # ================= ADMIN =================

    if user_id == ADMIN_ID:

        markup = types.InlineKeyboardMarkup(
            row_width=1
        )

        markup.add(
            types.InlineKeyboardButton(
                "🔐 إنشاء كود جديد",
                callback_data="create_code"
            ),
            types.InlineKeyboardButton(
                "📊 الكودات النشطة",
                callback_data="list_codes"
            ),
            types.InlineKeyboardButton(
                "👥 المستخدمين",
                callback_data="list_users"
            )
        )

        welcome = f"""
◈ <b>MULTI TOOL BOT</b> ◈
━━━━━━━━━━━━━━━━━━━━━━
✧ {VERSION}
✧ {AUTHOR}
━━━━━━━━━━━━━━━━━━━━━━

👑 <b>ADMIN PANEL</b>

✧ /start
✧ /gencode 10
✧ /stats

📁 يمكنك إرسال ملف TXT أيضًا.

━━━━━━━━━━━━━━━━━━━━━━
"""

        bot.reply_to(
            message,
            welcome,
            reply_markup=markup
        )

        return

    # ================= USER =================

    if is_authorized(user_id):

        expiry = get_user_expiry(user_id)

        welcome = f"""
◈ <b>MULTI TOOL BOT</b> ◈
━━━━━━━━━━━━━━━━━━━━━━
✧ {VERSION}
✧ {AUTHOR}
━━━━━━━━━━━━━━━━━━━━━━

✅ <b>ACCESS GRANTED</b>

📅 صلاحيتك تنتهي:
<code>{expiry}</code>

📁 يمكنك إرسال ملف TXT.

━━━━━━━━━━━━━━━━━━━━━━
✧ /start
✧ /stats
━━━━━━━━━━━━━━━━━━━━━━
"""

        bot.reply_to(
            message,
            welcome
        )

    else:

        bot.reply_to(
            message,
            f"""
❌ <b>ACCESS DENIED</b>

لا تملك صلاحية استخدام البوت.

🔑 استخدم:

<code>/activate CODE</code>

أو تواصل مع:
{DEV}
"""
        )


# ==================================================
# ACTIVATE
# ==================================================

@bot.message_handler(commands=["activate"])
def activate(message):

    user_id = message.from_user.id

    parts = message.text.split(
        maxsplit=1
    )

    if len(parts) < 2:

        bot.reply_to(
            message,
            """
❌ <b>طريقة الاستخدام:</b>

<code>/activate CODE</code>
"""
        )

        return

    code = parts[1].strip()

    if activate_user_code(
        user_id,
        code
    ):

        expiry = get_user_expiry(user_id)

        bot.reply_to(
            message,
            f"""
✅ <b>تم تفعيل الكود بنجاح!</b>

━━━━━━━━━━━━━━━━━━━━━

🔑 الكود:
<code>{code}</code>

📅 ينتهي:
<code>{expiry}</code>

━━━━━━━━━━━━━━━━━━━━━

يمكنك الآن استخدام البوت.
"""
        )

    else:

        bot.reply_to(
            message,
            """
❌ <b>الكود غير صالح</b>

قد يكون الكود:
• غير موجود
• مستخدم مسبقًا
• منتهي الصلاحية
"""
        )


# ==================================================
# GENERATE CODE
# ==================================================

@bot.message_handler(commands=["gencode"])
def gen_code(message):

    if message.from_user.id != ADMIN_ID:

        bot.reply_to(
            message,
            "❌ ACCESS DENIED"
        )

        return

    parts = message.text.split()

    if len(parts) < 2:

        bot.reply_to(
            message,
            """
❌ <b>طريقة الاستخدام:</b>

<code>/gencode 10</code>

10 = عدد الأيام
"""
        )

        return

    try:

        days = int(parts[1])

    except ValueError:

        bot.reply_to(
            message,
            "❌ يجب إدخال رقم صحيح."
        )

        return

    if days <= 0:

        bot.reply_to(
            message,
            "❌ عدد الأيام يجب أن يكون أكبر من صفر."
        )

        return

    code = generate_user_code(days)

    expiry = datetime.fromtimestamp(
        pending_codes[code]["expiry"]
    ).strftime("%Y-%m-%d %H:%M:%S")

    bot.reply_to(
        message,
        f"""
✅ <b>تم إنشاء الكود!</b>

━━━━━━━━━━━━━━━━━━━━━

🔑 الكود:
<code>{code}</code>

📅 المدة:
<b>{days} يوم</b>

⏰ ينتهي:
<code>{expiry}</code>

━━━━━━━━━━━━━━━━━━━━━

أرسل للمستخدم:

<code>/activate {code}</code>
"""
    )


# ==================================================
# STATS
# ==================================================

@bot.message_handler(commands=["stats"])
def stats(message):

    user_id = message.from_user.id

    if not is_authorized(user_id):

        bot.reply_to(
            message,
            "❌ ACCESS DENIED"
        )

        return

    # حذف المستخدمين المنتهيين
    expired_users = []

    for uid, data in user_codes.items():

        if data["expiry"] <= time.time():
            expired_users.append(uid)

    for uid in expired_users:
        user_codes.pop(uid, None)

    bot.reply_to(
        message,
        f"""
📊 <b>STATISTICS</b>

━━━━━━━━━━━━━━━━━━━━━

👥 المستخدمين:
<b>{len(user_codes)}</b>

🔑 الكودات النشطة:
<b>{len(pending_codes)}</b>

👑 الأدمن:
<b>1</b>

━━━━━━━━━━━━━━━━━━━━━

⚡ {VERSION}
👤 {AUTHOR}
"""
    )


# ==================================================
# FILE HANDLER
# ==================================================

@bot.message_handler(
    content_types=["document"]
)
def handle_file(message):

    user_id = message.from_user.id

    # التحقق من الصلاحية
    if not is_authorized(user_id):

        bot.reply_to(
            message,
            "❌ ACCESS DENIED"
        )

        return

    status_msg = bot.reply_to(
        message,
        "📂 <b>جاري تحميل الملف...</b>"
    )

    try:

        # الحصول على معلومات الملف
        file_info = bot.get_file(
            message.document.file_id
        )

        # تحميل الملف
        downloaded = bot.download_file(
            file_info.file_path
        )

        # قراءة الملف
        try:

            content = downloaded.decode(
                "utf-8"
            )

        except UnicodeDecodeError:

            content = downloaded.decode(
                "utf-8",
                errors="ignore"
            )

        # استخراج الأسطر
        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        filename = (
            message.document.file_name
            or "unknown"
        )

        filesize = len(downloaded)

        # تحديث الرسالة
        bot.edit_message_text(
            f"""
✅ <b>تم استلام الملف بنجاح!</b>

━━━━━━━━━━━━━━━━━━━━━

📁 الاسم:
<code>{filename}</code>

📦 الحجم:
<b>{filesize:,}</b> Bytes

📝 عدد الأسطر:
<b>{len(lines):,}</b>

━━━━━━━━━━━━━━━━━━━━━

⚡ {VERSION}
👤 {AUTHOR}
""",
            chat_id=user_id,
            message_id=status_msg.message_id
        )

    except Exception as e:

        bot.edit_message_text(
            f"""
❌ <b>حدث خطأ أثناء قراءة الملف</b>

━━━━━━━━━━━━━━━━━━━━━

<code>{str(e)[:500]}</code>

━━━━━━━━━━━━━━━━━━━━━
"""
            ,
            chat_id=user_id,
            message_id=status_msg.message_id
        )


# ==================================================
# ADMIN - CREATE CODE BUTTON
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "create_code"
)
def create_code_callback(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "❌ هذا الأمر للأدمن فقط"
        )

        return

    bot.answer_callback_query(
        call.id
    )

    msg = bot.send_message(
        call.from_user.id,
        """
📝 <b>أرسل مدة الكود بالأيام:</b>

مثال:

<code>30</code>
"""
    )

    bot.register_next_step_handler(
        msg,
        get_code_days
    )


def get_code_days(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        days = int(
            message.text.strip()
        )

        if days <= 0:
            raise ValueError

    except ValueError:

        bot.send_message(
            message.chat.id,
            "❌ أدخل رقمًا صحيحًا أكبر من 0."
        )

        return

    code = generate_user_code(days)

    expiry = datetime.fromtimestamp(
        pending_codes[code]["expiry"]
    ).strftime("%Y-%m-%d %H:%M:%S")

    bot.send_message(
        message.chat.id,
        f"""
✅ <b>تم إنشاء الكود بنجاح!</b>

━━━━━━━━━━━━━━━━━━━━━

🔑 <code>{code}</code>

📅 الصلاحية:
<b>{days} يوم</b>

⏰ الانتهاء:
<code>{expiry}</code>

━━━━━━━━━━━━━━━━━━━━━

<code>/activate {code}</code>
"""
    )


# ==================================================
# ADMIN - LIST CODES
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "list_codes"
)
def list_codes_callback(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "❌ للأدمن فقط"
        )

        return

    bot.answer_callback_query(
        call.id
    )

    # حذف الكودات المنتهية
    expired_codes = []

    for code, data in pending_codes.items():

        if data["expiry"] <= time.time():
            expired_codes.append(code)

    for code in expired_codes:
        pending_codes.pop(code, None)

    if not pending_codes:

        bot.send_message(
            call.from_user.id,
            "📭 لا توجد كودات نشطة."
        )

        return

    text = """
📋 <b>الكودات النشطة</b>

━━━━━━━━━━━━━━━━━━━━━
"""

    for code, data in pending_codes.items():

        expiry = datetime.fromtimestamp(
            data["expiry"]
        ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        text += f"""
🔑 <code>{code}</code>
⏰ {expiry}

"""

    bot.send_message(
        call.from_user.id,
        text
    )


# ==================================================
# ADMIN - LIST USERS
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "list_users"
)
def list_users_callback(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "❌ للأدمن فقط"
        )

        return

    bot.answer_callback_query(
        call.id
    )

    # حذف المنتهيين
    expired_users = []

    for uid, data in user_codes.items():

        if data["expiry"] <= time.time():
            expired_users.append(uid)

    for uid in expired_users:
        user_codes.pop(uid, None)

    if not user_codes:

        bot.send_message(
            call.from_user.id,
            "📭 لا يوجد مستخدمون نشطون."
        )

        return

    text = """
👥 <b>المستخدمين النشطين</b>

━━━━━━━━━━━━━━━━━━━━━
"""

    for uid, data in user_codes.items():

        expiry = datetime.fromtimestamp(
            data["expiry"]
        ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        text += f"""
🆔 <code>{uid}</code>
⏰ {expiry}

"""

    bot.send_message(
        call.from_user.id,
        text
    )


# ==================================================
# STOP BUTTON
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "stop"
)
def stop_callback(call):

    user_id = call.from_user.id

    stop_flags[user_id] = True

    bot.answer_callback_query(
        call.id,
        "⏹️ تم طلب الإيقاف"
    )


# ==================================================
# EMPTY BUTTON
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "x"
)
def x_callback(call):

    bot.answer_callback_query(
        call.id,
        "📊 لا توجد عملية حالية"
    )


# ==================================================
# FALLBACK
# ==================================================

@bot.message_handler(
    func=lambda message: True
)
def fallback(message):

    if not is_authorized(
        message.from_user.id
    ):

        bot.reply_to(
            message,
            f"""
❌ <b>ACCESS DENIED</b>

استخدم:

<code>/activate CODE</code>

للحصول على كود تواصل مع:

{DEV}
"""
        )

        return

    bot.reply_to(
        message,
        """
❓ <b>أمر غير معروف</b>

استخدم:

<code>/start</code>
"""
    )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    print("=" * 50)
    print("✅ TELEGRAM BOT STARTED")
    print(f"👤 {AUTHOR}")
    print(f"📦 {VERSION}")
    print("✅ نظام الأكواد مفعل")
    print("✅ نظام الصلاحيات مفعل")
    print("✅ استقبال ملفات TXT مفعل")
    print("=" * 50)

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )
