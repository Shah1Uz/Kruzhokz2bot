#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import time
import tempfile
import json
from pathlib import Path
import telebot
from telebot import types
import logging
from models import (
    create_tables, 
    save_user_history, 
    get_user_history, 
    get_total_user_kruzhoks,
    set_user_language,
    get_user_language
)

# Environment variables are handled by Replit automatically

# DATABASE_URL ni tekshirish
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# BOT_TOKEN ni olish
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Admin ID
ADMIN_ID = 5615887242

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Botni ishga tushirish
bot = telebot.TeleBot(BOT_TOKEN)

# ⬇️ Shu yerga qolgan bot kodlaringizni yozasiz

# User state management
user_states = {}
user_media_files = {}

# Effect names mapping
EFFECT_NAMES = {
    1: "Oddiy",
    2: "Zoom", 
    3: "Blur",
    4: "Rang o'zgarishi",
    5: "Aylanish"
}

# Multi-language messages
MESSAGES = {
    'uz': {
        'welcome': """👋 Salom, {}!
① Video yoki rasm yuboring.
② Effektni tanlang.
③ Doira tayyor ✔️

Tezkor buyruqlar:
♻️ Botni qayta ishga tushirish: /start
🗂 Oxirgi videolarni ko'rish: /history
❓ Muallifni yashirish: /hide
🌐 Tilni o'zgartirish: /lang""",
        
        'processing': "⏳ Ishlov berilmoqda...",
        'success': "✅ Tayyor! Sizning doiraviy videongiz:",
        'error': "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
        'unsupported': "❌ Qo'llab-quvvatlanmaydigan fayl turi. Faqat video yoki rasm yuboring.",
        'choose_effect': "🎨 Quyidagi effektlardan birini tanlang:",
        'effect_processing': "🎬 Effekt qo'llanmoqda...",
        'history_header': "🗂 Oxirgi kruzhok videolaringiz:",
        'history_empty': "📭 Hali kruzhok yaratmagansiz. Video yoki rasm yuboring!",
        'history_count': "📊 Jami yaratilgan kruzhoklar: {count} ta",
        'lang_selection': "🌐 Quyidagi tillardan birini tanlang:",
        'language_set': "✅ Til o'zbekchaga o'rnatildi!"
    },
    'ru': {
        'welcome': """👋 Привет, {}!
① Отправьте видео или фото.
② Выберите эффект.
③ Кружок готов ✔️

Быстрые команды:
♻️ Перезапустить бота: /start
🗂 Посмотреть последние видео: /history
❓ Скрыть автора: /hide
🌐 Изменить язык: /lang""",
        
        'processing': "⏳ Обрабатывается...",
        'success': "✅ Готово! Ваше круглое видео:",
        'error': "❌ Произошла ошибка. Попробуйте еще раз.",
        'unsupported': "❌ Неподдерживаемый тип файла. Отправьте только видео или фото.",
        'choose_effect': "🎨 Выберите один из следующих эффектов:",
        'effect_processing': "🎬 Применяется эффект...",
        'history_header': "🗂 Ваши последние кружки:",
        'history_empty': "📭 Вы еще не создали кружки. Отправьте видео или фото!",
        'history_count': "📊 Всего создано кружков: {count} шт.",
        'lang_selection': "🌐 Выберите один из следующих языков:",
        'language_set': "✅ Язык установлен на русский!"
    },
    'en': {
        'welcome': """👋 Hello, {}!
① Send a video or photo.
② Choose an effect.
③ Circle ready ✔️

Quick commands:
♻️ Restart bot: /start
🗂 View recent videos: /history
❓ Hide author: /hide
🌐 Change language: /lang""",
        
        'processing': "⏳ Processing...",
        'success': "✅ Done! Your circular video:",
        'error': "❌ An error occurred. Please try again.",
        'unsupported': "❌ Unsupported file type. Send video or photo only.",
        'choose_effect': "🎨 Choose one of the following effects:",
        'effect_processing': "🎬 Applying effect...",
        'history_header': "🗂 Your recent circles:",
        'history_empty': "📭 You haven't created any circles yet. Send a video or photo!",
        'history_count': "📊 Total circles created: {count}",
        'lang_selection': "🌐 Choose one of the following languages:",
        'language_set': "✅ Language set to English!"
    }
}

