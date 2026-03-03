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
        [InlineKeyboardButton(text="🎥 إنشاء فيديو", callback_data="new_video")],
        [InlineKeyboardButton(text="⭐ رصيدي اليومي", callback_data="daily_balance")],
        [InlineKeyboardButton(text="💎 ترقية Premium", callback_data="premium")]
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
    await callback.message.edit_text("🎨 اكتب وصف الصورة اللي تبغاها (بالعربي تماماً)")

@dp.message(F.text)
async def handle_prompt(message: types.Message):
    if message.text.startswith('/'):
        return

    prompt = message.text.strip()
    if len(prompt) < 5:
        await message.answer("اكتب وصف أطول شوي يا وحش 😅")
        return

    user_last_prompt[message.from_user.id] = prompt

    msg = await message.answer("⏳ جاري توليد الصورة... 🔥")
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
            reply_markup=image_action_keyboard(prompt)
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:200]}")

@dp.callback_query(F.data == "regenerate")
async def regenerate(callback: CallbackQuery):
    user_id = callback.from_user.id
    prompt = user_last_prompt.get(user_id)
    if not prompt:
        await callback.answer("❌ انتهت الجلسة", show_alert=True)
        return

    msg = await callback.message.answer("🔄 جاري إعادة التوليد...")
    try:
        response = await client.images.generate(model="grok-imagine-image", prompt=prompt, n=1)
        image_url = response.data[0].url
        await msg.edit_text("✅ تم التوليد!")
        await callback.message.answer_photo(
            image_url,
            caption=f"🎨 تم بنجاح (إعادة توليد)!\nPrompt: {prompt}",
            reply_markup=image_action_keyboard(prompt)
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:150]}")

@dp.callback_query(F.data == "edit_this")
async def edit_this(callback: CallbackQuery):
    await callback.answer("📸 ارفع الصورة الآن + اكتب في الكابشن:\nedit: وصف التعديل", show_alert=True)

@dp.callback_query(F.data == "to_video")
async def to_video(callback: CallbackQuery):
    await callback.answer("🎥 تحويل إلى فيديو قريباً إن شاء الله 🔥", show_alert=True)

@dp.callback_query(F.data == "upscale")
async def upscale(callback: CallbackQuery):
    await callback.answer("⬆️ تحسين الجودة قريباً إن شاء الله 🔥", show_alert=True)

@dp.callback_query(F.data == "save")
async def save(callback: CallbackQuery):
    await callback.answer("❤️ تم الحفظ في المفضلة!", show_alert=True)

@dp.callback_query(F.data == "share")
async def share(callback: CallbackQuery):
    await callback.answer("📤 تم مشاركة الصورة!", show_alert=True)

@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text("🏠 القائمة الرئيسية", reply_markup=main_menu())

@dp.message(F.photo)
async def handle_edit_photo(message: types.Message):
    if message.caption and ("edit" in message.caption.lower() or "تعديل" in message.caption):
        edit_text = message.caption.lower().replace("edit:", "").replace("تعديل:", "").strip() or "حسن الصورة"
        prompt = f"Edit this image: {edit_text}"
        msg = await message.answer("🖌️ جاري التعديل...")
        try:
            response = await client.images.generate(model="grok-imagine-image", prompt=prompt, n=1)
            image_url = response.data[0].url
            await msg.edit_text("✅ تم التعديل!")
            await message.answer_photo(image_url, caption=f"🖌️ تم التعديل!\n{edit_text}", reply_markup=image_action_keyboard(edit_text))
        except Exception as e:
            await msg.edit_text(f"❌ خطأ: {str(e)[:150]}")
    else:
        await message.answer("📸 ارفع الصورة + اكتب في الكابشن:\nedit: وصف التعديل")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())