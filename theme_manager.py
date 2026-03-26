# theme_manager.py
import os
import json


class ThemeManager:
    """Управление цветами темы с сохранением в файл"""
    _instance = None
    SETTINGS_FILE = "settings.cfg"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_colors()
        return cls._instance

    def __init__(self):
        # Загружаем тему при создании
        self._load_theme()

    def _init_colors(self):
        self.current_theme = 'light'
        self.set_light_theme()

    def _load_theme(self):
        """Загружает тему из файла настроек"""
        try:
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    theme = settings.get('theme', 'light')
                    if theme == 'dark':
                        self.set_dark_theme()
                    else:
                        self.set_light_theme()
                    print(f"🎨 Загружена тема из файла: {theme}")
                    return
            # Если файла нет или нет темы, используем светлую
            self.set_light_theme()
            self._save_theme()  # Создаем файл с настройками по умолчанию
            print("🎨 Создан файл настроек со светлой темой")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки темы: {e}")
            self.set_light_theme()

    def _save_theme(self):
        """Сохраняет тему в файл настроек"""
        try:
            settings = {'theme': self.current_theme}
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            print(f"💾 Тема сохранена в файл: {self.current_theme}")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения темы: {e}")

    def set_light_theme(self):
        self.current_theme = 'light'
        self.main_frame_color = '#FFFFFF'
        self.house_frame_color = '#FFFFFF'
        self.card_body_color = '#F1F3F4'
        self.sidebar_frame_color = '#F1F3F4'
        self.text_color = '#111318'
        self.text_color_secondary = '#6B7280'
        self.secondary_bg = '#F0F0F0'
        self.border_color = '#E5E7EB'
        self.button_primary = '#FF740F'
        self.button_success = '#10B981'
        self.button_info = '#3B82F6'
        self.button_warning = '#F59E0B'
        self.button_danger = '#EF4444'
        self.button_secondary = '#6B7280'
        self.button_purple = '#8B5CF6'
        self.button_blue = '#6366F1'

    def set_dark_theme(self):
        self.current_theme = 'dark'
        self.main_frame_color = '#1E211E'
        self.house_frame_color = '#242824'
        self.card_body_color = '#1E211E'
        self.sidebar_frame_color = '#242824'
        self.text_color = '#a67d43'
        self.text_color_secondary = '#9CA3AF'
        self.secondary_bg = '#3c3c3c'
        self.border_color = '#404040'
        self.button_primary = '#B85C1A'  # Более темный оранжевый (вместо #FF740F)
        self.button_success = '#0E7A4A'  # Темно-зеленый (вместо #10B981)
        self.button_info = '#2563A0'  # Темно-синий (вместо #3B82F6)
        self.button_warning = '#B45309'  # Темно-оранжевый (вместо #F59E0B)
        self.button_danger = '#9B2C2C'  # Темно-красный (вместо #EF4444)
        self.button_secondary = '#4B5563'  # Серый (вместо #6B7280)
        self.button_purple = '#6B21A5'  # Темно-фиолетовый (вместо #8B5CF6)
        self.button_blue = '#4338CA'

    def toggle_theme(self):
            """Переключает тему и сохраняет в файл"""
            if self.current_theme == 'light':
                self.set_dark_theme()
            else:
                self.set_light_theme()
            self._save_theme()  # Сохраняем в settings.cfg
            return self.current_theme


# Создаем глобальный экземпляр менеджера тем
theme_manager = ThemeManager()