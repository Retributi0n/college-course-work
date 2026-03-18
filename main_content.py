import customtkinter
from datetime import timedelta
import sqlite3
import os
from tkinter import messagebox, filedialog
from databases.app_database import add_object, change_object_info, delete_object, verify_object


def set_window_icon(window):
    """Устанавливает иконку для окна"""
    try:
        from PIL import Image, ImageTk

        # Загружаем изображение
        image = Image.open("icons/icon.png")

        # Создаем PhotoImage для иконки окна
        photo_image = ImageTk.PhotoImage(image)

        # Устанавливаем иконку
        window.after(100, lambda: window.iconphoto(True, photo_image))

        # Сохраняем ссылку, чтобы сборщик мусора не удалил изображение
        window._icon = photo_image

        print("Иконка успешно установлена")
        return True

    except Exception as e:
        print(f"Иконка не установлена: {e}")
        return False

class MainApp(customtkinter.CTk):
    def __init__(self, username, user_group):
        super().__init__()
        self.username = username
        self.user_group = user_group
        self.title("Domovoy - Бронирование домов")
        self.geometry("1600x1020")
        self.configure(fg_color="#FFFFFF")
        set_window_icon(self)

        # Настройка сетки
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_content()
        self.load_houses()

    def update_house_rating(self, house_id):
        """
        Обновляет отображение рейтинга для конкретного дома
        Вызывается после добавления отзыва
        """
        # Перезагружаем все дома (простой способ)
        self.load_houses()

        # Или можно найти конкретную карточку и обновить только ее
        # Но для простоты используем перезагрузку

    def show_house_reviews(self, house_id, address):
        """Показывает окно с отзывами о доме"""
        try:
            from review_dialog import ReviewsWindow
            ReviewsWindow(
                self,
                house_id,
                address,
                current_username=self.username  # Передаем имя пользователя
            )
        except Exception as e:
            print(f"Ошибка при открытии отзывов: {e}")
            messagebox.showerror("Ошибка", "Не удалось открыть окно отзывов")

    def logout(self):
        """Выход из аккаунта"""
        result = messagebox.askyesno(
            "Подтверждение",
            "Вы действительно хотите выйти из аккаунта?"
        )

        if result:
            # Закрываем текущее окно
            self.destroy()

            # Открываем окно входа
            from logining import LoginWindow
            login_window = LoginWindow()
            login_window.mainloop()

    def update_favorites_counter(self):
        """Обновляет счетчик избранного прямо в кнопке"""
        from databases.app_database import get_favorites_count

        try:
            # Получаем актуальное количество избранного
            fav_count = get_favorites_count(self.username)
            print(f"🔄 Обновление счетчика: {fav_count}")

            # Получаем боковую панель
            sidebar = self.grid_slaves(row=0, column=0)[0]

            # Перебираем все дочерние элементы в поисках кнопки избранного
            for child in sidebar.winfo_children():
                # Пропускаем не-кнопки
                if not isinstance(child, customtkinter.CTkButton):
                    continue

                try:
                    btn_text = child.cget("text")
                    # Ищем кнопку с избранным (по символу звезды)
                    if btn_text and "⭐" in btn_text:
                        # Формируем новый текст
                        if fav_count > 0:
                            new_text = f"⭐ Избранное • {fav_count}"
                        else:
                            new_text = "⭐ Избранное"

                        print(f"  Обновляем текст: '{btn_text}' -> '{new_text}'")
                        child.configure(text=new_text)

                        # Принудительно обновляем кнопку
                        child.update()
                        break
                except Exception as e:
                    print(f"  Ошибка при проверке кнопки: {e}")
                    continue

        except Exception as e:
            print(f"❌ Ошибка при обновлении счетчика: {e}")

    def show_all_houses(self):
        """Возврат к показу всех домов"""
        self.load_houses()

    def toggle_favorite(self, house_id, card):
        """
        Добавляет или удаляет дом из избранного (без всплывающих окон)
        """
        from databases.app_database import add_to_favorites, remove_from_favorites, is_favorite, get_favorites_count

        # Проверяем текущий статус
        is_fav = is_favorite(self.username, house_id)

        # Сохраняем текущее количество до операции
        old_count = get_favorites_count(self.username)

        if is_fav:
            # Удаляем из избранного
            if remove_from_favorites(self.username, house_id):
                print(f"✅ Дом {house_id} удален из избранного")
                # Обновляем кнопку в карточке
                for child in card.winfo_children():
                    if isinstance(child, customtkinter.CTkButton):
                        try:
                            btn_text = child.cget("text")
                            if btn_text in ["⭐", "☆"]:
                                child.configure(text="☆", fg_color="#6B7280")
                                break
                        except:
                            continue

                # Проверяем, не был ли это последний элемент
                new_count = get_favorites_count(self.username)

                # Если мы в режиме просмотра избранного
                try:
                    current_title = self.houses_frame.master.winfo_children()[0].cget("text")
                    if "⭐ Избранное" in current_title:
                        if new_count == 0:
                            # Если это был последний элемент, показываем пустой список
                            self.show_favorites()
                        else:
                            # Иначе просто обновляем счетчик и заголовок
                            title_label = self.houses_frame.master.winfo_children()[0]
                            if isinstance(title_label, customtkinter.CTkLabel):
                                title_label.configure(text=f"⭐ Избранное ({new_count})")
                except:
                    pass
        else:
            # Добавляем в избранное
            if add_to_favorites(self.username, house_id):
                print(f"✅ Дом {house_id} добавлен в избранное")
                # Обновляем кнопку в карточке
                for child in card.winfo_children():
                    if isinstance(child, customtkinter.CTkButton):
                        try:
                            btn_text = child.cget("text")
                            if btn_text in ["⭐", "☆"]:
                                child.configure(text="⭐", fg_color="#F59E0B")
                                break
                        except:
                            continue

        # Обновляем счетчик в боковой панели
        self.update_favorites_counter()

        # Принудительно обновляем интерфейс
        self.update_idletasks()

    def create_rounded_image(self, image_path, size, corner_radius=15):
        """Создает изображение со скругленными углами"""
        try:
            from PIL import Image, ImageDraw

            # Открываем и изменяем размер изображения
            image = Image.open(image_path)
            image = image.resize(size, Image.Resampling.LANCZOS)

            # Создаем маску с скругленными углами
            mask = Image.new('L', size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle([(0, 0), size], radius=corner_radius, fill=255)

            # Применяем маску к изображению
            result = Image.new('RGBA', size, (0, 0, 0, 0))
            result.putalpha(mask)
            result.paste(image, (0, 0), mask)

            return customtkinter.CTkImage(light_image=result, size=size)

        except Exception as e:
            print(f"Ошибка создания скругленного изображения: {e}")
            return None

    def show_all_users(self):
        """Показывает список всех пользователей"""
        import sqlite3

        conn = sqlite3.connect('databases/app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, user_group FROM users ORDER BY id")
        users = cursor.fetchall()
        conn.close()

        # Создаем простое окно с информацией
        from tkinter import Toplevel, Text, Scrollbar
        import tkinter as tk

        users_window = Toplevel(self)
        users_window.title("Все пользователи")
        users_window.geometry("400x500")
        users_window.configure(bg="white")

        # Создаем текстовое поле со скроллом
        text_frame = tk.Frame(users_window, bg="white")
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget = Text(text_frame, wrap="word", font=("Arial", 10), bg="white")
        scrollbar = Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Добавляем данные
        if users:
            for user in users:
                user_id, username, user_group = user
                text_widget.insert("end", f"ID: {user_id}\n")
                text_widget.insert("end", f"Имя: {username}\n")
                text_widget.insert("end", f"Группа: {user_group}\n")
                text_widget.insert("end", "-" * 30 + "\n\n")
        else:
            text_widget.insert("end", "Нет пользователей в базе данных")

        text_widget.configure(state="disabled")  # Только для чтения

        # Кнопка закрытия
        close_btn = tk.Button(users_window, text="Закрыть",
                              command=users_window.destroy,
                              bg="#6366F1", fg="white", font=("Arial", 12))
        close_btn.pack(pady=10)

    def setup_sidebar(self):
        # Боковая панель для фильтров
        sidebar = customtkinter.CTkFrame(self, fg_color="#F1F3F4", width=300, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        sidebar.grid_propagate(False)

        # Настраиваем веса строк для правильного расположения
        sidebar.grid_rowconfigure(98, weight=0)  # Все обычные строки
        sidebar.grid_rowconfigure(99, weight=1)  # Растягивающаяся строка (пустая)
        sidebar.grid_rowconfigure(100, weight=0)  # Нижний фрейм с кнопкой выхода

        # Информация о пользователе
        user_info_label = customtkinter.CTkLabel(sidebar,
                                                 text=f"Пользователь: {self.username}\nГруппа: {self.user_group}",
                                                 text_color="#111318",
                                                 font=("Arial", 12))
        user_info_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Заголовок фильтров
        filter_label = customtkinter.CTkLabel(sidebar,
                                              text="Фильтры",
                                              text_color="#111318",
                                              font=("Arial", 18, "bold"))
        filter_label.grid(row=1, column=0, padx=20, pady=(20, 10), sticky="w")

        # Поля для фильтрации
        self.area_filter = customtkinter.CTkEntry(sidebar,
                                                  placeholder_text="Площадь (Кв/М)",
                                                  fg_color="#F0F0F0",
                                                  text_color="#111318",
                                                  placeholder_text_color="#6B7280",
                                                  border_color="#F0F0F0",
                                                  height=40)
        self.area_filter.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.floor_filter = customtkinter.CTkEntry(sidebar,
                                                   placeholder_text="Этаж",
                                                   fg_color="#F0F0F0",
                                                   text_color="#111318",
                                                   placeholder_text_color="#6B7280",
                                                   border_color="#F0F0F0",
                                                   height=40)
        self.floor_filter.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.rooms_filter = customtkinter.CTkEntry(sidebar,
                                                   placeholder_text="Количество комнат",
                                                   fg_color="#F0F0F0",
                                                   text_color="#111318",
                                                   placeholder_text_color="#6B7280",
                                                   border_color="#F0F0F0",
                                                   height=40)
        self.rooms_filter.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        self.price_filter = customtkinter.CTkEntry(sidebar,
                                                   placeholder_text="Макс. цена",
                                                   fg_color="#F0F0F0",
                                                   text_color="#111318",
                                                   placeholder_text_color="#6B7280",
                                                   border_color="#F0F0F0",
                                                   height=40)
        self.price_filter.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        # Кнопки фильтров
        filter_button = customtkinter.CTkButton(sidebar,
                                                text="Применить фильтры",
                                                command=self.apply_filters,
                                                fg_color="#FF740F",
                                                text_color="#111318",
                                                height=40)
        filter_button.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        clear_button = customtkinter.CTkButton(sidebar,
                                               text="Сбросить фильтры",
                                               command=self.clear_filters,
                                               fg_color="#6B7280",
                                               text_color="#FFFFFF",
                                               height=40)
        clear_button.grid(row=7, column=0, padx=20, pady=5, sticky="ew")

        # Кнопка добавления (только для зарегистрированных пользователей)
        if self.user_group in ['admin', 'user']:
            add_button = customtkinter.CTkButton(sidebar,
                                                 text="+ Добавить объект",
                                                 command=self.show_add_dialog,
                                                 fg_color="#10B981",
                                                 text_color="#FFFFFF",
                                                 height=40)
            add_button.grid(row=8, column=0, padx=20, pady=(20, 5), sticky="ew")

        # ===== ДЛЯ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ (НЕ АДМИН) =====
        if self.user_group == 'user':
            # Кнопка "Мои бронирования"
            my_bookings_btn = customtkinter.CTkButton(
                sidebar,
                text="📋 Мои бронирования",
                command=self.show_my_bookings,
                fg_color="#3B82F6",
                text_color="#FFFFFF",
                height=40
            )
            my_bookings_btn.grid(row=9, column=0, padx=20, pady=5, sticky="ew")

            # Кнопка "Избранное"
            from databases.app_database import get_favorites_count
            fav_count = get_favorites_count(self.username)
            btn_text = "⭐ Избранное"
            if fav_count > 0:
                btn_text = f"⭐ Избранное • {fav_count}"

            favorites_btn = customtkinter.CTkButton(
                sidebar,
                text=btn_text,
                command=self.show_favorites,
                fg_color="#F59E0B",
                text_color="#FFFFFF",
                height=40,
                anchor="w"
            )
            favorites_btn.grid(row=10, column=0, padx=20, pady=5, sticky="ew")

        # ===== ДЛЯ АДМИНИСТРАТОРА =====
        if self.user_group == 'admin':
            # Кнопка просмотра непроверенных объектов
            unverified_button = customtkinter.CTkButton(
                sidebar,
                text="⏳ Непроверенные объекты",
                command=self.show_unverified,
                fg_color="#F59E0B",
                text_color="#FFFFFF",
                height=40
            )
            unverified_button.grid(row=9, column=0, padx=20, pady=5, sticky="ew")

            # Кнопка просмотра всех бронирований
            all_bookings_btn = customtkinter.CTkButton(
                sidebar,
                text="📊 Все бронирования",
                command=self.show_all_bookings,
                fg_color="#8B5CF6",
                text_color="#FFFFFF",
                height=40
            )
            all_bookings_btn.grid(row=10, column=0, padx=20, pady=5, sticky="ew")

            # Разделитель админки
            separator = customtkinter.CTkFrame(sidebar, height=2, fg_color="#D1D5DB")
            separator.grid(row=11, column=0, padx=20, pady=20, sticky="ew")

            # Заголовок админки
            admin_label = customtkinter.CTkLabel(
                sidebar,
                text="Админ-панель",
                text_color="#111318",
                font=("Arial", 16, "bold")
            )
            admin_label.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="w")

            # Кнопка добавления пользователя
            add_user_btn = customtkinter.CTkButton(
                sidebar,
                text="➕ Добавить пользователя",
                command=self.show_add_user_dialog,
                fg_color="#8B5CF6",
                text_color="#FFFFFF",
                height=40
            )
            add_user_btn.grid(row=13, column=0, padx=20, pady=5, sticky="ew")

            # Кнопка просмотра всех пользователей
            view_users_btn = customtkinter.CTkButton(
                sidebar,
                text="👥 Все пользователи",
                command=self.show_all_users,
                fg_color="#6366F1",
                text_color="#FFFFFF",
                height=40
            )
            view_users_btn.grid(row=14, column=0, padx=20, pady=5, sticky="ew")

        # ===== КНОПКА ВЫХОДА (ДЛЯ ВСЕХ) =====
        bottom_frame = customtkinter.CTkFrame(sidebar, fg_color="transparent")
        bottom_frame.grid(row=100, column=0, sticky="ew", padx=20, pady=(20, 20))
        bottom_frame.grid_columnconfigure(0, weight=1)

        # Разделитель
        separator_exit = customtkinter.CTkFrame(bottom_frame, height=2, fg_color="#D1D5DB")
        separator_exit.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Кнопка выхода
        exit_btn = customtkinter.CTkButton(
            bottom_frame,
            text="🚪 Выйти из аккаунта",
            command=self.logout,
            fg_color="#EF4444",
            text_color="#FFFFFF",
            height=40,
            font=("Arial", 12, "bold")
        )
        exit_btn.grid(row=1, column=0, sticky="ew")


    def setup_main_content(self):
        # Основная область контента
        main_frame = customtkinter.CTkFrame(self, fg_color="#FFFFFF")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Заголовок
        title_label = customtkinter.CTkLabel(main_frame,
                                             text="Дома для бронирования",  # Изменили текст
                                             text_color="#111318",
                                             font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        # Фрейм для карточек домов
        self.houses_frame = customtkinter.CTkScrollableFrame(main_frame,
                                                             fg_color="#FFFFFF")
        self.houses_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.houses_frame.grid_columnconfigure(0, weight=1)

        # Привязка колесика мыши для скроллинга
        self.bind_mouse_wheel()

    def show_my_bookings(self):
        """Показывает бронирования текущего пользователя"""
        try:
            from bookings_view import BookingsWindow
            BookingsWindow(self, self.username, self.user_group)
        except Exception as e:
            print(f"Ошибка при открытии бронирований: {e}")
            messagebox.showerror("Ошибка", "Не удалось открыть окно бронирований")

    def show_all_bookings(self):
        """Для админа - показывает все бронирования"""
        if self.user_group == 'admin':
            try:
                from bookings_view import AdminBookingsWindow
                AdminBookingsWindow(self, self.username)
            except Exception as e:
                print(f"Ошибка при открытии всех бронирований: {e}")
                messagebox.showerror("Ошибка", "Не удалось открыть окно всех бронирований")
        else:
            messagebox.showerror("Ошибка", "Эта функция доступна только администраторам")

    def show_favorites(self):
        """
        Показывает только избранные дома
        """
        from databases.app_database import get_user_favorites

        # Очищаем существующие карточки
        for widget in self.houses_frame.winfo_children():
            widget.destroy()

        # Загружаем избранные дома
        favorites = get_user_favorites(self.username)

        if not favorites:
            # Используем pack для сообщения об отсутствии избранного
            no_data_label = customtkinter.CTkLabel(
                self.houses_frame,
                text="⭐ У вас пока нет избранных домов",
                text_color="#6B7280",
                font=("Arial", 16)
            )
            no_data_label.pack(pady=50)

            # Добавляем кнопку "Назад" отдельно
            back_btn = customtkinter.CTkButton(
                self.houses_frame,
                text="← Назад к общему списку",
                command=self.show_all_houses,
                fg_color="#6B7280",
                width=200,
                height=35
            )
            back_btn.pack(pady=10)

            # Обновляем счетчик (будет 0)
            self.update_favorites_counter()
            return  # Выходим из метода, дальше ничего не выполняем

        # Если есть избранные дома - создаем карточки
        for i, house in enumerate(favorites):
            self.create_house_card(house, i)

        # Добавляем кнопку "Назад" после всех карточек
        back_frame = customtkinter.CTkFrame(self.houses_frame, fg_color="transparent")
        back_frame.grid(row=len(favorites), column=0, pady=20)

        back_btn = customtkinter.CTkButton(
            back_frame,
            text="← Назад к общему списку",
            command=self.show_all_houses,
            fg_color="#6B7280",
            width=200,
            height=35
        )
        back_btn.pack()

        # Обновляем заголовок
        title_label = self.houses_frame.master.winfo_children()[0]
        if isinstance(title_label, customtkinter.CTkLabel):
            title_label.configure(text=f"⭐ Избранное ({len(favorites)})")

        # Обновляем счетчик в боковой панели
        self.update_favorites_counter()

    def show_add_user_dialog(self):
        """Открывает диалог добавления пользователя"""
        # Проверяем, не открыт ли уже диалог
        if hasattr(self, '_add_user_dialog') and self._add_user_dialog.winfo_exists():
            self._add_user_dialog.lift()  # Поднимаем существующий диалог
            self._add_user_dialog.focus_set()
            return

        # Создаем новый диалог
        self._add_user_dialog = self.AddUserDialog(self)

        # Отслеживаем закрытие диалога
        self._add_user_dialog.bind("<Destroy>", lambda e: self.on_add_user_dialog_closed())

    def on_add_user_dialog_closed(self):
        """Вызывается при закрытии диалога добавления пользователя"""
        if hasattr(self, '_add_user_dialog'):
            del self._add_user_dialog

    def check_user_dialog_closed(self, dialog):
        """Проверяет, закрыт ли диалог добавления пользователя"""
        if not dialog.winfo_exists():
            # Диалог закрыт, можно обновить что-то если нужно
            pass
        else:
            self.after(100, self.check_user_dialog_closed, dialog)

    class AddUserDialog(customtkinter.CTkToplevel):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.title("Добавить пользователя")
            self.geometry("400x450")
            self.configure(fg_color="#FFFFFF")
            self.resizable(False, False)

            # НЕ делаем grab_set сразу - окно еще не готово
            self.transient(parent)

            # Заголовок
            title_label = customtkinter.CTkLabel(self,
                                                 text="Добавление пользователя",
                                                 text_color="#111318",
                                                 font=("Arial", 20, "bold"))
            title_label.pack(pady=20)

            # Поля ввода с использованием нового метода create_input_field
            self.username_entry = self.create_input_field("Имя пользователя", 0)
            self.password_entry = self.create_input_field("Пароль", 1, show="•")
            self.password_repeat_entry = self.create_input_field("Повторите пароль", 2, show="•")

            # Выбор группы
            group_frame = customtkinter.CTkFrame(self, fg_color="transparent")
            group_frame.pack(pady=10)

            customtkinter.CTkLabel(group_frame,
                                   text="Группа:",
                                   font=("Arial", 12, "bold")).pack(side="left", padx=(0, 10))

            self.group_var = customtkinter.StringVar(value="user")
            self.group_menu = customtkinter.CTkOptionMenu(group_frame,
                                                          values=["user", "admin"],
                                                          variable=self.group_var,
                                                          width=100)
            self.group_menu.pack(side="left")

            # Сообщение об ошибке/успехе
            self.message_label = customtkinter.CTkLabel(self,
                                                        text="",
                                                        text_color="#EF4444",
                                                        font=("Arial", 12))
            self.message_label.pack(pady=10)

            # Кнопки
            button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
            button_frame.pack(pady=20)

            cancel_btn = customtkinter.CTkButton(button_frame,
                                                 text="Отмена",
                                                 fg_color="#6B7280",
                                                 command=self.destroy)
            cancel_btn.pack(side="left", padx=10)

            add_btn = customtkinter.CTkButton(button_frame,
                                              text="Добавить",
                                              fg_color="#10B981",
                                              command=self.add_user)
            add_btn.pack(side="left", padx=10)

            # Через 100мс, когда окно будет готово, центрируем и захватываем фокус
            self.after(100, self.finalize_dialog)

        def create_input_field(self, placeholder, row_offset, show=""):
            """Создает поле ввода с меткой"""
            frame = customtkinter.CTkFrame(self, fg_color="transparent")
            frame.pack(pady=(0, 10))

            label = customtkinter.CTkLabel(frame,
                                           text=placeholder + ":",
                                           font=("Arial", 12, "bold"),
                                           width=150,
                                           anchor="w")
            label.pack(side="left", padx=(20, 10))

            entry = customtkinter.CTkEntry(frame,
                                           placeholder_text=placeholder,
                                           show=show,
                                           width=200)
            entry.pack(side="left")

            return entry

        def finalize_dialog(self):
            """Завершает настройку диалога после его отображения"""
            self.center_window()
            self.grab_set()
            self.focus_set()
            self.lift()  # Поднимаем окно поверх других
            self.protocol("WM_DELETE_WINDOW", self.destroy)  # Обработка закрытия

        def center_window(self):
            """Центрирует окно относительно родителя"""
            self.update_idletasks()  # Обновляем информацию о размерах

            # Получаем размеры родительского окна
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()

            # Получаем размеры этого окна
            width = self.winfo_width()
            height = self.winfo_height()

            # Вычисляем позицию для центрирования
            x = parent_x + (parent_width - width) // 2
            y = parent_y + (parent_height - height) // 2

            # Устанавливаем позицию
            self.geometry(f"{width}x{height}+{x}+{y}")

        def add_user(self):
            """Добавляет пользователя в БД"""
            username = self.username_entry.get().strip()
            password = self.password_entry.get()
            password_repeat = self.password_repeat_entry.get()
            user_group = self.group_var.get()

            # Валидация
            if not all([username, password, password_repeat]):
                self.message_label.configure(text="Заполните все поля", text_color="#EF4444")
                return

            if password != password_repeat:
                self.message_label.configure(text="Пароли не совпадают", text_color="#EF4444")
                return

            if len(password) < 4:
                self.message_label.configure(text="Пароль слишком короткий", text_color="#EF4444")
                return

            # Проверяем имя пользователя
            if not all(c.isalnum() or c == '_' for c in username):
                self.message_label.configure(text="Имя пользователя может содержать только буквы, цифры и _",
                                             text_color="#EF4444")
                return

            # Добавляем в БД (используем функцию из app_database.py)
            from databases.app_database import add_user
            success = add_user(username, password, user_group)

            if success:
                self.message_label.configure(text="✅ Пользователь добавлен!", text_color="#10B981")
                # Закрываем окно через 2 секунды
                self.after(2000, self.destroy)
            else:
                self.message_label.configure(text="❌ Пользователь уже существует", text_color="#EF4444")

    def bind_mouse_wheel(self):
        """Упрощенная привязка колесика мыши"""

        def on_mouse_wheel(event):
            try:
                self.houses_frame._parent_canvas.yview_scroll(int(-event.delta / 120), "units")
            except Exception as e:
                print(f"Ошибка скроллинга: {e}")

        self.houses_frame.bind("<MouseWheel>", on_mouse_wheel)

        # Для Linux
        self.houses_frame.bind("<Button-4>", lambda e: self.houses_frame._parent_canvas.yview_scroll(-1, "units"))
        self.houses_frame.bind("<Button-5>", lambda e: self.houses_frame._parent_canvas.yview_scroll(1, "units"))

    def load_houses(self, filters=None, show_unverified=False):
        # Очищаем существующие карточки
        for widget in self.houses_frame.winfo_children():
            widget.destroy()

        # Сбрасываем заголовок на стандартный
        title_label = self.houses_frame.master.winfo_children()[0]
        if isinstance(title_label, customtkinter.CTkLabel):
            title_label.configure(text="Дома для бронирования")

        # Загружаем данные из БД
        conn = sqlite3.connect('databases/app.db')
        cursor = conn.cursor()

        query = "SELECT * FROM houses"
        params = []

        where_conditions = []

        # Для обычных пользователей показываем только проверенные объекты
        if self.user_group == 'user' and not show_unverified:
            where_conditions.append("verified = 1")
        # Для админа в обычном режиме тоже показываем только проверенные
        elif self.user_group == 'admin' and not show_unverified:
            where_conditions.append("verified = 1")
        # Для админа в режиме просмотра непроверенных
        elif show_unverified:
            where_conditions.append("verified = 0")

        if filters:
            if filters.get('area'):
                where_conditions.append("area = ?")
                params.append(filters['area'])
            if filters.get('floor'):
                where_conditions.append("floor = ?")
                params.append(filters['floor'])
            if filters.get('rooms_amount'):
                where_conditions.append("rooms_amount = ?")
                params.append(filters['rooms_amount'])
            if filters.get('price'):
                where_conditions.append("CAST(REPLACE(REPLACE(price, '₽', ''), ' ', '') AS INTEGER) <= ?")
                params.append(filters['price'])

        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)

        print(f"Выполняем запрос: {query}")  # Для отладки
        print(f"Параметры: {params}")  # Для отладки

        cursor.execute(query, params)
        houses = cursor.fetchall()
        conn.close()

        print(f"Найдено домов: {len(houses)}")  # Для отладки

        # Создаем карточки для каждого дома
        for i, house in enumerate(houses):
            self.create_house_card(house, i)

        # Если дома не найдены
        if not houses:
            no_data_label = customtkinter.CTkLabel(self.houses_frame,
                                                   text="Дома не найдены" if not show_unverified else "Непроверенных домов нет",
                                                   text_color="#6B7280",
                                                   font=("Arial", 16))
            no_data_label.grid(row=0, column=0, padx=20, pady=20)

    def show_unverified(self):
        """Показать непроверенные объекты (только для админа)"""
        if self.user_group == 'admin':
            self.load_houses(show_unverified=True)
        else:
            from tkinter import messagebox
            messagebox.showerror("Ошибка", "Эта функция доступна только для администраторов")

    def create_house_card(self, house, index):
        card = customtkinter.CTkFrame(self.houses_frame,
                                      fg_color="#F1F3F4",
                                      corner_radius=10)
        card.grid(row=index, column=0, sticky="ew", padx=(0, 10), pady=5)
        card.grid_columnconfigure(1, weight=1)

        house_id, address, area, floor, rooms, price, image_path, verified, created_by = house

        # Добавляем badge верификации
        if not verified and self.user_group == 'admin':
            verification_badge = customtkinter.CTkLabel(card,
                                                        text="⏳ НЕ ПРОВЕРЕНО",
                                                        text_color="#EF4444",
                                                        font=("Arial", 10, "bold"))
            verification_badge.grid(row=0, column=2, padx=15, pady=(15, 0), sticky="ne")

        # Картинка (если есть)
        if image_path and os.path.exists(image_path):
            try:
                # Создаем скругленное изображение
                house_image = self.create_rounded_image(image_path, (150, 100), 12)
                if house_image:
                    image_label = customtkinter.CTkLabel(card,
                                                         image=house_image,
                                                         text="",
                                                         fg_color="transparent")
                    image_label.grid(row=0, column=0, rowspan=3, padx=15, pady=15, sticky="nsew")
                else:
                    raise Exception("Не удалось создать скругленное изображение")

            except Exception as e:
                print(f"Ошибка загрузки изображения: {e}")
                # Заглушка
                no_image_label = customtkinter.CTkLabel(card,
                                                        text="🏠",
                                                        text_color="#6B7280",
                                                        font=("Arial", 24))
                no_image_label.grid(row=0, column=0, rowspan=3, padx=15, pady=15, sticky="nsew")
        else:
            # Заглушка если нет картинки
            no_image_label = customtkinter.CTkLabel(card,
                                                    text="🏠",
                                                    text_color="#6B7280",
                                                    font=("Arial", 24))
            no_image_label.grid(row=0, column=0, rowspan=3, padx=15, pady=15, sticky="nsew")

        # Адрес
        address_label = customtkinter.CTkLabel(card,
                                               text=f"📍 {address}",
                                               text_color="#111318",
                                               font=("Arial", 16, "bold"),
                                               anchor="w")
        address_label.grid(row=0, column=1, columnspan=2, padx=15, pady=(15, 5), sticky="w")

        # ===== РЕЙТИНГ =====
        from databases.app_database import get_house_average_rating
        rating_info = get_house_average_rating(house_id)

        avg_rating = rating_info['average']
        reviews_count = rating_info['count']

        # Фрейм для рейтинга и кнопки просмотра
        rating_frame = customtkinter.CTkFrame(card, fg_color="transparent")
        rating_frame.grid(row=0, column=2, padx=(0, 15), pady=(15, 5), sticky="e")

        if reviews_count > 0:
            rating_text = f"{avg_rating} ⭐ ({reviews_count})"
        else:
            rating_text = "0.0 ⭐ (0)"

        rating_label = customtkinter.CTkLabel(
            rating_frame,
            text=rating_text,
            text_color="#F59E0B",
            font=("Arial", 12, "bold")
        )
        rating_label.pack(side="right", padx=(0, 5))

        # Кнопка просмотра отзывов
        view_reviews_btn = customtkinter.CTkButton(
            rating_frame,
            text="👁",
            width=30,
            height=30,
            fg_color="#3B82F6",
            command=lambda hid=house_id, addr=address: self.show_house_reviews(hid, addr)
        )
        view_reviews_btn.pack(side="right", padx=(0, 10))

        # КНОПКА ИЗБРАННОГО (только для зарегистрированных пользователей)
        if self.user_group in ['user']:
            from databases.app_database import is_favorite
            is_fav = is_favorite(self.username, house_id)

            fav_btn = customtkinter.CTkButton(
                card,
                text="⭐" if is_fav else "☆",
                width=40,
                height=40,
                fg_color="#F59E0B" if is_fav else "#6B7280",
                text_color="#FFFFFF",
                font=("Arial", 16),
                command=lambda hid=house_id, btn=None: self.toggle_favorite(hid, card)
            )
            fav_btn.grid(row=0, column=3, padx=(0, 15), pady=(15, 5), sticky="e")
            fav_btn.lift()

        # Детали
        details_text = f"🏘️ Площадь (Кв/м): {area} | 🏢 Этаж: {floor} | 🚪 Комнат: {rooms}"
        details_label = customtkinter.CTkLabel(card,
                                               text=details_text,
                                               text_color="#6B7280",
                                               font=("Arial", 12),
                                               anchor="w")
        details_label.grid(row=1, column=1, columnspan=2, padx=15, pady=5, sticky="w")

        # Цена
        formatted_price = self.format_price(price)
        price_label = customtkinter.CTkLabel(card,
                                             text=f"Цена: {formatted_price}",
                                             text_color="#111318",
                                             font=("Arial", 14, "bold"),
                                             anchor="w")
        price_label.grid(row=2, column=1, padx=15, pady=(5, 15), sticky="w")

        # Кнопки действий
        button_frame = customtkinter.CTkFrame(card, fg_color="transparent")
        button_frame.grid(row=2, column=2, padx=15, pady=(5, 15), sticky="e")

        # Кнопка "Календарь"
        if self.user_group in ['user']:
            calendar_btn = customtkinter.CTkButton(
                button_frame,
                text="📅 Календарь",
                width=100,
                height=30,
                fg_color="#8B5CF6",
                text_color="#FFFFFF",
                font=("Arial", 12),
                command=lambda h=house_id, a=address: self.show_calendar(h, a)
            )
            calendar_btn.pack(side="right", padx=5)

        # Кнопка бронирования
        if self.user_group in ['user']:
            book_btn = customtkinter.CTkButton(
                button_frame,
                text="📅 Забронировать",
                width=140,
                height=35,
                fg_color="#10B981",
                text_color="#FFFFFF",
                font=("Arial", 12, "bold"),
                command=lambda h=house: self.book_house(h)
            )
            book_btn.pack(side="right", padx=5)

        # Кнопки админа
        if self.user_group == 'admin':
            if not verified:
                verify_btn = customtkinter.CTkButton(button_frame,
                                                     text="✓ Верифицировать",
                                                     width=130,
                                                     height=30,
                                                     fg_color="#10B981",
                                                     text_color="#FFFFFF",
                                                     command=lambda hid=house_id: self.verify_house(hid))
                verify_btn.pack(side="right", padx=(5, 0))

            edit_btn = customtkinter.CTkButton(button_frame,
                                               text="✏ Редактировать",
                                               width=130,
                                               height=30,
                                               fg_color="#3B82F6",
                                               text_color="#FFFFFF",
                                               command=lambda h=house: self.show_edit_dialog(h))
            edit_btn.pack(side="right", padx=(5, 0))

            delete_btn = customtkinter.CTkButton(button_frame,
                                                 text="🗑 Удалить️",
                                                 width=100,
                                                 height=30,
                                                 fg_color="#EF4444",
                                                 text_color="#FFFFFF",
                                                 command=lambda hid=house_id: self.delete_house(hid))
            delete_btn.pack(side="right", padx=(5, 0))

    def book_house(self, house):
        """Новая функция бронирования (дипломная работа)"""
        house_id, address, area, floor, rooms, price, image_path, verified, created_by = house

        # Открываем диалог бронирования
        from booking import BookingDialog  # Создашь отдельный файл
        dialog = BookingDialog(self, house)

    def verify_house(self, house_id):
        """Верификация дома (только для админа)"""
        if verify_object(house_id):
            messagebox.showinfo("Успех", "Объект успешно верифицирован")
            self.load_houses()
        else:
            messagebox.showerror("Ошибка", "Не удалось верифицировать объект")

    def format_price(self, price_str):
        """Форматирует цену с разделителями тысяч"""
        try:
            # Убираем все нецифровые символы
            clean_price = ''.join(c for c in price_str if c.isdigit())
            if clean_price:
                price_num = int(clean_price)
                # Форматируем с пробелами как разделителями тысяч
                return "{:,}".format(price_num).replace(',', ' ') + " ₽"
            return price_str
        except ValueError:
            return price_str

    def apply_filters(self):
        filters = {}
        if self.area_filter.get():
            try:
                filters['area'] = int(self.area_filter.get())  # Преобразуем в число
            except ValueError:
                messagebox.showerror("Ошибка", "Площадь должна быть числом")
                return
        if self.floor_filter.get():
            try:
                filters['floor'] = int(self.floor_filter.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Этаж должен быть числом")
                return
        if self.rooms_filter.get():
            try:
                filters['rooms_amount'] = int(self.rooms_filter.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Количество комнат должно быть числом")
                return
        if self.price_filter.get():
            try:
                filters['price'] = int(self.price_filter.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Цена должна быть числом")
                return

        self.load_houses(filters)

    def clear_filters(self):
        self.area_filter.delete(0, 'end')
        self.floor_filter.delete(0, 'end')
        self.rooms_filter.delete(0, 'end')
        self.price_filter.delete(0, 'end')
        self.load_houses()

    def show_add_dialog(self):
        # Проверяем, не открыт ли уже диалог
        if hasattr(self, '_add_edit_dialog') and self._add_edit_dialog.winfo_exists():
            self._add_edit_dialog.lift()
            self._add_edit_dialog.focus_set()
            return

        self._add_edit_dialog = AddEditDialog(self, "Добавить объект", self.username)
        self._add_edit_dialog.bind("<Destroy>", lambda e: self.on_add_edit_dialog_closed())
        self.after(100, self.check_dialog_closed, self._add_edit_dialog)

    def show_edit_dialog(self, house):
        # Проверяем, не открыт ли уже диалог
        if hasattr(self, '_add_edit_dialog') and self._add_edit_dialog.winfo_exists():
            self._add_edit_dialog.lift()
            self._add_edit_dialog.focus_set()
            return

        self._add_edit_dialog = AddEditDialog(self, "Редактировать объект", self.username, house)
        self._add_edit_dialog.bind("<Destroy>", lambda e: self.on_add_edit_dialog_closed())
        self.after(100, self.check_dialog_closed, self._add_edit_dialog)

    def on_add_edit_dialog_closed(self):
        """Вызывается при закрытии диалога добавления/редактирования"""
        if hasattr(self, '_add_edit_dialog'):
            del self._add_edit_dialog

    def check_dialog_closed(self, dialog):
        """Проверяет, закрыт ли диалог и обновляет список"""
        if not dialog.winfo_exists():
            self.load_houses()
            # Очищаем ссылку на диалог
            if hasattr(self, '_add_edit_dialog') and self._add_edit_dialog == dialog:
                del self._add_edit_dialog
        else:
            self.after(100, self.check_dialog_closed, dialog)

    def delete_house(self, house_id):
        result = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этот объект?")
        if result:
            if delete_object(house_id):
                messagebox.showinfo("Успех", "Объект успешно удален")
                self.load_houses()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить объект")

    def show_calendar(self, house_id, address):
        """Показывает календарь занятости для дома"""
        from calendar_widget import AvailabilityCalendar

        # Создаем новое окно
        calendar_window = customtkinter.CTkToplevel(self)
        calendar_window.title(f"Календарь занятости - {address}")
        calendar_window.geometry("500x500")
        calendar_window.configure(fg_color="#FFFFFF")
        calendar_window.transient(self)

        # Центрируем окно
        calendar_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - calendar_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - calendar_window.winfo_height()) // 2
        calendar_window.geometry(f"+{x}+{y}")

        # Добавляем календарь
        calendar = AvailabilityCalendar(
            calendar_window,
            house_id,
            on_date_selected=lambda d: self.on_date_selected_from_calendar(d, house_id, address)
        )
        calendar.pack(fill="both", expand=True, padx=20, pady=20)

        # Кнопка закрытия
        close_btn = customtkinter.CTkButton(
            calendar_window,
            text="Закрыть",
            fg_color="#6B7280",
            command=calendar_window.destroy
        )
        close_btn.pack(pady=(0, 20))

    def on_date_selected_from_calendar(self, date, house_id, address):
        """Обработчик выбора даты из календаря"""
        from datetime import datetime

        # Получаем полную информацию о доме
        conn = sqlite3.connect('databases/app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM houses WHERE id = ?", (house_id,))
        house = cursor.fetchone()
        conn.close()

        if house:
            # Открываем окно бронирования с выбранной датой
            from booking import BookingDialog
            dialog = BookingDialog(self, house)

            # Устанавливаем выбранную дату как дату заезда
            dialog.start_day.delete(0, 'end')
            dialog.start_day.insert(0, date.strftime("%d"))
            dialog.start_month.delete(0, 'end')
            dialog.start_month.insert(0, date.strftime("%m"))
            dialog.start_year.delete(0, 'end')
            dialog.start_year.insert(0, date.strftime("%Y"))

            # Устанавливаем следующий день как дату выезда
            next_day = date + timedelta(days=1)
            dialog.end_day.delete(0, 'end')
            dialog.end_day.insert(0, next_day.strftime("%d"))
            dialog.end_month.delete(0, 'end')
            dialog.end_month.insert(0, next_day.strftime("%m"))
            dialog.end_year.delete(0, 'end')
            dialog.end_year.insert(0, next_day.strftime("%Y"))

            # Сразу рассчитываем стоимость
            dialog.calculate_total()


class AddEditDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, title, username, house=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x750")
        self.configure(fg_color="#FFFFFF")
        self.resizable(False, False)

        self.house = house
        self.parent = parent
        self.username = username
        self.image_path = None

        # НЕ делаем grab_set сразу
        self.transient(parent)

        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        for i in range(14):
            self.grid_rowconfigure(i, weight=0)

        # Заголовок
        title_label = customtkinter.CTkLabel(self,
                                             text=title,
                                             text_color="#111318",
                                             font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Поля формы с labels
        self.create_form_field_with_label("Адрес", "address", 1)
        self.create_form_field_with_label("Площадь (Кв/м)", "area", 3)
        self.create_form_field_with_label("Этаж", "floor", 5)
        self.create_form_field_with_label("Количество комнат", "rooms", 7)
        self.create_form_field_with_label("Цена", "price", 9, "Например: 50000₽")

        # Поле для загрузки изображения
        image_label = customtkinter.CTkLabel(self,
                                             text="Изображение",
                                             text_color="#111318",
                                             font=("Arial", 12, "bold"),
                                             anchor="w")
        image_label.grid(row=11, column=0, padx=20, pady=(10, 0), sticky="w")

        image_button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        image_button_frame.grid(row=12, column=0, padx=20, pady=(2, 10), sticky="ew")
        image_button_frame.grid_columnconfigure(0, weight=1)
        image_button_frame.grid_columnconfigure(1, weight=1)

        self.image_btn = customtkinter.CTkButton(image_button_frame,
                                                 text="Выбрать изображение",
                                                 command=self.select_image,
                                                 fg_color="#6B7280",
                                                 text_color="#FFFFFF",
                                                 height=40)
        self.image_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.remove_image_btn = customtkinter.CTkButton(image_button_frame,
                                                        text="Удалить изображение",
                                                        command=self.remove_image,
                                                        fg_color="#EF4444",
                                                        text_color="#FFFFFF",
                                                        height=40)
        self.remove_image_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.image_path_label = customtkinter.CTkLabel(self,
                                                       text="Изображение не выбрано",
                                                       text_color="#6B7280",
                                                       font=("Arial", 10))
        self.image_path_label.grid(row=13, column=0, padx=20, pady=(0, 10), sticky="w")

        # Заполняем поля если редактируем
        if house:
            self.fill_form(house)

        # Кнопки
        button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=14, column=0, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        cancel_btn = customtkinter.CTkButton(button_frame,
                                             text="Отмена",
                                             fg_color="#6B7280",
                                             text_color="#FFFFFF",
                                             height=40,
                                             command=self.destroy)
        cancel_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        save_btn = customtkinter.CTkButton(button_frame,
                                           text="Сохранить",
                                           fg_color="#FF740F",
                                           text_color="#111318",
                                           height=40,
                                           command=self.save_house)
        save_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")

        # Через 100мс завершаем настройку
        self.after(100, self.finalize_dialog)

    def finalize_dialog(self):
        """Завершает настройку диалога после его отображения"""
        self._setup_dialog()

    def _setup_dialog(self):
        """Настройка диалога после полной инициализации"""
        self.grab_set()
        self.focus_set()
        self.lift()

        # Центрируем относительно родительского окна
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


    def fill_form(self, house):
        house_id, address, area, floor, rooms, price, image_path, verified, created_by = house
        self.address_entry.insert(0, address)
        self.area_entry.insert(0, area)
        self.floor_entry.insert(0, str(floor))
        self.rooms_entry.insert(0, str(rooms))
        self.price_entry.insert(0, price)

        if image_path:
            self.image_path = image_path
            self.image_path_label.configure(
                text=f"Выбрано: {os.path.basename(image_path)}",
                text_color="#111318"
            )

    def save_house(self):
        # Получаем данные из формы
        address = self.address_entry.get()
        area = self.area_entry.get()
        floor = self.floor_entry.get()
        rooms = self.rooms_entry.get()
        price = self.price_entry.get()

        # Валидация
        if not all([address, area, floor, rooms, price]):
            messagebox.showerror("Ошибка", "Заполните все поля")
            return

        try:
            floor = int(floor)
            rooms = int(rooms)
        except ValueError:
            messagebox.showerror("Ошибка", "Этаж и количество комнат должны быть числами")
            return

        # Получаем ID пользователя для created_by
        conn = sqlite3.connect('databases/app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (self.username,))
        user_result = cursor.fetchone()
        user_id = user_result[0] if user_result else None
        conn.close()

        # Сохраняем в БД
        if self.house:
            # Редактирование - получаем ID текущего дома
            house_id = self.house[0]
            if change_object_info(house_id, address, area, floor, rooms, price, self.image_path):
                messagebox.showinfo("Успех", "Объект успешно обновлен")
                self.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить объект")
        else:
            # Добавление
            if add_object(address, area, floor, rooms, price, self.image_path, user_id):
                messagebox.showinfo("Успех", "Объект успешно добавлен и ожидает проверки")
                self.destroy()
            else:
                messagebox.showerror("Ошибка", "Объект с таким адресом уже существует")


if __name__ == "__main__":
    app = MainApp("guest", "user")  # Для тестирования
    app.mainloop()