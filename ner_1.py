
# -*- coding: utf-8 -*-
import requests
import time
import json
import threading
import sys
from datetime import datetime, timedelta

TOKEN = "your token"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}/"

ADMINS = [your id namber]
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "gold": {
        "enabled": True,
        "interval": 900,
        "delete_after": 10,
        "start_hour": 10,
        "end_hour": 23
    },
    "destinations": {},
    "scheduled_messages": [],
    "polls": {}
}

settings_lock = threading.RLock()
settings = None
update_offset = 0
admin_state = {}

def load_settings():
    global settings
    settings = json.loads(json.dumps(DEFAULT_SETTINGS))
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                if "gold" in loaded and isinstance(loaded["gold"], dict):
                    for k, v in loaded["gold"].items():
                        settings["gold"][k] = v
                if "destinations" in loaded and isinstance(loaded["destinations"], dict):
                    settings["destinations"] = loaded["destinations"]
                if "scheduled_messages" in loaded and isinstance(loaded["scheduled_messages"], list):
                    settings["scheduled_messages"] = loaded["scheduled_messages"]
                if "polls" in loaded and isinstance(loaded["polls"], dict):
                    settings["polls"] = loaded["polls"]
    except Exception as e:
        print(f"[Load] خطا: {e}")
    save_settings()
    print("[Load] ✅ settings بارگذاری شد")

def save_settings():
    with settings_lock:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

def api_post(method, payload):
    try:
        response = requests.post(BASE_URL + method, json=payload, timeout=15)
        if response.status_code != 200:
            return None
        data = response.json()
        return data if data.get("ok") else None
    except:
        return None

def send_message(chat_id, text, keyboard=None):
    result = api_post("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "reply_markup": keyboard})
    if result:
        try:
            return result["result"]["message_id"]
        except:
            pass
    return None

def delete_message(chat_id, message_id):
    if not message_id:
        return False
    result = api_post("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    return result is not None

def edit_message(chat_id, message_id, text):
    result = api_post("editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"})
    return result is not None

def get_updates(offset):
    try:
        response = requests.get(BASE_URL + "getUpdates", params={"timeout": 20, "offset": offset}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])
        return []
    except:
        return []

def answer_callback(callback_id, text=""):
    api_post("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})

def main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📈 نرخ طلا", "callback_data": "gold"}],
            [{"text": "📢 مقصدها", "callback_data": "destinations"}],
            [{"text": "📅 پیام زمان‌بندی", "callback_data": "scheduled"}],
            [{"text": "🗳 نظرسنجی", "callback_data": "poll"}],
            [{"text": "📊 وضعیت", "callback_data": "status"}]
        ]
    }

def back_button():
    return {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "back"}]]}

def send_panel(chat_id):
    with settings_lock:
        gold_enabled = settings["gold"]["enabled"]
        status = "🟢 روشن" if gold_enabled else "🔴 خاموش"
        destination_count = len(settings["destinations"])
        scheduled_count = len(settings["scheduled_messages"])
    text = f"⚙️ *پنل مدیریت ربات*\n\n📈 نرخ طلا: {status}\n📢 مقصدها: `{destination_count}`\n📅 پیام‌های زمان‌بندی: `{scheduled_count}`\n\nیک گزینه را انتخاب کن:"
    send_message(chat_id, text, keyboard=main_keyboard())

def gold_keyboard():
    with settings_lock:
        enabled = settings["gold"]["enabled"]
        interval = settings["gold"]["interval"] // 60
        start = settings["gold"]["start_hour"]
        end = settings["gold"]["end_hour"]
    switch_text = "🔴 خاموش کردن" if enabled else "🟢 روشن کردن"
    return {
        "inline_keyboard": [
            [{"text": switch_text, "callback_data": "gold_toggle"}],
            [{"text": f"⏱ زمان ارسال: {interval} دقیقه", "callback_data": "gold_interval"}],
            [{"text": f"🕐 ساعت فعال: {start:02d}:00 تا {end:02d}:00", "callback_data": "gold_hours"}],
            [{"text": "🧹 حذف بعد از", "callback_data": "gold_delete"}],
            [{"text": "🔙 بازگشت", "callback_data": "back"}]
        ]
    }

def show_gold_panel(chat_id):
    with settings_lock:
        enabled = settings["gold"]["enabled"]
        interval = settings["gold"]["interval"] // 60
        start = settings["gold"]["start_hour"]
        end = settings["gold"]["end_hour"]
        delete_after = settings["gold"]["delete_after"]
    status = "🟢 روشن" if enabled else "🔴 خاموش"
    text = f"📈 *تنظیمات نرخ طلا (پیش‌فرض)*\n\nوضعیت: {status}\n⏱ هر `{interval}` دقیقه\n🕐 فعال از `{start:02d}:00` تا `{end:02d}:00`\n🧹 حذف پیام بعد از `{delete_after}` ثانیه"
    send_message(chat_id, text, keyboard=gold_keyboard())

def interval_keyboard():
    values = [5, 10, 15, 30, 60]
    rows = []
    for i in range(0, len(values), 2):
        row = []
        for value in values[i:i+2]:
            row.append({"text": f"{value} دقیقه", "callback_data": f"gold_interval:{value}"})
        rows.append(row)
    rows.append([{"text": "🔢 زمان دلخواه", "callback_data": "gold_custom_interval"}])
    rows.append([{"text": "🔙 بازگشت", "callback_data": "gold"}])
    return {"inline_keyboard": rows}

