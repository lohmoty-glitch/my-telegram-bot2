# -*- coding: utf-8 -*-
import telebot
from telebot import apihelper
import subprocess
import os
import sys
import pyautogui
import psutil
import webbrowser
import datetime
import time
import ctypes
import platform
import io
import threading
import cv2
import numpy as np
import pyperclip
from PIL import Image, ImageGrab
import requests
import random
import string

# =============== НАСТРОЙКИ ===============
TOKEN = "8543792830:AAF1S5OYXzPMIUesRMbI6l8rPtcOJy5J5D0"  # Ваш токен
YOUR_CHAT_ID = 6266098974  # Ваш ID

# Увеличиваем таймауты для всех запросов
apihelper.READ_TIMEOUT = 120
apihelper.CONNECT_TIMEOUT = 120

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Глобальные переменные для состояний
recording = False
recording_thread = None
timers = {}
active_downloads = {}

# =============== ПРОВЕРКА АВТОРИЗАЦИИ ===============
def is_authorized(message):
    """Проверяет, авторизован ли пользователь"""
    return message.chat.id == YOUR_CHAT_ID

# =============== КОМАНДА СТАРТ ===============
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_authorized(message):
        bot.reply_to(message, "❌ Извините, вы не авторизованы для управления этим компьютером.")
        return
    
    welcome_text = """
🤖 **Добро пожаловать в PC Controller Bot!**

Я помогу вам управлять компьютером удаленно через Telegram.

📋 **Основные команды:**
/help - показать все команды
/menu - показать меню управления
/myid - показать ваш Chat ID

⚡ **Быстрые команды:**
🔹 /screenshot - сделать скриншот
🔹 /webcam - фото с веб-камеры
🔹 /lock - заблокировать экран
🔹 /shutdown - выключить ПК

_Отправьте /help для полного списка команд_
    """
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

# =============== КОМАНДА MYID ===============
@bot.message_handler(commands=['myid'])
def show_my_id(message):
    bot.reply_to(message, f"🆔 Ваш Chat ID: `{message.chat.id}`", parse_mode='Markdown')

