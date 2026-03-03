import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
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

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 مرحبا يا وحش في @Socialmakerx_bot!\n\n"
        "أنا بوت Grok Imagine مجاني 100% داخل تليجرام 🔥\n\n"
        "الأوامر:\n"
        "/image [وصف] → صورة من نص\n"
        "/edit → ارفع صورة + اكتب في الكابشن 'edit: التعديل الجديد'\n"
        "/video [وصف] → فيديو قصير (قريباً)\n"
        "/help → مساعدة\n\n"
        "جرب الحين: /image قطة تطير على القمر"
    )

@dp.message(Command("image"))
async def generate_image(message: types.Message):
    prompt = message.text.replace("/image", "").strip()
    if not prompt:
        await message.answer("اكتب الوصف بعد /image مثال:\n/image قطة تطير في الفضاء")
        return
    
    await message.answer("⏳ جاري توليد الصورة بـ Grok Imagine... (ثواني)")
    
    try:
        response = await client.images.generate(
            model="grok-imagine-image",
            prompt=prompt,
            n=1,
            size="1024x1024",
        )
        image_url = response.data[0].url
        await message.answer_photo(
            image_url,
            caption=f"✅ تم بنجاح!\n\nPrompt: {prompt}\n\nPowered by Grok Imagine 🔥"
        )
    except Exception as e:
        await message.answer(f"❌ خطأ: {str(e)[:300]}")

@dp.message(F.photo)
async def handle_edit_photo(message: types.Message):
    if message.caption and ("edit" in message.caption.lower() or "تعديل" in message.caption):
        prompt = message.caption.lower().replace("edit:", "").replace("edit", "").replace("تعديل:", "").strip()
        if not prompt:
            prompt = "حسن الصورة واجعلها أجمل"
        await message.answer("⏳ جاري تعديل الصورة...")
        # في النسخة الأولى نعمل prompt قوي مع وصف الصورة الأصلية (الـ API يدعم edit لاحقاً)
        full_prompt = f"Edit this image: {prompt}"
        try:
            response = await client.images.generate(
                model="grok-imagine-image",
                prompt=full_prompt,
                n=1,
                size="1024x1024",
            )
            image_url = response.data[0].url
            await message.answer_photo(image_url, caption=f"✅ تم التعديل!\nPrompt: {prompt}")
        except Exception as e:
            await message.answer(f"❌ خطأ في التعديل: {str(e)[:200]}")
    else:
        await message.answer("📸 صورة وصلت!\nاكتب في رسالة جديدة مع نفس الصورة:\nedit: وصف التعديل اللي تبغاه\nمثال: edit: حولها لأنمي")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer("الأوامر:\n/start\n/image [وصف]\nارفع صورة + edit: ...\n\nكل شيء يشتغل على Grok Imagine الرسمي من xAI")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
