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
        [InlineKeyboardButton(text="🎥 إنشاء فيديو (5 ثواني)", callback_data="new_video")],
        [InlineKeyboardButton(text="⭐ رصيدي اليومي", callback_data="daily_balance")],
        [InlineKeyboardButton(text="💎 ترقية الحساب", callback_data="premium")]
    ])
    return kb

def video_action_keyboard(prompt: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 توليد فيديو جديد", callback_data="regenerate_video")],
        [InlineKeyboardButton(text="🖼️ استخراج فريم كصورة", callback_data="extract_frame")],
        [InlineKeyboardButton(text="❤️ حفظ", callback_data="save")],
        [InlineKeyboardButton(text="📤 مشاركة", callback_data="share")],
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

@dp.callback_query(F.data == "new_video")
async def start_new_video(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎥 اكتب وصف الفيديو القصير (5 ثواني)\n"
        "مثال: قط يركض على الشاطئ ويطارد كرة\n"
        "أو ارفع صورة + اكتب في الكابشن وصف الحركة"
    )

@dp.message(F.text)
async def handle_video_prompt(message: types.Message):
    prompt = message.text.strip()
    if len(prompt) < 5:
        await message.answer("اكتب وصف أطول شوي يا وحش 😅")
        return

    user_last_prompt[message.from_user.id] = prompt

    msg = await message.answer("🎥 جاري توليد فيديو 5 ثواني... 🔥")
    try:
        response = await client.images.generate(
            model="grok-imagine-video",
            prompt=prompt,
            n=1
        )
        video_url = response.data[0].url

        await msg.edit_text("✅ تم توليد الفيديو!")
        await message.answer_video(
            video_url,
            caption=f"🎥 فيديو 5 ثواني\nPrompt: {prompt}",
            reply_markup=video_action_keyboard(prompt)
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:200]}\n(جاري تحسين الفيديو قريباً)")

@dp.callback_query(F.data == "regenerate_video")
async def regenerate_video(callback: CallbackQuery):
    user_id = callback.from_user.id
    prompt = user_last_prompt.get(user_id)
    if not prompt:
        await callback.answer("❌ انتهت الجلسة", show_alert=True)
        return

    msg = await callback.message.answer("🎥 جاري إعادة توليد الفيديو...")
    try:
        response = await client.images.generate(
            model="grok-imagine-video",
            prompt=prompt,
            n=1
        )
        video_url = response.data[0].url
        await msg.edit_text("✅ تم توليد الفيديو!")
        await callback.message.answer_video(
            video_url,
            caption=f"🎥 فيديو 5 ثواني (إعادة توليد)\nPrompt: {prompt}",
            reply_markup=video_action_keyboard(prompt)
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