def destinations_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "➕ افزودن مقصد", "callback_data": "destination_add"}],
            [{"text": "📋 لیست مقصدها", "callback_data": "destination_list"}],
            [{"text": "🔙 بازگشت", "callback_data": "back"}]
        ]
    }

def destination_full_keyboard(dest_id):
    return {
        "inline_keyboard": [
            [{"text": "🔄 روشن/خاموش", "callback_data": f"dest_toggle:{dest_id}"}],
            [{"text": "⏱ تنظیم فاصله ارسال", "callback_data": f"dest_interval:{dest_id}"}],
            [{"text": "🕐 تنظیم ساعت فعال", "callback_data": f"dest_hours:{dest_id}"}],
            [{"text": "🧹 تنظیم حذف بعد از", "callback_data": f"dest_delete_after:{dest_id}"}],
            [{"text": "✏️ قوانین ویرایش اختصاصی", "callback_data": f"dest_rules:{dest_id}"}],
            [{"text": "✏️ تغییر نام", "callback_data": f"dest_rename:{dest_id}"}],
            [{"text": "📊 آمار ارسال", "callback_data": f"dest_stats:{dest_id}"}],
            [{"text": "🗑 حذف مقصد", "callback_data": f"dest_delete:{dest_id}"}],
            [{"text": "🔙 بازگشت به لیست", "callback_data": "destination_list"}]
        ]
    }

def show_destinations(chat_id):
    with settings_lock:
        destinations = dict(settings["destinations"])
    
    if not destinations:
        send_message(chat_id, "📢 *مقصدی ثبت نشده.*\n\nربات را در کانال یا گروه موردنظر با دسترسی لازم قرار بده.", keyboard=destinations_keyboard())
        return
    
    text = "📢 *لیست مقصدها*\n\n"
    rows = []
    for dest_id, item in destinations.items():
        name = item.get("name", str(dest_id))
        enabled = item.get("enabled", True)
        interval = item.get("interval", settings["gold"]["interval"]) // 60
        rules_count = len(item.get("rules", []))
        status = "🟢" if enabled else "🔴"
        text += f"{status} `{dest_id}`\n"
        text += f"📌 {name}\n"
        text += f"⏱ هر {interval} دقیقه\n"
        text += f"✏️ {rules_count} قانون\n\n"
        rows.append([{"text": f"⚙️ {name[:20]}", "callback_data": f"dest_detail:{dest_id}"}])
    
    rows.append([{"text": "🔙 بازگشت", "callback_data": "destinations"}])
    send_message(chat_id, text, keyboard={"inline_keyboard": rows})

def show_destination_detail(chat_id, dest_id):
    with settings_lock:
        item = settings["destinations"].get(str(dest_id))
    
    if not item:
        send_message(chat_id, "❌ مقصد پیدا نشد.", keyboard=destinations_keyboard())
        return
    
    name = item.get("name", str(dest_id))
    enabled = item.get("enabled", True)
    interval = item.get("interval", settings["gold"]["interval"]) // 60
    start = item.get("start_hour", settings["gold"]["start_hour"])
    end = item.get("end_hour", settings["gold"]["end_hour"])
    delete_after = item.get("delete_after", settings["gold"]["delete_after"])
    rules_count = len(item.get("rules", []))
    status = "🟢 روشن" if enabled else "🔴 خاموش"
    
    text = f"📢 *تنظیمات مقصد*\n\n"
    text += f"🆔 `{dest_id}`\n"
    text += f"📌 نام: {name}\n"
    text += f"⏱ فاصله: {interval} دقیقه\n"
    text += f"🕐 ساعت فعال: {start:02d}:00 تا {end:02d}:00\n"
    text += f"🧹 حذف بعد از: {delete_after} ثانیه\n"
    text += f"✏️ قوانین: {rules_count} قانون\n"
    text += f"📊 وضعیت: {status}"
    
    send_message(chat_id, text, keyboard=destination_full_keyboard(dest_id))

def destination_add(chat_id):
    admin_state[chat_id] = {"action": "destination_add"}
    send_message(chat_id, "➕ *افزودن مقصد*\n\nشناسه کانال یا گروه را در پیام بعدی بفرست.\n\nمثال:\n`5816739801`\n\nربات باید در آن مقصد حضور داشته باشد.", keyboard=back_button())

def destination_rename(chat_id, dest_id):
    admin_state[chat_id] = {"action": "dest_rename", "dest_id": dest_id}
    send_message(chat_id, f"✏️ نام جدید برای مقصد `{dest_id}` را بفرست:", keyboard=back_button())

def destination_interval(chat_id, dest_id):
    admin_state[chat_id] = {"action": "dest_interval", "dest_id": dest_id}
    send_message(chat_id, f"⏱ فاصله ارسال جدید (بر حسب دقیقه) برای مقصد `{dest_id}` را بفرست:", keyboard=back_button())

def destination_hours(chat_id, dest_id):
    admin_state[chat_id] = {"action": "dest_hours", "dest_id": dest_id}
    send_message(chat_id, f"🕐 ساعت شروع و پایان را بفرست.\n\nمثال:\n`10 23`\n\nیعنی از ساعت ۱۰ تا ۲۳ فعال باشد.", keyboard=back_button())

