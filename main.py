import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = AsyncOpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

user_last_prompt = {}

def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼️ إنشاء / تعديل صور", callback_data="image_menu")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="main_menu")]
    ])
    return kb

def image_menu_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 إنشاء صورة جديدة", callback_data="new_image")],
        [InlineKeyboardButton(text="🖌️ تعديل الصورة", callback_data="edit_image")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="main_menu")]
    ])
    return kb

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 مرحبا يا وحش في @Socialmakerx_bot!\n"
        "Grok Imagine الرسمي 🔥\n\n"
        "اختر اللي تبغاه:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "image_menu")
async def show_image_menu(callback: CallbackQuery):
    await callback.message.edit_text("🖼️ اختر الخدمة:", reply_markup=image_menu_keyboard())

@dp.callback_query(F.data == "new_image")
async def new_image(callback: CallbackQuery):
    await callback.message.edit_text("🎨 اكتب وصف الصورة بالعربي")

@dp.callback_query(F.data == "edit_image")
async def edit_image(callback: CallbackQuery):
    await callback.message.answer(
        "📸 ارفع الصورة اللي تبغى تعدلها\n"
        "واكتب في الكابشن وصف التعديل\n"
        "مثال: غير لون القط إلى الزهري"
    )

@dp.message(F.text)
async def handle_text(message: types.Message):
    if message.text.startswith('/'):
        return

    prompt = message.text.strip()
    if len(prompt) < 5:
        await message.answer("اكتب وصف أطول شوي يا وحش 😅")
        return

    user_last_prompt[message.from_user.id] = prompt

    msg = await message.answer("⏳ جاري التوليد بـ Grok Imagine...")
    try:
        response = await client.images.generate(
            model="grok-imagine-image",
            prompt=prompt,
            n=1
        )
        image_url = response.data[0].url

        await msg.edit_text("✅ تم التوليد!")
        await message.answer_photo(
            image_url,
            caption=f"🎨 تم بنجاح!\nPrompt: {prompt}",
            reply_markup=main_menu()
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:200]}")

@dp.message(F.photo)
async def handle_photo_edit(message: types.Message):
    if not message.caption:
        await message.answer("❌ لازم تكتب وصف التعديل في الكابشن")
        return

    edit_desc = message.caption.strip()
    msg = await message.answer("🖌️ جاري تعديل الصورة بـ grok-imagine-image-pro...")

    try:
        response = await client.images.generate(
            model="grok-imagine-image-pro",   # ← النموذج الـ Pro للتعديل
            prompt=f"Edit this image: {edit_desc}",
            n=1
        )
        image_url = response.data[0].url

        await msg.edit_text("✅ تم التعديل بـ Pro!")
        await message.answer_photo(
            image_url,
            caption=f"🖌️ تم التعديل!\nالتعديل: {edit_desc}",
            reply_markup=main_menu()
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:200]}")

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text("🏠 القائمة الرئيسية", reply_markup=main_menu())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
