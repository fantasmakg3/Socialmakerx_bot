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

    user_last_prompt[message.from_user.id] = prompt

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

# تعديل صورة موجودة (Image-to-Image الحقيقي)
@dp.message(F.photo)
async def handle_edit_image(message: types.Message):
    if not message.caption:
        await message.answer("❌ ارفع الصورة + اكتب في الكابشن وصف التعديل")
        return

    edit_desc = message.caption.strip()

    # نحصل على رابط الصورة العام من تليجرام
    photo = message.photo[-1]
    file = await photo.get_file()
    image_url = file.file_url

    # برومبت قوي جداً ليجبر Grok يعدل الصورة الأصلية
    full_prompt = (
        f"Edit the EXACT uploaded image: {image_url}. "
        f"Keep the same person, same face, same pose, same background, same lighting, same clothes style, same everything. "
        f"Only apply this change: {edit_desc}. "
        f"Do not create a new scene or new person."
    )

    msg = await message.answer("🖌️ جاري تعديل الصورة بالضبط...")

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