def destination_delete_after(chat_id, dest_id):
    admin_state[chat_id] = {"action": "dest_delete_after", "dest_id": dest_id}
    send_message(chat_id, f"🧹 زمان حذف پیام (بر حسب ثانیه) برای مقصد `{dest_id}` را بفرست:\n\nمثال:\n`10`\n\n`0` یعنی حذف نشود.", keyboard=back_button())

def destination_stats(chat_id, dest_id):
    with settings_lock:
        item = settings["destinations"].get(str(dest_id), {})
        sent_count = item.get("sent_count", 0)
        last_sent = item.get("last_sent", 0)
        last_sent_time = datetime.fromtimestamp(last_sent).strftime("%Y-%m-%d %H:%M:%S") if last_sent else "هنوز ارسالی نداشته"
    
    text = f"📊 *آمار ارسال به مقصد*\n\n"
    text += f"🆔 `{dest_id}`\n"
    text += f"📨 تعداد کل ارسال‌ها: {sent_count}\n"
    text += f"⏱ آخرین ارسال: {last_sent_time}"
    send_message(chat_id, text, keyboard=destination_full_keyboard(dest_id))

def destination_toggle(chat_id, dest_id):
    with settings_lock:
        if dest_id in settings["destinations"]:
            current = settings["destinations"][dest_id].get("enabled", True)
            settings["destinations"][dest_id]["enabled"] = not current
    save_settings()
    show_destination_detail(chat_id, dest_id)

def destination_delete(chat_id, dest_id):
    with settings_lock:
        settings["destinations"].pop(str(dest_id), None)
    save_settings()
    send_message(chat_id, f"🗑 مقصد `{dest_id}` حذف شد.", keyboard=destinations_keyboard())

def destination_rules_keyboard(dest_id):
    return {
        "inline_keyboard": [
            [{"text": "➕ افزودن قانون", "callback_data": f"dest_rule_add:{dest_id}"}],
            [{"text": "📋 لیست قوانین", "callback_data": f"dest_rule_list:{dest_id}"}],
            [{"text": "🗑 حذف قانون", "callback_data": f"dest_rule_delete:{dest_id}"}],
            [{"text": "🔙 بازگشت به تنظیمات", "callback_data": f"dest_detail:{dest_id}"}]
        ]
    }

def show_destination_rules(chat_id, dest_id):
    with settings_lock:
        item = settings["destinations"].get(str(dest_id), {})
        rules = item.get("rules", [])
    
    text = f"✏️ *قوانین ویرایش مقصد `{dest_id}`*\n\n"
    text += f"📌 تعداد قوانین: {len(rules)}\n\n"
    text += "هر قانون به این شکل است:\n"
    text += "`عبارت اصلی | عبارت جایگزین`"
    
    send_message(chat_id, text, keyboard=destination_rules_keyboard(dest_id))

def show_destination_rule_list(chat_id, dest_id):
    with settings_lock:
        item = settings["destinations"].get(str(dest_id), {})
        rules = item.get("rules", [])
    
    if not rules:
        send_message(chat_id, f"📭 هیچ قانونی برای مقصد `{dest_id}` وجود ندارد.", keyboard=destination_rules_keyboard(dest_id))
        return
    
    text = f"📋 *قوانین مقصد `{dest_id}`*\n\n"
    for i, rule in enumerate(rules, 1):
        text += f"*{i}.*\n"
        text += f"🔎 `{rule['find']}`\n"
        text += f"➡️ `{rule['replace']}`\n\n"
    
    send_message(chat_id, text, keyboard=destination_rules_keyboard(dest_id))

def destination_rule_add(chat_id, dest_id):
    admin_state[chat_id] = {"action": "dest_rule_add", "dest_id": dest_id}
    send_message(chat_id, f"✏️ قانون جدید برای مقصد `{dest_id}` را بفرست.\n\nفرمت:\n`عبارت اصلی | جایگزین`\n\nمثال:\n`قیمت طلا | 💰 قیمت طلا`", keyboard=back_button())

def destination_rule_delete(chat_id, dest_id):
    with settings_lock:
        item = settings["destinations"].get(str(dest_id), {})
        rules = item.get("rules", [])
    
    if not rules:
        send_message(chat_id, f"📭 هیچ قانونی برای مقصد `{dest_id}` وجود ندارد.", keyboard=destination_rules_keyboard(dest_id))
        return
    
    rows = []
    for i, rule in enumerate(rules):
        rows.append([{"text": f"🗑 {i+1}. {rule['find'][:18]}", "callback_data": f"dest_rule_remove:{dest_id}:{i}"}])
    rows.append([{"text": "🔙 بازگشت", "callback_data": f"dest_rules:{dest_id}"}])
    send_message(chat_id, f"🗑 قانون موردنظر را برای مقصد `{dest_id}` انتخاب کن:", keyboard={"inline_keyboard": rows})

def scheduled_panel():
    return {
        "inline_keyboard": [
            [{"text": "➕ پیام جدید", "callback_data": "schedule_add"}],
            [{"text": "📋 پیام‌های موجود", "callback_data": "schedule_list"}],
            [{"text": "🗑 حذف پیام", "callback_data": "schedule_delete"}],
            [{"text": "🔙 بازگشت", "callback_data": "back"}]
        ]
    }

