from balethon import Client as Bc
from balethon.conditions import private
from balethon.objects import Message, ReplyKeyboard
from aiobale import Client, Dispatcher
from aiobale.types import Message as rt
from aiobale.enums import AuthErrors, ChatType
from aiobale.methods import MessageSetReaction, UpvotePost
from aiobale.types import Peer
from pathlib import Path
from datetime import datetime, timedelta
import os
import json
import asyncio
import re
import shutil
import gc
import zipfile
import time
import random

bot = Bc("Token")

admins = []

reactions = [
    "❤️", "👍", "👎", "😂", "😭", "👌", "🙏",
    "🇮🇷", "🇵🇸", "🌷", "😍", "😎", "😱", "😡", "😐",
    "🤯","🥳","👏", "🤲", "🔥", "✅", "😔", "🖤"
]

clients = {}
dispatchers = {}

clients1 = {}
dispatchers1 = {}

user_data = {}

def convert_to_english_numbers(text):
    persian_to_english = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    arabic_to_english = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    
    result = ""
    for char in text:
        if char in persian_to_english:
            result += persian_to_english[char]
        elif char in arabic_to_english:
            result += arabic_to_english[char]
        else:
            result += char
    return result

def get_valid_phone_number(text):
    text = convert_to_english_numbers(text)
    phone = re.sub(r'\D', '', text)
    
    if len(phone) == 10:
        if not phone.startswith('9'):
            phone = '9' + phone
    elif len(phone) == 11:
        if phone.startswith('09'):
            phone = phone[1:]
    
    return phone if phone.isdigit() else None

def get_delay():
    with open("data/panel.json", "r") as file:
        data = json.load(file)
        return data['delay']

def get_data():
    with open("data/panel.json") as file:
        return json.load(file)

def add_group(group: str):
    data = get_data()
    data['group'].append(group)
    with open("data/panel.json","w") as file:
        json.dump(data, file, indent=4)

def remove_group(group: str):
    data = get_data()
    data['group'].remove(group)
    with open("data/panel.json","w") as file:
        json.dump(data, file, indent=4)

def get_group():
    data = get_data()
    return data['group']

def iv(val):
    return getattr(val, "value", val)

async def get_coder(session_file: str, admin: int):
    dp = Dispatcher()

    try:
        client = Client(dp, session_file=f"sessions/{session_file}")
    except:
        await bot.send_message(admin, "متاسفانه ارتباط با سشن ممکن نیست.")
        return
    @dp.message()
    async def lablab(msg):
        if msg.text:
            if "Code" in msg.text:
                await bot.send_message(admin, msg.text)
    
    task = asyncio.create_task(client.start())
    await asyncio.sleep(60)
    task.cancel()
    await bot.send_message(admin, "به پایان رسید.")