# =============== КОМАНДА HELP ===============
@bot.message_handler(commands=['help'])
def send_help(message):
    if not is_authorized(message):
        return
    
    help_text = """
📚 **ПОЛНЫЙ СПИСОК КОМАНД**

🔹 **Управление питанием:**
/shutdown - выключить через 30 сек
/shutdown_now - выключить СЕЙЧАС
/restart - перезагрузить
/lock - заблокировать экран
/sleep - спящий режим

🔹 **Таймеры:**
/timer [мин] - установить таймер выключения
/cancel_timer - отменить таймер

🔹 **Экран и камера:**
/screenshot - сделать скриншот
/webcam - фото с веб-камеры
/start_recording - начать запись экрана
/stop_recording - остановить запись

🔹 **Звук:**
/volume_up - увеличить громкость
/volume_down - уменьшить громкость
/volume_mute - выключить звук
/volume_set [0-100] - установить громкость

🔹 **Медиа:**
/media_play - play/pause
/media_next - следующий трек
/media_prev - предыдущий трек

🔹 **Браузер и интернет:**
/browser - открыть браузер
/url [ссылка] - открыть сайт
/wifi_on - включить Wi-Fi
/wifi_off - выключить Wi-Fi
/wifi_status - статус Wi-Fi

🔹 **Файлы:**
/list_dir [путь] - список файлов
/download [путь] - скачать файл
/get_clip - получить буфер обмена
/set_clip [текст] - установить текст в буфер

🔹 **Программы:**
/run [путь] - запустить программу
/ps - список процессов
/kill [имя] - завершить процесс
/top - топ процессов по CPU

🔹 **Система:**
/info - информация о системе
/status - состояние системы
/monitor - детальный мониторинг
/battery - состояние батареи
/uptime - время работы

🔹 **Управление:**
/cmd [команда] - выполнить команду
/notify [текст] - уведомление на ПК
/say [текст] - озвучить текст

🔹 **Прочее:**
/menu - показать меню
/hide_menu - скрыть меню
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# =============== МЕНЮ ===============
@bot.message_handler(commands=['menu'])
def show_menu(message):
    if not is_authorized(message):
        return
    
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Создаем кнопки по категориям
    btn_screen = telebot.types.KeyboardButton('📸 Скриншот')
    btn_webcam = telebot.types.KeyboardButton('📷 Веб-камера')
    btn_record = telebot.types.KeyboardButton('🎥 Запись экрана')
    
    btn_media = telebot.types.KeyboardButton('🎵 Медиа')
    btn_volume_up = telebot.types.KeyboardButton('🔊 Громкость +')
    btn_volume_down = telebot.types.KeyboardButton('🔉 Громкость -')
    btn_mute = telebot.types.KeyboardButton('🔇 Без звука')
    
    btn_files = telebot.types.KeyboardButton('📁 Файлы')
    btn_clip = telebot.types.KeyboardButton('📋 Буфер')
    btn_notify = telebot.types.KeyboardButton('🔔 Уведомление')
    btn_say = telebot.types.KeyboardButton('🗣 Озвучить')
    
    btn_wifi = telebot.types.KeyboardButton('📶 Wi-Fi')
    btn_timer = telebot.types.KeyboardButton('⏰ Таймер')
    btn_monitor = telebot.types.KeyboardButton('📊 Монитор')
    btn_battery = telebot.types.KeyboardButton('🔋 Батарея')
    
    btn_lock = telebot.types.KeyboardButton('🔒 Блокировка')
    btn_shutdown = telebot.types.KeyboardButton('⏻ Выключить')
    btn_restart = telebot.types.KeyboardButton('🔄 Перезагрузить')
    
    btn_hide = telebot.types.KeyboardButton('❌ Скрыть меню')
    
    markup.add(btn_screen, btn_webcam, btn_record)
    markup.add(btn_media, btn_volume_up, btn_volume_down, btn_mute)
    markup.add(btn_files, btn_clip, btn_notify, btn_say)
    markup.add(btn_wifi, btn_timer, btn_monitor, btn_battery)
    markup.add(btn_lock, btn_shutdown, btn_restart)
    markup.add(btn_hide)
    
    bot.send_message(message.chat.id, "📱 **Расширенное меню управления:**", reply_markup=markup, parse_mode='Markdown')

# =============== ОБРАБОТКА КНОПОК МЕНЮ ===============
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if not is_authorized(message):
        return
    
    text = message.text
    
    if text == '📸 Скриншот':
        make_screenshot(message)
    elif text == '📷 Веб-камера':
        take_webcam_photo(message)
    elif text == '🎥 Запись экрана':
        bot.send_message(message.chat.id, "Используйте /start_recording для начала и /stop_recording для остановки")
    elif text == '🎵 Медиа':
        media_control_menu(message)
    elif text == '🔊 Громкость +':
        volume_up(message)
    elif text == '🔉 Громкость -':
        volume_down(message)
    elif text == '🔇 Без звука':
        volume_mute(message)
    elif text == '📁 Файлы':
        bot.send_message(message.chat.id, "Используйте /list_dir [путь] для просмотра файлов")
    elif text == '📋 Буфер':
        get_clipboard(message)
    elif text == '🔔 Уведомление':
        bot.send_message(message.chat.id, "Отправьте /notify [текст]")
    elif text == '🗣 Озвучить':
        bot.send_message(message.chat.id, "Отправьте /say [текст]")
    elif text == '📶 Wi-Fi':
        wifi_status(message)
    elif text == '⏰ Таймер':
        bot.send_message(message.chat.id, "Отправьте /timer [минуты]")
    elif text == '📊 Монитор':
        monitor_system(message)
    elif text == '🔋 Батарея':
        battery_info(message)
    elif text == '🔒 Блокировка':
        lock_computer(message)
    elif text == '⏻ Выключить':
        shutdown_computer(message)
    elif text == '🔄 Перезагрузить':
        restart_computer(message)
    elif text == '❌ Скрыть меню':
        hide_menu(message)

# =============== УПРАВЛЕНИЕ ПИТАНИЕМ ===============
@bot.message_handler(commands=['shutdown'])
def shutdown_computer(message):
    if not is_authorized(message):
        return
    bot.reply_to(message, "⏻ Компьютер будет выключен через 30 секунд.")
    os.system("shutdown /s /t 30")

@bot.message_handler(commands=['shutdown_now'])
def shutdown_now(message):
    if not is_authorized(message):
        return
    bot.reply_to(message, "⏻ Выключаю компьютер...")
    os.system("shutdown /s /t 5")

@bot.message_handler(commands=['restart'])
def restart_computer(message):
    if not is_authorized(message):
        return
    bot.reply_to(message, "🔄 Перезагружаю компьютер...")
    os.system("shutdown /r /t 10")

@bot.message_handler(commands=['sleep'])
def sleep_computer(message):
    if not is_authorized(message):
        return
    bot.reply_to(message, "😴 Перевод компьютер в спящий режим...")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

@bot.message_handler(commands=['lock'])
def lock_computer(message):
    if not is_authorized(message):
        return
    ctypes.windll.user32.LockWorkStation()
    bot.reply_to(message, "🔒 Экран заблокирован")

# =============== ТАЙМЕРЫ ===============
@bot.message_handler(commands=['timer'])
def set_timer(message):
    if not is_authorized(message):
        return
    try:
        minutes = int(message.text.split()[1])
        chat_id = message.chat.id
        
        def shutdown_after_timer():
            bot.send_message(chat_id, f"⏰ Таймер истек! Выключаю компьютер...")
            os.system("shutdown /s /t 10")
        
        timer = threading.Timer(minutes * 60, shutdown_after_timer)
        timer.start()
        timers[chat_id] = timer
        bot.reply_to(message, f"⏰ Таймер установлен на {minutes} минут")
    except:
        bot.reply_to(message, "❌ Используйте: /timer [минуты]")

@bot.message_handler(commands=['cancel_timer'])
def cancel_timer(message):
    if not is_authorized(message):
        return
    if message.chat.id in timers:
        timers[message.chat.id].cancel()
        del timers[message.chat.id]
        bot.reply_to(message, "✅ Таймер отменен")
    else:
        bot.reply_to(message, "❌ Нет активных таймеров")

# =============== СКРИНШОТЫ ===============
@bot.message_handler(commands=['screenshot'])
def make_screenshot(message):
    if not is_authorized(message):
        return
    
    try:
        status_msg = bot.reply_to(message, "📸 Делаю скриншот...")
        
        # Захватываем экран
        screenshot = pyautogui.screenshot()
        
        # Уменьшаем размер
        width, height = screenshot.size
        if width > 1280:
            new_width = 1280
            new_height = int(height * (1280 / width))
            screenshot = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Сохраняем в буфер
        img_buffer = io.BytesIO()
        screenshot.convert('RGB').save(img_buffer, format='JPEG', quality=70, optimize=True)
        img_buffer.seek(0)
        
        # Отправляем
        bot.send_photo(
            message.chat.id,
            img_buffer,
            timeout=120
        )
        
        bot.delete_message(message.chat.id, status_msg.message_id)
        img_buffer.close()
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# =============== ВЕБ-КАМЕРА ===============
@bot.message_handler(commands=['webcam'])
def take_webcam_photo(message):
    if not is_authorized(message):
        return
    
    try:
        status_msg = bot.reply_to(message, "📷 Делаю фото с веб-камеры...")
        
        # Пробуем разные индексы камер (0, 1, -1)
        cap = None
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                break
            cap.release()
        
        if cap and cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Конвертируем BGR в RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                
                # Уменьшаем размер
                img.thumbnail((800, 600))
                
                # Сохраняем в буфер
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=80)
                img_buffer.seek(0)
                
                # Отправляем
                bot.send_photo(message.chat.id, img_buffer, caption="📷 Фото с веб-камеры")
                img_buffer.close()
                bot.delete_message(message.chat.id, status_msg.message_id)
            else:
                bot.reply_to(message, "❌ Не удалось получить изображение с камеры")
        else:
            bot.reply_to(message, "❌ Веб-камера не найдена или занята другим приложением")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")



# =============== ЗАПИСЬ ЭКРАНА ===============
@bot.message_handler(commands=['start_recording'])
def start_recording(message):
    global recording, recording_thread
    
    if not is_authorized(message):
        return
    
    if not recording:
        recording = True
        bot.reply_to(message, "🎥 Начинаю запись экрана... Используйте /stop_recording чтобы остановить")
        
        def record_screen():
            # Создаем локальную копию состояния записи
            is_recording = True
            
            try:
                # Получаем размер экрана
                screen = pyautogui.size()
                
                # Уменьшаем разрешение для записи
                target_size = (1280, 720)
                
                # Настройки записи
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter('screen_record.mp4', fourcc, 10.0, target_size)
                
                # Используем локальную переменную для проверки состояния
                while is_recording and recording:
                    # Захват экрана
                    img = pyautogui.screenshot()
                    
                    # Уменьшаем размер
                    img = img.resize(target_size, Image.Resampling.LANCZOS)
                    
                    # Конвертируем в numpy array
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Записываем кадр
                    out.write(frame)
                    time.sleep(0.1)  # 10 FPS
                
                out.release()
                
            except Exception as e:
                print(f"Ошибка записи: {e}")
        
        recording_thread = threading.Thread(target=record_screen)
        recording_thread.start()
    else:
        bot.reply_to(message, "❌ Запись уже идет")

@bot.message_handler(commands=['stop_recording'])
def stop_recording(message):
    global recording
    
    if not is_authorized(message):
        return
    
    if recording:
        recording = False
        bot.reply_to(message, "⏹ Запись остановлена, отправляю файл...")
        
        # Ждем завершения записи
        time.sleep(2)
        
        if os.path.exists('screen_record.mp4'):
            try:
                with open('screen_record.mp4', 'rb') as video:
                    bot.send_video(
                        message.chat.id, 
                        video, 
                        caption="🎥 Запись экрана",
                        timeout=180,
                        supports_streaming=True
                    )
                os.remove('screen_record.mp4')
            except Exception as e:
                bot.reply_to(message, f"❌ Ошибка при отправке: {e}")
        else:
            bot.reply_to(message, "❌ Файл записи не найден")
    else:
        bot.reply_to(message, "❌ Запись не активна")

# =============== УПРАВЛЕНИЕ ГРОМКОСТЬЮ ===============
@bot.message_handler(commands=['volume_up'])
def volume_up(message):
    if not is_authorized(message):
        return
    try:
        pyautogui.press('volumeup', presses=5)
        bot.reply_to(message, "🔊 Громкость увеличена")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['volume_down'])
def volume_down(message):
    if not is_authorized(message):
        return
    try:
        pyautogui.press('volumedown', presses=5)
        bot.reply_to(message, "🔊 Громкость уменьшена")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['volume_mute'])
def volume_mute(message):
    if not is_authorized(message):
        return
    try:
        pyautogui.press('volumemute')
        bot.reply_to(message, "🔇 Звук выключен")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['volume_set'])
def volume_set(message):
    if not is_authorized(message):
        return
    try:
        level = int(message.text.split()[1])
        level = max(0, min(level, 100))
        # Примерная имитация установки уровня громкости
        presses = level // 10
        pyautogui.press('volumedown', presses=50)  # Сначала убавляем
        pyautogui.press('volumeup', presses=presses)  # Потом прибавляем до нужного уровня
        bot.reply_to(message, f"🔊 Громкость установлена на {level}%")
    except:
        bot.reply_to(message, "❌ Используйте: /volume_set [0-100]")

# =============== УПРАВЛЕНИЕ МЕДИА ===============
@bot.message_handler(commands=['media_play'])
def media_play(message):
    if not is_authorized(message):
        return
    pyautogui.press('playpause')
    bot.reply_to(message, "⏯ Play/Pause")

@bot.message_handler(commands=['media_next'])
def media_next(message):
    if not is_authorized(message):
        return
    pyautogui.press('nexttrack')
    bot.reply_to(message, "⏭ Следующий трек")

@bot.message_handler(commands=['media_prev'])
def media_prev(message):
    if not is_authorized(message):
        return
    pyautogui.press('prevtrack')
    bot.reply_to(message, "⏮ Предыдущий трек")

def media_control_menu(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn_play = telebot.types.InlineKeyboardButton("⏯", callback_data="media_play")
    btn_next = telebot.types.InlineKeyboardButton("⏭", callback_data="media_next")
    btn_prev = telebot.types.InlineKeyboardButton("⏮", callback_data="media_prev")
    markup.row(btn_prev, btn_play, btn_next)
    bot.send_message(message.chat.id, "🎵 Управление медиа:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "media_play":
        pyautogui.press('playpause')
        bot.answer_callback_query(call.id, "Play/Pause")
    elif call.data == "media_next":
        pyautogui.press('nexttrack')
        bot.answer_callback_query(call.id, "Следующий трек")
    elif call.data == "media_prev":
        pyautogui.press('prevtrack')
        bot.answer_callback_query(call.id, "Предыдущий трек")

# =============== БРАУЗЕР ===============
@bot.message_handler(commands=['browser'])
def open_browser(message):
    if not is_authorized(message):
        return
    webbrowser.open('https://www.google.com')
    bot.reply_to(message, "🌐 Браузер открыт")

@bot.message_handler(commands=['url'])
def open_url(message):
    if not is_authorized(message):
        return
    try:
        url = message.text.split()[1]
        if not url.startswith('http'):
            url = 'https://' + url
        webbrowser.open(url)
        bot.reply_to(message, f"🌐 Открываю: {url}")
    except:
        bot.reply_to(message, "❌ Используйте: /url [ссылка]")

# =============== УПРАВЛЕНИЕ WI-FI ===============
@bot.message_handler(commands=['wifi_status'])
def wifi_status(message):
    if not is_authorized(message):
        return
    try:
        # Используем utf-8 кодировку для результата
        result = subprocess.check_output(
            "netsh wlan show interfaces", 
            shell=True, 
            text=True, 
            encoding='cp866',  # Для русской Windows
            errors='ignore'
        )
        
        if "состояние" in result.lower() or "state" in result.lower():
            bot.send_message(message.chat.id, f"📊 **Статус Wi-Fi:**\n```\n{result[:2000]}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Wi-Fi не подключен или отключен")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# =============== ФАЙЛОВЫЙ МЕНЕДЖЕР ===============
@bot.message_handler(commands=['list_dir'])
def list_directory(message):
    if not is_authorized(message):
        return
    
    try:
        # Получаем путь из сообщения или используем корень C:
        parts = message.text.split(maxsplit=1)
        path = parts[1] if len(parts) > 1 else 'C:\\'
        
        # Убираем лишние кавычки и скобки
        path = path.strip('"').strip("'").strip('[]')
        
        if not os.path.exists(path):
            bot.reply_to(message, f"❌ Путь не существует: {path}")
            return
        
        files = os.listdir(path)
        
        # Разделяем на папки и файлы
        folders = []
        files_list = []
        
        for f in sorted(files)[:50]:  # Ограничиваем до 50 элементов
            try:
                full_path = os.path.join(path, f)
                if os.path.isdir(full_path):
                    folders.append(f)
                else:
                    # Добавляем размер файла
                    size = os.path.getsize(full_path)
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024**2:
                        size_str = f"{size/1024:.1f} KB"
                    elif size < 1024**3:
                        size_str = f"{size/1024**2:.1f} MB"
                    else:
                        size_str = f"{size/1024**3:.1f} GB"
                    files_list.append(f"{f} ({size_str})")
            except:
                continue
        
        # Формируем ответ
        response = f"📁 **Папки в {path}:**\n"
        response += "\n".join(["📂 " + f for f in folders[:15]])
        response += f"\n\n📄 **Файлы (первые 15):**\n"
        response += "\n".join(["📄 " + f for f in files_list[:15]])
        
        if len(folders) > 15 or len(files_list) > 15:
            response += f"\n\n... и еще {len(folders)-15 if len(folders)>15 else 0} папок, {len(files_list)-15 if len(files_list)>15 else 0} файлов"
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['download'])
def download_file(message):
    if not is_authorized(message):
        return
    
    try:
        file_path = message.text.replace('/download', '').strip()
        file_path = file_path.strip('"').strip("'")
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Проверяем размер файла
            file_size = os.path.getsize(file_path) / (1024*1024)  # в МБ
            
            if file_size > 50:  # Если файл больше 50 МБ
                bot.reply_to(message, f"❌ Файл слишком большой ({file_size:.1f} МБ). Максимальный размер 50 МБ")
                return
            
            with open(file_path, 'rb') as f:
                bot.send_document(
                    message.chat.id, 
                    f, 
                    caption=f"📎 {os.path.basename(file_path)}",
                    timeout=180
                )
        else:
            bot.reply_to(message, f"❌ Файл не найден: {file_path}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# =============== БУФЕР ОБМЕНА ===============
@bot.message_handler(commands=['get_clip'])
def get_clipboard(message):
    if not is_authorized(message):
        return
    
    try:
        text = pyperclip.paste()
        if text:
            if len(text) > 4000:
                text = text[:4000] + "..."
            bot.send_message(message.chat.id, f"📋 **Содержимое буфера:**\n```\n{text}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "📋 Буфер обмена пуст")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['set_clip'])
def set_clipboard(message):
    if not is_authorized(message):
        return
    
    try:
        text = message.text.replace('/set_clip', '').strip()
        if text:
            pyperclip.copy(text)
            bot.reply_to(message, f"✅ Текст скопирован в буфер: {text[:50]}...")
        else:
            bot.reply_to(message, "❌ Введите текст для копирования")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# =============== ПРОГРАММЫ И ПРОЦЕССЫ ===============
@bot.message_handler(commands=['run'])
def run_program(message):
    if not is_authorized(message):
        return
    try:
        program = message.text.replace('/run', '').strip()
        if program:
            os.startfile(program)
            bot.reply_to(message, f"✅ Запущено: {program}")
        else:
            bot.reply_to(message, "❌ Укажите путь к программе")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['ps'])
def list_processes(message):
    if not is_authorized(message):
        return
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(f"{proc.info['pid']}: {proc.info['name']} (CPU: {proc.info['cpu_percent']}%, MEM: {proc.info['memory_percent']:.1f}%)")
            except:
                pass
        
        proc_text = "\n".join(processes[:30])
        bot.send_message(message.chat.id, f"📋 **Процессы (первые 30):**\n{proc_text}", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['kill'])
def kill_process(message):
    if not is_authorized(message):
        return
    try:
        name = message.text.replace('/kill', '').strip()
        killed = False
        
        for proc in psutil.process_iter(['pid', 'name']):
            if name.lower() in proc.info['name'].lower():
                proc.terminate()
                killed = True
        
        if killed:
            bot.reply_to(message, f"✅ Процесс(ы) '{name}' завершены")
        else:
            bot.reply_to(message, f"❌ Процесс '{name}' не найден")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['top'])
def top_processes(message):
    if not is_authorized(message):
        return
    
    try:
        processes = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'mem': proc.info['memory_percent']
                })
            except:
                pass
        
        # Сортируем по CPU
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        
        top_text = "🔥 **Топ процессов по CPU:**\n"
        for i, p in enumerate(processes[:10], 1):
            top_text += f"{i}. {p['name']}: {p['cpu']:.1f}% CPU, {p['mem']:.1f}% MEM\n"
        
        bot.send_message(message.chat.id, top_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# =============== СИСТЕМНАЯ ИНФОРМАЦИЯ ===============
@bot.message_handler(commands=['info'])
def system_info(message):
    if not is_authorized(message):
        return
    
    try:
        uname = platform.uname()
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')
        
        info_text = f"""