def show_scheduled(chat_id):
    with settings_lock:
        items = list(settings["scheduled_messages"])
    if not items:
        send_message(chat_id, "📭 پیام زمان‌بندی‌شده‌ای وجود ندارد.", keyboard=scheduled_panel())
        return
    text = "📅 *پیام‌های زمان‌بندی‌شده:*\n\n"
    for i, item in enumerate(items, 1):
        text += f"*{i}.* {item.get('time', '--:--')} — {item.get('text', '')[:60]}\n"
    send_message(chat_id, text, keyboard=scheduled_panel())

def schedule_delete_keyboard():
    with settings_lock:
        items = list(settings["scheduled_messages"])
    rows = []
    for i, item in enumerate(items):
        rows.append([{"text": f"🗑 {i+1} - {item.get('time', '--:--')}", "callback_data": f"schedule_remove:{i}"}])
    rows.append([{"text": "🔙 بازگشت", "callback_data": "scheduled"}])
    return {"inline_keyboard": rows}

def schedule_add(chat_id):
    admin_state[chat_id] = {"action": "schedule_time"}
    send_message(chat_id, "📅 *پیام زمان‌بندی‌شده*\n\nاول ساعت ارسال را بفرست.\n\nمثال:\n`00:00`", keyboard=back_button())

def poll_start(chat_id):
    admin_state[chat_id] = {"action": "poll_question"}
    send_message(chat_id, "🗳 *ساخت نظرسنجی*\n\nاول سؤال نظرسنجی را بفرست.\n\nمثال:\n`به نظر شما بازار فردا چگونه است؟`", keyboard=back_button())

def poll_keyboard(poll_id, options, votes):
    total = sum(votes)
    rows = []
    for i, option in enumerate(options):
        count = votes[i]
        percent = (count * 100 / total) if total else 0
        filled = int(percent / 10)
        filled = max(0, min(filled, 10))
        bar = "█" * filled + "░" * (10 - filled)
        rows.append([{"text": f"{option} {bar} {percent:.0f}%", "callback_data": f"poll_vote:{poll_id}:{i}"}])
    return {"inline_keyboard": rows}

def render_poll(poll_id):
    with settings_lock:
        poll = settings["polls"].get(str(poll_id))
    if not poll:
        return
    options = poll["options"]
    votes = poll["votes"]
    total = sum(votes)
    text = f"🗳 *{poll['question']}*\n\n"
    for i, option in enumerate(options):
        count = votes[i]
        percent = (count * 100 / total) if total else 0
        filled = int(percent / 10)
        filled = max(0, min(filled, 10))
        bar = "█" * filled + "░" * (10 - filled)
        text += f"{option}\n{bar} `{percent:.0f}%` ({count})\n\n"
    text += f"👥 مجموع رأی‌ها: `{total}`"
    return text

def create_poll(chat_id):
    state = admin_state.get(chat_id)
    if not state:
        return
    options = state.get("options", [])
    if len(options) < 2:
        send_message(chat_id, "❌ حداقل دو گزینه لازم است.")
        return
    poll_id = str(int(time.time() * 1000))
    poll = {"question": state["question"], "options": options, "votes": [0] * len(options), "voters": [], "chat_id": None, "message_id": None}
    with settings_lock:
        settings["polls"][poll_id] = poll
    save_settings()
    with settings_lock:
        destinations = list(settings["destinations"].items())
    if not destinations:
        send_message(chat_id, "❌ هیچ کانال/گروهی برای ارسال ثبت نشده است.")
        return
    sent_count = 0
    for dest_id, item in destinations:
        message_id = send_message(dest_id, render_poll(poll_id), keyboard=poll_keyboard(poll_id, options, poll["votes"]))
        if message_id:
            sent_count += 1
            with settings_lock:
                poll = settings["polls"][poll_id]
                if poll["chat_id"] is None:
                    poll["chat_id"] = dest_id
                    poll["message_id"] = message_id
    save_settings()
    admin_state.pop(chat_id, None)
    send_message(chat_id, f"✅ نظرسنجی ساخته شد.\n\n📤 تعداد مقصدهای موفق: `{sent_count}`", keyboard=main_keyboard())

def handle_poll_vote(callback, poll_id, option_index):
    user = callback.get("from", {})
    user_id = user.get("id")
    if not user_id:
        return
    with settings_lock:
        poll = settings["polls"].get(str(poll_id))
    if not poll:
        answer_callback(callback["id"], "این نظرسنجی دیگر وجود ندارد.")
        return
    voters = poll.get("voters", [])
    if user_id in voters:
        answer_callback(callback["id"], "شما قبلاً رأی داده‌اید.")
        return
    if option_index < 0 or option_index >= len(poll["options"]):
        return
    poll["votes"][option_index] += 1
    voters.append(user_id)
    poll["voters"] = voters
    save_settings()
    answer_callback(callback["id"], "✅ رأی شما ثبت شد.")
    chat_id = callback.get("message", {}).get("chat", {}).get("id")
    message_id = callback.get("message", {}).get("message_id")
    if chat_id and message_id:
        edit_message(chat_id, message_id, render_poll(poll_id))