@bot.on_message(private)
async def handler(message: Message):
    user_id = message.author.id
    if user_id not in admins:
        return
    
    text = message.text if message.text else "none"

    if text == "/cancel":
        if user_id in user_data:
            del user_data[user_id]
            await message.reply("❌ عملیات کنسل شد")

    elif text == "/start":
        keyboard = [
            ["📊 اطلاعات کامل"],
            ["📥 جوین دسته‌جمعی", "📤 لیو دسته‌جمعی"],
            ["🔍 بررسی سشن‌ها", "✨ ساخت سشن"],
            ["💻 مدیریت سشن", "🎩 برترین ها"],
            ["⨻ گزارش"],
            ["⚙️ تنظیمات", "📦 دریافت بکاپ"],
            ["📚 راهنما"]
        ]
        welcome_text = """✨ *به پنل مدیریت ربات خوش آمدید*

🔹 *دستورات قابل استفاده:*
• اطلاعات کامل - نمایش آمار اکانت‌ها
• جوین دسته‌جمعی - عضویت در گروه با چند اکانت
• لیو دسته‌جمعی - خروج از گروه با چند اکانت
• بررسی سشن‌ها - بررسی و پاکسازی سشن‌های خراب
• ساخت سشن - ساخت سشن جدید
• تنظیمات - تنظیم Delay و سایر موارد
• دریافت بکاپ - دریافت نسخه پشتیبان

💡 برای راهنمایی بیشتر گزینه "راهنما" را انتخاب کنید."""
        await message.reply(welcome_text, ReplyKeyboard(*keyboard))
    
    elif text == "📊 اطلاعات کامل":
        loading = await message.reply("🔄 در حال دریافت اطلاعات...")
        files = [f for f in os.listdir("sessions") if f.endswith(".bale")]
        salem, nasalem = 0, 0
        pag, page = len(files) // 10, len(files) // 10
        num = 0
        money = 0
        for file in files:
            try:
                dp = Dispatcher()
                client = Client(dp, session_file=f"sessions/{file}")
                salem += 1
                wallet = await client.get_wallet()
                money += (wallet.wallet.balance // 10)
            except Exception as e:
                nasalem += 1
            finally:
                if client:
                    await client.stop()
                num += 1
                if num >= (page + pag):
                    page += pag
                    await loading.edit_text(f"🔄 در حال دریافت اطلاعات...({num} / {len(files)})")
        maten = f"""📊 *گزارش کامل وضعیت اکانت‌ها*

📈 *آمار کلی:*
• *کل اکانت‌ها:* {len(files)} عدد
• *اکانت‌های سالم:* {salem} عدد
• *اکانت‌های خراب:* {nasalem} عدد

💰 *مجموع موجودی:* {money:,} تومان

✅ وضعیت: آنلاین و فعال"""
        await loading.edit_text(maten)
    
    elif text == "📥 جوین دسته‌جمعی":
        await message.reply("""📥 *راهنمای جوین دسته‌جمعی*

برای عضویت در یک گروه با چند اکانت، از فرمت زیر استفاده کنید:

`عضو شو
[تعداد]
[لینک گروه]`

📌 *مثال:*
`عضو شو
5
https://ble.ai/join/ABCDEFG`

⚙️ *تنظیمات پیشرفته:*
• فاصله بین هر جوین: بر اساس Delay تنظیم شده

💡 نکته: حتماً از لینک معتبر استفاده کنید.""")
    
    elif text == "📤 لیو دسته‌جمعی":
        await message.reply("""📤 *راهنمای لیو دسته‌جمعی*

برای خروج از یک گروه با چند اکانت (فقط اکانت‌هایی که عضو هستند)، از فرمت زیر استفاده کنید:

`لفت بده پیشرفته
[تعداد]
[لینک گروه]`

📌 *مثال:*
`لفت بده پیشرفته
10
https://ble.ai/join/ABCDEFG`

✅ *ویژگی‌ها:*
• فقط اکانت‌های عضو گروه را شناسایی می‌کند
• از تعداد مشخص شده، اکانت‌های عضو را خارج می‌کند
• دارای Delay بین هر خروج

⚠️ توجه: اگر تعداد اکانت‌های عضو کمتر از تعداد درخواستی باشد، همان تعداد خارج می‌شوند.""")
    
    elif text == "⚙️ تنظیمات":
        settings_text = """⚙️ *پنل تنظیمات*

گزینه‌های موجود:
• تغییر Delay - تنظیم فاصله زمانی بین عملیات‌ها
• پاکسازی گروه‌ها - خروج از همه گروه‌های ذخیره شده

برای تغییر Delay، گزینه "تغییر Delay" را انتخاب کنید."""
        keyboard = [
            ["⏱ تغییر Delay"],
            ["🧹 پاکسازی گروه‌ها"],
            ["🔙 بازگشت"]
        ]
        await message.reply(settings_text, ReplyKeyboard(*keyboard))
    
    elif text == "💻 مدیریت سشن":
        moderator_text = """*پنل 💻 مدیریت سشن*

از گزینه های زیر انتخاب کنید."""
        keyboard = [
            ["⨠ به روزرسانی دیتابیس"],
            ["🔍 سرچ سشن"],
            ["⪢ ورود به اکانت"],
            ["🔙 بازگشت"]
        ]
        await message.reply(moderator_text, ReplyKeyboard(*keyboard))

    elif text == "⨠ به روزرسانی دیتابیس":
        start = await message.reply("⩘ در حال اپدیت منتظر بمانید.")
        await start.edit_text("৹ اقدامات اولیه . . .")
        files = [f for f in os.listdir("sessions") if f.endswith(".bale")]
        pag, page = len(files) // 10, len(files) // 10
        await start.edit_text("৹ بررسی و افزودن")
        data = {}
        for file in files:
            try:
                dp = Dispatcher()
                client = Client(dp, session_file=f"sessions/{file}")
                phone = await client.get_full_me()
                phone = phone.contact_info.value
                idt = await client.get_me()
                id = idt.id
                wallet = await client.get_wallet()
                balance = wallet.wallet.balance
                data[id] = {
                    "id": id,
                    "name": idt.name,
                    "phone": phone,
                    "locate": file,
                    "money": balance
                }
            except:
                pass
            finally:
                if client:
                    await client.stop()
                if len(data) >= (page + pag):
                    page += pag
                    await start.edit_text(f"৹ {len(data)} / {len(files)} بررسی و افزوده شده.")
        with open("sessions.json", "w") as fil:
            json.dump(data, fil, indent=4)
        await start.edit_text("⫹ دیتابیس با موفیقت به روزرسانی شد.")
    
    elif text == "🔍 سرچ سشن":
        user_data[user_id] = "search"
        await message.reply("🔎 ID/Phone/Name مورد نظر را ارسال کنید")
    
    elif user_id in user_data and "search" == user_data[user_id]:
        await message.reply("🔎 عملیات سرچ شروع شد منتظر بمانید...")
        del user_data[user_id]
        with open("sessions.json") as file:
            data = json.load(file)
        for key, item in data.items():
            if text.isdigit():
                if int(text) == item['id'] or int(text) == item['phone']:
                    y = f"""Name: {item['name']}
Phone: {item['phone']}
ID: {item['id']}
Locate: {item['locate']}
Money: {item['money']}"""
                    await bot.send_message(user_id, y)
            if text == item['name'] or text == item['locate']:
                y = f"""Name: {item['name']}
Phone: {item['phone']}
ID: {item['id']}
Locate: {item['locate']}
Money: {item['money']}"""
                await bot.send_message(user_id, y)
        await bot.send_message(user_id, "تکمیل شد.")

    elif text == "⪢ ورود به اکانت":
        user_data[user_id] = "login_to_sessions"
        await message.reply("اسم فایل سشن مورد نظر را ارسال کنید.")
    
    elif user_id in user_data and "login_to_sessions" == user_data[user_id]:
        current_dir = os.getcwd()
        full_path = os.path.join(current_dir, f"sessions/{text}")
        if os.path.exists(full_path):
            del user_data[user_id]
            await message.reply("تا 60 ثانیه دیگر هر پیامی شامل کد برای شما ارسال خواهد شد.")
            await get_coder(text, user_id)

        else:
            await message.reply("⨻ فایل پیدا نشد!")

    elif text == "🔙 بازگشت":
        keyboard = [
            ["📊 اطلاعات کامل"],
            ["📥 جوین دسته‌جمعی", "📤 لیو دسته‌جمعی"],
            ["🔍 بررسی سشن‌ها", "✨ ساخت سشن"],
            ["💻 مدیریت سشن", "🎩 برترین ها"],
            ["⨻ گزارش"],
            ["⚙️ تنظیمات", "📦 دریافت بکاپ"],
            ["📚 راهنما"]
        ]
        await message.reply("🔙 بازگشت به منوی اصلی", ReplyKeyboard(*keyboard))
    
    elif text == "🎩 برترین ها":
        start = await message.reply("‣ بررسی شروع شد منتظر بمانید")
        with open("sessions.json") as file:
            data = json.load(file)
        sorted_accounts = sorted(data.items(), key=lambda item: item[1]['money'], reverse=True)

        top_10 = sorted_accounts[:10]

        output_lines = [f"لیست ۱۰ حساب برتر بر اساس موجودی (شامل آیدی):\n", "="*60, f"\n"]

        for index, (key, account_data) in enumerate(top_10):
            line = (f"{index+1}. ID: {account_data['id']} |\n"
                    f"نام: {account_data['name']:<6} | \n"
                    f"تلفن: {account_data['phone']} | \n"
                    f"موجودی: {account_data['money']:,} ریال\n\n")
            output_lines.append(line)

        result_string = "\n".join(output_lines)

        await start.edit_text(result_string)

    elif text == "⨻ گزارش":
        user_data[user_id] = "get_report"
        await message.reply("آیدی چت مورد نظر برای ریپورت را بنویسید: ")
    
    elif user_id in user_data and "get_report" == user_data[user_id]:
        sp = text.split("\n")
        if sp[0].isdigit() and sp[1]:
            files = [f for f in os.listdir("sessions") if f.endswith(".bale")]
            number = int(sp[1])
            if len(files) < number:
                await message.reply(f"⚠️ اخطار\nتعداد انتخابی بیشتر از سشن های موجود است.(سشن های موجود: {len(files)})")
            else:
                start = await message.reply("🔄 در حال دریافت سشن های سالم . . .")
                accounts = []
                pag, page = len(files) // 10, len(files) // 10
                for file in files:
                    try:
                        dp = Dispatcher()
                        client = Client(dp, f"sessions/{file}")
                        accounts.append(file)
                    except:
                        pass
                    finally:
                        if client:
                            await client.stop()
                    if len(accounts) >= (page + pag):
                        page += pag
                        await start.edit_text(f"🔄 در حال دریافت سشن های سالم . . .({len(accounts)} / {number})")
                await start.edit_text("🔄 در حال ریپورت زدن. . .")
                shod, nashod = 0, 0
                delay = get_delay()
                pag, page = len(accounts) // 10, len(accounts) // 10
                num = 0
                type = {
                    "1": ChatType.PRIVATE,
                    "2": ChatType.CHANNEL,
                    "3": ChatType.GROUP
                }
                list_reasion = ["فحش میده", "فحاشی", "محتوای بد", "کودک آزاری", "فحش میدن", "بد حرف میزنه"]
                for account in accounts:
                    try:
                        dp = Dispatcher()
                        client = Client(dp, f"sessions/{account}")
                        await client.report_chat(int(sp[0]), type[sp[1]], random.choice(list_reasion))
                        shod +=1
                    except Exception as e:
                        print(e)
                        nashod += 1
                    finally:
                        if client:
                            await client.stop()
                        num += 1
                        if num >= (page + pag):
                            page += pag
                            await start.edit_text(f"🔄 ریپورت زدیم!({num} / {len(accounts)})")
                    await asyncio.sleep(delay)
                await start.edit_text(f"""✅ *تکمیل شد*

📊 *گزارش نهایی:*
- *تعداد کل:* {number}
- *انجام شده:* {shod}
- *انجام نشده:* {nashod}

✨ *با موفقیت به پایان رسید*""")

    elif text == "📚 راهنما":
        help_text = """📚 *راهنمای کامل ربات*

🔹 *دستورات متنی:*
• `/start` - نمایش منوی اصلی
• `/cancel` - لغو عملیات جاری

🔸 *بخش جوین/لیو:*
• *جوین دسته‌جمعی:* عضویت در گروه با فرمت:
  `عضو شو
  [تعداد]
  [لینک]`

• *لیو دسته‌جمعی:* خروج از گروه با فرمت:
  `لفت بده پیشرفته
  [تعداد]
  [لینک]`

🔹 *مدیریت سشن:*
• ساخت سشن جدید با ارسال شماره
• بررسی خودکار سشن‌های خراب
• آپلود سشن با فرمت .bale یا .zip
• دریافت بکاپ از تمام سشن‌ها

🔸 *ری‌اکشن و مجله:*
• ارسال واکنش به پست‌ها
• آپ‌وت در مجله‌ها

💡 *نکات مهم:*
• Delay پیش‌فرض: 2 ثانیه
• تمام عملیات در پس‌زمینه اجرا می‌شود"""
        await message.reply(help_text)
    
    elif text == "📦 دریافت بکاپ":
        start = await message.reply("در حال آماده‌سازی بکاپ...")
        shutil.make_archive("sessions", "zip", "sessions")
        await message.reply_document("sessions.zip", """📦 *بکاپ با موفقیت آماده شد*

✅ تمام سشن‌ها با موفقیت در فایل زیر ذخیره شدند.
🗓 تاریخ: """ + datetime.now().strftime("%Y/%m/%d - %H:%M:%S"))
        await start.delete()
        gc.collect()
        await asyncio.sleep(3)
        os.remove("sessions.zip")
    
    elif text == "⏱ تغییر Delay":
        user_data[user_id] = "delay"
        await message.reply("⏱ تایم جدید را بر حسب ثانیه ارسال کنید\n(لغو عملیات: /cancel)")
    
    elif user_id in user_data and "delay" in user_data[user_id]:
        if text.isdigit():
            data = get_data()
            data['delay'] = int(text)
            with open("data/panel.json", "w") as file:
                json.dump(data, file, indent=4)
            await message.reply(f"""✅ *تنظیمات با موفقیت اعمال شد*

⏱ *مقدار Delay جدید:* {text} ثانیه
📊 *وضعیت:* فعال و ذخیره شد

🔄 از این به بعد تمام عملیات با فاصله {text} ثانیه اجرا می‌شوند.""")
            del user_data[user_id]
        else:
            await message.reply("به عدد وارد کنید.")

    elif text.startswith("عضو شو"):
        sp = text.split("\n")
        if len(sp) == 3:
            if sp[1].isdigit():
                files = [f for f in os.listdir("sessions") if f.endswith(".bale")]
                number = int(sp[1])
                if len(files) < number:
                    await message.reply(f"⚠️ اخطار\nتعداد انتخابی بیشتر از سشن های موجود است.(سشن های موجود: {len(files)})")
                else:
                    start = await message.reply("🔄 در حال دریافت سشن های سالم . . .")
                    accounts = []
                    pag, page = len(files) // 10, len(files) // 10
                    for file in files:
                        try:
                            dp = Dispatcher()
                            client = Client(dp, f"sessions/{file}")
                            accounts.append(file)
                        except:
                            pass
                        finally:
                            if client:
                                await client.stop()
                        if len(accounts) >= (page + pag):
                            page += pag
                            await start.edit_text(f"🔄 در حال دریافت سشن های سالم . . .({len(accounts)} / {number})")
                        if len(accounts) >= number:
                            break
                    if len(accounts) < number:
                        await message.edit_text(f"""⚠️ خطا - تعداد ناکافی

تعداد کل اکانت‌های سالم از تعداد انتخابی کمتر است.

📊 وضعیت فعلی:

تعداد اکانت‌های سالم: {len(accounts)}

تعداد درخواستی: {number}

با این تعداد شروع میکنیم.""")
                    await start.edit_text("🔄 در حال عضو شدن . . .")
                    shod, nashod = 0, 0
                    delay = get_delay()
                    pag, page = len(accounts) // 10, len(accounts) // 10
                    num = 0
                    for account in accounts:
                        try:
                            dp = Dispatcher()
                            client = Client(dp, f"sessions/{account}")
                            await client.join_chat(sp[2])
                            shod +=1
                        except:
                            nashod += 1
                        finally:
                            if client:
                                await client.stop()
                            num += 1
                            if num >= (page + pag):
                                page += pag
                                await start.edit_text(f"🔄 در حال عضو شدن . . .({num} / {len(accounts)})")
                        await asyncio.sleep(delay)
                    add_group(sp[2])
                    await start.edit_text(f"""✅ *تکمیل شد*

📊 *گزارش نهایی:*
- *تعداد کل:* {number}
- *انجام شده:* {shod}
- *انجام نشده:* {nashod}

✨ *با موفقیت به پایان رسید*""")

    elif text.startswith("لفت بده پیشرفته"):
        sp = text.split("\n")
        if len(sp) == 3:
            if sp[1].isdigit():
                files = [f for f in os.listdir("sessions") if f.endswith(".bale")]
                number = int(sp[1])
                if len(files) < number:
                    await message.reply(f"⚠️ اخطار\nتعداد انتخابی بیشتر از سشن های موجود است.(سشن های موجود: {len(files)})")
                else:
                    start = await message.reply("🔄 در حال دریافت سشن های سالم . . .")
                    accounts = []
                    id = 0
                    pag, page = len(files) // 10 , len(files) // 10
                    for file in files:
                        try:
                            dp = Dispatcher()
                            client = Client(dp, f"sessions/{file}")
                            result = await client.get_group_preview(sp[2])
                            if result.is_joined:
                                accounts.append(file)
                        except:
                            pass
                        finally:
                            if client:
                                await client.stop()
                        
                        if len(accounts) >= (page + page):
                            page += pag
                            await start.edit_text(f"🔄 در حال دریافت سشن های سالم . . .({len(accounts)} / {number})")

                        if len(accounts) >= number:
                            if result:
                                id = result.id + (2 ** 32)
                            break
                    if len(accounts) < number:
                        await message.reply(f"متاسفم اما فقط [{len(accounts)}] از اکانت هامون در اینجا عضو است.")
                    shod, nashod = 0, 0
                    pag, page, num = len(accounts) // 10, len(accounts) // 10, 0
                    delay = get_delay()
                    await start.edit_text(f"🔄 در حال ترک دادن . . .")
                    for account in accounts:
                        try:
                            dp = Dispatcher()
                            client = Client(dp, f"sessions/{account}")
                            await client.leave_group(id)
                            shod += 1
                        except:
                            nashod += 1
                        finally:
                            if client:
                                await client.stop()
                            num += 1
                            if num >= (page + pag):
                                page += pag
                                await start.edit_text(f"🔄 در حال ترک دادن . . .({num} / {len(accounts)})")
                        await asyncio.sleep(delay)
                    await start.edit_text(f"""✅ *تکمیل شد*

📊 *گزارش نهایی:*
- *تعداد کل:* {number}
- *انجام شده:* {shod}
- *انجام نشده:* {nashod}

✨ *با موفقیت به پایان رسید*""")

    elif text == "🧹 پاکسازی گروه‌ها":
        group = get_group()
        if len(group) == 0:
            await message.reply("لیستی موجود نیست!")
            return
        start = await message.reply("🔄 در حال دریافت سشن های سالم . . .")
        files = [f for f in os.listdir("sessions") if f.endswith(".bale")]
        pag, page = len(files) // 10, len(files) // 10
        accounts = []
        for file in files:
            try:
                dp = Dispatcher()
                cli = Client(dp, f"sessions/{file}")
                accounts.append(file)
            except:
                pass
            finally:
                if cli:
                    await cli.stop()
                if len(accounts) >= (page + pag):
                    page += pag
                    await start.edit_text(f"🔄 در حال دریافت سشن های سالم . . .({len(accounts)} / {len(files)})")
        await start.edit_text("🔄 در حال پاکسازی . . .")
        anjam = 0
        delay = get_delay()
        for groh in group:
            try:
                dp1 = Dispatcher()
                c = Client(dp1, f"sessions/{accounts[0]}")
                result = await c.get_group_preview(groh)
                id = result.id
            except:
                await message.reply(f"نتوانستیم اطلاعات [{groh}] را بگیریم.")
                remove_group(groh)
                continue
            finally:
                if c:
                    await  c.stop()
            for account in accounts:
                await start.edit_text(f"🔄 در حال پاکسازی برای {result.title}")
                try:
                    dp = Dispatcher()
                    client = Client(dp, f"sessions/{account}")
                    await client.leave_group(id)
                except:
                    pass
                finally:
                    await client.stop()
                await asyncio.sleep(delay)
            anjam += 1
            remove_group(groh)
        await start.edit_text(f"""✅ *تکمیل شد*

📊 *گزارش نهایی:*
- *تعداد کل:* {len(group)}
- *انجام شده:* {anjam}
- *انجام نشده:* {len(group) - anjam}

✨ *با موفقیت به پایان رسید*""")

    elif text == "✨ ساخت سشن":
        user_data[user_id] = "cs"
        await message.reply("عملیات ساخت سشن لغو /cancel")

    elif user_id in user_data and "cs" in user_data[user_id]:
        try:
            phone_number = get_valid_phone_number(message.text)

            if (Path(__file__).parent / "sessions" / f"{message.text}.bale").exists():
                await message.answer("✅ سشن شما از قبل وجود دارد")
                return
            
            if phone_number and len(phone_number) >= 10:
                phone_int = int(phone_number)
                dp = Dispatcher()
                c = Client(dp, session_file=f"sessions/{phone_number}.id")
                t = await c.start_phone_auth(phone_number=phone_int)
                
                if type(t) == AuthErrors:
                    await message.reply(
                        "⚠️ مشکل در ارسال کد تأیید\n"
                        "لطفاً شماره تلفن خود را به فرمت زیر ارسال کنید:\n"
                        "📱 989123456789"
                    )
                else:
                    user_data[user_id] = {
                        "send_time": datetime.now(),
                        "transaction_hash": t.transaction_hash,
                        "code_attempts": 0,
                        "password_attempts": 0,
                        "phone": phone_number
                    }
                    
                    await message.reply(
                        f"📨 کد تأیید برای شماره {phone_number} ارسال شد\n"
                        "⏰ زمان شما: ۹۰ ثانیه\n"
                        "🔢 لطفاً کد دریافتی را وارد کنید"
                    )
            else:
                await message.reply(
                    "⚠️ شماره تلفن نامعتبر\n"
                    "لطفاً شماره تلفن خود را به فرمت‌ زیر ارسال کنید:\n"
                    "• 989123456789\n"
                )
            
        except Exception as e:
            await message.reply(f"❌ خطا در ارسال کد:\n{str(e)}")
    
    elif user_id in user_data and "password_attempts" in user_data[user_id] and user_data[user_id].get("waiting_for_password"):
        phone = user_data[user_id]["phone"]
        dp = Dispatcher()
        c = Client(dp, session_file=f"sessions/{phone}.id")
        t = await c.validate_password(message.text, user_data[user_id]['transaction_hash'])
        
        if t == AuthErrors.WRONG_PASSWORD:
            user_data[user_id]['password_attempts'] += 1
            
            if user_data[user_id]['password_attempts'] >= 2:
                del user_data[user_id]
                await message.reply("🚫 فرصت‌های وارد کردن رمز به پایان رسید")
                return
            
            remaining = 2 - user_data[user_id]['password_attempts']
            await message.reply(f"🔒 رمز عبور نامعتبر است\n🔄 فرصت باقی‌مانده: {remaining} بار")
            return
        elif t == AuthErrors.UNKNOWN:
            await message.reply("خطا ناشناخته❌")
            del user_data[user_id]
        
        session_file = f"{phone}.id"
        await message.reply("🎉 لاگین با موفقیت انجام شد و سشن ثبت گردید")
        del user_data[user_id]
    
    elif user_id in user_data and "code_attempts" in user_data[user_id]:
        login_data = user_data[user_id]
        elapsed_time = datetime.now() - login_data["send_time"]
        
        if elapsed_time > timedelta(seconds=90):
            await message.reply("⏰ زمان وارد کردن کد به پایان رسیده است")
            del user_data[user_id]
            return
        
        elif message.text and message.text.isdigit():
            code = convert_to_english_numbers(message.text)
            
            try:
                phone = user_data[user_id]["phone"]
                dp = Dispatcher()
                c = Client(dp, session_file=f"sessions/{phone}.id")
                t = await c.validate_code(
                    code=code,
                    transaction_hash=login_data["transaction_hash"]
                )
                if t == AuthErrors.WRONG_CODE:
                    user_data[user_id]['code_attempts'] += 1
                    
                    if user_data[user_id]['code_attempts'] >= 2:
                        del user_data[user_id]
                        await message.reply("🚫 کد نامعتبر است و فرصت‌های شما به پایان رسید")
                        return
                    
                    remaining = 2 - user_data[user_id]['code_attempts']
                    await message.reply(f"❌ کد اشتباه است\n🔄 فرصت باقی‌مانده: {remaining} بار")
                    return
                elif t == AuthErrors.UNKNOWN:
                    await message.reply("خطا ناشناخته❌")
                    del user_data[user_id]
                    return
                elif t == AuthErrors.PASSWORD_NEEDED:
                    user_data[user_id]['waiting_for_password'] = True
                    await message.reply(
                        "🔐 تأیید دو مرحله‌ای فعال است\n"
                        "لطفاً رمز عبور دو مرحله‌ای خود را وارد کنید"
                    )
                    return
                
                session_file = f"{phone}.id"
                await message.reply("🎉 لاگین با موفقیت انجام شد و سشن ثبت گردید")
                del user_data[user_id]
                
            except Exception as e:
                await message.reply(f"⚠️ خطا در تأیید کد:\n{str(e)}")
        
        else:
            await message.reply("📝 لطفاً فقط عدد وارد کنید")
    elif text == "🔍 بررسی سشن‌ها":
        start = await message.reply("عملیات شروع شد(بررسی اکانت ها)")
        files = [f for f in os.listdir("sessions") if f.endswith(".bale")]
        ok, no, dup = 0, 0, 0
        dupl =[]
        page, pag = len(files) // 10, len(files) // 10
        for file in files:
            try:
                dp = Dispatcher()
                client = Client(dp, session_file=f"sessions/{file}")
                me = await client.get_me()
                if me.id not in dupl:
                    dupl.append(me.id)
                    ok += 1
                else:
                    dup += 1
                    os.remove(f"sessions/{file}")
            except:
                os.remove(f"sessions/{file}")
                no += 1
            finally:
                if client:
                    await client.stop()
                if (ok + no) >= page:
                    await start.edit_text(f"عملیات شروع شد(بررسی شده: {ok + no})")
                    page += pag
        await start.edit_text(f"""✅ *تکمیل شد*

📊 *گزارش نهایی:*
- *تعداد کل:* {len(files)}
- *سشن های درست:* {ok}
- *سشن های خراب:* {no}
- *سشن های تکراری:* {dup}

(سشن های خراب و تکراری پاک شدند)

✨ *با موفقیت به پایان رسید*""")

    if message.document:
        if message.document.name.endswith(".bale"):
            a = await bot.download(message.document.id)
            pathes = f"check/{message.document.name}"
            with open(pathes, "wb") as file:
                file.write(a)
            try:
                dp3 = Dispatcher()
                client = Client(dp3, session_file=pathes)
                await client.get_me()
                with open(f"sessions/{message.document.name}", "wb") as file:
                    file.write(a)
                    await message.reply("""✅ *فایل سشن با موفقیت ذخیره شد*

📁 *مسیر ذخیره:* sessions/
🆔 *نام فایل:* """ + message.document.name + """

✨ فایل شما بررسی و تایید شد و آماده استفاده است.""")
            except:
                await message.reply("""❌ *خطا در بررسی فایل سشن*

🚫 *فایل ارسالی خراب یا نامعتبر است*

📌 *دلایل احتمالی:*
• فایل سشن آسیب دیده است
• فرمت فایل صحیح نیست
• رمزگذاری فایل مشکل دارد

💡 *راهنمایی:*
لطفاً یک فایل سشن معتبر و سالم ارسال کنید
یا از طریق گزینه "ساخت سشن" اقدام نمایید""")
            finally:
                if client:
                    await client.stop()
                await asyncio.sleep(0.5)
                try:
                    os.remove(pathes)
                except:
                    pass
        elif message.document.name.endswith(".zip"):
            start = await message.reply("عملیات شروع شد(دانلود زیپ) 📥")
            a = await bot.download(message.document.id)
            
            with open("check/newpack.zip", "wb") as file:
                file.write(a)
            
            await start.edit_text("عملیات شروع شد(استخراج سشن ها) 📦")
            
            ok, no = 0, 0
            with zipfile.ZipFile("check/newpack.zip", 'r') as zip_ref:
                all_files = zip_ref.namelist()
                bale_files = [f for f in all_files if f.endswith('.bale')]
                
                for file in bale_files:
                    file_name = os.path.basename(file)
                    temp_path = os.path.join("check", f"temp_{file_name}")
                    final_path = os.path.join("check", file_name)
                    
                    try:
                        with zip_ref.open(file) as source_file:
                            content = source_file.read()
                        
                        with open(temp_path, 'wb') as target_file:
                            target_file.write(content)
                        
                        dp3 = Dispatcher()
                        client = Client(dp3, session_file=temp_path)
                        await client.get_me()
                        
                        with open(final_path, 'wb') as final_file:
                            final_file.write(content)
                        
                        ok += 1
                        
                    except Exception as e:
                        no += 1
                        
                    finally:
                        if 'client' in locals() and client:
                            await client.stop()
                        
                        try:
                            yu = f"check/{file_name}"
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            if os.path.exists(yu):
                                os.remove(yu)
                        except:
                            pass
                        
                        await asyncio.sleep(0.5)
            try:
                os.remove("check/newpack.zip")
            except:
                pass
            await start.edit_text(f"""✅ *تکمیل شد*

📊 *گزارش نهایی:*
- *تعداد کل:* {len(bale_files)}
- *سشن های درست:* {ok}
- *سشن های خراب:* {no}

(سشن های درست ذخیره شدند)

✨ *با موفقیت به پایان رسید*""")


bot.run()