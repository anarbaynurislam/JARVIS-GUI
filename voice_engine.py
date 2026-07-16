import os
import time
import asyncio
import edge_tts
import pygame

VOICE = "ru-RU-DmitryNeural" 

def stop_speaking():
    """Мгновенно останавливает воспроизведение только голоса, не трогая музыку."""
    try:
        if pygame.mixer.get_init():
            # Останавливаем все каналы, кроме музыки (музыка играет на отдельном системном канале)
            pygame.mixer.stop() 
    except Exception as e:
        print(f"[Ошибка остановки голоса]: {e}")

def speak(text: str):
    """Генерирует голос, используя выделенный канал микшера."""
    if not text.strip():
        return

    clean_text = text.replace("===", "").replace("---", "").replace("*", "").replace("🤖", "").strip()
    
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    unique_id = int(time.time() * 1000)
    filename = os.path.join(CURRENT_DIR, f"jarvis_voice_{unique_id}.mp3")
    
    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed(): raise RuntimeError
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        communicate = edge_tts.Communicate(clean_text, VOICE, rate="+10%", pitch="-2Hz")
        loop.run_until_complete(communicate.save(filename))
        
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
            
        try:
            voice_sound = pygame.mixer.Sound(filename)
            # Явно запрашиваем свободный канал
            voice_channel = pygame.mixer.find_channel(force=True)
            if voice_channel:
                voice_channel.play(voice_sound)
                while voice_channel.get_busy():
                    time.sleep(0.05)
        except Exception as play_err:
            print(f"[Ошибка воспроизведения голоса]: {play_err}")
        
        # Пробуем удалить файл. Если занят — его подчистит clean_voice_cache() при старте/выходе
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except:
            pass
            
    except Exception as e:
        print(f"[Ошибка голосового движка]: {e}")