def handle_callback(callback):
    callback_id = callback.get("id")
    data = callback.get("data", "")
    user = callback.get("from", {})
    user_id = user.get("id")
    
    if user_id not in ADMINS and not data.startswith("poll_vote:"):
        answer_callback(callback_id, "⛔ دسترسی ندارید.")
        return
    
    if data.startswith("poll_vote:"):
        parts = data.split(":")
        if len(parts) == 3:
            handle_poll_vote(callback, parts[1], int(parts[2]))
        return
    
    answer_callback(callback_id)
    chat_id = user_id
    
    if data == "back":
        send_panel(chat_id)
        return
    
    if data == "gold":
        show_gold_panel(chat_id)
        return
    if data == "gold_toggle":
        with settings_lock:
            settings["gold"]["enabled"] = not settings["gold"]["enabled"]
        save_settings()
        show_gold_panel(chat_id)
        return
    if data == "gold_interval":
        send_message(chat_id, "⏱ زمان ارسال را انتخاب کن:", keyboard=interval_keyboard())
        return
    if data.startswith("gold_interval:"):
        minutes = int(data.split(":")[1])
        with settings_lock:
            settings["gold"]["interval"] = minutes * 60
        save_settings()
        send_message(chat_id, f"✅ هر `{minutes}` دقیقه تنظیم شد.", keyboard=gold_keyboard())
        return
    if data == "gold_custom_interval":
        admin_state[chat_id] = {"action": "gold_custom_interval"}
        send_message(chat_id, "🔢 تعداد دقیقه را بفرست:", keyboard=back_button())
        return
    if data == "gold_hours":
        admin_state[chat_id] = {"action": "gold_hours"}
        send_message(chat_id, "🕐 ساعت شروع و پایان را بفرست.\n\nمثال:\n`10 23`", keyboard=back_button())
        return
    if data == "gold_delete":
        admin_state[chat_id] = {"action": "gold_delete_after"}
        send_message(chat_id, "🧹 زمان حذف پیام (بر حسب ثانیه) را بفرست:\n\nمثال:\n`10`\n\n`0` یعنی حذف نشود.", keyboard=back_button())
        return
    
    if data == "destinations":
        send_message(chat_id, "📢 *مدیریت مقصدها*", keyboard=destinations_keyboard())
        return
    if data == "destination_add":
        destination_add(chat_id)
        return
    if data == "destination_list":
        show_destinations(chat_id)
        return
    if data.startswith("dest_detail:"):
        dest_id = data.split(":", 1)[1]
        show_destination_detail(chat_id, dest_id)
        return
    if data.startswith("dest_rename:"):
        dest_id = data.split(":", 1)[1]
        destination_rename(chat_id, dest_id)
        return
    if data.startswith("dest_interval:"):
        dest_id = data.split(":", 1)[1]
        destination_interval(chat_id, dest_id)
        return
    if data.startswith("dest_hours:"):
        dest_id = data.split(":", 1)[1]
        destination_hours(chat_id, dest_id)
        return
    if data.startswith("dest_delete_after:"):
        dest_id = data.split(":", 1)[1]
        destination_delete_after(chat_id, dest_id)
        return
    if data.startswith("dest_stats:"):
        dest_id = data.split(":", 1)[1]
        destination_stats(chat_id, dest_id)
        return
    if data.startswith("dest_toggle:"):
        dest_id = data.split(":", 1)[1]
        destination_toggle(chat_id, dest_id)
        return
    if data.startswith("dest_delete:"):
        dest_id = data.split(":", 1)[1]
        destination_delete(chat_id, dest_id)
        return
    
    if data.startswith("dest_rules:"):
        dest_id = data.split(":", 1)[1]
        show_destination_rules(chat_id, dest_id)
        return
    if data.startswith("dest_rule_list:"):
        dest_id = data.split(":", 1)[1]
        show_destination_rule_list(chat_id, dest_id)
        return
    if data.startswith("dest_rule_add:"):
        dest_id = data.split(":", 1)[1]
        destination_rule_add(chat_id, dest_id)
        return
    if data.startswith("dest_rule_delete:"):
        dest_id = data.split(":", 1)[1]
        destination_rule_delete(chat_id, dest_id)
        return
    if data.startswith("dest_rule_remove:"):
        parts = data.split(":")
        dest_id = parts[1]
        index = int(parts[2])
        with settings_lock:
            if dest_id in settings["destinations"]:
                rules = settings["destinations"][dest_id].get("rules", [])
                if index < len(rules):
                    removed = rules.pop(index)
                    settings["destinations"][dest_id]["rules"] = rules
        save_settings()
        send_message(chat_id, f"✅ قانون حذف شد:\n`{removed['find']}`", keyboard=destination_rules_keyboard(dest_id))
        return
    
    if data == "scheduled":
        send_message(chat_id, "📅 *پیام‌های زمان‌بندی‌شده*", keyboard=scheduled_panel())
        return
    if data == "schedule_add":
        schedule_add(chat_id)
        return
    if data == "schedule_list":
        show_scheduled(chat_id)
        return
    if data == "schedule_delete":
        send_message(chat_id, "پیام موردنظر را انتخاب کن:", keyboard=schedule_delete_keyboard())
        return
    if data.startswith("schedule_remove:"):
        index = int(data.split(":")[1])
        with settings_lock:
            if index < len(settings["scheduled_messages"]):
                settings["scheduled_messages"].pop(index)
        save_settings()
        send_message(chat_id, "🗑 پیام زمان‌بندی حذف شد.", keyboard=scheduled_panel())
        return
    
    if data == "poll":
        poll_start(chat_id)
        return
    if data == "poll_create":
        create_poll(chat_id)
        return
    
    if data == "status":
        show_status(chat_id)
        return
    
    if data.startswith("schedule_dest:"):
        dest_id = data.split(":", 1)[1]
        state = admin_state.get(chat_id)
        if state:
            item = {"time": state["time"], "text": state["text"], "destinations": [dest_id]}
            with settings_lock:
                settings["scheduled_messages"].append(item)
            save_settings()
            admin_state.pop(chat_id, None)
            answer_callback(callback["id"], "پیام زمان‌بندی شد.")
            send_message(chat_id, "✅ پیام زمان‌بندی شد.", keyboard=scheduled_panel())
        return
    if data == "schedule_all":
        state = admin_state.get(chat_id)
        if state:
            with settings_lock:
                destinations = list(settings["destinations"].keys())
                item = {"time": state["time"], "text": state["text"], "destinations": destinations}
                settings["scheduled_messages"].append(item)
            save_settings()
            admin_state.pop(chat_id, None)
            answer_callback(callback["id"], "پیام زمان‌بندی شد.")
            send_message(chat_id, "✅ پیام برای همه مقصدها زمان‌بندی شد.", keyboard=scheduled_panel())
        return

