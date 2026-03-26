# bookings_view.py
import customtkinter
from tkinter import messagebox
from datetime import datetime
import sqlite3
from databases.app_database import get_user_bookings, cancel_booking, update_booking_statuses
from booking_details import BookingDetailsWindow
from theme_manager import theme_manager


class BookingsWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, username, user_group='user'):
        super().__init__(parent)
        self.parent = parent
        self.username = username
        self.user_group = user_group

        self.title("Мои бронирования" if user_group == 'user' else "Все бронирования")
        self.geometry("1000x600")
        self.configure(fg_color=theme_manager.main_frame_color)

        # Обновляем статусы при открытии, но только для прошлых дат
        # Это не должно менять статус ТОЛЬКО ЧТО созданных бронирований
        update_booking_statuses()  # Эта функция теперь обновляет только просроченные

        # Настройка окна
        self.transient(parent)
        self.after(100, self.finalize_dialog)

        # Основной контейнер
        main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = customtkinter.CTkLabel(
            main_frame,
            text="Мои бронирования" if user_group == 'user' else "Все бронирования системы",
            text_color=theme_manager.text_color,
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Фильтры по статусу
        filter_frame = customtkinter.CTkFrame(main_frame, fg_color=theme_manager.house_frame_color, corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 20))

        filter_label = customtkinter.CTkLabel(
            filter_frame,
            text="Фильтр по статусу:",
            text_color=theme_manager.text_color,
            font=("Arial", 12, "bold")
        )
        filter_label.pack(side="left", padx=10, pady=10)

        self.status_filter = customtkinter.CTkComboBox(
            filter_frame,
            values=["Все", "Активные", "Завершенные", "Отмененные"],
            command=self.apply_filter,
            width=150
        )
        self.status_filter.set("Все")
        self.status_filter.pack(side="left", padx=10, pady=10)

        # Статистика
        self.stats_frame = customtkinter.CTkFrame(main_frame, fg_color=theme_manager.house_frame_color, corner_radius=10)
        self.stats_frame.pack(fill="x", pady=(0, 20))

        # Scrollable frame для бронирований
        self.bookings_frame = customtkinter.CTkScrollableFrame(
            main_frame,
            fg_color="transparent"
        )
        self.bookings_frame.pack(fill="both", expand=True)

        # Загружаем бронирования
        self.load_bookings()

    def leave_review(self, booking):
        """Открывает окно для оставления отзыва"""
        try:
            from review_dialog import ReviewDialog
            ReviewDialog(
                self,
                self.username,
                booking['house_id'],
                booking['address'],
                booking_id=booking['id']
            )
        except Exception as e:
            print(f"Ошибка при открытии окна отзыва: {e}")
            messagebox.showerror("Ошибка", "Не удалось открыть окно отзыва")

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

    def apply_filter(self, choice):
        """Применяет фильтр по статусу"""
        self.load_bookings()

    def get_status_from_filter(self, filter_text):
        """Преобразует текст фильтра в статус БД"""
        status_map = {
            "Активные": "active",
            "Завершенные": "completed",
            "Отмененные": "cancelled"
        }
        return status_map.get(filter_text, None)

    def load_bookings(self):
        """Загружает и отображает бронирования"""
        # Очищаем предыдущие
        for widget in self.bookings_frame.winfo_children():
            widget.destroy()

        # Получаем статус из фильтра
        status = self.get_status_from_filter(self.status_filter.get())

        # Загружаем бронирования
        bookings = get_user_bookings(self.username, status)

        if not bookings:
            no_data_label = customtkinter.CTkLabel(
                self.bookings_frame,
                text="У вас пока нет бронирований" if self.user_group == 'user' else "В системе нет бронирований",
                text_color="#6B7280",
                font=("Arial", 16)
            )
            no_data_label.pack(pady=50)
            self.update_stats(bookings)
            return

        # Группируем по статусам для статистики
        self.update_stats(bookings)

        # Создаем карточки бронирований
        for booking in bookings:
            self.create_booking_card(booking)

    def update_stats(self, bookings):
        """Обновляет статистику"""
        # Очищаем статистику
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        if not bookings:
            return

        # Подсчитываем статистику
        total_count = len(bookings)
        active_count = len([b for b in bookings if b['status'] == 'active'])
        completed_count = len([b for b in bookings if b['status'] == 'completed'])
        cancelled_count = len([b for b in bookings if b['status'] == 'cancelled'])

        # Создаем метки статистики
        stats_text = f"📊 Всего: {total_count} | ✅ Активных: {active_count} | 👍 Завершено: {completed_count} | ❌ Отменено: {cancelled_count}"

        stats_label = customtkinter.CTkLabel(
            self.stats_frame,
            text=stats_text,
            font=("Arial", 12, "bold"),
            text_color="#111318"
        )
        stats_label.pack(pady=10)

    def create_booking_card(self, booking):
        """Создает карточку бронирования"""
        card = customtkinter.CTkFrame(
            self.bookings_frame,
            fg_color="#F1F3F4",
            corner_radius=10
        )
        card.pack(fill="x", pady=5, padx=5)
        card.grid_columnconfigure(1, weight=1)

        # Статус с цветом
        status_colors = {
            'active': '#10B981',  # Зеленый
            'completed': '#6B7280',  # Серый
            'cancelled': '#EF4444'  # Красный
        }
        status_text = {
            'active': 'Активно',
            'completed': 'Завершено',
            'cancelled': 'Отменено'
        }

        status_frame = customtkinter.CTkFrame(
            card,
            fg_color=status_colors.get(booking['status'], '#6B7280'),
            corner_radius=15,
            height=25,
            width=100
        )
        status_frame.grid(row=0, column=2, padx=15, pady=(15, 0), sticky="ne")
        status_frame.pack_propagate(False)

        status_label = customtkinter.CTkLabel(
            status_frame,
            text=status_text.get(booking['status'], booking['status']),
            text_color="#FFFFFF",
            font=("Arial", 10, "bold")
        )
        status_label.pack(expand=True)

        # Адрес
        address_label = customtkinter.CTkLabel(
            card,
            text=f"📍 {booking['address']}",
            text_color=theme_manager.text_color,
            font=("Arial", 16, "bold"),
            anchor="w"
        )
        address_label.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="w")

        # Даты
        dates_text = f"📅 {booking['start_date']} → {booking['end_date']}  ({booking['nights']} ноч.)"
        dates_label = customtkinter.CTkLabel(
            card,
            text=dates_text,
            text_color="#6B7280",
            font=("Arial", 12)
        )
        dates_label.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="w")

        # Цена
        price_label = customtkinter.CTkLabel(
            card,
            text=f"💰 {booking['total_price']:,} ₽".replace(',', ' '),
            text_color=	theme_manager.text_color,
            font=("Arial", 14, "bold")
        )
        price_label.grid(row=2, column=0, padx=15, pady=(5, 15), sticky="w")

        # Кнопки
        button_frame = customtkinter.CTkFrame(card, fg_color="transparent")
        button_frame.grid(row=2, column=2, padx=15, pady=(5, 15), sticky="e")

        # Кнопка "Подробнее"
        details_btn = customtkinter.CTkButton(
            button_frame,
            text="👁 Подробнее",
            width=120,
            height=30,
            fg_color="#3B82F6",
            command=lambda b=booking: self.show_booking_details(b['id'])
        )
        details_btn.pack(side="right", padx=5)
        # В методе create_booking_card, после кнопки "Подробнее":

        # Кнопка "Оставить отзыв" (только для завершенных бронирований без отзыва)
        if booking['status'] == 'completed':
            from databases.app_database import get_user_review_for_booking
            review = get_user_review_for_booking(self.username, booking['id'])

            if not review:
                review_btn = customtkinter.CTkButton(
                    button_frame,
                    text="⭐ Оставить отзыв",
                    width=120,
                    height=30,
                    fg_color="#F59E0B",
                    command=lambda b=booking: self.leave_review(b)
                )
                review_btn.pack(side="right", padx=5)
            else:
                # Если отзыв уже есть, показываем "Отзыв оставлен"
                review_label = customtkinter.CTkLabel(
                    button_frame,
                    text="✅ Отзыв оставлен",
                    text_color="#10B981",
                    font=("Arial", 10, "bold")
                )
                review_label.pack(side="right", padx=5)


        # Кнопка "Отменить" (только для активных)
        if booking['status'] == 'active':
            cancel_btn = customtkinter.CTkButton(
                button_frame,
                text="❌ Отменить",
                width=100,
                height=30,
                fg_color="#EF4444",
                command=lambda b=booking: self.cancel_booking(b['id'])
            )
            cancel_btn.pack(side="right", padx=5)

    def show_booking_details(self, booking_id):
        """Показывает детали бронирования"""
        BookingDetailsWindow(self, booking_id, self.username)

    def cancel_booking(self, booking_id):
        """Отменяет бронирование"""
        result = messagebox.askyesno(
            "Подтверждение",
            "Вы уверены, что хотите отменить бронирование?\n\n"
            "⚠️ Это действие нельзя отменить!"
        )

        if result:
            if cancel_booking(booking_id, self.username):
                messagebox.showinfo("Успех", "Бронирование успешно отменено")
                self.load_bookings()  # Перезагружаем список
            else:
                messagebox.showerror("Ошибка", "Не удалось отменить бронирование")


