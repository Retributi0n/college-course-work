# booking_details.py
import customtkinter
from datetime import datetime
from databases.app_database import get_booking_details
from tkinter import messagebox


class BookingDetailsWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, booking_id, username):
        super().__init__(parent)
        self.parent = parent
        self.booking_id = booking_id
        self.username = username

        self.title("Детали бронирования")
        self.geometry("600x700")
        self.configure(fg_color="#FFFFFF")

        self.transient(parent)

        # Загружаем данные
        self.booking = get_booking_details(booking_id, username)

        if not self.booking:
            messagebox.showerror("Ошибка", "Бронирование не найдено")
            self.destroy()
            return

        self.setup_ui()
        self.after(100, self.finalize_dialog)

    def setup_ui(self):
        """Создает интерфейс"""
        main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Заголовок
        title_label = customtkinter.CTkLabel(
            main_frame,
            text="Детали бронирования",
            text_color="#111318",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Статус
        status_colors = {
            'active': '#10B981',
            'completed': '#6B7280',
            'cancelled': '#EF4444'
        }
        status_text = {
            'active': 'Активно',
            'completed': 'Завершено',
            'cancelled': 'Отменено'
        }

        status_frame = customtkinter.CTkFrame(
            main_frame,
            fg_color=status_colors.get(self.booking['status'], '#6B7280'),
            corner_radius=20,
            height=40
        )
        status_frame.pack(pady=(0, 20))
        status_frame.pack_propagate(False)

        status_label = customtkinter.CTkLabel(
            status_frame,
            text=status_text.get(self.booking['status'], self.booking['status']),
            text_color="#FFFFFF",
            font=("Arial", 14, "bold")
        )
        status_label.pack(expand=True, padx=30)

        # Информация о доме
        house_frame = self.create_info_section(
            main_frame,
            "🏠 Информация о доме",
            [
                f"📍 Адрес: {self.booking['address']}",
                f"📐 Площадь: {self.booking['area']} м²",
                f"🏢 Этаж: {self.booking['floor']}",
                f"🚪 Комнат: {self.booking['rooms']}",
                f"💰 Цена за ночь: {self.booking['price_per_night']}"
            ]
        )
        house_frame.pack(fill="x", pady=(0, 15))

        # Информация о бронировании
        booking_frame = self.create_info_section(
            main_frame,
            "📅 Детали бронирования",
            [
                f"📆 Заезд: {self.booking['start_date']}",
                f"📆 Выезд: {self.booking['end_date']}",
                f"🌙 Количество ночей: {self.booking['nights']}",
                f"💰 Общая стоимость: {self.booking['total_price']:,} ₽".replace(',', ' '),
                f"🕐 Забронировано: {self.booking['created_at']}"
            ]
        )
        booking_frame.pack(fill="x", pady=(0, 15))

        # Дополнительная информация
        if self.booking['status'] == 'active':
            # Проверяем, можно ли еще отменить
            from datetime import datetime, timedelta
            start = datetime.strptime(self.booking['start_date'], '%Y-%m-%d')
            today = datetime.now()

            if (start - today).days >= 1:
                info_label = customtkinter.CTkLabel(
                    main_frame,
                    text="✅ Вы можете отменить бронирование бесплатно до завтрашнего дня",
                    text_color="#10B981",
                    font=("Arial", 12)
                )
                info_label.pack(pady=(0, 20))
            else:
                info_label = customtkinter.CTkLabel(
                    main_frame,
                    text="⚠️ Отмена бронирования менее чем за 24 часа может повлечь штраф",
                    text_color="#F59E0B",
                    font=("Arial", 12)
                )
                info_label.pack(pady=(0, 20))

        # Кнопка закрытия
        close_btn = customtkinter.CTkButton(
            main_frame,
            text="Закрыть",
            fg_color="#6B7280",
            command=self.destroy,
            height=40
        )
        close_btn.pack(pady=20)

    def create_info_section(self, parent, title, items):
        """Создает секцию с информацией"""
        frame = customtkinter.CTkFrame(parent, fg_color="#F1F3F4", corner_radius=10)

        # Заголовок секции
        title_label = customtkinter.CTkLabel(
            frame,
            text=title,
            text_color="#111318",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 10))

        # Элементы
        for item in items:
            item_label = customtkinter.CTkLabel(
                frame,
                text=item,
                text_color="#111318",
                font=("Arial", 12),
                anchor="w",
                justify="left"
            )
            item_label.pack(anchor="w", padx=15, pady=2)

        # Нижний отступ
        padding = customtkinter.CTkFrame(frame, fg_color="transparent", height=10)
        padding.pack()

        return frame

    def finalize_dialog(self):
        """Завершает настройку диалога"""
        self.center_window()
        self.grab_set()
        self.focus_set()
        self.lift()

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