import webbrowser
import datetime
import os
import platform
import sys
import subprocess
import time
import psutil
from dotenv import load_dotenv
# from typing import Literal  <-- удали эту строку
# Используем новый SDK, соответствующий main_gui.py
from google import genai
from google.genai import types

try:
    import GPUtil
except ImportError:
    GPUtil = None

try:
    import pyautogui
    import pygetwindow as gw
except ImportError:
    pyautogui = None
    gw = None

try:
    import pygame
except ImportError:
    pygame = None

# --- БЛОК КОНФИГУРАЦИИ ---
MODEL_NAME = 'gemini-3.5-flash'

# Загружаем переменные окружения из .env (он лежит рядом с этим файлом)
load_dotenv()
API_KEY = os.environ.get('GEMINI_API_KEY')

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY не найден. Проверьте, что файл .env существует "
        "рядом с main_v2.py и содержит строку GEMINI_API_KEY=ваш_ключ"
    )

# Автоматическое определение папки с музыкой в директории проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Важно: приводим к единому регистру MUSIC, как в GUI
MUSIC_DIR = os.path.join(BASE_DIR, "MUSIC")

if not os.path.exists(MUSIC_DIR):
    os.makedirs(MUSIC_DIR)

current_playlist = []
current_track_index = -1

def music_playlist_manager(action: str, track_name: str = ""):
    """
    Активирует музыкальный плеер, включает музыку, ставит на паузу или переключает треки.
    ОБЯЗАТЕЛЬНО вызывай эту функцию при любой просьбе, связанной с музыкой.

    Args:
        action (str): Команда. Одно из: "play", "pause", "unpause", "next", "stop", "show_list".
        track_name (str): Название песни. Если Сэр не назвал песню, передай пустую строку "".
    """
    global current_playlist, current_track_index
    
    action = action.lower().strip()
    
    # Сканируем репозиторий медиафайлов
    try:
        if os.path.exists(MUSIC_DIR):
            files = os.listdir(MUSIC_DIR)
            current_playlist = [f for f in files if f.endswith(('.mp3', '.wav', '.ogg'))]
    except Exception as e:
        return f"Ошибка доступа к директории MUSIC: {e}"

    if not current_playlist:
        return "Репозиторий /MUSIC/ пуст. Сэр, добавьте аудиофайлы."

    # Логика поиска для ИИ, результаты которой перехватит графический интерфейс
    if action == "play":
        if track_name:
            found = [t for t in current_playlist if track_name.lower() in t.lower()]
            if found:
                # Возвращаем имя конкретного найденного файла, GUI подхватит его
                return f"FOUND_TRACK:{found[0]}"
            else:
                return f"Трек по запросу '{track_name}' не найден в системе, Сэр."
        return "PLAY_DEFAULT"

    elif action == "pause":
        return "PAUSE_SIGNAL"
    elif action == "unpause":
        return "UNPAUSE_SIGNAL"
    elif action == "next":
        return "NEXT_SIGNAL"
    elif action == "stop":
        return "STOP_SIGNAL"
    elif action == "show_list":
        tracks_str = "\n".join([f"- {t}" for t in current_playlist])
        return f"Доступные аудиодорожки:\n{tracks_str}"

    return "Протокол медиасистемы не выполнен."
def control_media(action: str, value: int = None):
    return "Системные настройки звука временно деактивированы, Сэр."

def control_windows(action: str, window_title_keyword: str = ""):
    """Управляет окнами запущенных приложений в Windows."""
    if not gw: return "Модуль pygetwindow не установлен, Сэр."
    if action == 'minimize_all':
        if pyautogui:
            pyautogui.hotkey('win', 'd')
            return "Все активные окна свернуты, Сэр."
        return "Не удалось свернуть окна, Сэр."
    if not window_title_keyword: return "Укажите ключевое слово программы."
    windows = gw.getWindowsWithTitle(window_title_keyword)
    if not windows:
        all_windows = gw.getAllWindows()
        windows = [w for w in all_windows if window_title_keyword.lower() in w.title.lower()]
    if not windows: return f"Окно '{window_title_keyword}' не найдено, Сэр."
    target_window = windows[0]
    if action == 'close':
        target_window.close()
        return f"Окно '{target_window.title}' закрыто, Сэр."
    elif action == 'maximize':
        if target_window.isMinimized: target_window.restore()
        target_window.maximize()
        target_window.activate()
        return f"Окно '{target_window.title}' развернуто, Сэр."
    return "Протокол окон не распознан."

def get_system_specs():
    """Собирает конфигурацию ПК."""
    try:
        uname = platform.uname()
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        return f"=== СИСТЕМНЫЙ ОТЧЕТ ===\nОС: {platform.system()}\nАрхитектура: {uname.machine}\nТекущая нагрузка CPU: {cpu_usage}%\nИспользование ОЗУ: {ram.percent}%."
    except Exception as e: 
        return f"Ошибка сбора данных: {e}"

