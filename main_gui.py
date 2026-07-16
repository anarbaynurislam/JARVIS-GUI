import os
import threading
import time
import glob
import customtkinter as ctk
import pygame
from google import genai
from google.genai import types

from voice_engine import speak, stop_speaking 
from main_v2 import (
    get_system_specs, check_thermal_status, optimize_system,
    control_media, control_windows, open_website, close_browsers,
    run_system_command, create_folder, create_file,
    music_playlist_manager,
    tools_list, MODEL_NAME, API_KEY, SYSTEM_PROMPT as BASE_PROMPT
)

ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "jarvis_memory.txt")
MUSIC_DIR = os.path.join(BASE_DIR, "MUSIC")

if not os.path.exists(MUSIC_DIR):
    os.makedirs(MUSIC_DIR)

TOOL_FUNCTIONS = {
    "get_system_specs": get_system_specs,
    "check_thermal_status": check_thermal_status,
    "optimize_system": optimize_system,
    "control_media": control_media,
    "control_windows": control_windows,
    "open_website": open_website,
    "close_browsers": close_browsers,
    "run_system_command": run_system_command,
    "create_folder": create_folder,
    "create_file": create_file,
    "music_playlist_manager": music_playlist_manager,
}

try:
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
except Exception as e:
    print(f"[КРИТИЧЕСКАЯ ОШИБКА ИНИЦИАЛИЗАЦИИ ЗВУКА]: {e}")

def clean_voice_cache():
    try:
        voice_files = glob.glob(os.path.join(BASE_DIR, "jarvis_voice_*.mp3"))
        for file_path in voice_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    continue
    except Exception as e:
        print(f"[ОШИБКА ОЧИСТКИ КЭША ГОЛОСА]: {e}")

clean_voice_cache()