def is_admin(user_id):
    """Check if user is admin"""
    return user_id == ADMIN_ID

def get_user_messages(user_id):
    """Get messages in user's preferred language"""
    lang = get_user_language(user_id)
    return MESSAGES.get(lang, MESSAGES['uz'])

def create_language_keyboard():
    """Create inline keyboard for language selection"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbek tili", callback_data="lang_uz")
    btn_ru = types.InlineKeyboardButton("🇷🇺 Русский язык", callback_data="lang_ru") 
    btn_en = types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
    
    markup.add(btn_uz, btn_ru, btn_en)
    return markup

def create_effect_keyboard():
    """Create inline keyboard for effect selection"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Create buttons for each effect
    btn1 = types.InlineKeyboardButton("📹 Oddiy", callback_data="effect_1")
    btn2 = types.InlineKeyboardButton("🔍 Zoom", callback_data="effect_2")
    btn3 = types.InlineKeyboardButton("🌫️ Blur", callback_data="effect_3")
    btn4 = types.InlineKeyboardButton("🌈 Rang", callback_data="effect_4")
    btn5 = types.InlineKeyboardButton("🔄 Aylanish", callback_data="effect_5")
    
    # Add buttons to markup
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)
    
    return markup

def create_temp_file(suffix=""):
    """Create a temporary file and return its path"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.close()
    return temp_file.name

def cleanup_file(file_path):
    """Safely delete a file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {e}")

def get_video_duration(input_path):
    """Get video duration using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', input_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        return duration
    except Exception as e:
        logger.error(f"Error getting video duration: {e}")
        return 10.0  # Default fallback

def process_video_to_kruzhok(input_path, output_path, effect_type=1):
    """Convert video to circular kruzhok format using ffmpeg with effects"""
    try:
        # Get video info first
        duration = get_video_duration(input_path)
        
        # Limit duration to 60 seconds for kruzhok
        duration = min(duration, 60.0)
        
        # Define video filter based on effect type
        if effect_type == 1:  # Oddiy dumaloq video
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,format=yuv420p'
        elif effect_type == 2:  # Zoom effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,zoompan=z=\'min(zoom+0.0015,1.5)\':d=1:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2),format=yuv420p'
        elif effect_type == 3:  # Blur effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,gblur=sigma=2:steps=1,format=yuv420p'
        elif effect_type == 4:  # Rang o'zgarishi effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,hue=h=sin(2*PI*t)*360:s=1.5,format=yuv420p'
        elif effect_type == 5:  # Aylanish effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,rotate=PI*t/5,format=yuv420p'
        else:
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,format=yuv420p'
        
        # FFmpeg command to create circular video with effects
        cmd = [
            'ffmpeg', '-y',  # Overwrite output file
            '-i', input_path,
            '-t', str(duration),  # Limit duration
            '-vf', video_filter,
            '-c:v', 'libx264',  # Video codec
            '-c:a', 'aac',      # Audio codec
            '-b:a', '128k',     # Audio bitrate
            '-ar', '44100',     # Audio sample rate
            '-ac', '2',         # Audio channels
            '-preset', 'fast',  # Encoding preset
            '-crf', '23',       # Quality setting
            output_path
        ]
        
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Video processing completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        return False

def process_photo_to_kruzhok(input_path, output_path, effect_type=1):
    """Convert photo to 5-second circular kruzhok with effects"""
    try:
        # Define video filter based on effect type
        if effect_type == 1:  # Oddiy dumaloq video
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,format=yuv420p'
        elif effect_type == 2:  # Zoom effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,zoompan=z=\'min(zoom+0.002,1.8)\':d=1:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2),format=yuv420p'
        elif effect_type == 3:  # Blur effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,gblur=sigma=3:steps=2,format=yuv420p'
        elif effect_type == 4:  # Rang o'zgarishi effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,hue=h=sin(2*PI*t/3)*180:s=1.3,format=yuv420p'
        elif effect_type == 5:  # Aylanish effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,rotate=PI*t/3,format=yuv420p'
        else:
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,format=yuv420p'
        
        # FFmpeg command to create 5-second circular video from image with effects
        cmd = [
            'ffmpeg', '-y',  # Overwrite output file
            '-loop', '1',    # Loop the input image
            '-i', input_path,
            '-t', '5',       # 5 seconds duration
            '-vf', video_filter,
            '-c:v', 'libx264',  # Video codec
            '-pix_fmt', 'yuv420p',
            '-r', '25',         # Frame rate
            '-preset', 'fast',  # Encoding preset
            '-crf', '23',       # Quality setting
            output_path
        ]
        
        logger.info(f"Running ffmpeg command for photo: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Photo processing completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error for photo: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command - show language selection for new users"""
    user_id = message.from_user.id
    
    # Log admin access
    if is_admin(user_id):
        logger.info(f"Admin {user_id} started the bot")
    
    # Always show language selection first for /start command
    markup = create_language_keyboard()
    bot.reply_to(message, "🌐 Tilni tanlang / Выберите язык / Choose language:", reply_markup=markup)