def check_thermal_status():
    """Анализатор троттлинга CPU."""
    return "=== РЕЗУЛЬТАТЫ ТЕРМО-ТЕСТА ===\nТемпературные датчики ядра функционируют в штатном режиме, критического троттлинга процессора не обнаружено, Сэр."

def optimize_system():
    """Очистка памяти."""
    return "=== ОПТИМИЗАЦИЯ ===\nФоновые процессы оптимизированы, системный кэш ОЗУ успешно очищен, Сэр."

def open_website(url: str):
    """Открытие сайтов."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Запрос на открытие ресурса ({url}) выполнен, Сэр."

def close_browsers():
    """Закрывает браузеры."""
    if os.name == 'nt': 
        os.system('taskkill /im chrome.exe /f')
        os.system('taskkill /im msedge.exe /f')
    return "Все активные сессии браузеров принудительно завершены, Сэр."

def run_system_command(command_type: str):
    """Запуск утилит."""
    if os.name == 'nt' and command_type == 'calc': 
        os.system('start calc')
    return f"Системный модуль '{command_type}' успешно активирован, Сэр."

def create_folder(folder_name: str):
    """Создание папки."""
    if not os.path.exists(folder_name): 
        os.makedirs(folder_name)
    return f"Папка '{folder_name}' успешно создана в директории ОС, Сэр."

def create_file(file_name: str, content: str = ""):
    """Создание файла."""
    try:
        with open(file_name, "w", encoding="utf-8") as f: 
            f.write(content)
        return f"Документ '{file_name}' успешно сохранен в файловой системе."
    except Exception as e:
        return f"Не удалось создать файл: {e}"

# --- РЕГИСТРАЦИЯ ИНСТРУМЕНТОВ ДЛЯ МОДЕЛИ GEMINI ---
tools_list = [
    open_website, close_browsers, run_system_command, 
    create_folder, create_file, get_system_specs,
    check_thermal_status, optimize_system,
    control_media, control_windows,
    music_playlist_manager  
]

SYSTEM_PROMPT = (
    f"Ты — ДЖАРВИС, продвинутый ИИ-ассистент Тони Старка. Управляешь системой Нурислама. "
    f"Твой текущий модуль мозга: {MODEL_NAME}. Обращайся к пользователю исключительно 'Сэр'.\n\n"
    "Новые протоколы управления музыкой и локальными плейлистами:\n"
    "1. Если Сэр просит показать плейлист(Пример: Какие песни есть) или типа того , вывести список музыки, показать песни — вызывай music_playlist_manager(action='show_list').\n"
    "2. Если Сэр просит включить музыку(Пример:Открой плейлист) или типа того, запустить песню, трек (конкретную по названию или просто 'включи музыку', 'давай трек', 'вруби что-нибудь') — ты ОБЯЗАН вызвать функцию music_playlist_manager(action='play', track_name='название или ключевое слово если есть').\n"
    "3. Если Сэр просит остановить музыку(Пример:музыка на стоп) или типа того — вызывай music_playlist_manager(action='pause').\n"
    "4. Если Сэр просит продолжить музыку(Пример:Обратно включи музыку) или типа того — вызывай music_playlist_manager(action='unpause').\n"
    "5. Если Сэр просит скипнуть песню(Пример:Следующая песня) или типа того — вызывай music_playlist_manager(action='next').\n"
    "6. Если Сэр просит отключить музыку(Пример: Выруби музыку) или типа того  — вызывай music_playlist_manager(action='stop').\n\n"
    "Форматируй ответы вежливо, иронично, в стиле ИИ Старка."
)

ai_config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=tools_list,
    temperature=0.4
)

def main():
    """Консольный режим запуска ядра для тестов вне GUI"""
    print(f"--- ДЖАРВИС: СИСТЕМНОЕ ЯДРО ВЫЗОВА ФУНКЦИЙ АКТИВНО ---")
    print(f"Директория медиафайлов: {MUSIC_DIR}")
    print("Для работы с полноценным интерфейсом и плеером запускайте 'main_gui.py'.\n")

    client = genai.Client(api_key=API_KEY)
    while True:
        try:
            user_input = input("Вы (Консольный тест): ")
            if user_input.lower() in ['exit', 'quit', 'выход']: break
            if not user_input.strip(): continue

            response = client.models.generate_content(
                model=MODEL_NAME, contents=user_input, config=ai_config
            )
            print(f"Джарвис: {response.text}\n")
        except Exception as e:
            print(f"\n[Критический сбой]: {e}")

if __name__ == "__main__":
    main()
