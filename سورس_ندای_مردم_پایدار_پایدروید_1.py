import requests
import re
import time
import threading
import traceback
from html import unescape
from urllib.parse import urljoin

# =========================
# تنظیمات
# =========================
TOKEN = "1083598035:VhHYTXYvbHN7R2FtNvUPACk9NYyaNr6kx7I"
CHANNEL = "@nedayeh_mardom"

API = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"

# منابع و موضوعات متنوع
# تمرکز بیشتر روی: جهان، ورزش، علم و فناوری، فرهنگ و هنر، حوادث، خودرو و اقتصاد
feeds = {
    "🇺🇸 اخبار آمریکا": "https://news.google.com/rss/search?q=%D8%A2%D9%85%D8%B1%DB%8C%DA%A9%D8%A7+when%3A1d&hl=fa&gl=IR&ceid=IR%3Afa",
    "🇮🇱 اخبار اسرائیل": "https://news.google.com/rss/search?q=%D8%A7%D8%B3%D8%B1%D8%A7%D8%A6%DB%8C%D9%84+when%3A1d&hl=fa&gl=IR&ceid=IR%3Afa",
    "🇺🇸🇮🇱 آمریکا و اسرائیل": "https://news.google.com/rss/search?q=%D8%A2%D9%85%D8%B1%DB%8C%DA%A9%D8%A7+%D8%A7%D8%B3%D8%B1%D8%A7%D8%A6%DB%8C%D9%84+when%3A1d&hl=fa&gl=IR&ceid=IR%3Afa",
    "🌍 خاورمیانه": "https://news.google.com/rss/search?q=%D8%AE%D8%A7%D9%88%D8%B1%D9%85%DB%8C%D8%A7%D9%86%D9%87+when%3A1d&hl=fa&gl=IR&ceid=IR%3Afa",
    "🌍 جهان": "https://www.parseek.com/rss/?type=WORLD",
}

SIGN = """*[『 ندای مردم 』](ble.ir/join/FuG5vvUddF) *"""

sent_links = set()

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Android) DarkerNewsBot/2.0",
    "Connection": "keep-alive"
})


def clean_text(text):
    text = re.sub(r"<.*?>", "", text, flags=re.S)
    text = unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_description(text):
    text = clean_text(text)

    # Google News گاهی نام رسانه را در انتهای description می‌چسباند.
    # این نام‌ها را فقط وقتی در انتهای متن باشند حذف می‌کنیم.
    source_names = [
        "میزان", "انتخاب", "ایسنا", "ایرنا", "فارس", "تسنیم",
        "مهر", "خبرآنلاین", "همشهری آنلاین", "شرق", "اعتماد",
        "دنیای اقتصاد", "تابناک", "باشگاه خبرنگاران جوان",
        "خبرگزاری صدا و سیما", "صدا و سیما"
    ]

    for name in sorted(source_names, key=len, reverse=True):
        text = re.sub(rf"(?:\s*[|،,:؛-]?\s*){re.escape(name)}\s*$", "", text, flags=re.I)

    return text.strip()


def get_tag(block, tag):
    # تگ‌های ساده RSS
    m = re.search(
        rf"<{tag}(?:\s[^>]*)?>(.*?)</{tag}\s*>",
        block,
        re.S | re.I
    )
    return clean_text(m.group(1)) if m else ""


def read_rss(source, url):
    for attempt in range(2):
        try:
            print(f"🔎 {source}", flush=True)

            r = session.get(url, timeout=(10, 25))
            r.raise_for_status()
            xml = r.text

            # روش اصلی: جدا کردن itemهای RSS
            blocks = re.findall(
                r"<item(?:\s[^>]*)?>(.*?)</item\s*>",
                xml,
                re.S | re.I
            )

            news = []

            for block in blocks[:20]:
                title = get_tag(block, "title")
                desc = clean_description(get_tag(block, "description"))
                link = get_tag(block, "link")

                # بعضی RSSها لینک را داخل CDATA می‌گذارند
                link = clean_text(link)

                if title and link:
                    news.append((title, desc, link))

            print(f"✅ {source}: {len(news)} خبر", flush=True)
            return news

        except requests.RequestException as e:
            print(f"⚠️ {source} خطای اتصال: {e}", flush=True)
            if attempt == 0:
                time.sleep(3)
            else:
                print(f"⏭️ رد شد: {source}", flush=True)

        except Exception as e:
            print(f"⚠️ {source} خطای RSS: {e}", flush=True)
            break

    return []