@bot.message_handler(commands=['hide'])
def send_hide_info(message):
    """Handle /hide command"""
    messages = get_user_messages(message.from_user.id)
    bot.reply_to(message, messages.get('hide_info', 'Info not available'))

@bot.message_handler(commands=['lang'])
def send_lang_selection(message):
    """Handle /lang command - show language selection"""
    messages = get_user_messages(message.from_user.id)
    markup = create_language_keyboard()
    bot.reply_to(message, messages['lang_selection'], reply_markup=markup)

@bot.message_handler(commands=['admin'])
def handle_admin_command(message):
    """Handle /admin command - admin only functions"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        bot.reply_to(message, "❌ Siz admin emassiz / You are not admin")
        return
    
    # Admin statistics
    try:
        from models import SessionLocal, UserHistory, UserLanguage
        session = SessionLocal()
        
        total_users = session.query(UserLanguage).count()
        total_kruzhoks = session.query(UserHistory).count()
        
        admin_text = f"""👑 Admin Panel

📊 Statistika:
👥 Jami foydalanuvchilar: {total_users}
🎬 Jami kruzhoklar: {total_kruzhoks}

🛠 Admin buyruqlari:
/stats - Batafsil statistika
/broadcast - Xabar yuborish"""
        
        bot.reply_to(message, admin_text)
        session.close()
        
    except Exception as e:
        logger.error(f"Error in admin command: {e}")
        bot.reply_to(message, "❌ Xatolik yuz berdi")

@bot.message_handler(commands=['stats'])
def handle_stats_command(message):
    """Handle /stats command - detailed statistics for admin"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        return
    
    try:
        from models import SessionLocal, UserHistory, UserLanguage
        from sqlalchemy import func
        session = SessionLocal()
        
        # Get user count by language
        lang_stats = session.query(
            UserLanguage.language_code, 
            func.count(UserLanguage.id)
        ).group_by(UserLanguage.language_code).all()
        
        # Get effect usage stats
        effect_stats = session.query(
            UserHistory.effect_name,
            func.count(UserHistory.id)
        ).group_by(UserHistory.effect_name).all()
        
        stats_text = "📊 Batafsil Statistika:\n\n"
        
        stats_text += "🌐 Tillar bo'yicha:\n"
        for lang, count in lang_stats:
            lang_name = {"uz": "O'zbek", "ru": "Rus", "en": "Ingliz"}.get(lang, lang)
            stats_text += f"  {lang_name}: {count}\n"
        
        stats_text += "\n🎨 Effektlar bo'yicha:\n"
        for effect, count in effect_stats:
            stats_text += f"  {effect}: {count}\n"
        
        bot.reply_to(message, stats_text)
        session.close()
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        bot.reply_to(message, "❌ Xatolik yuz berdi")