💻 **ИНФОРМАЦИЯ О СИСТЕМЕ**

**Система:** {uname.system} {uname.release}
**Версия:** {uname.version}
**Имя ПК:** {uname.node}
**Процессор:** {cpu_count} ядер
**Частота CPU:** {cpu_freq.current:.2f} МГц
**ОЗУ всего:** {ram.total / (1024**3):.1f} ГБ
**ОЗУ доступно:** {ram.available / (1024**3):.1f} ГБ
**Диск C: всего:** {disk.total / (1024**3):.1f} ГБ
**Диск C: свободно:** {disk.free / (1024**3):.1f} ГБ
        """
        
        bot.send_message(message.chat.id, info_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['status'])
def system_status(message):
    if not is_authorized(message):
        return
    
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('C:\\').percent
        
        cpu_bar = '█' * int(cpu / 10) + '░' * (10 - int(cpu / 10))
        ram_bar = '█' * int(ram / 10) + '░' * (10 - int(ram / 10))
        disk_bar = '█' * int(disk / 10) + '░' * (10 - int(disk / 10))
        
        status_text = f"""
📊 **СОСТОЯНИЕ СИСТЕМЫ**

⚙️ **CPU:** {cpu_bar} {cpu}%
📝 **RAM:** {ram_bar} {ram}%
💾 **Disk:** {disk_bar} {disk}%
        """
        
        bot.send_message(message.chat.id, status_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['monitor'])
def monitor_system(message):
    if not is_authorized(message):
        return
    
    try:
        # Собираем данные
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq().current
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')
        
        # Сетевые соединения
        connections = len(psutil.net_connections())
        
        # Активные пользователи
        users = len(psutil.users())
        
        monitor_text = f"""