# Для админа - отдельный класс
class AdminBookingsWindow(BookingsWindow):
    def __init__(self, parent, username):
        super().__init__(parent, username, 'admin')

    def load_bookings(self):
        """Для админа загружает все бронирования"""
        from databases.app_database import get_all_bookings_for_admin

        # Очищаем предыдущие
        for widget in self.bookings_frame.winfo_children():
            widget.destroy()

        bookings = get_all_bookings_for_admin()

        if not bookings:
            no_data_label = customtkinter.CTkLabel(
                self.bookings_frame,
                text="В системе нет бронирований",
                text_color="#6B7280",
                font=("Arial", 16)
            )
            no_data_label.pack(pady=50)
            return

        for booking in bookings:
            self.create_admin_booking_card(booking)

    def create_admin_booking_card(self, booking):
        """Карточка бронирования для админа"""
        # booking: (id, user, address, start_date, end_date, total_price, status, created_at)
        card = customtkinter.CTkFrame(
            self.bookings_frame,
            fg_color="#F1F3F4",
            corner_radius=10
        )
        card.pack(fill="x", pady=5, padx=5)

        info_text = (
            f"👤 Пользователь: {booking[1]}\n"
            f"🏠 Адрес: {booking[2]}\n"
            f"📅 {booking[3]} → {booking[4]}\n"
            f"💰 {booking[5]} ₽ | Статус: {booking[6]}"
        )

        info_label = customtkinter.CTkLabel(
            card,
            text=info_text,
            text_color=	theme_manager.text_color,
            font=("Arial", 12),
            justify="left"
        )
        info_label.pack(padx=15, pady=15, anchor="w")