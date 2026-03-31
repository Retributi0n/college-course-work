# review_dialog.py
import customtkinter
from tkinter import messagebox
from databases.app_database import add_review, get_house_average_rating
from theme_manager import theme_manager


class ReviewDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, username, house_id, address, booking_id=None):
        super().__init__(parent)
        self.parent = parent
        self.username = username
        self.house_id = house_id
        self.address = address
        self.booking_id = booking_id

        self.title(f"Отзыв о доме")
        self.geometry("500x600")
        self.configure(fg_color=theme_manager.main_frame_color)
        self.resizable(False, False)

        self.transient(parent)

        self.setup_ui()
        self.after(100, self.finalize_dialog)

    def setup_ui(self):
        """Создает интерфейс окна отзыва"""
        main_frame = customtkinter.CTkFrame(self, fg_color=theme_manager.house_frame_color)
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Заголовок
        title_label = customtkinter.CTkLabel(
            main_frame,
            text="Оставьте ваш отзыв",
            text_color=theme_manager.text_color,
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Адрес дома
        address_label = customtkinter.CTkLabel(
            main_frame,
            text=f"📍 {self.address}",
            text_color=theme_manager.text_color,
            font=("Arial", 14)
        )
        address_label.pack(pady=(0, 30))

        # Рейтинг (звезды)
        rating_label = customtkinter.CTkLabel(
            main_frame,
            text="Ваша оценка:",
            text_color=theme_manager.text_color_secondary,
            font=("Arial", 16, "bold")
        )
        rating_label.pack(pady=(0, 10))

        # Фрейм для звезд - используем обычный Frame без прозрачности
        self.stars_frame = customtkinter.CTkFrame(main_frame, fg_color=theme_manager.sidebar_frame_color)
        self.stars_frame.pack(pady=(0, 20))

        self.selected_rating = 0
        self.star_buttons = []

        # Создаем 5 звезд
        for i in range(5):
            star_btn = customtkinter.CTkButton(
                self.stars_frame,
                text="☆",
                width=40,
                height=40,
                fg_color="#FFFFFF",  # Не прозрачный
                text_color="#F59E0B",
                hover_color="#F0F0F0",  # Цвет при наведении
                font=("Arial", 24),
                command=lambda idx=i + 1: self.set_rating(idx)
            )
            star_btn.pack(side="left", padx=2)
            self.star_buttons.append(star_btn)

        # Текст отзыва
        comment_label = customtkinter.CTkLabel(
            main_frame,
            text="Ваш отзыв:",
            text_color=theme_manager.text_color,
            font=("Arial", 16, "bold")
        )
        comment_label.pack(pady=(0, 10))

        self.comment_text = customtkinter.CTkTextbox(
            main_frame,
            height=150,
            fg_color=theme_manager.main_frame_color,
            text_color=theme_manager.text_color_secondary,
            font=("Arial", 12)
        )
        self.comment_text.pack(fill="x", pady=(0, 20))

        # Кнопки
        button_frame = customtkinter.CTkFrame(main_frame, fg_color="#FFFFFF")
        button_frame.pack(fill="x", pady=(10, 0))

        cancel_btn = customtkinter.CTkButton(
            button_frame,
            text="Отмена",
            fg_color="#6B7280",
            command=self.destroy,
            width=120,
            height=40
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        self.submit_btn = customtkinter.CTkButton(
            button_frame,
            text="Отправить отзыв",
            fg_color="#F59E0B",
            command=self.submit_review,
            width=200,
            height=40,
            state="disabled"
        )
        self.submit_btn.pack(side="left")

        # Метка для подсказки
        self.hint_label = customtkinter.CTkLabel(
            main_frame,
            text="Поставьте оценку, чтобы отправить отзыв",
            text_color="#6B7280",
            font=("Arial", 11)
        )
        self.hint_label.pack(pady=(10, 0))

    def set_rating(self, rating):
        """Устанавливает рейтинг и обновляет звезды"""
        self.selected_rating = rating

        # Обновляем отображение звезд
        for i, btn in enumerate(self.star_buttons):
            if i < rating:
                btn.configure(text="⭐", text_color="#F59E0B", fg_color="#FFFFFF")
            else:
                btn.configure(text="☆", text_color="#F59E0B", fg_color="#FFFFFF")

        # Активируем кнопку отправки
        self.submit_btn.configure(state="normal")
        self.hint_label.configure(text="")

    def submit_review(self):
        """Отправляет отзыв"""
        comment = self.comment_text.get("1.0", "end-1c").strip()

        if not comment:
            messagebox.showwarning("Предупреждение", "Пожалуйста, напишите текст отзыва")
            return

        # Добавляем отзыв в БД
        success = add_review(
            username=self.username,
            house_id=self.house_id,
            booking_id=self.booking_id,
            rating=self.selected_rating,
            comment=comment
        )

        if success:
            messagebox.showinfo("Спасибо!", "Спасибо за ваш отзыв!")

            # Обновляем рейтинг в родительском окне (если нужно)
            if hasattr(self.parent, 'update_house_rating'):
                self.parent.update_house_rating(self.house_id)

            self.destroy()
        else:
            messagebox.showerror("Ошибка",
                                 "Не удалось отправить отзыв. Возможно, вы уже оставляли отзыв для этого дома.")

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


class ReviewsWindow(customtkinter.CTkToplevel):
    """Окно для просмотра всех отзывов о доме"""

    def __init__(self, parent, house_id, address, current_username=None, booking_id=None):
        super().__init__(parent)
        self.parent = parent
        self.house_id = house_id
        self.address = address
        self.current_username = current_username  # Текущий пользователь
        self.booking_id = booking_id  # ID конкретного бронирования (если есть)

        self.title(f"Отзывы - {address}")
        self.geometry("600x700")
        self.configure(fg_color=theme_manager.main_frame_color)

        self.transient(parent)

        self.load_reviews()
        self.setup_ui()
        self.after(100, self.finalize_dialog)

    def load_reviews(self):
        """Загружает отзывы из БД"""
        from databases.app_database import get_house_reviews, get_house_average_rating

        self.reviews = get_house_reviews(self.house_id)
        self.rating_info = get_house_average_rating(self.house_id)

        # Проверяем, может ли текущий пользователь оставить отзыв
        self.can_review = False
        if self.current_username:
            from databases.app_database import get_completed_bookings_for_review
            completed_bookings = get_completed_bookings_for_review(self.current_username)

            # Проверяем, есть ли у пользователя завершенное бронирование этого дома
            for booking in completed_bookings:
                if booking['house_id'] == self.house_id and not booking['has_review']:
                    self.can_review = True
                    self.available_booking_id = booking['booking_id']
                    break

    def setup_ui(self):
        """Создает интерфейс окна отзывов"""
        main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = customtkinter.CTkLabel(
            main_frame,
            text=f"Отзывы о доме",
            text_color=theme_manager.text_color,
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=(0, 5))

        # Адрес
        address_label = customtkinter.CTkLabel(
            main_frame,
            text=self.address,
            text_color="#6B7280",
            font=("Arial", 14)
        )
        address_label.pack(pady=(0, 10))

        # Средний рейтинг
        rating_frame = customtkinter.CTkFrame(main_frame, fg_color=theme_manager.sidebar_frame_color, corner_radius=10)
        rating_frame.pack(fill="x", pady=(0, 20))

        avg_rating = self.rating_info['average']
        reviews_count = self.rating_info['count']

        rating_text = f"⭐ {avg_rating} / 5  •  {reviews_count} отзывов"
        if reviews_count == 0:
            rating_text = "⭐ Пока нет отзывов"

        avg_label = customtkinter.CTkLabel(
            rating_frame,
            text=rating_text,
            text_color=theme_manager.text_color,
            font=("Arial", 16, "bold")
        )
        avg_label.pack(padx=20, pady=15)

        # Кнопка "Оставить отзыв" (если пользователь может)
        if self.can_review:
            review_btn = customtkinter.CTkButton(
                main_frame,
                text="✍️ Оставить отзыв",
                fg_color="#F59E0B",
                command=self.open_review_dialog,
                height=40,
                font=("Arial", 13, "bold")
            )
            review_btn.pack(pady=(0, 20))

        # Список отзывов
        if not self.reviews:
            no_reviews_label = customtkinter.CTkLabel(
                main_frame,
                text="😔 Пока нет отзывов",
                text_color="#6B7280",
                font=("Arial", 14)
            )
            no_reviews_label.pack(pady=20)

            if not self.can_review:
                hint_label = customtkinter.CTkLabel(
                    main_frame,
                    text="Забронируйте этот дом и проживите в нем,\nчтобы оставить отзыв!",
                    text_color="#6B7280",
                    font=("Arial", 12)
                )
                hint_label.pack(pady=10)
        else:
            # Scrollable frame для отзывов
            scroll_frame = customtkinter.CTkScrollableFrame(main_frame, fg_color="transparent")
            scroll_frame.pack(fill="both", expand=True)

            for review in self.reviews:
                self.create_review_card(scroll_frame, review)

        # Кнопка закрытия
        close_btn = customtkinter.CTkButton(
            main_frame,
            text="Закрыть",
            fg_color="#6B7280",
            command=self.destroy,
            height=40
        )
        close_btn.pack(pady=20)

    def open_review_dialog(self):
        """Открывает диалог для написания отзыва"""
        try:
            from review_dialog import ReviewDialog
            dialog = ReviewDialog(
                self,
                self.current_username,
                self.house_id,
                self.address,
                booking_id=self.available_booking_id
            )

            # После закрытия диалога обновляем список отзывов
            dialog.wait_window()
            self.load_reviews()
            self.setup_ui()  # Пересоздаем интерфейс с обновленными данными

        except Exception as e:
            print(f"Ошибка при открытии окна отзыва: {e}")
            messagebox.showerror("Ошибка", "Не удалось открыть окно отзыва")

    def create_review_card(self, parent, review):
        """Создает карточку отзыва"""
        card = customtkinter.CTkFrame(parent, fg_color=theme_manager.house_frame_color, corner_radius=10)
        card.pack(fill="x", pady=5)

        # Заголовок с именем и датой
        header_frame = customtkinter.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 5))

        name_label = customtkinter.CTkLabel(
            header_frame,
            text=f"👤 {review['username']}",
            text_color=theme_manager.text_color,
            font=("Arial", 12, "bold")
        )
        name_label.pack(side="left")

        date_label = customtkinter.CTkLabel(
            header_frame,
            text=review['created_at'][:10],
            text_color="#6B7280",
            font=("Arial", 10)
        )
        date_label.pack(side="right")

        # Звезды рейтинга
        stars_frame = customtkinter.CTkFrame(card, fg_color="transparent")
        stars_frame.pack(anchor="w", padx=15, pady=(0, 5))

        for i in range(5):
            star_text = "⭐" if i < review['rating'] else "☆"
            star_label = customtkinter.CTkLabel(
                stars_frame,
                text=star_text,
                text_color="#F59E0B",
                font=("Arial", 12)
            )
            star_label.pack(side="left")

        # Текст отзыва
        if review['comment']:
            comment_label = customtkinter.CTkLabel(
                card,
                text=review['comment'],
                text_color=theme_manager.text_color_secondary,
                font=("Arial", 11),
                wraplength=500,
                justify="left"
            )
            comment_label.pack(anchor="w", padx=15, pady=(0, 15))

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