📊 **ДЕТАЛЬНЫЙ МОНИТОРИНГ**

**CPU:** {cpu_percent}% ({cpu_freq:.1f} МГц)
**RAM:** {ram.percent}% ({ram.used / 1024**3:.1f}/{ram.total / 1024**3:.1f} ГБ)
**Диск C:** {disk.percent}% ({disk.free / 1024**3:.1f} ГБ свободно)
**Сетевых соединений:** {connections}
**Активных пользователей:** {users}
        """
        
        bot.send_message(message.chat.id, monitor_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['battery'])
def battery_info(message):
    if not is_authorized(message):
        return
    
    try:
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = "Да" if battery.power_plugged else "Нет"
            
            bar = '█' * int(percent / 10) + '░' * (10 - int(percent / 10))
            
            batt_text = f"""
🔋 **СОСТОЯНИЕ БАТАРЕИ**

{bar} {percent}%
**Зарядка:** {plugged}
            """
            
            bot.send_message(message.chat.id, batt_text, parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Батарея не обнаружена")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['uptime'])
def uptime_info(message):
    if not is_authorized(message):
        return
    
    try:
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        current_time = datetime.datetime.now()
        uptime = current_time - boot_time
        
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        uptime_text = f"""
⏱ **ВРЕМЯ РАБОТЫ**