def handle_admin_text(message):
    chat_id = message.get("chat", {}).get("id")
    if chat_id not in ADMINS:
        return
    text = message.get("text", "").strip()
    if not text:
        return
    if text == "/start":
        send_panel(chat_id)
        return
    state = admin_state.get(chat_id)
    if not state:
        send_panel(chat_id)
        return
    action = state.get("action")
    
    if action == "gold_custom_interval":
        try:
            minutes = int(text)
            if minutes <= 0:
                raise ValueError
            with settings_lock:
                settings["gold"]["interval"] = minutes * 60
            save_settings()
            admin_state.pop(chat_id, None)
            send_message(chat_id, f"✅ هر `{minutes}` دقیقه تنظیم شد.", keyboard=gold_keyboard())
        except:
            send_message(chat_id, "❌ یک عدد مثبت بر حسب دقیقه بفرست.", keyboard=back_button())
        return
    if action == "gold_hours":
        try:
            parts = text.split()
            if len(parts) != 2:
                raise ValueError
            start = int(parts[0])
            end = int(parts[1])
            if not 0 <= start <= 23 or not 0 <= end <= 23:
                raise ValueError
            with settings_lock:
                settings["gold"]["start_hour"] = start
                settings["gold"]["end_hour"] = end
            save_settings()
            admin_state.pop(chat_id, None)
            send_message(chat_id, f"✅ ساعت فعال بودن نرخ طلا:\n`{start:02d}:00` تا `{end:02d}:00`", keyboard=gold_keyboard())
        except:
            send_message(chat_id, "❌ فرمت صحیح:\n`10 23`", keyboard=back_button())
        return
    if action == "gold_delete_after":
        try:
            seconds = int(text)
            if seconds < 0:
                raise ValueError
            with settings_lock:
                settings["gold"]["delete_after"] = seconds
            save_settings()
            admin_state.pop(chat_id, None)
            send_message(chat_id, f"✅ حذف بعد از `{seconds}` ثانیه تنظیم شد.", keyboard=gold_keyboard())
        except:
            send_message(chat_id, "❌ یک عدد مثبت یا صفر بفرست.", keyboard=back_button())
        return
    
    if action == "destination_add":
        try:
            dest_id = int(text)
            with settings_lock:
                if str(dest_id) not in settings["destinations"]:
                    settings["destinations"][str(dest_id)] = {
                        "name": str(dest_id),
                        "enabled": True,
                        "interval": settings["gold"]["interval"],
                        "start_hour": settings["gold"]["start_hour"],
                        "end_hour": settings["gold"]["end_hour"],
                        "delete_after": settings["gold"]["delete_after"],
                        "rules": [],
                        "sent_count": 0,
                        "last_sent": 0
                    }
            save_settings()
            admin_state.pop(chat_id, None)
            send_message(chat_id, f"✅ مقصد `{dest_id}` اضافه شد.", keyboard=destinations_keyboard())
        except:
            send_message(chat_id, "❌ شناسه عددی صحیح وارد کن.", keyboard=back_button())
        return
    if action == "dest_rename":
        dest_id = state.get("dest_id")
        if dest_id:
            with settings_lock:
                if dest_id in settings["destinations"]:
                    settings["destinations"][dest_id]["name"] = text
            save_settings()
            admin_state.pop(chat_id, None)
            show_destination_detail(chat_id, dest_id)
        return
    if action == "dest_interval":
        dest_id = state.get("dest_id")
        if dest_id:
            try:
                minutes = int(text)
                if minutes <= 0:
                    raise ValueError
                with settings_lock:
                    if dest_id in settings["destinations"]:
                        settings["destinations"][dest_id]["interval"] = minutes * 60
                save_settings()
                admin_state.pop(chat_id, None)
                send_message(chat_id, f"✅ فاصله ارسال به `{minutes}` دقیقه تنظیم شد.", keyboard=destination_full_keyboard(dest_id))
            except:
                send_message(chat_id, "❌ یک عدد مثبت بر حسب دقیقه بفرست.", keyboard=back_button())
        return
    if action == "dest_hours":
        dest_id = state.get("dest_id")
        if dest_id:
            try:
                parts = text.split()
                if len(parts) != 2:
                    raise ValueError
                start = int(parts[0])
                end = int(parts[1])
                if not 0 <= start <= 23 or not 0 <= end <= 23:
                    raise ValueError
                with settings_lock:
                    if dest_id in settings["destinations"]:
                        settings["destinations"][dest_id]["start_hour"] = start
                        settings["destinations"][dest_id]["end_hour"] = end
                save_settings()
                admin_state.pop(chat_id, None)
                send_message(chat_id, f"✅ ساعت فعال برای مقصد تنظیم شد:\n`{start:02d}:00` تا `{end:02d}:00`", keyboard=destination_full_keyboard(dest_id))
            except:
                send_message(chat_id, "❌ فرمت صحیح:\n`10 23`", keyboard=back_button())
        return
    if action == "dest_delete_after":
        dest_id = state.get("dest_id")
        if dest_id:
            try:
                seconds = int(text)
                if seconds < 0:
                    raise ValueError
                with settings_lock:
                    if dest_id in settings["destinations"]:
                        settings["destinations"][dest_id]["delete_after"] = seconds
                save_settings()
                admin_state.pop(chat_id, None)
                send_message(chat_id, f"✅ حذف بعد از `{seconds}` ثانیه تنظیم شد.", keyboard=destination_full_keyboard(dest_id))
            except:
                send_message(chat_id, "❌ یک عدد مثبت یا صفر بفرست.", keyboard=back_button())
        return
    
    if action == "dest_rule_add":
        dest_id = state.get("dest_id")
        if dest_id:
            if "|" not in text:
                send_message(chat_id, "❌ فرمت صحیح:\n`عبارت اصلی | جایگزین`", keyboard=back_button())
                return
            find_text, replace_text = text.split("|", 1)
            find_text = find_text.strip()
            replace_text = replace_text.strip()
            if not find_text:
                send_message(chat_id, "❌ عبارت اصلی خالی است.", keyboard=back_button())
                return
            with settings_lock:
                if dest_id in settings["destinations"]:
                    rules = settings["destinations"][dest_id].get("rules", [])
                    rules.append({"find": find_text, "replace": replace_text})
                    settings["destinations"][dest_id]["rules"] = rules
            save_settings()
            admin_state.pop(chat_id, None)
            send_message(chat_id, f"✅ قانون برای مقصد `{dest_id}` اضافه شد.", keyboard=destination_rules_keyboard(dest_id))
        return
    
    if action == "schedule_time":
        try:
            datetime.strptime(text, "%H:%M")
        except:
            send_message(chat_id, "❌ ساعت باید مثل این باشد:\n`00:00`", keyboard=back_button())
            return
        admin_state[chat_id] = {"action": "schedule_text", "time": text}
        send_message(chat_id, "📝 حالا متن پیام را بفرست.", keyboard=back_button())
        return
    if action == "schedule_text":
        schedule_time = state["time"]
        admin_state[chat_id] = {"action": "schedule_destination", "time": schedule_time, "text": text}
        with settings_lock:
            destinations = list(settings["destinations"].items())
        if not destinations:
            send_message(chat_id, "❌ اول حداقل یک مقصد اضافه کن.", keyboard=destinations_keyboard())
            admin_state.pop(chat_id, None)
            return
        rows = []
        for dest_id, item in destinations:
            name = item.get("name", str(dest_id))
            rows.append([{"text": f"📢 {name[:25]}", "callback_data": f"schedule_dest:{dest_id}"}])
        rows.append([{"text": "📢 همه مقصدها", "callback_data": "schedule_all"}])
        rows.append([{"text": "🔙 لغو", "callback_data": "scheduled"}])
        send_message(chat_id, "📢 پیام در کجا ارسال شود؟", keyboard={"inline_keyboard": rows})
        return
    
    if action == "poll_question":
        admin_state[chat_id] = {"action": "poll_options", "question": text}
        send_message(chat_id, "🔘 گزینه‌ها را در یک پیام بفرست.\n\nهر گزینه در یک خط.\n\nمثال:\n`صعودی`\n`نزولی`\n`بدون تغییر`", keyboard=back_button())
        return
    if action == "poll_options":
        options = [x.strip() for x in text.splitlines() if x.strip()]
        if len(options) < 2:
            send_message(chat_id, "❌ حداقل دو گزینه لازم است.", keyboard=back_button())
            return
        if len(options) > 8:
            send_message(chat_id, "❌ حداکثر ۸ گزینه.", keyboard=back_button())
            return
        admin_state[chat_id] = {"action": "poll_confirm", "question": state["question"], "options": options}
        rows = [[{"text": "✅ انتشار نظرسنجی", "callback_data": "poll_create"}], [{"text": "❌ لغو", "callback_data": "back"}]]
        text_preview = f"🗳 *پیش‌نمایش نظرسنجی*\n\n*{state['question']}*\n\n"
        for i, option in enumerate(options, 1):
            text_preview += f"{i}. {option}\n"
        send_message(chat_id, text_preview, keyboard={"inline_keyboard": rows})
        return

