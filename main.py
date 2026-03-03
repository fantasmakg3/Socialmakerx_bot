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
user_waiting_for_edit = {}

# ==================== KEYBOARDS ====================
def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼️ إنشاء / تعديل صور", callback_data="image_menu")],
        [InlineKeyboardButton(text="🎥 إنشاء فيديو", callback_data="new_video")],
        [InlineKeyboardButton(text="👤 حساب المستخدم", callback_data="user_account")],
        [InlineKeyboardButton(text="💎 ترقية الحساب", callback_data="premium")],
        [
            InlineKeyboardButton(text="🇸🇦 عربي", callback_data="lang_ar"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ]
    ])
    return kb

def image_submenu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 إنشاء صورة جديدة", callback_data="new_image")],
        [InlineKeyboardButton(text="🖌️ تعديل صورة", callback_data="edit_image")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="main_menu")]
    ])
    return kb

def image_action_keyboard(prompt: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 توليد جديد بنفس الوصف", callback_data="regenerate")],
        [InlineKeyboardButton(text="⬆️ تحسين الجودة", callback_data="upscale")],
        [
            InlineKeyboardButton(text="❤️ حفظ", callback_data="save"),
            InlineKeyboardButton(text="📤 مشاركة", callback_data="share")
        ],
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

@dp.callback_query(F.data == "image_menu")
async def image_menu(callback: CallbackQuery):
    await callback.message.edit_text("🖼️ اختر الخدمة:", reply_markup=image_submenu())

@dp.callback_query(F.data == "new_image")
async def new_image(callback: CallbackQuery):
    await callback.message.edit_text("🎨 اكتب وصف الصورة اللي تبغاها (بالعربي تماماً)")

@dp.callback_query(F.data == "edit_image")
async def edit_image(callback: CallbackQuery):
    user_waiting_for_edit[callback.from_user.id] = True
    await callback.message.answer("📸 ارفع الصورة اللي تبغى تعدلها + اكتب في الكابشن وصف التعديل\nمثال: edit: حولها لأنمي")

@dp.message(F.text)
async def handle_text(message: types.Message):
    user_id = message.from_user.id

    # وضع التعديل
    if user_waiting_for_edit.get(user_id, False):
        edit_desc = message.text.strip()
        msg = await message.answer("🖌️ جاري تعديل الصورة...")
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
                reply_markup=image_action_keyboard(edit_desc)
            )
            user_waiting_for_edit[user_id] = False
        except Exception as e:
            await msg.edit_text(f"❌ خطأ: {str(e)[:150]}")
            user_waiting_for_edit[user_id] = False
        return

    # توليد صورة عادية
    prompt = message.text.strip()
    if len(prompt) < 5:
        await message.answer("اكتب وصف أطول شوي يا وحش 😅")
        return

    user_last_prompt[user_id] = prompt

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