def send_message(text):
    for attempt in range(3):
        try:
            r = session.post(
                API,
                data={
                    "chat_id": CHANNEL,
                    "text": text
                },
                timeout=(10, 60)
            )

            if r.status_code == 200:
                try:
                    result = r.json()
                except Exception:
                    result = {}

                if result.get("ok"):
                    print("✅ sent", flush=True)
                    return True

                print("❌ Bale:", result, flush=True)
            else:
                print(f"❌ Bale HTTP {r.status_code}", flush=True)

        except requests.RequestException as e:
            print(f"⚠️ ارسال {attempt + 1}/3 (اختلال موقت در اتصال به بله):", e, flush=True)
            time.sleep(5 * (attempt + 1))

        except Exception as e:
            print("❌ send error:", e, flush=True)
            break

    return False


def process_news():
    for source, url in feeds.items():
        try:
            news_list = read_rss(source, url)

            for title, desc, link in news_list:

                if link in sent_links:
                    continue

                # فقط اخبار مرتبط با آمریکا، اسرائیل و تحولات بین‌المللی.
                # خبرهای مربوط به جمهوری اسلامی/نهادهای نظامی و داخلی ایران حذف می‌شوند.
                iran_block_words = [
                    "سردار", "سپاه پاسداران", "سپاه", "لشکر", "بسیج",
                    "نیروی قدس", "ارتش ایران", "فرمانده سپاه", "قرارگاه",
                    "سازمان انرژی اتمی ایران", "انرژی اتمی ایران",
                    "رئیس‌جمهور ایران", "رئیس جمهور ایران",
                    "مجلس ایران", "دولت ایران", "وزیر ایران",
                    "نماینده مجلس ایران", "رهبر ایران", "جمهوری اسلامی",
                    "ایران اسلامی", "مقامات ایرانی", "مقام ایرانی",
                    "نیروهای مسلح ایران", "نیروی انتظامی", "فراجا",
                ]

                combined_text = f"{title} {desc}".replace("ي", "ی").replace("ك", "ک")
                if any(word in combined_text for word in iran_block_words):
                    print("⏭️ خبر مربوط به ایران/نهادهای داخلی رد شد:", title, flush=True)
                    continue

                # بله محدودیت طول پیام دارد؛ متن را تا نزدیک سقف امن نگه می‌داریم
                # و دیگر مثل نسخه قبلی فقط 650 کاراکتر از توضیح را نمی‌بریم.
                full_desc = desc.strip()
                if not full_desc:
                    full_desc = "برای مشاهده جزئیات کامل خبر، لینک منبع را باز کنید."

                text = f"""📰 *{source}*

🌟 *{title}*

{full_desc}

{SIGN}"""

                # سقف امن برای پیام بله
                if len(text) > 3900:
                    text = text[:3890].rstrip() + "…"


                if send_message(text):
                    sent_links.add(link)
                    print("✅ منتشر شد:", title, flush=True)
                else:
                    print("⚠️ ارسال نشد:", title, flush=True)

                # فاصله ضد اسپم
                time.sleep(20)

        except Exception as e:
            print(f"❌ خطای منبع {source}:", e, flush=True)


def keep_alive():
    while True:
        try:
            print(
                "💚 Bot alive:",
                time.strftime("%Y-%m-%d %H:%M:%S"),
                flush=True
            )
            time.sleep(60)
        except Exception:
            time.sleep(10)


def main():
    print("=" * 50, flush=True)
    print("🚀 ندای مردم - USA / ISRAEL NEWS BOT", flush=True)
    print("🇺🇸 آمریکا | 🇮🇱 اسرائیل | 🇺🇸🇮🇱 آمریکا و اسرائیل | 🌍 خاورمیانه | 🌍 جهان", flush=True)
    print("🛡️ حالت پایدار برای Pydroid", flush=True)
    print("=" * 50, flush=True)

    while True:
        try:
            process_news()
            print("💚 ربات هنوز فعال است:", time.strftime("%Y-%m-%d %H:%M:%S"), flush=True)
        except KeyboardInterrupt:
            print("🛑 توقف توسط کاربر", flush=True)
            raise
        except BaseException as e:
            print("🔥 خطای اصلی؛ ربات متوقف نمی‌شود:", repr(e), flush=True)
            traceback.print_exc()

        # زمان کوتاه‌تر برای اینکه Pydroid ظاهراً بیکار نماند.
        for remaining in range(30, 0, -1):
            if remaining in (30, 20, 10, 5, 1):
                print(f"⏳ بررسی دوباره در {remaining} ثانیه...", flush=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