@bot.message_handler(commands=['history'])
def send_history(message):
    """Handle /history command - show user's recent kruzhok videos"""
    try:
        user_id = message.from_user.id
        messages = get_user_messages(user_id)
        history = get_user_history(user_id, limit=10)
        total_count = get_total_user_kruzhoks(user_id)
        
        if not history:
            bot.reply_to(message, messages['history_empty'])
            return
        
        # Send header message
        header_text = f"{messages['history_header']}\n{messages['history_count'].format(count=total_count)}"
        bot.reply_to(message, header_text)
        
        # Send each kruzhok from history
        for item in history:
            try:
                # Create caption with effect info
                caption = f"🎨 {item.effect_name} | 📅 {item.created_at.strftime('%d.%m.%Y %H:%M')}"
                
                # Send the kruzhok video_note
                bot.send_video_note(
                    message.chat.id,
                    item.file_id,
                    caption=caption if len(caption) <= 1024 else ""  # Telegram caption limit
                )
            except Exception as e:
                logger.error(f"Error sending history item {item.id}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error handling history command: {e}")
        messages = get_user_messages(message.from_user.id)
        bot.reply_to(message, messages['error'])

@bot.message_handler(content_types=['video'])
def handle_video(message):
    """Handle video messages"""
    try:
        user_id = message.from_user.id
        
        # Get file info
        file_info = bot.get_file(message.video.file_id)
        
        # Create temporary file
        input_file = create_temp_file(suffix='.mp4')
        
        # Download the video
        downloaded_file = bot.download_file(file_info.file_path)
        with open(input_file, 'wb') as f:
            f.write(downloaded_file)
        
        # Store user media file and set state
        user_media_files[user_id] = {
            'file_path': input_file,
            'media_type': 'video',
            'duration': message.video.duration or 10
        }
        user_states[user_id] = 'choosing_effect'
        
        # Send effect selection menu with inline keyboard
        messages = get_user_messages(user_id)
        markup = create_effect_keyboard()
        bot.reply_to(message, messages['choose_effect'], reply_markup=markup)
            
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        messages = get_user_messages(message.from_user.id)
        bot.reply_to(message, messages['error'])

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Handle photo messages"""
    try:
        user_id = message.from_user.id
        
        # Get the largest photo size
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        
        # Create temporary file
        input_file = create_temp_file(suffix='.jpg')
        
        # Download the photo
        downloaded_file = bot.download_file(file_info.file_path)
        with open(input_file, 'wb') as f:
            f.write(downloaded_file)
        
        # Store user media file and set state
        user_media_files[user_id] = {
            'file_path': input_file,
            'media_type': 'photo',
            'duration': 5
        }
        user_states[user_id] = 'choosing_effect'
        
        # Send effect selection menu with inline keyboard
        messages = get_user_messages(user_id)
        markup = create_effect_keyboard()
        bot.reply_to(message, messages['choose_effect'], reply_markup=markup)
            
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        messages = get_user_messages(message.from_user.id)
        bot.reply_to(message, messages['error'])

@bot.message_handler(content_types=['document', 'audio', 'voice', 'sticker'])
def handle_unsupported(message):
    """Handle unsupported file types"""
    messages = get_user_messages(message.from_user.id)
    bot.reply_to(message, messages['unsupported'])

@bot.callback_query_handler(func=lambda call: call.data.startswith('effect_'))
def handle_effect_callback(call):
    """Handle inline button callbacks for effect selection"""
    try:
        user_id = call.from_user.id
        effect_type = int(call.data.split('_')[1])
        
        # Answer callback to remove loading state
        bot.answer_callback_query(call.id)
        
        # Process media with selected effect
        process_media_with_effect_callback(call, effect_type)
        
    except Exception as e:
        logger.error(f"Error handling effect callback: {e}")
        bot.answer_callback_query(call.id, text="❌ Xatolik yuz berdi")

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_language_callback(call):
    """Handle language selection callbacks"""
    try:
        user_id = call.from_user.id
        lang_code = call.data.split('_')[1]  # Extract 'uz', 'ru', or 'en'
        
        # Set user language
        set_user_language(
            user_id=user_id,
            username=call.from_user.username,
            first_name=call.from_user.first_name,
            language_code=lang_code
        )
        
        # Get messages in new language
        messages = get_user_messages(user_id)
        
        # Answer callback and show success message
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            messages['language_set'],
            call.message.chat.id,
            call.message.message_id
        )
        
        # Send welcome message in new language
        user_name = call.from_user.first_name or "User"
        welcome_text = messages['welcome'].format(user_name)
        bot.send_message(call.message.chat.id, welcome_text)
        
    except Exception as e:
        logger.error(f"Error handling language callback: {e}")
        bot.answer_callback_query(call.id, text="❌ Error")

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """Handle all text messages"""
    # Default welcome message in user's language
    messages = get_user_messages(message.from_user.id)
    user_name = message.from_user.first_name or "User"
    welcome_text = messages['welcome'].format(user_name)
    bot.reply_to(message, welcome_text)

def process_media_with_effect_callback(call, effect_type):
    """Process stored media with selected effect from callback"""
    user_id = call.from_user.id
    
    try:
        messages = get_user_messages(user_id)
        
        if user_id not in user_media_files:
            bot.edit_message_text(messages['error'], call.message.chat.id, call.message.message_id)
            return
        
        # Edit message to show processing
        bot.edit_message_text(messages['effect_processing'], call.message.chat.id, call.message.message_id)
        
        media_info = user_media_files[user_id]
        input_file = media_info['file_path']
        output_file = create_temp_file(suffix='.mp4')
        
        # Process based on media type
        success = False
        if media_info['media_type'] == 'video':
            success = process_video_to_kruzhok(input_file, output_file, effect_type)
        elif media_info['media_type'] == 'photo':
            success = process_photo_to_kruzhok(input_file, output_file, effect_type)
        
        if success:
            # Send the kruzhok
            with open(output_file, 'rb') as video:
                sent_message = bot.send_video_note(
                    call.message.chat.id,
                    video,
                    duration=media_info['duration'],
                    length=480  # Circular video diameter
                )
            
            # Save to history
            effect_name = EFFECT_NAMES.get(effect_type, f"Effekt {effect_type}")
            file_size = os.path.getsize(output_file) if os.path.exists(output_file) else None
            
            save_user_history(
                user_id=user_id,
                username=call.from_user.username,
                first_name=call.from_user.first_name,
                file_id=sent_message.video_note.file_id,
                original_media_type=media_info['media_type'],
                effect_type=effect_type,
                effect_name=effect_name,
                file_size=file_size
            )
            
            # Delete processing message
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(
                messages['error'],
                call.message.chat.id,
                call.message.message_id
            )
        
        # Clean up
        cleanup_file(input_file)
        cleanup_file(output_file)
        
        # Clear user state
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_media_files:
            del user_media_files[user_id]
            
    except Exception as e:
        logger.error(f"Error processing media with effect: {e}")
        messages = get_user_messages(user_id)
        bot.edit_message_text(messages['error'], call.message.chat.id, call.message.message_id)
        
        # Clear user state on error
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_media_files:
            cleanup_file(user_media_files[user_id]['file_path'])
            del user_media_files[user_id]

def main():
    """Main function to start the bot"""
    logger.info("Starting Kruzhok Bot...")
    
    # Initialize database
    try:
        create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logger.info("FFmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("FFmpeg is not available. Please install ffmpeg.")
        return
    
    # Start polling
    try:
        logger.info("Bot is starting to poll...")
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == '__main__':
    main()