class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("J.A.R.V.I.S. OS - MEDIA HUB")
        self.geometry("1150x760")
        self.minsize(950, 650)
        self.attributes("-alpha", 0.94)

        self.client = genai.Client(api_key=API_KEY)
        
        self.media_hub_active = False  
        self.is_animating = False      
        self.sidebar_containers = []   
        self.current_track = "Не выбрано"
        self._pending_track = None  
        
        self.track_duration = 0.1
        self.current_pos_sec = 0.0
        self.seek_start_time = 0.0   
        self.is_sliding = False

        self.disc_frames = ["◤(●)◢", "◥(●)◤", "◢(●)◣", "◣(●)◥"]
        self.disc_frame_index = 0

        try:
            if not os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, "w", encoding="utf-8") as f: f.write("")
        except Exception as e: print(f"[ОШИБКА ХРАНИЛИЩА ПАМЯТИ]: {e}")

        current_memory = self.read_memory_data()
        
        # ИСПРАВЛЕННЫЙ ПРОМПТ ДЛЯ GUI (СЛИЯНИЕ С БАЗОВЫМ)
        # ИСПРАВЛЕННЫЙ ПРОМПТ ДЛЯ GUI (СЛИЯНИЕ С БАЗОВЫМ)
        self.SYSTEM_PROMPT = (
            f"{BASE_PROMPT}\n\n"
            "--- СТРОГИЕ ПРАВИЛА ИНТЕРФЕЙСА ---\n"
            "1. КРИТИЧЕСКИ ВАЖНО: ЗАПРЕЩЕНО словесно подтверждать действия до их выполнения! Если Сэр просит включить музыку, открыть сайт или выполнить команду — СНАЧАЛА ВЫЗОВИ ФУНКЦИЮ (Tool Call). Никакого текста до вызова функции!\n"
            "2. Пиши текстовый ответ ТОЛЬКО если запрос не требует функций, ИЛИ если функция уже отработала и вернула результат.\n"
            f"=== ТЕКУЩАЯ ПАМЯТЬ ===\n{current_memory}\n"
            "======================\n"
            "3. ФОРМАТ ОТВЕТА: Твой текстовый ответ ВСЕГДА должен содержать [VOICE].\n"
            "ДО маркера [VOICE] — текст для экрана терминала.\n"
            "ПОСЛЕ маркера [VOICE] — короткая фраза для озвучки голосом."
        )
        
        self.ai_config = types.GenerateContentConfig(system_instruction=self.SYSTEM_PROMPT, tools=tools_list, temperature=0.4)

        self.grid_columnconfigure(0, weight=0, minsize=105) 
        self.grid_columnconfigure(1, weight=1)             
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, corner_radius=20, fg_color="#0d0e12", width=105)
        self.sidebar.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        self.sidebar.pack_propagate(False) 
        
        self.logo_btn = ctk.CTkButton(
            self.sidebar, text="⚡", font=ctk.CTkFont(size=26), text_color="#5ce1e6",
            fg_color="transparent", hover_color="#1c222d", width=50, height=50, corner_radius=25,
            command=self.toggle_media_hub
        )
        self.logo_btn.pack(padx=10, pady=20)

        self.create_round_stealth_button("📊", "Статус", "Выведи системный отчет конфигурации") 
        self.create_round_stealth_button("🧠", "Память", "Проведи оптимизацию системы")          
        self.create_round_stealth_button("🔥", "Термо", "Сделай термо-тест процессора")        

        self.chat_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="#050608")
        self.chat_frame.grid(row=0, column=1, padx=12, pady=12, sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)  
        self.chat_frame.grid_rowconfigure(1, weight=0)  
        self.chat_frame.grid_rowconfigure(2, weight=0)  

        self.main_split_frame = ctk.CTkFrame(self.chat_frame, fg_color="#050608")
        self.main_split_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.main_split_frame.grid_columnconfigure(0, weight=1) 
        self.main_split_frame.grid_columnconfigure(1, weight=0, minsize=0) 
        self.main_split_frame.grid_rowconfigure(0, weight=1)

        self.left_workspace = ctk.CTkFrame(self.main_split_frame, fg_color="#050608")
        self.left_workspace.grid(row=0, column=0, sticky="nsew")
        self.left_workspace.grid_columnconfigure(0, weight=1)
        self.left_workspace.grid_rowconfigure(0, weight=0) 
        self.left_workspace.grid_rowconfigure(1, weight=1) 

        self.player_controls_frame = ctk.CTkFrame(self.left_workspace, fg_color="#0d1117", corner_radius=15, border_width=1, border_color="#1f293d")
        self.build_player_interface()

        self.terminal = ctk.CTkTextbox(
            self.left_workspace,
            font=ctk.CTkFont(size=14, family="Consolas"),
            fg_color="#020305",
            text_color="#5ce1e6",
            border_width=0,
            wrap="word",
            activate_scrollbars=True,
        )
        self.terminal.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.terminal.insert("end", ">>> Главные подсистемы MARK-V успешно запущены, Сэр.\n\n")
        self.terminal.configure(state="disabled")

        self.playlist_frame = ctk.CTkFrame(self.main_split_frame, fg_color="#090b11", corner_radius=18, border_width=1, border_color="#1c2333")
        self.build_playlist_interface()

        self.status_bar = ctk.CTkLabel(self.chat_frame, text="[ МАРК-V: МОНИТОР СТАБИЛЕН ]", font=ctk.CTkFont(size=11, family="Consolas", weight="bold"), text_color="#41495d")
        self.status_bar.grid(row=1, column=0, padx=15, pady=2, sticky="w")

        self.entry_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.entry_frame.grid(row=2, column=0, padx=15, pady=12, sticky="ew")
        self.entry_frame.grid_columnconfigure(0, weight=1)

        self.user_input = ctk.CTkEntry(self.entry_frame, placeholder_text="Введите приказ для Джарвиса, Сэр...", font=ctk.CTkFont(size=14), corner_radius=15, height=42)
        self.user_input.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.user_input.bind("<Return>", lambda event: self.send_command()) 

        self.btn_stop = ctk.CTkButton(self.entry_frame, text="🛑", width=42, height=42, corner_radius=21, fg_color="#4d0c0c", hover_color="#731111", command=stop_speaking)
        self.btn_stop.grid(row=0, column=1, padx=(0, 10), sticky="e")

        self.btn_send = ctk.CTkButton(self.entry_frame, text="Запуск", width=95, height=42, corner_radius=12, font=ctk.CTkFont(weight="bold"), command=self.send_command)
        self.btn_send.grid(row=0, column=2, sticky="e")

        self.is_thinking = False
        
        self.protocol("WM_DELETE_WINDOW", self.on_exit_app)
        
        self.update_slider_loop()
        self.update_disc_animation_loop()

        self.after(1000, lambda: threading.Thread(target=lambda: speak("Все системы синхронизированы. Слушаю вас, Сэр."), daemon=True).start())

    def create_round_stealth_button(self, icon, title_text, ai_command):
        container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        container.pack(pady=8, fill="x")
        self.sidebar_containers.append(container)

        btn = ctk.CTkButton(container, text=icon, width=46, height=46, corner_radius=23, font=ctk.CTkFont(size=18), fg_color="transparent", hover_color="#181d26", text_color="#5ce1e6")
        btn.configure(command=lambda: self.animate_and_run(btn, ai_command))
        btn.pack(anchor="center")

        lbl = ctk.CTkLabel(container, text=title_text, font=ctk.CTkFont(size=10, family="Consolas"), text_color="#474f62")
        lbl.pack(pady=(2, 0))

    def build_player_interface(self):
        self.player_controls_frame.grid_columnconfigure(0, weight=1)
        
        self.track_lbl = ctk.CTkLabel(self.player_controls_frame, text="◤(●)◢ СЕЙЧАС ИГРАЕТ: Не выбрано", font=ctk.CTkFont(size=13, family="Consolas", weight="bold"), text_color="#5ce1e6")
        self.track_lbl.grid(row=0, column=0, pady=(12, 4), padx=15, sticky="w")

        slider_layout = ctk.CTkFrame(self.player_controls_frame, fg_color="transparent")
        slider_layout.grid(row=1, column=0, padx=15, pady=4, sticky="ew")
        slider_layout.grid_columnconfigure(1, weight=1)

        self.time_current_lbl = ctk.CTkLabel(slider_layout, text="0:00", font=ctk.CTkFont(size=11, family="Consolas"), text_color="#7e8a9f")
        self.time_current_lbl.grid(row=0, column=0, padx=(0, 8))

        self.audio_slider = ctk.CTkSlider(
            slider_layout, from_=0, to=100, number_of_steps=1000, 
            progress_color="#5ce1e6", button_color="#5ce1e6", button_hover_color="#a3f7f9", 
            fg_color="#282828", height=14, command=self.on_slider_scroll
        )
        self.audio_slider.grid(row=0, column=1, sticky="ew")
        self.audio_slider.set(0)
        
        self.audio_slider.bind("<ButtonPress-1>", self.on_slider_press)
        self.audio_slider.bind("<ButtonRelease-1>", self.on_slider_release)

        self.time_total_lbl = ctk.CTkLabel(slider_layout, text="0:00", font=ctk.CTkFont(size=11, family="Consolas"), text_color="#7e8a9f")
        self.time_total_lbl.grid(row=0, column=2, padx=(8, 0))

        controls = ctk.CTkFrame(self.player_controls_frame, fg_color="transparent")
        controls.grid(row=2, column=0, pady=(4, 12))

        ctk.CTkButton(controls, text="⏮", width=42, height=32, corner_radius=8, fg_color="#1c2331", command=self.prev_track).pack(side="left", padx=6)
        self.master_play_btn = ctk.CTkButton(controls, text="▶ ПАУЗА / СТАРТ", width=130, height=32, corner_radius=8, fg_color="#1c2331", text_color="#5ce1e6", font=ctk.CTkFont(weight="bold"), command=self.toggle_playback)
        self.master_play_btn.pack(side="left", padx=6)
        ctk.CTkButton(controls, text="⏭", width=42, height=32, corner_radius=8, fg_color="#1c2331", command=self.next_track).pack(side="left", padx=6)

    def build_playlist_interface(self):
        self.playlist_frame.grid_columnconfigure(0, weight=1)
        self.playlist_frame.grid_rowconfigure(2, weight=1)

        header = ctk.CTkLabel(self.playlist_frame, text="⚡ Playlist", font=ctk.CTkFont(size=15, weight="bold"), text_color="#5ce1e6")
        header.grid(row=0, column=0, padx=20, pady=(15, 2), sticky="w")
        
        sub_hdr = ctk.CTkLabel(self.playlist_frame, text="Каталог репозитория: /MUSIC/", font=ctk.CTkFont(size=11, family="Consolas"), text_color="#576275")
        sub_hdr.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")

        self.scroll_playlist = ctk.CTkScrollableFrame(self.playlist_frame, fg_color="#050609", corner_radius=12)
        self.scroll_playlist.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.reload_playlist()

    def reload_playlist(self):
        for widget in self.scroll_playlist.winfo_children():
            widget.destroy()

        self.tracks = [f for f in os.listdir(MUSIC_DIR) if f.endswith(('.mp3', '.wav', '.ogg'))]
        
        if not self.tracks:
            empty_lbl = ctk.CTkLabel(self.scroll_playlist, text="Папка MUSIC пуста.\nДобавьте аудиофайлы, Сэр.", font=ctk.CTkFont(size=13), text_color="#41495d")
            empty_lbl.pack(pady=40)
            return

        for index, track in enumerate(self.tracks, start=1):
            track_item = ctk.CTkFrame(self.scroll_playlist, fg_color="transparent", height=42)
            track_item.pack(fill="x", pady=2, padx=5)
            track_item.pack_propagate(False)

            track_item.bind("<Enter>", lambda e, item=track_item: item.configure(fg_color="#121620"))
            track_item.bind("<Leave>", lambda e, item=track_item: item.configure(fg_color="transparent"))

            lbl_num = ctk.CTkLabel(track_item, text=str(index), width=30, text_color="#576275", font=ctk.CTkFont(weight="bold"))
            lbl_num.pack(side="left", padx=5)

            btn_title = ctk.CTkButton(
                track_item, text=track, anchor="w", fg_color="transparent", 
                text_color="#cbd3e0", hover=False, font=ctk.CTkFont(size=13),
                command=lambda t=track: self.play_track(t)
            )
            btn_title.pack(side="left", fill="both", expand=True)

    def play_track(self, track_name):
        self.current_track = track_name
        self.seek_start_time = 0.0
        self.current_pos_sec = 0.0
        
        self.track_lbl.configure(text=f"{self.disc_frames[self.disc_frame_index]} СЕЙЧАС ИГРАЕТ: {track_name}")
        
        full_path = os.path.join(MUSIC_DIR, track_name)
        try:
            snd = pygame.mixer.Sound(full_path)
            self.track_duration = snd.get_length()
            del snd 
        except:
            self.track_duration = 180.0  

        self.audio_slider.configure(from_=0, to=self.track_duration)
        self.audio_slider.set(0)
        
        tot_min, tot_sec = divmod(int(self.track_duration), 60)
        self.time_total_lbl.configure(text=f"{tot_min}:{tot_sec:02d}")
        self.time_current_lbl.configure(text="0:00")

        try:
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Ошибка загрузки трека: {e}")

    def play_back_in_black_automatically(self):
        if hasattr(self, 'tracks') and self.tracks:
            for track in self.tracks:
                if "back in black" in track.lower():
                    self.play_track(track)
                    return
            self.play_track(self.tracks[0])

    def toggle_playback(self):
        try:
            if pygame.mixer.get_init():
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()
                    self.safe_update_status("[ МЕДИАПОТОК: ПАУЗА ]")
                else:
                    pygame.mixer.music.unpause()
                    self.safe_update_status("[ МЕДИАПОТОК: ВОСПРОИЗВЕДЕНИЕ ]")
        except Exception as e:
            print(f"[ОШИБКА КНОПКИ ПЛЕЕРА]: {e}")

    def next_track(self):
        if hasattr(self, 'tracks') and self.tracks and self.current_track in self.tracks:
            idx = self.tracks.index(self.current_track)
            self.play_track(self.tracks[(idx + 1) % len(self.tracks)])

    def prev_track(self):
        if hasattr(self, 'tracks') and self.tracks and self.current_track in self.tracks:
            idx = self.tracks.index(self.current_track)
            self.play_track(self.tracks[(idx - 1) % len(self.tracks)])

    def on_slider_press(self, event):
        self.is_sliding = True

    def on_slider_scroll(self, value):
        cur_min, cur_sec = divmod(int(value), 60)
        self.time_current_lbl.configure(text=f"{cur_min}:{cur_sec:02d}")

    def on_slider_release(self, event):
        if self.current_track != "Не выбрано":
            new_pos = self.audio_slider.get()
            self.seek_start_time = new_pos
            self.current_pos_sec = new_pos
            try:
                pygame.mixer.music.set_pos(new_pos)
            except Exception:
                try:
                    full_path = os.path.join(MUSIC_DIR, self.current_track)
                    pygame.mixer.music.load(full_path)
                    pygame.mixer.music.play(loops=0, start=int(new_pos))
                except Exception as e:
                    print(f"Ошибка перемотки (фоллбэк): {e}")
        self.is_sliding = False

    def update_slider_loop(self):
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                if not self.is_sliding:
                    pos_ms = pygame.mixer.music.get_pos()
                    if pos_ms >= 0:
                        self.current_pos_sec = self.seek_start_time + (pos_ms / 1000.0)
                        if self.current_pos_sec > self.track_duration:
                            self.current_pos_sec = self.track_duration
                        
                        self.audio_slider.set(self.current_pos_sec)
                        cur_min, cur_sec = divmod(int(self.current_pos_sec), 60)
                        self.time_current_lbl.configure(text=f"{cur_min}:{cur_sec:02d}")

                        if self.track_duration > 0 and (self.track_duration - self.current_pos_sec) < 0.6:
                            self.after(200, self.next_track)
        except Exception as e:
            print(f"Ошибка цикла времени: {e}")
        
        self.after(400, self.update_slider_loop)

    def update_disc_animation_loop(self):
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                if self.current_track != "Не выбрано":
                    self.disc_frame_index = (self.disc_frame_index + 1) % len(self.disc_frames)
                    current_frame = self.disc_frames[self.disc_frame_index]
                    self.track_lbl.configure(text=f"{current_frame} СЕЙЧАС ИГРАЕТ: {self.current_track}")
        except Exception as e:
            print(f"Ошибка цикла диска: {e}")
        
        self.after(180, self.update_disc_animation_loop)

    def safe_log_to_terminal(self, sender, text):
        self.after(0, lambda: self._log_to_terminal_main_thread(sender, text))

    def safe_update_status(self, text, color=None):
        if color:
            self.after(0, lambda: self.status_bar.configure(text=text, text_color=color))
        else:
            self.after(0, lambda: self.status_bar.configure(text=text))

    def _log_to_terminal_main_thread(self, sender: str, text: str):
        self.terminal.configure(state="normal")
        self.terminal.insert("end", f"{sender}: {text}\n\n")
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def toggle_media_hub(self):
        if self.is_animating: return
        self.is_animating = True

        if not self.media_hub_active:
            self.media_hub_active = True
            for container in self.sidebar_containers:
                container.pack_forget()
            self.animate_sidebar(105, 65, -4)
        else:
            self.media_hub_active = False
            self.animate_playlist_close(520, 0, -40)

    def animate_sidebar(self, current_width, target_width, step):
        if current_width == target_width:
            self.player_controls_frame.grid(row=0, column=0, padx=12, pady=(10, 5), sticky="ew")
            self.playlist_frame.grid(row=0, column=1, padx=(5, 12), pady=12, sticky="nsew")
            self.reload_playlist()
            if self._pending_track:
                self.play_track(self._pending_track)
                self._pending_track = None
            elif not pygame.mixer.music.get_busy():
                self.play_back_in_black_automatically()
            self.animate_playlist_open(0, 520, 40)
            return
        next_width = current_width + step
        self.sidebar.configure(width=next_width)
        self.grid_columnconfigure(0, minsize=next_width)
        self.after(6, lambda: self.animate_sidebar(next_width, target_width, step))

    def animate_playlist_open(self, current_width, target_width, step):
        if current_width >= target_width:
            self.main_split_frame.grid_columnconfigure(1, weight=2, minsize=380)
            self.is_animating = False
            return
        next_width = current_width + step
        self.main_split_frame.grid_columnconfigure(1, minsize=next_width)
        self.after(6, lambda: self.animate_playlist_open(next_width, target_width, step))

    def animate_playlist_close(self, current_width, target_width, step):
        if current_width <= target_width:
            self.main_split_frame.grid_columnconfigure(1, weight=0, minsize=0)
            self.playlist_frame.grid_forget()
            self.player_controls_frame.grid_forget()
            self.animate_sidebar_expand(65, 105, 4)
            return
        next_width = current_width + step
        self.main_split_frame.grid_columnconfigure(1, minsize=next_width)
        self.after(6, lambda: self.animate_playlist_close(next_width, target_width, step))

    def animate_sidebar_expand(self, current_width, target_width, step):
        if current_width == target_width:
            for container in self.sidebar_containers: container.pack(pady=8, fill="x")
            self.is_animating = False
            return
        next_width = current_width + step
        self.sidebar.configure(width=next_width)
        self.grid_columnconfigure(0, minsize=next_width)
        self.after(6, lambda: self.animate_sidebar_expand(next_width, target_width, step))

    def read_memory_data(self):
        if not os.path.exists(MEMORY_FILE): return "[Блокнот пуст.]"
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return content if content else "[Блокнот пуст.]"
        except: return "[Ошибка доступа]"

    def clear_memory_data(self):
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f: f.write("")
        except Exception as e: print(f"Ошибка очистки: {e}")

    def show_thinking_animation(self, frame_index=0):
        if not self.is_thinking:
            return
        frames = ["▶ [ СИСТЕМА ДУМАЕТ .   ]", "▶ [ СИСТЕМА ДУМАЕТ ..  ]", "▶ [ СИСТЕМА ДУМАЕТ ... ]"]
        current_frame = frames[frame_index % len(frames)]
        self.status_bar.configure(text=current_frame, text_color="#5ce1e6")
        self.after(300, lambda: self.show_thinking_animation(frame_index + 1))

    def send_command(self):
        command = self.user_input.get().strip()
        if not command: return
        self.user_input.delete(0, "end")
        self._log_to_terminal_main_thread("Вы", command)
        
        self.is_thinking = True
        self.show_thinking_animation()
        threading.Thread(target=self.process_ai_response, args=(command,), daemon=True).start()

    def animate_and_run(self, button_widget, ai_command: str):
        def flash():
            button_widget.configure(fg_color="#5ce1e6", text_color="#050608")
            time.sleep(0.18) 
            button_widget.configure(fg_color="transparent", text_color="#5ce1e6")
        threading.Thread(target=flash, daemon=True).start()
        
        self.is_thinking = True
        self.show_thinking_animation()
        threading.Thread(target=self.process_ai_response, args=(ai_command,), daemon=True).start()

    def process_ai_response(self, text_command: str):
        try:
            lower_cmd = text_command.strip().lower()
            
            if any(word in lower_cmd for word in ["очисти память", "сотри память", "очисти блокнот"]):
                self.clear_memory_data()
                self.is_thinking = False
                self.safe_update_status("[ МАРК-V: СТАБИЛЕН ]", "#41495d")
                self.safe_log_to_terminal("Джарвис", "Память блокнота очищена.\n\n[VOICE] Готово, Сэр.")
                speak("Память очищена по вашему приказу, Сэр.")
                return

            response = self.client.models.generate_content(
                model=MODEL_NAME, 
                contents=text_command, 
                config=self.ai_config
            )

            while response.function_calls:
                for call in response.function_calls:
                    func_name = call.name
                    func_args = call.args
                    
                    self.safe_update_status(f"[ АКТИВАЦИЯ МОДУЛЯ: {func_name.upper()} ]", "#5ce1e6")
                    
                    if func_name == "music_playlist_manager":
                        action = func_args.get("action", "")
                        track_name = func_args.get("track_name", None)
                        
                        if not self.media_hub_active and action in ["play", "next", "prev", "unpause", "show_list"]:
                            self.after(0, self.toggle_media_hub)
                        
                        if action == "play":
                            available_tracks = getattr(self, 'tracks', None) or \
                                [f for f in os.listdir(MUSIC_DIR) if f.endswith(('.mp3', '.wav', '.ogg'))]
                            
                            target = None
                            if track_name:
                                matched = [t for t in available_tracks if track_name.lower() in t.lower()]
                                target = matched[0] if matched else None
                            elif not available_tracks:
                                target = None
                            else:
                                target = available_tracks[0] if self.current_track == "Не выбрано" else None
                            
                            if not self.media_hub_active:
                                self._pending_track = target
                                self.after(0, self.toggle_media_hub)
                                result = f"Открываю медиа-хаб и запускаю: {target or 'текущий трек'}"
                            else:
                                if target:
                                    self.after(0, lambda t=target: self.play_track(t))
                                    result = f"Включаю трек: {target}"
                                else:
                                    self.after(0, self.toggle_playback)
                                    result = "Музыкальный плеер MARK-V запущен."
                        elif action == "pause":
                            self.after(0, self.toggle_playback)
                            result = "Музыка поставлена на паузу."
                        elif action == "unpause":
                            self.after(0, self.toggle_playback)
                            result = "Музыка снята с паузы."
                        elif action == "next":
                            self.after(0, self.next_track)
                            result = "Переключаю на следующий медиапоток."
                        elif action == "stop":
                            if self.media_hub_active:
                                self.after(0, self.toggle_media_hub)
                            self.after(0, lambda: pygame.mixer.music.stop())
                            result = "Медиаплеер полностью остановлен."
                        elif action == "show_list":
                            try:
                                all_tracks = [f for f in os.listdir(MUSIC_DIR) if f.endswith(('.mp3', '.wav', '.ogg'))]
                            except Exception:
                                all_tracks = []
                            if all_tracks:
                                if not self.media_hub_active:
                                    self.after(0, self.toggle_media_hub)
                                result = "Плейлист /MUSIC/:\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(all_tracks))
                            else:
                                result = "Папка /MUSIC/ пуста. Добавьте аудиофайлы, Сэр."
                        else:
                            result = "Неизвестное действие с плеером."

                    else:
                        if func_name in TOOL_FUNCTIONS:
                            try:
                                result = TOOL_FUNCTIONS[func_name](**func_args)
                            except Exception as e:
                                result = f"Ошибка выполнения модуля {func_name}: {e}"
                        else:
                            result = f"Системный компонент '{func_name}' не зарегистрирован."
                    
                    response = self.client.models.generate_content(
                        model=MODEL_NAME,
                        contents=[
                            types.Content(role="user", parts=[types.Part.from_text(text=text_command)]),
                            response.candidates[0].content,
                            types.Content(
                                role="tool",
                                parts=[types.Part.from_function_response(name=func_name, response={"result": result})]
                            )
                        ],
                        config=self.ai_config
                    )

            full_response = response.text
            if not full_response:
                full_response = "Системный протокол выполнен. [VOICE] Готово, Сэр."
            self.is_thinking = False
            self.safe_update_status("[ МАРК-V: СТАБИЛЕН ]", "#41495d")
            
            if "[VOICE]" in full_response:
                screen_text, voice_text = full_response.split("[VOICE]", 1)
                screen_text, voice_text = screen_text.strip(), voice_text.strip()
            else:
                screen_text = voice_text = full_response
            
            self.safe_log_to_terminal("Джарвис", screen_text)
            threading.Thread(target=lambda: speak(voice_text), daemon=True).start()

        except Exception as e:
            self.is_thinking = False
            self.safe_update_status("[ СБОЙ ЯДРА ]", "#8a1414")
            self.safe_log_to_terminal("СИСТЕМА", f"Критический сбой синаптической сети: {e}")

    def on_exit_app(self):
        clean_voice_cache()
        self.destroy()

if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()