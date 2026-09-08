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
        "BOT_TOKEN غير موجود. أضفه في Environment Variables في Railway."
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
# AUTH FUNCTIONS
# ==================================================

def is_authorized(user_id):
    # الأدمن دائمًا مسموح له
    if user_id == ADMIN_ID:
        return True

    # مستخدم غير موجود
    if user_id not in user_codes:
        return False

    expiry = user_codes[user_id]["expiry"]

    # انتهت الصلاحية
    if expiry <= time.time():
        del user_codes[user_id]
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

    # التحقق من انتهاء الكود
    if data["expiry"] <= time.time():
        del pending_codes[code]
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

        markup = types.InlineKeyboardMarkup(row_width=1)

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

━━━━━━━━━━━━━━━━━━━━━━
"""

        bot.reply_to(
            message,
            welcome,
            reply_markup=markup,
            parse_mode="HTML"
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

━━━━━━━━━━━━━━━━━━━━━━
✧ /start
✧ /stats
━━━━━━━━━━━━━━━━━━━━━━
"""

        bot.reply_to(
            message,
            welcome,
            parse_mode="HTML"
        )

    else:

        bot.reply_to(
            message,
            f"""
❌ <b>ACCESS DENIED</b>

✧ لا تملك صلاحية استخدام البوت.

🔑 استخدم:
<code>/activate CODE</code>

أو تواصل مع:
{DEV}
""",
            parse_mode="HTML"
        )


# ==================================================
# ACTIVATE
# ==================================================

@bot.message_handler(commands=["activate"])
def activate(message):

    user_id = message.from_user.id

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:

        bot.reply_to(
            message,
            """
❌ <b>طريقة الاستخدام:</b>

<code>/activate CODE</code>
""",
            parse_mode="HTML"
        )

        return

    code = parts[1].strip()

    if activate_user_code(user_id, code):

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
""",
            parse_mode="HTML"
        )

    else:

        bot.reply_to(
            message,
            """
❌ <b>الكود غير صالح</b>

قد يكون:
• غير موجود
• مستخدم مسبقًا
• منتهي الصلاحية
""",
            parse_mode="HTML"
        )


# ==================================================
# GENERATE CODE
# ==================================================

@bot.message_handler(commands=["gencode"])
def gen_code(message):

    user_id = message.from_user.id

    if user_id != ADMIN_ID:

        bot.reply_to(
            message,
            "❌ ACCESS DENIED",
            parse_mode="HTML"
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
""",
            parse_mode="HTML"
        )

        return

    try:
        days = int(parts[1])
    except ValueError:

        bot.reply_to(
            message,
            "❌ يجب إدخال رقم صحيح.",
            parse_mode="HTML"
        )

        return

    if days <= 0:

        bot.reply_to(
            message,
            "❌ عدد الأيام يجب أن يكون أكبر من صفر.",
            parse_mode="HTML"
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
""",
        parse_mode="HTML"
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

    # تنظيف المستخدمين المنتهيين
    expired = []

    for uid, data in user_codes.items():

        if data["expiry"] <= time.time():
            expired.append(uid)

    for uid in expired:
        user_codes.pop(uid, None)

    bot.reply_to(
        message,
        f"""
📊 <b>STATISTICS</b>
━━━━━━━━━━━━━━━━━━━━━

👥 المستخدمين:
<b>{len(user_codes)}</b>

🔑 الكودات المتاحة:
<b>{len(pending_codes)}</b>

👑 الأدمن:
<b>1</b>

━━━━━━━━━━━━━━━━━━━━━

⚡ {VERSION}
👤 {AUTHOR}
""",
        parse_mode="HTML"
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

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.from_user.id,
        """
📝 <b>أرسل مدة الكود بالأيام:</b>

مثال:
<code>30</code>
""",
        parse_mode="HTML"
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
            "❌ أدخل رقمًا صحيحًا أكبر من 0.",
            parse_mode="HTML"
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
""",
        parse_mode="HTML"
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

    bot.answer_callback_query(call.id)

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

    expired_codes = []

    for code, data in pending_codes.items():

        if data["expiry"] <= time.time():
            expired_codes.append(code)
            continue

        expiry = datetime.fromtimestamp(
            data["expiry"]
        ).strftime("%Y-%m-%d %H:%M:%S")

        text += f"""
🔑 <code>{code}</code>
⏰ {expiry}

"""

    for code in expired_codes:
        pending_codes.pop(code, None)

    if len(text.strip()) <= 45:

        bot.send_message(
            call.from_user.id,
            "📭 لا توجد كودات نشطة."
        )

        return

    bot.send_message(
        call.from_user.id,
        text,
        parse_mode="HTML"
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

    bot.answer_callback_query(call.id)

    if not user_codes:

        bot.send_message(
            call.from_user.id,
            "📭 لا يوجد مستخدمون نشطون."
        )

        return

    text = """
👥 <b>المستخدمين</b>
━━━━━━━━━━━━━━━━━━━━━
"""

    expired_users = []

    for uid, data in user_codes.items():

        if data["expiry"] <= time.time():
            expired_users.append(uid)
            continue

        expiry = datetime.fromtimestamp(
            data["expiry"]
        ).strftime("%Y-%m-%d %H:%M:%S")

        text += f"""
🆔 <code>{uid}</code>
⏰ {expiry}

"""

    for uid in expired_users:
        user_codes.pop(uid, None)

    bot.send_message(
        call.from_user.id,
        text,
        parse_mode="HTML"
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
# TEST BUTTON
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
# ERROR HANDLER
# ==================================================

@bot.message_handler(
    func=lambda message: True
)
def fallback(message):

    if not is_authorized(message.from_user.id):

        bot.reply_to(
            message,
            f"""
❌ <b>ACCESS DENIED</b>

استخدم:
<code>/activate CODE</code>

للحصول على كود تواصل مع:
{DEV}
""",
            parse_mode="HTML"
        )

        return

    bot.reply_to(
        message,
        """
❓ أمر غير معروف.

استخدم:
<code>/start</code>
""",
        parse_mode="HTML"
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
    print("=" * 50)

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )
