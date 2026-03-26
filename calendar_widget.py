# calendar_widget.py (исправленная версия)

import customtkinter
import calendar
from datetime import datetime, timedelta, date
import sqlite3
from tkinter import messagebox
from theme_manager import theme_manager

class AvailabilityCalendar(customtkinter.CTkFrame):
    """
    Календарь занятости дома
    Зеленый - свободно
    Красный - занято
    Серый - прошедшие даты
    """

    def __init__(self, parent, house_id, on_date_selected=None):
        super().__init__(parent, fg_color=theme_manager.main_frame_color, corner_radius=10)
        self.parent = parent
        self.house_id = house_id
        self.on_date_selected = on_date_selected  # колбэк при выборе даты

        # Текущий отображаемый месяц
        self.current_date = datetime.now()
        self.selected_start_date = None
        self.selected_end_date = None

        # Загружаем забронированные даты
        self.load_booked_dates()

        # Создаем интерфейс
        self.setup_calendar()

    def load_booked_dates(self):
        """Загружает все забронированные даты для этого дома"""
        conn = sqlite3.connect('databases/app.db')
        cursor = conn.cursor()

        # Получаем все активные бронирования для этого дома
        cursor.execute('''
            SELECT start_date, end_date FROM bookings 
            WHERE house_id = ? AND status = 'active'
        ''', (self.house_id,))

        self.booked_dates = set()  # Множество для быстрой проверки

        for start_str, end_str in cursor.fetchall():
            start = datetime.strptime(start_str, '%Y-%m-%d').date()
            end = datetime.strptime(end_str, '%Y-%m-%d').date()

            # Добавляем все даты между start и end
            current = start
            while current <= end:
                self.booked_dates.add(current)
                current += timedelta(days=1)

        conn.close()
        print(f"📅 Загружено {len(self.booked_dates)} забронированных дат")

    def setup_calendar(self):
        """Создает интерфейс календаря"""

        # Используем grid для основного фрейма
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # calendar_frame будет растягиваться

        # Заголовок с навигацией
        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)  # Центральная колонка растягивается

        # Кнопка "Предыдущий месяц"
        prev_btn = customtkinter.CTkButton(
            header_frame,
            text="◀",
            width=30,
            height=30,
            fg_color=theme_manager.button_secondary,
            command=self.prev_month
        )
        prev_btn.grid(row=0, column=0, padx=5)

        # Название месяца и года
        self.month_label = customtkinter.CTkLabel(
            header_frame,
            text=self.current_date.strftime("%B %Y"),
            text_color=theme_manager.text_color,
            font=("Arial", 16, "bold")
        )
        self.month_label.grid(row=0, column=1, padx=5)

        # Кнопка "Сегодня"
        today_btn = customtkinter.CTkButton(
            header_frame,
            text="Сегодня",
            width=60,
            height=30,
            fg_color=theme_manager.button_info,
            command=self.go_to_today
        )
        today_btn.grid(row=0, column=2, padx=5)

        # Кнопка "Следующий месяц"
        next_btn = customtkinter.CTkButton(
            header_frame,
            text="▶",
            width=30,
            height=30,
            fg_color=theme_manager.button_secondary,
            command=self.next_month
        )
        next_btn.grid(row=0, column=3, padx=5)

        # Легенда
        legend_frame = customtkinter.CTkFrame(self, fg_color=theme_manager.sidebar_frame_color, corner_radius=5)
        legend_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Свободно
        free_frame = customtkinter.CTkFrame(legend_frame, fg_color="transparent")
        free_frame.pack(side="left", padx=10, pady=5)

        free_color = customtkinter.CTkFrame(free_frame, width=20, height=20, fg_color=theme_manager.button_success, corner_radius=3)
        free_color.pack(side="left", padx=5)

        free_label = customtkinter.CTkLabel(free_frame, text="Свободно", text_color=theme_manager.text_color)
        free_label.pack(side="left")

        # Занято
        booked_frame = customtkinter.CTkFrame(legend_frame, fg_color="transparent")
        booked_frame.pack(side="left", padx=10, pady=5)

        booked_color = customtkinter.CTkFrame(booked_frame, width=20, height=20, fg_color=theme_manager.button_danger, corner_radius=3)
        booked_color.pack(side="left", padx=5)

        booked_label = customtkinter.CTkLabel(booked_frame, text="Занято", text_color=theme_manager.text_color)
        booked_label.pack(side="left")

        # Прошедшие
        past_frame = customtkinter.CTkFrame(legend_frame, fg_color="transparent")
        past_frame.pack(side="left", padx=10, pady=5)

        past_color = customtkinter.CTkFrame(past_frame, width=20, height=20, fg_color=theme_manager.button_secondary, corner_radius=3)
        past_color.pack(side="left", padx=5)

        past_label = customtkinter.CTkLabel(past_frame, text="Прошедшие", text_color=theme_manager.text_color)
        past_label.pack(side="left")

        # Контейнер для дней недели и дат - ИСПОЛЬЗУЕМ GRID
        self.calendar_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.calendar_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.calendar_frame.grid_columnconfigure(tuple(range(7)), weight=1)  # 7 колонок для дней недели

        # Отображаем текущий месяц
        self.show_month()

    def show_month(self):
        """Отображает сетку месяцев"""
        # Очищаем предыдущий календарь
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        # Дни недели (Пн, Вт, Ср, Чт, Пт, Сб, Вс)
        for i, day in enumerate(["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]):
            day_label = customtkinter.CTkLabel(
                self.calendar_frame,
                text=day,
                text_color=theme_manager.text_color_secondary,
                font=("Arial", 12, "bold")
            )
            day_label.grid(row=0, column=i, padx=2, pady=5, sticky="nsew")

        # Получаем информацию о месяце
        year = self.current_date.year
        month = self.current_date.month

        # Первый день месяца (0 = понедельник, 6 = воскресенье)
        first_day = date(year, month, 1).weekday()

        # Количество дней в месяце
        days_in_month = calendar.monthrange(year, month)[1]

        # Сегодняшняя дата
        today = date.today()

        # Создаем сетку дат
        day_row = 1
        day_col = first_day

        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)

            # Определяем цвет в зависимости от статуса
            if current_date < today:
                bg_color = theme_manager.button_secondary  # Серый для прошедших
                text_color = theme_manager.text_color_secondary
                state = "disabled"
                hover_color = "#9CA3AF"
            elif current_date in self.booked_dates:
                bg_color = theme_manager.button_danger  # Красный для занятых
                text_color = "#FFFFFF"
                state = "normal"
                hover_color = theme_manager.button_danger
            else:
                bg_color = theme_manager.button_success  # Зеленый для свободных
                text_color = "#FFFFFF"
                state = "normal"
                hover_color = theme_manager.button_success

            # Создаем кнопку для дня
            day_btn = customtkinter.CTkButton(
                self.calendar_frame,
                text=str(day),
                fg_color=bg_color,
                text_color=text_color,
                hover_color=hover_color,
                state=state,
                command=lambda d=current_date: self.on_day_click(d)
            )
            day_btn.grid(row=day_row, column=day_col, padx=2, pady=2, sticky="nsew")

            # Переход к следующему дню
            day_col += 1
            if day_col > 6:
                day_col = 0
                day_row += 1

        # Обновляем заголовок
        self.month_label.configure(text=self.current_date.strftime("%B %Y"))

    def on_day_click(self, clicked_date):
        """Обработчик клика по дню"""
        if clicked_date < date.today():
            messagebox.showinfo("Информация", "Нельзя выбрать прошедшую дату")
            return

        if clicked_date in self.booked_dates:
            messagebox.showinfo("Информация", "Эта дата уже занята")
            return

        # Если есть колбэк, вызываем его
        if self.on_date_selected:
            self.on_date_selected(clicked_date)

    def prev_month(self):
        """Переход к предыдущему месяцу"""
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.show_month()

    def next_month(self):
        """Переход к следующему месяцу"""
        next_month = self.current_date.replace(day=28) + timedelta(days=4)
        self.current_date = next_month.replace(day=1)
        self.show_month()

    def go_to_today(self):
        """Переход к текущему месяцу"""
        self.current_date = datetime.now()
        self.show_month()

    def refresh(self):
        """Обновляет календарь (перезагружает забронированные даты)"""
        self.load_booked_dates()
        self.show_month()


class DateRangeCalendar(AvailabilityCalendar):
    """
    Расширенный календарь для выбора диапазона дат
    """

    def __init__(self, parent, house_id, on_range_selected=None):
        self.selected_start = None
        self.selected_end = None
        self.on_range_selected = on_range_selected
        super().__init__(parent, house_id)

        # Добавляем информацию о выбранном диапазоне
        self.selection_frame = customtkinter.CTkFrame(self, fg_color=theme_manager.sidebar_frame_color, corner_radius=5)
        self.selection_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        self.selection_label = customtkinter.CTkLabel(
            self.selection_frame,
            text="Выберите дату заезда",
            text_color=theme_manager.text_color,
            font=("Arial", 12)
        )
        self.selection_label.pack(pady=5)

        # Кнопка сброса
        self.reset_btn = customtkinter.CTkButton(
            self.selection_frame,
            text="Сбросить",
            width=80,
            height=30,
            fg_color=theme_manager.button_secondary,
            command=self.reset_selection
        )
        self.reset_btn.pack(pady=5)

    def on_day_click(self, clicked_date):
        """Обработчик клика для выбора диапазона"""
        if clicked_date < date.today():
            messagebox.showinfo("Информация", "Нельзя выбрать прошедшую дату")
            return

        if clicked_date in self.booked_dates:
            messagebox.showinfo("Информация", "Эта дата уже занята")
            return

        if self.selected_start is None:
            # Выбираем дату заезда
            self.selected_start = clicked_date
            self.update_selection_label()
        elif self.selected_end is None:
            # Выбираем дату выезда
            if clicked_date <= self.selected_start:
                messagebox.showinfo("Информация", "Дата выезда должна быть позже даты заезда")
                return

            # Проверяем, нет ли занятых дат в выбранном диапазоне
            current = self.selected_start + timedelta(days=1)
            while current < clicked_date:
                if current in self.booked_dates:
                    messagebox.showinfo(
                        "Информация",
                        f"Дата {current.strftime('%d.%m.%Y')} уже занята.\n"
                        "Выберите другой диапазон."
                    )
                    return
                current += timedelta(days=1)

            self.selected_end = clicked_date

            # Вызываем колбэк
            if self.on_range_selected:
                self.on_range_selected(self.selected_start, self.selected_end)

            self.update_selection_label()
        else:
            # Сбрасываем и начинаем заново
            self.selected_start = clicked_date
            self.selected_end = None
            self.update_selection_label()

        # Перерисовываем календарь для подсветки выбранных дат
        self.show_month()

    def update_selection_label(self):
        """Обновляет текст с выбранными датами"""
        if self.selected_start and self.selected_end:
            nights = (self.selected_end - self.selected_start).days
            self.selection_label.configure(
                text=f"✅ Выбрано: {self.selected_start.strftime('%d.%m.%Y')} → {self.selected_end.strftime('%d.%m.%Y')}\n"
                     f"🌙 Ночей: {nights}"
            )
        elif self.selected_start:
            self.selection_label.configure(
                text=f"📅 Заезд: {self.selected_start.strftime('%d.%m.%Y')}\n"
                     f"Теперь выберите дату выезда"
            )
        else:
            self.selection_label.configure(text="Выберите дату заезда")

    def reset_selection(self):
        """Сбрасывает выбор дат"""
        self.selected_start = None
        self.selected_end = None
        self.update_selection_label()
        self.show_month()

    def get_selected_range(self):
        """Возвращает выбранный диапазон"""
        if self.selected_start and self.selected_end:
            return {
                'start': self.selected_start.strftime('%Y-%m-%d'),
                'end': self.selected_end.strftime('%Y-%m-%d'),
                'nights': (self.selected_end - self.selected_start).days
            }
        return None