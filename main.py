import os
import asyncio
import logging
import aiohttp
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

PASSWORD = "onlykggrok"  # باسورد ثابت لكل الصور المرفوعة

def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 إنشاء صورة جديدة", callback_data="new_image")],
        [InlineKeyboardButton(text="🖌️ تعديل صورة موجودة", callback_data="edit_image")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="main_menu")]
    ])
    return kb

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 مرحبا يا وحش في @Socialmakerx_bot!\n"
        "Grok Imagine الرسمي (يدعم تعديل الصور) 🔥\n\n"
        "اختر اللي تبغاه:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "new_image")
async def new_image(callback: CallbackQuery):
    await callback.message.edit_text("🎨 اكتب وصف الصورة بالعربي")

@dp.callback_query(F.data == "edit_image")
async def edit_image(callback: CallbackQuery):
    await callback.message.answer(
        "📸 ارفع الصورة اللي تبغى تعدلها\n"
        "واكتب في الكابشن وصف التعديل فقط\n"
        "مثال: غير لون التيشيرت إلى الزهري"
    )

# إنشاء صورة جديدة
@dp.message(F.text)
async def handle_new_image(message: types.Message):
    if message.text.startswith('/'):
        return

    prompt = message.text.strip()
    if len(prompt) < 5:
        await message.answer("اكتب وصف أطول شوي يا وحش 😅")
        return

    msg = await message.answer("⏳ جاري التوليد...")
    try:
        response = await client.images.generate(
            model="grok-imagine-image",
            prompt=prompt,
            n=1
        )
        image_url = response.data[0].url
        await msg.edit_text("✅ تم التوليد!")
        await message.answer_photo(image_url, caption=f"🎨 تم بنجاح!\nPrompt: {prompt}", reply_markup=main_menu())
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:200]}")

# تعديل صورة موجودة (مع رفع على Temp-Image.com)
@dp.message(F.photo)
async def handle_edit_image(message: types.Message):
    if not message.caption:
        await message.answer("❌ ارفع الصورة + اكتب في الكابشن وصف التعديل")
        return

    edit_desc = message.caption.strip()

    # تحميل الصورة من تليجرام
    photo = message.photo[-1]
    file = await photo.get_file()
    file_bytes = await bot.download_file(file.file_path)

    msg = await message.answer("📤 جاري رفع الصورة بأمان على Temp-Image (5 دقايق + باسورد)...")

    # رفع على Temp-Image.com
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('file', file_bytes, filename='image.jpg', content_type='image/jpeg')
        data.add_field('expiration', '5')   # 5 دقايق
        data.add_field('password', PASSWORD)

        async with session.post('https://temp-image.com/upload', data=data) as resp:
            result = await resp.json()
            image_url = result.get('url')

    if not image_url:
        await msg.edit_text("❌ فشل رفع الصورة، حاول مرة ثانية")
        return

    # برومبت قوي جداً لـ Grok
    full_prompt = (
        f"Edit the EXACT uploaded image: {image_url}. "
        f"Password: {PASSWORD}. "
        f"Keep the same person, same face, same pose, same background, same lighting, same everything. "
        f"Only apply this change: {edit_desc}. "
        f"Do not create a new scene or new person."
    )

    await msg.edit_text("🖌️ جاري تعديل الصورة بالضبط بـ Grok Imagine...")

    try:
        response = await client.images.generate(
            model="grok-imagine-image",
            prompt=full_prompt,
            n=1
        )
        new_image_url = response.data[0].url

        await msg.edit_text("✅ تم التعديل بنجاح!")
        await message.answer_photo(
            new_image_url,
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
