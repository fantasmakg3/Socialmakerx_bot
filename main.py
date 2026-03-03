import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import fal_client
from googletrans import Translator

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FAL_KEY = os.getenv("FAL_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = fal_client.AsyncClient(key=FAL_KEY)
translator = Translator()

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
        "بوت Flux Pro + Kling 🔥\n\n"
        "اكتب أي وصف بالعربي وسيشتغل بإذن الله",
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
    await callback.message.edit_text("🎨 اكتب وصف الصورة بالعربي (طويل ومفصل أفضل)")

@dp.message(F.text)
async def handle_prompt(message: types.Message):
    if message.text.startswith('/'):
        return

    arabic_prompt = message.text.strip()
    if len(arabic_prompt) < 5:
        await message.answer("اكتب وصف أطول شوي يا وحش 😅")
        return

    user_last_prompt[message.from_user.id] = arabic_prompt

    msg = await message.answer("⏳ جاري الترجمة والتوليد بـ Flux Pro (9:16)... 🔥")

    try:
        # ترجمة عربي → إنجليزي
        english = translator.translate(arabic_prompt, dest='en').text
        
        # prompt engineering قوي جداً
        enhanced = f"masterpiece, best quality, ultra detailed, 8k, photorealistic, cinematic lighting, sharp focus, dynamic composition, {english}, highly detailed, vibrant colors, 9:16 vertical reel format"

        result = await client.subscribe(
            "fal-ai/flux-dev",
            arguments={
                "prompt": enhanced,
                "image_size": {"width": 832, "height": 1472},
                "num_inference_steps": 40,
                "guidance_scale": 9.0,
                "enable_safety_checker": False
            }
        )
        image_url = result["images"][0]["url"]

        await msg.edit_text("✅ تم التوليد بـ Flux Pro!")
        await message.answer_photo(
            image_url,
            caption=f"🎨 تم بنجاح!\nالوصف: {arabic_prompt}",
            reply_markup=image_action_keyboard(arabic_prompt)
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:200]}")

@dp.callback_query(F.data == "regenerate")
async def regenerate(callback: CallbackQuery):
    user_id = callback.from_user.id
    arabic_prompt = user_last_prompt.get(user_id)
    if not arabic_prompt:
        await callback.answer("❌ انتهت الجلسة", show_alert=True)
        return

    msg = await callback.message.answer("🔄 جاري إعادة التوليد...")
    try:
        english = translator.translate(arabic_prompt, dest='en').text
        enhanced = f"masterpiece, best quality, ultra detailed, 8k, photorealistic, cinematic lighting, sharp focus, dynamic composition, {english}, highly detailed, vibrant colors, 9:16 vertical reel format"

        result = await client.subscribe("fal-ai/flux-dev", arguments={
            "prompt": enhanced,
            "image_size": {"width": 832, "height": 1472},
            "num_inference_steps": 40,
            "guidance_scale": 9.0,
            "enable_safety_checker": False
        })
        image_url = result["images"][0]["url"]
        await msg.edit_text("✅ تم التوليد!")
        await callback.message.answer_photo(image_url, caption=f"🎨 تم بنجاح (إعادة)!\nالوصف: {arabic_prompt}", reply_markup=image_action_keyboard(arabic_prompt))
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
