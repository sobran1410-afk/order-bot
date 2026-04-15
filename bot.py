import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

def init_db():
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  product_link TEXT,
                  review_text TEXT,
                  status TEXT,
                  created_at TEXT)""")
    conn.commit()
    conn.close()

init_db()

def save_order(user_id, username, product_link, review_text):
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, username, product_link, review_text, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, username, product_link, review_text, "pending", datetime.now().isoformat()))
    conn.commit()
    conn.close()

main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📝 Сделать заказ", callback_data="new_order")],
    [InlineKeyboardButton(text="ℹ️ Как это работает", callback_data="info")],
    [InlineKeyboardButton(text="📞 Поддержка", callback_data="support")]
])

class OrderForm(StatesGroup):
    waiting_for_product_link = State()
    waiting_for_review_text = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🤖 *Бот для заказа отзывов*\n\n💰 500₽ за 5 отзывов\n⏱ 2 часа\n\nНажми кнопку ниже",
        reply_markup=main_keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "new_order")
async def new_order(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📎 Отправь ссылку на товар (Ozon или WB)", parse_mode="Markdown")
    await state.set_state(OrderForm.waiting_for_product_link)
    await callback.answer()

@dp.message(OrderForm.waiting_for_product_link)
async def get_product_link(message: Message, state: FSMContext):
    link = message.text
    if "ozon" not in link.lower() and "wildberries" not in link.lower():
        await message.answer("❌ Отправь ссылку на Ozon или Wildberries")
        return
    await state.update_data(product_link=link)
    await message.answer("✍️ Напиши 3 ключевые фразы для отзывов", parse_mode="Markdown")
    await state.set_state(OrderForm.waiting_for_review_text)

@dp.message(OrderForm.waiting_for_review_text)
async def get_review_text(message: Message, state: FSMContext):
    keywords = message.text
    data = await state.get_data()
    product_link = data.get("product_link")
    
    save_order(
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name,
        product_link=product_link,
        review_text=keywords
    )
    
    if ADMIN_ID:
        await bot.send_message(ADMIN_ID, f"🆕 Новый заказ!\n👤 @{message.from_user.username}\n🔗 {product_link}\n📝 {keywords}")
    
    await message.answer("✅ Заказ принят! Отзывы через 2 часа. 500₽ после получения.")
    await state.clear()

@dp.callback_query(F.data == "info")
async def show_info(callback: CallbackQuery):
    await callback.message.edit_text("📖 1️⃣ Ссылка → 2️⃣ Ключи → 3️⃣ 5 отзывов → 4️⃣ 500₽", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]]))
    await callback.answer()

@dp.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    await callback.message.edit_text("📞 Поддержка: @your_support", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]]))
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=main_keyboard)
    await callback.answer()

async def on_startup():
    logging.info("Бот запущен!")

if __name__ == "__main__":
    async def main():
        await on_startup()
        await dp.start_polling(bot)
    asyncio.run(main())