def process_channel_message(message):
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return
    text = message.get("text")
    message_id = message.get("message_id")
    if not text or not message_id:
        return
    
    with settings_lock:
        dest = settings["destinations"].get(str(chat_id), {})
        rules = dest.get("rules", [])
    
    new_text = text
    changed = False
    for rule in rules:
        find_text = rule.get("find", "")
        replace_text = rule.get("replace", "")
        if find_text and find_text in new_text:
            new_text = new_text.replace(find_text, replace_text)
            changed = True
    
    if changed:
        edit_message(chat_id, message_id, new_text)

def is_gold_active_for_dest(dest_settings):
    now = datetime.now()
    hour = now.hour
    start = dest_settings.get("start_hour", settings["gold"]["start_hour"])
    end = dest_settings.get("end_hour", settings["gold"]["end_hour"])
    if start == end:
        return True
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end

def gold_worker():
    print("[Gold] Worker started.")
    while True:
        try:
            with settings_lock:
                main_enabled = settings["gold"]["enabled"]
                destinations = dict(settings["destinations"])
            
            now = time.monotonic()
            
            for chat_id, item in destinations.items():
                if not main_enabled:
                    continue
                if not item.get("enabled", True):
                    continue
                if not is_gold_active_for_dest(item):
                    continue
                
                interval = item.get("interval", settings["gold"]["interval"])
                last_sent = item.get("last_sent", 0)
                
                if now - last_sent < interval:
                    continue
                
                message_id = send_message(chat_id, "نرخ طلا")
                if message_id:
                    print(f"[Gold] ✅ {chat_id} message={message_id}")
                    with settings_lock:
                        settings["destinations"][chat_id]["last_sent"] = now
                        settings["destinations"][chat_id]["sent_count"] = settings["destinations"][chat_id].get("sent_count", 0) + 1
                        delete_after = item.get("delete_after", settings["gold"]["delete_after"])
                    save_settings()
                    if delete_after > 0:
                        threading.Thread(target=lambda: (time.sleep(delete_after), delete_message(chat_id, message_id)), daemon=True).start()
            
            time.sleep(5)
            
        except Exception as e:
            print(f"[Gold] ❌ {e}")
            time.sleep(5)

