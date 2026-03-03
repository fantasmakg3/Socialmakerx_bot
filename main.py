import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import fal_client

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FAL_KEY = os.getenv("FAL_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = fal_client.AsyncFalClient(key=FAL_KEY)

user_last_prompt = {}

def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼️ إنشاء / تعديل صور", callback_data="image_menu")],
        [InlineKeyboardButton(text="🎥 إنشاء فيديو 5 ثواني", callback_data="new_video")],
        [InlineKeyboardButton(text="⭐ رصيدي اليومي", callback_data="daily_balance")],
        [InlineKeyboardButton(text="💎 ترقية الحساب", callback_data="premium")]
    ])
    return kb

def image_action_keyboard(prompt: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 توليد جديد", callback_data="regenerate")],
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
        "بوت fal.ai (Flux + Kling) مجاني 100% 🔥\n\n"
        "اختر اللي تبغاه 👇",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "image_menu")
async def image_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 إنشاء صورة جديدة", callback_data="new_image")],
        [InlineKeyboardButton(text="🖌️ تعديل صورة", callback_data="edit_image")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="main_menu")]
    ])
    await callback.message.edit_text("🖼️ اختر الخدمة:", reply_markup=kb)

@dp.callback_query(F.data == "new_image")
async def new_image(callback: CallbackQuery):
    await callback.message.edit_text("🎨 اكتب وصف الصورة (بالعربي تماماً)")

@dp.callback_query(F.data == "new_video")
async def new_video(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎥 اكتب وصف الفيديو (5 ثواني)\n"
        "مثال: قط يركض على الشاطئ ويطارد كرة\n"
        "أو ارفع صورة + اكتب في الكابشن وصف الحركة"
    )

@dp.message(F.text)
async def handle_prompt(message: types.Message):
    prompt = message.text.strip()
    if len(prompt) < 5:
        await message.answer("اكتب وصف أطول شوي يا وحش 😅")
        return

    user_last_prompt[message.from_user.id] = prompt

    msg = await message.answer("⏳ جاري التوليد بـ Flux... 🔥")
    try:
        result = await client.subscribe(
            "fal-ai/flux-pro/v1.1",
            arguments={
                "prompt": prompt,
                "image_size": {"width": 1024, "height": 1792},  # 9:16 ريلز عمودي
                "num_inference_steps": 28,
                "guidance_scale": 3.5
            }
        )
        image_url = result["images"][0]["url"]

        await msg.edit_text("✅ تم التوليد بـ Flux!")
        await message.answer_photo(
            image_url,
            caption=f"🎨 تم بنجاح!\nPrompt: {prompt}",
            reply_markup=image_action_keyboard(prompt)
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:200]}")

@dp.callback_query(F.data == "regenerate")
async def regenerate(callback: CallbackQuery):
    # نفس الكود الخاص بالتوليد أعلاه (مختصر)
    user_id = callback.from_user.id
    prompt = user_last_prompt.get(user_id)
    if not prompt:
        await callback.answer("❌ انتهت الجلسة", show_alert=True)
        return
    # ... (أعد استخدام نفس كود التوليد أعلاه)
    await callback.answer("🔄 جاري إعادة التوليد...")

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
