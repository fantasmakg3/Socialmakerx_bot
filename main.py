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

client = AsyncOpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)

# حفظ آخر prompt لكل يوزر (بسيط في الذاكرة)
last_prompt = {}

# ==================== KEYBOARDS ====================
def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 إنشاء صورة جديدة", callback_data="new_image")],
        [InlineKeyboardButton(text="🎥 إنشاء فيديو", callback_data="new_video")],
        [InlineKeyboardButton(text="🖼️ تعديل صورة", callback_data="edit_mode")],
        [InlineKeyboardButton(text="⭐ رصيدي اليومي", callback_data="daily_balance")],
        [InlineKeyboardButton(text="💎 ترقية Premium", callback_data="premium")]
    ])
    return kb

def image_keyboard(prompt: str):
    # callback_data قصيرة جداً (ما يتجاوز 64 حرف)
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

# ==================== HANDLERS ====================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 مرحبا يا وحش في @Socialmakerx_bot!\n"
        "بوت Grok Imagine مجاني 100% داخل تليجرام 🔥\n\n"
        "اختر اللي تبغاه 👇",
        reply_markup=main_menu()
    )

@dp.message(Command("image"))
async def generate_image(message: types.Message):
    prompt = message.text.replace("/image", "").strip()
    if not prompt:
        await message.answer("اكتب الوصف بعد /image مثال:\n/image قطة تطير على القمر")
        return

    # حفظ الـ prompt لليوزر عشان الـ regenerate
    last_prompt[message.from_user.id] = prompt

    msg = await message.answer("⏳ جاري توليد الصورة بـ Grok Imagine... 🔥")
    
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
            caption=f"🎨 تم بنجاح!\n\nPrompt: {prompt}",
            reply_markup=image_keyboard(prompt)
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:200]}")

@dp.callback_query()
async def handle_buttons(callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id

    if data == "main_menu":
        await callback.message.edit_text("🏠 القائمة الرئيسية", reply_markup=main_menu())

    elif data == "regenerate":
        prompt = last_prompt.get(user_id, "قطة جميلة")
        await callback.message.answer(f"🔄 جاري إعادة التوليد...\n{prompt}")
        # نعمل توليد جديد
        msg = await callback.message.answer("⏳ جاري توليد الصورة...")
        try:
            response = await client.images.generate(model="grok-imagine-image", prompt=prompt, n=1)
            image_url = response.data[0].url
            await msg.edit_text("✅ تم التوليد!")
            await callback.message.answer_photo(
                image_url,
                caption=f"🎨 تم بنجاح!\n\nPrompt: {prompt}",
                reply_markup=image_keyboard(prompt)
            )
        except Exception as e:
            await msg.edit_text(f"❌ خطأ: {str(e)[:150]}")

    elif data == "edit_this":
        await callback.message.answer("📸 ارفع الصورة الآن + اكتب في الكابشن:\nedit: وصف التعديل")

    elif data == "new_image":
        await callback.message.answer("🎨 اكتب /image + الوصف الجديد")

    else:
        await callback.answer("⏳ قريباً إن شاء الله 🔥", show_alert=True)

@dp.message(F.photo)
async def handle_edit_photo(message: types.Message):
    if message.caption and ("edit" in message.caption.lower() or "تعديل" in message.caption):
        prompt = message.caption.lower().replace("edit:", "").replace("edit", "").replace("تعديل:", "").strip() or "حسن الصورة"
        await message.answer("🖌️ جاري التعديل...")
        
        full_prompt = f"Edit this image: {prompt}"
        try:
            response = await client.images.generate(
                model="grok-imagine-image",
                prompt=full_prompt,
                n=1
            )
            await message.answer_photo(
                response.data[0].url, 
                caption=f"✅ تم التعديل!\n{prompt}",
                reply_markup=image_keyboard(prompt)
            )
        except Exception as e:
            await message.answer(f"❌ خطأ: {str(e)[:150]}")
    else:
        await message.answer("📸 ارفع صورة + اكتب edit: التعديل في الكابشن")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())