def scheduled_worker():
    print("[Schedule] Worker started.")
    sent_today = {}
    while True:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            date_key = now.strftime("%Y-%m-%d")
            with settings_lock:
                items = list(settings["scheduled_messages"])
            for index, item in enumerate(items):
                if item.get("time") != current_time:
                    continue
                unique_key = f"{date_key}-{index}-{current_time}"
                if sent_today.get(unique_key):
                    continue
                sent_today[unique_key] = True
                text = item.get("text", "")
                destinations = item.get("destinations", [])
                for chat_id in destinations:
                    send_message(chat_id, text)
                    print(f"[Schedule] ✅ {chat_id} {current_time}")
            if len(sent_today) > 1000:
                sent_today = {k: v for k, v in sent_today.items() if k.startswith(date_key)}
            time.sleep(1)
        except Exception as e:
            print(f"[Schedule] ❌ {e}")
            time.sleep(5)

def update_worker():
    global update_offset
    print("[Updates] Worker started.")
    while True:
        try:
            updates = get_updates(update_offset)
            for update in updates:
                update_offset = update["update_id"] + 1
                callback = update.get("callback_query")
                if callback:
                    handle_callback(callback)
                    continue
                message = update.get("message")
                if not message:
                    continue
                chat_id = message.get("chat", {}).get("id")
                if chat_id in ADMINS:
                    handle_admin_text(message)
                else:
                    process_channel_message(message)
        except Exception as e:
            print(f"[Updates] ❌ {e}")
            time.sleep(5)

def show_status(chat_id):
    with settings_lock:
        destinations = len(settings["destinations"])
        scheduled = len(settings["scheduled_messages"])
        gold = settings["gold"]["enabled"]
        interval = settings["gold"]["interval"] // 60
    gold_status = "🟢 روشن" if gold else "🔴 خاموش"
    text = f"📊 *وضعیت ربات*\n\n📈 نرخ طلا: {gold_status}\n⏱ فاصله: `{interval}` دقیقه\n📢 مقصدها: `{destinations}`\n📅 زمان‌بندی‌ها: `{scheduled}`\n🟢 Bot: فعال"
    send_message(chat_id, text, keyboard=back_button())

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 BALE GOLD MANAGEMENT BOT")
    print("=" * 60)
    load_settings()
    print(f"👤 Admins: {ADMINS}")
    print("📁 Settings loaded.")
    threading.Thread(target=update_worker, daemon=True).start()
    threading.Thread(target=gold_worker, daemon=True).start()
    threading.Thread(target=scheduled_worker, daemon=True).start()
    print("🟢 All workers started.")
    print("💬 Send /start to the bot PV.")
    print("🛑 Ctrl+C to stop.")
    print("=" * 60)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped.")
        sys.exit(0)
