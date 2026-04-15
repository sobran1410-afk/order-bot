import asyncio
import os
import requests
from bs4 import BeautifulSoup
from aiogram import Bot

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

KEYWORDS = ["telegram бот", "python", "парсинг", "отзывы", "тексты"]
MIN_PRICE = 500
CHECK_INTERVAL = 600  # 10 минут

bot = Bot(token=BOT_TOKEN)

sent_links = set()


# === PARSER ===
def parse_kwork():
    orders = []

    for keyword in KEYWORDS:
        try:
            url = f"https://kwork.ru/projects?keyword={keyword}"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            cards = soup.find_all("div", class_="project-card")

            for card in cards:
                try:
                    title_tag = card.find("a")
                    if not title_tag:
                        continue

                    title = title_tag.text.strip()
                    link = "https://kwork.ru" + title_tag["href"]

                    text = card.get_text()
                    price = int(''.join(filter(str.isdigit, text)))

                    if price >= MIN_PRICE and link not in sent_links:
                        orders.append((title, price, link))
                        sent_links.add(link)

                except Exception:
                    continue

        except Exception as e:
            print("Ошибка парсинга:", e)

    return orders


# === GENERATE REPLY ===
def generate_reply(title):
    return f"""Сделаю сегодня.

Есть опыт в похожих задачах: {title}

Готов быстро реализовать и показать результат.
Могу начать сразу.
"""


# === SEND ORDERS ===
async def send_orders():
    orders = parse_kwork()

    for title, price, link in orders:
        message = f"""
🔥 {title}

💸 {price} ₽
🔗 {link}

📩 Отклик:
{generate_reply(title)}
"""
        try:
            await bot.send_message(ADMIN_ID, message)
        except Exception as e:
            print("Ошибка отправки:", e)


# === MAIN LOOP ===
async def main():
    print("Бот запущен...")

    while True:
        try:
            await send_orders()
        except Exception as e:
            print("Ошибка цикла:", e)

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
