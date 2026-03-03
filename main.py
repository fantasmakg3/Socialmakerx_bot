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

RATIO_PROMPT = {
    "1:1": "perfect square 1:1 aspect ratio",
    "9:16": "EXTREMELY TALL VERTICAL 9:16 portrait reel format, tall narrow image, full vertical composition",
    "16:9": "wide horizontal 16:9 landscape format",
    "4:5": "4:5 portrait format",
    "3:2": "classic 3:2 aspect ratio"
}

def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 إنشاء صورة جديدة", callback_data="new_image")],
        [InlineKeyboardButton(text="🎥 إنشاء فيديو", callback_data="new_video")],
        [InlineKeyboardButton(text="🖼️ تعديل صورة", callback_data="edit_mode")],
        [InlineKeyboardButton(text="⭐ رصيدي اليومي", callback_data="daily_balance")],
        [InlineKeyboardButton(text="💎 ترقية Premium", callback_data="premium")]
    ])
    return kb

def aspect_ratio_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬜ 1:1 مربع", callback_data="ratio:1:1")],
        [InlineKeyboardButton(text="📱 9:16 ريلز عمودي", callback_data="ratio:9:16")],
        [InlineKeyboardButton(text="🖥️ 16:9 ريلز أفقي", callback_data="ratio:16:9")],
        [InlineKeyboardButton(text="📲 4:5 إنستا", callback_data="ratio:4:5")],
        [InlineKeyboardButton(text="📷 3:2 كلاسيكي", callback_data="ratio:3:2")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="main_menu")]
    ])
    return kb

def image_action_keyboard(prompt: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 توليد جديد بنفس الوصف", callback_data="regenerate")],
        [InlineKeyboardButton(text="🖌️ تعديل هذه الصورة", callback_data="edit_this")],
        [InlineKeyboardButton(text="🎥 حولها إلى فيديو", callback_data="to_video")],
        [InlineKeyboardButton(text="⬆️ تحسين الجودة", callback_data="upscale")],
        [InlineKeyboardButton(text="❤️ حفظ", callback_data="save"), 
         InlineKeyboardButton(text="📤 مشاركة", callback_data="share")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="main_menu")]
    ])
    return kb

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 مرحبا يا وحش في @Socialmakerx_bot!\n"
        "بوت Grok Imagine مجاني 100% داخل تليجرام 🔥\n\n"
        "اختر اللي تبغاه 👇",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "new_image")
async def start_new_image(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎨 اكتب وصف الصورة اللي تبغاها (بالعربي تماماً)\n"
        "مثال: قط جميل يمشي على سطح القمر يرتدي نظارات"
    )

@dp.message(F.text & \~F.text.startswith('/'))
async def handle_prompt(message: types.Message):
    prompt = message.text.strip()
    if len(prompt) < 5:
        await message.answer("اكتب وصف أطول شوي يا وحش 😅")
        return

    user_last_prompt[message.from_user.id] = prompt
    await message.answer("✅ وصفك مسجل!\nاختر قياس الصورة 👇", reply_markup=aspect_ratio_keyboard())

@dp.callback_query(F.data.startswith("ratio:"))
async def generate_image(callback: CallbackQuery):
    ratio_code = callback.data.split(":")[1]
    user_id = callback.from_user.id
    base_prompt = user_last_prompt.get(user_id)

    if not base_prompt:
        await callback.answer("❌ انتهت الجلسة، اضغط إنشاء صورة جديدة", show_alert=True)
        return

    ratio_instruction = RATIO_PROMPT.get(ratio_code, "")
    final_prompt = f"{base_prompt}, {ratio_instruction}, masterpiece, highly detailed, best quality"

    msg = await callback.message.edit_text(f"⏳ جاري توليد الصورة...\nقياس: {ratio_code}")

    try:
        response = await client.images.generate(
            model="grok-imagine-image",
            prompt=final_prompt,
            n=1
        )
        image_url = response.data[0].url

        await msg.edit_text("✅ تم التوليد!")
        await callback.message.answer_photo(
            image_url,
            caption=f"🎨 تم بنجاح!\nقياس: {ratio_code}\nPrompt: {base_prompt}",
            reply_markup=image_action_keyboard(base_prompt)
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:180]}")

@dp.callback_query(F.data == "regenerate")
async def regenerate(callback: CallbackQuery):
    user_id = callback.from_user.id
    base_prompt = user_last_prompt.get(user_id)
    if not base_prompt:
        await callback.answer("❌ انتهت الجلسة", show_alert=True)
        return

    ratio_code = "9:16"  # آخر قياس اختاره
    ratio_instruction = RATIO_PROMPT.get(ratio_code, "")
    final_prompt = f"{base_prompt}, {ratio_instruction}, masterpiece, highly detailed"

    msg = await callback.message.answer("🔄 جاري إعادة التوليد...")
    try:
        response = await client.images.generate(model="grok-imagine-image", prompt=final_prompt, n=1)
        image_url = response.data[0].url
        await msg.edit_text("✅ تم التوليد!")
        await callback.message.answer_photo(
            image_url,
            caption=f"🎨 تم بنجاح (إعادة توليد)!\nقياس: {ratio_code}\nPrompt: {base_prompt}",
            reply_markup=image_action_keyboard(base_prompt)
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:150]}")

@dp.callback_query()
async def other_buttons(callback: CallbackQuery):
    if callback.data == "main_menu":
        await callback.message.edit_text("🏠 القائمة الرئيسية", reply_markup=main_menu())
    else:
        await callback.answer("⏳ قريباً إن شاء الله 🔥", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())