**Система работает:** {days}д {hours}ч {minutes}м
**Включен:** {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        bot.send_message(message.chat.id, uptime_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# =============== УВЕДОМЛЕНИЯ ===============
@bot.message_handler(commands=['notify'])
def send_notification(message):
    if not is_authorized(message):
        return
    
    try:
        text = message.text.replace('/notify', '').strip()
        if text:
            # Используем системное уведомление через PowerShell
            ps_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            $notify = New-Object System.Windows.Forms.NotifyIcon
            $notify.Icon = [System.Drawing.SystemIcons]::Information
            $notify.BalloonTipTitle = "Уведомление от Telegram"
            $notify.BalloonTipText = "{text}"
            $notify.Visible = $True
            $notify.ShowBalloonTip(5000)
            '''
            
            with open('notify.ps1', 'w', encoding='utf-8') as f:
                f.write(ps_script)
            
            subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'notify.ps1'], capture_output=True)
            os.remove('notify.ps1')
            
            bot.reply_to(message, "✅ Уведомление отправлено на ПК")
        else:
            bot.reply_to(message, "❌ Введите текст уведомления. Пример: /notify Привет!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# =============== TTS (ОЗВУЧКА) ===============
@bot.message_handler(commands=['say'])
def text_to_speech(message):
    if not is_authorized(message):
        return
    
    try:
        text = message.text.replace('/say', '').strip()
        if text:
            # Используем PowerShell для TTS
            ps_script = f'''
            Add-Type -AssemblyName System.Speech
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $synth.Speak("{text}")
            '''
            
            with open('speak.ps1', 'w', encoding='utf-8') as f:
                f.write(ps_script)
            
            subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'speak.ps1'], capture_output=True)
            os.remove('speak.ps1')
            
            bot.reply_to(message, f"🔊 Сказано: {text[:50]}...")
        else:
            bot.reply_to(message, "❌ Введите текст для озвучки. Пример: /say Привет!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# =============== КОМАНДЫ В ТЕРМИНАЛЕ ===============
@bot.message_handler(commands=['cmd'])
def run_command(message):
    if not is_authorized(message):
        return
    
    try:
        command = message.text.replace('/cmd', '').strip()
        if command:
            result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT, timeout=30)
            
            if len(result) > 4000:
                result = result[:4000] + "...\n(сообщение обрезано)"
            
            bot.reply_to(message, f"✅ **Результат:**\n```\n{result}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Введите команду")
    except subprocess.TimeoutExpired:
        bot.reply_to(message, "❌ Команда выполнялась слишком долго")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# =============== СКРЫТЬ МЕНЮ ===============
@bot.message_handler(commands=['hide_menu'])
def hide_menu(message):
    if not is_authorized(message):
        return
    
    hide_markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "✅ Меню скрыто. Используйте /menu чтобы показать снова", reply_markup=hide_markup)

# =============== ОБРАБОТКА НЕИЗВЕСТНЫХ КОМАНД ===============
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if not is_authorized(message):
        return
    bot.reply_to(message, "❌ Неизвестная команда. Используйте /help")

# =============== ЗАПУСК БОТА ===============
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 TELEGRAM PC CONTROLLER BOT - РАСШИРЕННАЯ ВЕРСИЯ")
    print("=" * 50)
    print(f"✅ Бот запущен!")
    print(f"🔑 Ваш Chat ID: {YOUR_CHAT_ID}")
    print("=" * 50)
    print("📋 Загруженные модули:")
    print("   ✓ Управление питанием")
    print("   ✓ Таймеры")
    print("   ✓ Скриншоты")
    print("   ✓ Веб-камера")
    print("   ✓ Запись экрана")
    print("   ✓ Управление громкостью")
    print("   ✓ Медиа-контроль")
    print("   ✓ Wi-Fi управление")
    print("   ✓ Файловый менеджер")
    print("   ✓ Буфер обмена")
    print("   ✓ Мониторинг системы")
    print("   ✓ Уведомления")
    print("   ✓ TTS озвучка")
    print("=" * 50)
    
    # Бесконечный цикл работы бота
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)
async def main():
    """Запуск бота с веб-хуками для Render"""
    
    # Создаем приложение бота (без Updater)
    application = Application.builder().token(TOKEN).updater(None).build()
    
    # Регистрируем обработчики команд
    # ВАЖНО: Здесь нужно добавить обработчики для всех ваших команд!
    # Это пример, вам нужно добавить все свои:
    application.add_handler(CommandHandler("start", send_welcome))
    application.add_handler(CommandHandler("help", send_help))
    application.add_handler(CommandHandler("menu", show_menu))
    application.add_handler(CommandHandler("myid", show_my_id))
    # ... и так далее для всех команд
    
    # Обработчик для обычных сообщений (кнопки меню)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    
    # Устанавливаем веб-хук
    webhook_url = f"{RENDER_EXTERNAL_URL}/telegram"
    await application.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
    logging.info(f"Webhook установлен на {webhook_url}")
    
    # Создаем Starlette приложение для приема веб-хуков
    async def telegram(request: Request) -> Response:
        """Обработчик веб-хуков от Telegram"""
        try:
            data = await request.json()
            update = Update.de_json(data, application.bot)
            await application.update_queue.put(update)
            return Response()
        except Exception as e:
            logging.error(f"Ошибка обработки веб-хука: {e}")
            return Response(status_code=500)
    
    async def health(request: Request) -> PlainTextResponse:
        """Health check для Render"""
        return PlainTextResponse("OK")
    
    async def root(request: Request) -> PlainTextResponse:
        """Корневой endpoint"""
        return PlainTextResponse("Bot is running!")
    
    # Настраиваем маршруты
    starlette_app = Starlette(routes=[
        Route("/telegram", telegram, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
        Route("/healthcheck", health, methods=["GET"]),
        Route("/", root, methods=["GET"]),
    ])
    
    # Запускаем
    server = uvicorn.Server(
        uvicorn.Config(
            app=starlette_app,
            host="0.0.0.0",
            port=PORT,
            log_level="info"
        )
    )
    
    async with application:
        await application.start()
        await server.serve()
        await application.stop()

# =============== ЗАПУСК ===============
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 TELEGRAM PC CONTROLLER BOT - RENDER EDITION")
    print("=" * 50)
    print(f"✅ Бот запускается...")
    print(f"🔑 Chat ID: {YOUR_CHAT_ID}")
    print(f"🌐 Webhook URL: {RENDER_EXTERNAL_URL}/telegram")
    print("=" * 50)
    
    asyncio.run(main())
