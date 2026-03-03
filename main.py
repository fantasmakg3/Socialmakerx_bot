import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

client = AsyncOpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

class ImageStates(StatesGroup):
    waiting_for_prompt = State()

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

def aspect_ratio_keyboard(prompt: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬜ 1:1 (مربع)", callback_data=f"ratio:1:1:{prompt}")],
        [InlineKeyboardButton(text="📱 9:16 (ريلز عمودي)", callback_data=f"ratio:9:16:{prompt}")],
        [InlineKeyboardButton(text="🖥️ 16:9 (ريلز أفقي)", callback_data=f"ratio:16:9:{prompt}")],
        [InlineKeyboardButton(text="📲 4:5 (إنستا/فيسبوك)", callback_data=f"ratio:4:5:{prompt}")],
        [InlineKeyboardButton(text="📷 3:2 (كلاسيكي)", callback_data=f"ratio:3:2:{prompt}")],
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

@dp.callback_query(F.data == "new_image")
async def start_image_creation(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🎨 اكتب وصف الصورة اللي تبغاها (بالعربي تماماً)\nمثال: قطة تطير على سطح القمر")
    await state.set_state(ImageStates.waiting_for_prompt)

@dp.message(ImageStates.waiting_for_prompt)
async def receive_prompt(message: types.Message, state: FSMContext):
    prompt = message.text.strip()
    if not prompt:
        await message.answer("اكتب وصف حقيقي يا وحش 😅")
        return

    await message.answer("اختر قياس الصورة 👇", reply_markup=aspect_ratio_keyboard(prompt))
    await state.clear()

@dp.callback_query(F.data.startswith("ratio:"))
async def generate_with_ratio(callback: CallbackQuery):
    _, ratio, prompt = callback.data.split(":", 2)
    
    msg = await callback.message.edit_text(f"⏳ جاري توليد الصورة...\nقياس: {ratio}\nوصف: {prompt[:80]}...")
    
    try:
        response = await client.images.generate(
            model="grok-imagine-image",
            prompt=prompt,
            n=1,
            aspect_ratio=ratio
        )
        image_url = response.data[0].url
        
        await msg.edit_text("✅ تم التوليد!")
        await callback.message.answer_photo(
            image_url,
            caption=f"🎨 تم بنجاح!\nقياس: {ratio}\nPrompt: {prompt}",
            reply_markup=aspect_ratio_keyboard(prompt)  # أزرار جديدة تحت الصورة
        )
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:200]}")

# باقي الأزرار (القديمة) للتوافق
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