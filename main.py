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
        [InlineKeyboardButton(text="🎨 إنشاء صورة", callback_data="new_image")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="main_menu")]
    ])
    return kb

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 مرحبا يا وحش في @Socialmakerx_bot!\n"
        "بوت Grok Imagine الرسمي 🔥\n\n"
        "اضغط على الزر و اكتب الوصف",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "new_image")
async def new_image(callback: CallbackQuery):
    await callback.message.edit_text("🎨 اكتب وصف الصورة بالعربي (طويل أفضل)")

@dp.message(F.text)
async def handle_text(message: types.Message):
    if message.text.startswith('/'):
        return

    prompt = message.text.strip()
    if len(prompt) < 5:
        await message.answer("اكتب وصف أطول شوي يا وحش 😅")
        return

    user_last_prompt[message.from_user.id] = prompt

    msg = await message.answer("⏳ جاري التوليد بـ Grok Imagine... 🔥")
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
async def handle_edit(message: types.Message):
    if not message.caption:
        await message.answer("ارفع الصورة + اكتب في الكابشن وصف التعديل\nمثال: غير لون القط إلى الزهري")
        return

    edit_desc = message.caption.strip()
    msg = await message.answer("🖌️ جاري تعديل الصورة بـ Grok Imagine...")

    try:
        response = await client.images.generate(
            model="grok-imagine-image",
            prompt=f"Edit this image: {edit_desc}",
            n=1
        )
        image_url = response.data[0].url

        await msg.edit_text("✅ تم التعديل!")
        await message.answer_photo(
            image_url,
            caption=f"🖌️ تم التعديل!\n{edit_desc}",
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
