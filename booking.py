# booking.py
import customtkinter
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import sqlite3
from databases.app_database import add_booking, check_booking_availability


class BookingDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, house):
        super().__init__(parent)
        self.parent = parent
        self.house = house
        self.username = parent.username

        house_id, address, area, floor, rooms, price, image_path, verified, created_by = house

        self.title(f"Бронирование: {address}")
        self.geometry("500x650")
        self.configure(fg_color="#FFFFFF")
        self.resizable(False, False)

        # Не делаем grab_set сразу
        self.transient(parent)

        # Основной контейнер
        main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = customtkinter.CTkLabel(main_frame,
                                             text=f"Бронирование дома",
                                             text_color="#111318",
                                             font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 10))

        # Адрес
        address_label = customtkinter.CTkLabel(main_frame,
                                               text=f"📍 {address}",
                                               text_color="#111318",
                                               font=("Arial", 16))
        address_label.pack(pady=(0, 20))

        # Информация о доме
        info_frame = customtkinter.CTkFrame(main_frame, fg_color="#F1F3F4", corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 20))

        info_text = (
            f"🏘️ Площадь: {area} м²\n"
            f"🏢 Этаж: {floor}\n"
            f"🚪 Комнат: {rooms}\n"
            f"💰 Цена за ночь: {price}"
        )

        info_label = customtkinter.CTkLabel(info_frame,
                                            text=info_text,
                                            text_color="#111318",
                                            font=("Arial", 12),
                                            justify="left")
        info_label.pack(padx=15, pady=15, anchor="w")

        # Даты бронирования
        dates_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        dates_frame.pack(fill="x", pady=(0, 20))

        # Дата заезда
        start_frame = customtkinter.CTkFrame(dates_frame, fg_color="transparent")
        start_frame.pack(fill="x", pady=5)

        start_label = customtkinter.CTkLabel(start_frame,
                                             text="📅 Дата заезда:",
                                             font=("Arial", 12, "bold"))
        start_label.pack(side="left", padx=(0, 10))

        self.start_day = customtkinter.CTkEntry(start_frame, width=40, placeholder_text="ДД")
        self.start_day.pack(side="left", padx=2)

        self.start_month = customtkinter.CTkEntry(start_frame, width=40, placeholder_text="ММ")
        self.start_month.pack(side="left", padx=2)

        self.start_year = customtkinter.CTkEntry(start_frame, width=60, placeholder_text="ГГГГ")
        self.start_year.pack(side="left", padx=2)

        # Кнопка "Сегодня"
        today_btn = customtkinter.CTkButton(start_frame,
                                            text="Сегодня",
                                            width=80,
                                            command=self.set_today_start)
        today_btn.pack(side="left", padx=10)

        # Дата выезда
        end_frame = customtkinter.CTkFrame(dates_frame, fg_color="transparent")
        end_frame.pack(fill="x", pady=5)

        end_label = customtkinter.CTkLabel(end_frame,
                                           text="📅 Дата выезда:",
                                           font=("Arial", 12, "bold"))
        end_label.pack(side="left", padx=(0, 10))

        self.end_day = customtkinter.CTkEntry(end_frame, width=40, placeholder_text="ДД")
        self.end_day.pack(side="left", padx=2)

        self.end_month = customtkinter.CTkEntry(end_frame, width=40, placeholder_text="ММ")
        self.end_month.pack(side="left", padx=2)

        self.end_year = customtkinter.CTkEntry(end_frame, width=60, placeholder_text="ГГГГ")
        self.end_year.pack(side="left", padx=2)

        # Кнопка "Завтра"
        tomorrow_btn = customtkinter.CTkButton(end_frame,
                                               text="Завтра",
                                               width=80,
                                               command=self.set_tomorrow_end)
        tomorrow_btn.pack(side="left", padx=10)

        # Кнопка открытия календаря
        calendar_btn = customtkinter.CTkButton(
            dates_frame,
            text="📅 Открыть календарь",
            command=self.open_calendar,
            fg_color="#8B5CF6",
            width=150
        )
        calendar_btn.pack(pady=10)

        # Кнопка рассчитать
        calc_frame = customtkinter.CTkFrame(dates_frame, fg_color="transparent")
        calc_frame.pack(fill="x", pady=10)

        calc_btn = customtkinter.CTkButton(calc_frame,
                                           text="🔄 Рассчитать стоимость",
                                           command=self.calculate_total,
                                           fg_color="#F59E0B")
        calc_btn.pack()

        # Метка для отображения ошибок
        self.error_label = customtkinter.CTkLabel(main_frame,
                                                  text="",
                                                  text_color="#EF4444",
                                                  font=("Arial", 12))
        self.error_label.pack(pady=(0, 10))

        # Итоговая стоимость - ИСПРАВЛЕНО
        self.total_frame = customtkinter.CTkFrame(main_frame, fg_color="#10B981", corner_radius=10)
        self.total_frame.pack(fill="x", pady=(10, 20))  # <- ИЗМЕНЕНО: (10, 20) вместо (0, 20)
        # Первое число 10 - это отступ СВЕРХУ от предыдущего элемента (кнопки "Рассчитать")
        # Второе число 20 - отступ СНИЗУ до следующего элемента (разделителя/кнопок)
        self.total_frame.pack_forget()  # Скрываем до расчета

        self.total_label = customtkinter.CTkLabel(self.total_frame,
                                                  text="",
                                                  text_color="#FFFFFF",
                                                  font=("Arial", 14, "bold"))
        self.total_label.pack(padx=15, pady=15)

        # Разделитель для визуального отделения
        separator = customtkinter.CTkFrame(main_frame, height=2, fg_color="#E5E7EB")
        separator.pack(fill="x", pady=(10, 20))

        # Кнопки
        button_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        cancel_btn = customtkinter.CTkButton(button_frame,
                                             text="Отмена",
                                             fg_color="#6B7280",
                                             command=self.destroy,
                                             width=120)
        cancel_btn.pack(side="left", padx=(0, 10))

        self.confirm_btn = customtkinter.CTkButton(button_frame,
                                                   text="Подтвердить бронирование",
                                                   fg_color="#10B981",
                                                   command=self.confirm_booking,
                                                   width=200,
                                                   state="disabled")
        self.confirm_btn.pack(side="left")

        # Устанавливаем сегодняшнюю и завтрашнюю дату по умолчанию
        self.set_today_start()
        self.set_tomorrow_end()

        # Через 100мс завершаем настройку
        self.after(100, self.finalize_dialog)

    def finalize_dialog(self):
        """Завершает настройку диалога после его отображения"""
        self.center_window()
        self.grab_set()
        self.focus_set()
        self.lift()

    def open_calendar(self):
        """Открывает календарь для выбора дат"""
        from calendar_widget import DateRangeCalendar

        calendar_window = customtkinter.CTkToplevel(self)
        calendar_window.title("Выберите даты")
        calendar_window.geometry("500x550")
        calendar_window.configure(fg_color="#FFFFFF")
        calendar_window.transient(self)

        # Центрируем
        calendar_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - calendar_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - calendar_window.winfo_height()) // 2
        calendar_window.geometry(f"+{x}+{y}")

        # Создаем календарь с выбором диапазона
        calendar = DateRangeCalendar(
            calendar_window,
            self.house[0],  # house_id
            on_range_selected=lambda s, e: self.on_calendar_range_selected(s, e, calendar_window)
        )
        calendar.pack(fill="both", expand=True, padx=20, pady=20)

    def on_calendar_range_selected(self, start_date, end_date, window):
        """Обработчик выбора диапазона из календаря"""
        # Устанавливаем даты в поля ввода
        self.start_day.delete(0, 'end')
        self.start_day.insert(0, start_date.strftime("%d"))
        self.start_month.delete(0, 'end')
        self.start_month.insert(0, start_date.strftime("%m"))
        self.start_year.delete(0, 'end')
        self.start_year.insert(0, start_date.strftime("%Y"))

        self.end_day.delete(0, 'end')
        self.end_day.insert(0, end_date.strftime("%d"))
        self.end_month.delete(0, 'end')
        self.end_month.insert(0, end_date.strftime("%m"))
        self.end_year.delete(0, 'end')
        self.end_year.insert(0, end_date.strftime("%Y"))

        # Рассчитываем стоимость
        self.calculate_total()

        # Закрываем окно календаря
        window.destroy()

    def center_window(self):
        """Центрирует окно относительно родителя"""
        self.update_idletasks()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        width = self.winfo_width()
        height = self.winfo_height()

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f"+{x}+{y}")

    def set_today_start(self):
        """Устанавливает сегодняшнюю дату как дату заезда"""
        today = datetime.now()
        self.start_day.delete(0, tk.END)
        self.start_day.insert(0, today.strftime("%d"))
        self.start_month.delete(0, tk.END)
        self.start_month.insert(0, today.strftime("%m"))
        self.start_year.delete(0, tk.END)
        self.start_year.insert(0, today.strftime("%Y"))

    def set_tomorrow_end(self):
        """Устанавливает завтрашнюю дату как дату выезда"""
        tomorrow = datetime.now() + timedelta(days=1)
        self.end_day.delete(0, tk.END)
        self.end_day.insert(0, tomorrow.strftime("%d"))
        self.end_month.delete(0, tk.END)
        self.end_month.insert(0, tomorrow.strftime("%m"))
        self.end_year.delete(0, tk.END)
        self.end_year.insert(0, tomorrow.strftime("%Y"))

    def parse_date(self, day_widget, month_widget, year_widget):
        """Парсит дату из виджетов"""
        try:
            day = int(day_widget.get())
            month = int(month_widget.get())
            year = int(year_widget.get())

            # Проверяем корректность даты
            test_date = datetime(year, month, day)

            # Проверяем, что дата не в прошлом (кроме сегодня)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if test_date < today:
                return None, "Дата не может быть в прошлом"

            return f"{year:04d}-{month:02d}-{day:02d}", None
        except ValueError as e:
            return None, f"Некорректная дата: {e}"
        except (ValueError, TypeError):
            return None, "Введите корректную дату"

    def extract_price_number(self, price_str):
        """Извлекает число из строки с ценой"""
        try:
            # Убираем все нецифровые символы
            clean_price = ''.join(c for c in price_str if c.isdigit())
            return int(clean_price) if clean_price else 0
        except:
            return 0

    def calculate_total(self):
        """Рассчитывает общую стоимость и проверяет доступность"""
        # Очищаем предыдущие ошибки
        self.error_label.configure(text="")

        # Скрываем предыдущий результат
        self.total_frame.pack_forget()
        self.confirm_btn.configure(state="disabled")

        house_id, address, area, floor, rooms, price, image_path, verified, created_by = self.house

        # Парсим даты
        start_date, start_error = self.parse_date(self.start_day, self.start_month, self.start_year)
        if start_error:
            self.error_label.configure(text=start_error)
            return

        end_date, end_error = self.parse_date(self.end_day, self.end_month, self.end_year)
        if end_error:
            self.error_label.configure(text=end_error)
            return

        # Проверяем, что дата выезда позже даты заезда
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            if end <= start:
                self.error_label.configure(text="Дата выезда должна быть позже даты заезда")
                return

            # Рассчитываем количество ночей
            nights = (end - start).days

            # Проверяем максимальный срок бронирования (например, 30 дней)
            if nights > 30:
                self.error_label.configure(text="Максимальный срок бронирования - 30 дней")
                return

            # Получаем цену за ночь
            price_per_night = self.extract_price_number(price)

            if price_per_night == 0:
                self.error_label.configure(text="Не удалось определить цену")
                return

            # Проверяем доступность дат
            if not check_booking_availability(house_id, start_date, end_date):
                self.error_label.configure(
                    text="❌ Дом уже забронирован на выбранные даты.\n"
                         "Пожалуйста, выберите другие даты."
                )
                return

            # Рассчитываем общую стоимость
            total_price = nights * price_per_night

            # Сохраняем данные для подтверждения
            self.booking_data = {
                'house_id': house_id,
                'start_date': start_date,
                'end_date': end_date,
                'nights': nights,
                'total_price': total_price,
                'price_per_night': price_per_night
            }

            # Показываем результат с бОльшим отступом снизу
            self.total_frame.pack(fill="x", pady=(10, 30))  # <- Увеличено с 20 до 30
            self.total_label.configure(
                text=f"✅ Дом свободен!\n\n"  # Добавлен дополнительный перенос строки
                     f"Итого: {nights} ноч. × {price_per_night:,} ₽ = {total_price:,} ₽"
            )

            # Активируем кнопку подтверждения
            self.confirm_btn.configure(state="normal")

        except ValueError as e:
            self.error_label.configure(text=f"Ошибка: {e}")

    def confirm_booking(self):
        """Подтверждает бронирование"""
        if not hasattr(self, 'booking_data'):
            messagebox.showerror("Ошибка", "Сначала рассчитайте стоимость")
            return

        house_id, address, area, floor, rooms, price, image_path, verified, created_by = self.house

        # **Дополнительная проверка доступности перед подтверждением**
        # (на случай, если кто-то другой забронировал пока мы считали)
        if not check_booking_availability(
                self.booking_data['house_id'],
                self.booking_data['start_date'],
                self.booking_data['end_date']
        ):
            messagebox.showerror(
                "Ошибка",
                "К сожалению, дом уже забронирован на выбранные даты.\n"
                "Пожалуйста, выберите другие даты."
            )
            self.calculate_total()  # Пересчитываем заново
            return

        # Подтверждение
        confirm_msg = (
            f"Подтвердить бронирование?\n\n"
            f"🏠 Дом: {address}\n"
            f"📅 Заезд: {self.booking_data['start_date']}\n"
            f"📅 Выезд: {self.booking_data['end_date']}\n"
            f"🌙 Ночей: {self.booking_data['nights']}\n"
            f"💰 Итого: {self.booking_data['total_price']:,} ₽"
        )

        result = messagebox.askyesno("Подтверждение", confirm_msg)

        if result:
            # Сохраняем бронирование в БД
            success = add_booking(
                house_id=self.booking_data['house_id'],
                username=self.username,
                start_date=self.booking_data['start_date'],
                end_date=self.booking_data['end_date'],
                total_price=self.booking_data['total_price']
            )

            if success:
                messagebox.showinfo(
                    "Успех",
                    f"✅ Бронирование подтверждено!\n\n"
                    f"Адрес: {address}\n"
                    f"Даты: {self.booking_data['start_date']} - {self.booking_data['end_date']}\n"
                    f"Стоимость: {self.booking_data['total_price']:,} ₽\n\n"
                    f"Детали бронирования доступны в разделе 'Мои бронирования'."
                )
                self.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить бронирование")