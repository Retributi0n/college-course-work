import customtkinter
import hashlib
import threading
import time
import re

from databases import auth_database


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

class RegisterWindow(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Domovoy - Создание аккаунта")
        self.geometry("1280x720")
        self.configure(fg_color="#FFFFFF")
        set_window_icon(self)

        custom_font = customtkinter.CTkFont(
            size=14
        )

        # Настраиваем grid для центрирования
        self.grid_columnconfigure(0, weight=1)
        for i in range(6):  # Добавил еще одну строку для заголовка
            self.grid_rowconfigure(i, weight=1 if i in [0, 5] else 0)

        # Центрирующий фрейм
        center_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=1, column=0, rowspan=4, sticky="nsew")
        center_frame.grid_columnconfigure(0, weight=1)

        self.back_button = customtkinter.CTkButton(self,
                                                   text="← Назад",
                                                   command=self.back_to_login,
                                                   fg_color="transparent",  # Прозрачный фон
                                                   text_color="#6B7280",  # Серый текст
                                                   hover_color="#F0F0F0",  # Светлый фон при наведении
                                                   width=80,
                                                   height=30,
                                                   font=custom_font,
                                                   anchor="w"  # Выравнивание текста влево
                                                   )
        self.back_button.place(x=20, y=20)

        self.title_label = customtkinter.CTkLabel(center_frame,
                                                  text="Регистрация",
                                                  text_color="#111318",
                                                  font=("Arial", 24, "bold")  # Можно настроить шрифт
                                                  )
        self.title_label.grid(row=0, column=0, padx=20, pady=(0, 30))

        # Остальные элементы
        self.login = customtkinter.CTkEntry(center_frame,
                                            placeholder_text="Логин",
                                            fg_color="#F0F0F0",
                                            text_color="#111318",
                                            placeholder_text_color="#6B7280",
                                            border_color="#F0F0F0",
                                            width=300,
                                            height=40,
                                            validate="key",
                                            validatecommand=(self.register(self.validate_login), '%P'),
                                            font=custom_font
                                            )
        self.login.grid(row=1, column=0, padx=20, pady=10)

        self.password = customtkinter.CTkEntry(center_frame,
                                               placeholder_text="Пароль",
                                               fg_color="#F0F0F0",
                                               text_color="#111318",
                                               placeholder_text_color="#6B7280",
                                               border_color="#F0F0F0",
                                               show="✱︎",
                                               width=300,
                                               height=40,
                                               font=custom_font
                                               )
        self.password.grid(row=2, column=0, padx=20, pady=10)

        self.password_repeat = customtkinter.CTkEntry(center_frame,
                                                      placeholder_text="Повтор пароля",
                                                      fg_color="#F0F0F0",
                                                      text_color="#111318",
                                                      placeholder_text_color="#6B7280",
                                                      border_color="#F0F0F0",
                                                      show="✱︎",
                                                      width=300,
                                                      height=40,
                                                      font=custom_font
                                                      )
        self.password_repeat.grid(row=3, column=0, padx=20, pady=10)

        # Метка для отображения требований к паролю
        self.password_requirements = customtkinter.CTkLabel(center_frame,
                                                            text="Пароль должен содержать: минимум 8 символов, заглавные и строчные буквы, цифры и специальные символы (@$!%*?&)",
                                                            text_color="#6B7280",
                                                            font=("Arial", 12),
                                                            wraplength=300)
        self.password_requirements.grid(row=4, column=0, padx=20, pady=(0, 10))

        self.auth = customtkinter.CTkButton(center_frame,
                                            text="Зарегистрироваться",
                                            command=self.button_callback,
                                            fg_color="#FF740F",
                                            text_color="#111318",
                                            width=300,
                                            height=40,
                                            font=custom_font
                                            )
        self.auth.grid(row=5, column=0, padx=20, pady=10)

        self.countdown_label = customtkinter.CTkLabel(center_frame,
                                                      text="",
                                                      text_color="#111318",
                                                      font=("Arial", 16)
                                                      )
        self.countdown_label.grid(row=6, column=0, padx=20, pady=10)

        self.progressbar = customtkinter.CTkProgressBar(center_frame,
                                                        width=300,
                                                        height=10,
                                                        progress_color="#FF740F"
                                                        )
        self.progressbar.grid(row=7, column=0, padx=20, pady=10)
        self.progressbar.grid_remove()  # ← Скрываем сразу
        self.progressbar.set(0)

    def validate_password(self, password):
        """
        Проверяет пароль по условиям:
        - Минимум 8 символов
        - Хотя бы одна заглавная буква
        - Хотя бы одна строчная буква
        - Хотя бы одна цифра
        - Хотя бы один специальный символ (@$!%*?&)
        """
        if len(password) < 8:
            return False, "Пароль должен содержать минимум 8 символов"

        if not re.search(r'[A-Z]', password):
            return False, "Пароль должен содержать хотя бы одну заглавную букву"

        if not re.search(r'[a-z]', password):
            return False, "Пароль должен содержать хотя бы одну строчную букву"

        if not re.search(r'\d', password):
            return False, "Пароль должен содержать хотя бы одну цифру"

        if not re.search(r'[@$!%*?&]', password):
            return False, "Пароль должен содержать хотя бы один специальный символ (@$!%*?&)"

        return True, "Пароль соответствует требованиям"

    def button_callback(self):
        username = self.login.get()
        password = self.password.get()
        repeat_password = self.password_repeat.get()

        # Очищаем предыдущие ошибки
        self.countdown_label.configure(
            text="",
            text_color="#111318"
        )

        # Проверяем что все поля заполнены
        if not all([username, password, repeat_password]):
            self.countdown_label.configure(text="Заполните все поля!", text_color='#EF4444')
            return

        # Проверяем пароль на соответствие требованиям
        is_valid_password, password_message = self.validate_password(password)
        if not is_valid_password:
            self.countdown_label.configure(text=password_message, text_color="#EF4444")
            return

        # Проверяем совпадение паролей
        if password != repeat_password:
            self.countdown_label.configure(text="Пароли не совпадают!", text_color="#EF4444")
            return

        # Если все ок - регистрируем
        hash_object = hashlib.sha256(password.encode())
        hex_digest = hash_object.hexdigest()

        # Добавляем пользователя в базу
        if auth_database.add_user(username, hex_digest, 'user'):
            # Успешная регистрация
            self.progressbar.grid()
            self.countdown_label.grid()
            self.countdown_label.configure(text_color="#111318")
            threading.Thread(target=self.countdown, daemon=True).start()
        else:
            self.countdown_label.configure(text="Пользователь уже существует!", text_color="#EF4444")

    def countdown(self):
        """Обратный отсчет"""
        for i in range(5, 0, -1):
            # Обновляем UI в главном потоке
            self.after(0, lambda i=i: self.update_countdown(i))
            time.sleep(1)

        # После отсчета закрываем окно
        self.after(0, self.close_and_open_login)

    def update_countdown(self, seconds):
        """Обновляет текст и прогрессбар"""
        self.countdown_label.configure(text=f"Вас перенесет в окно входа через {seconds} секунд...")
        self.progressbar.set((5 - seconds) / 5)  # Прогресс от 0 до 1

    def close_and_open_login(self):
        """Закрывает текущее окно и открывает вход"""
        self.destroy()
        from logining import LoginWindow
        login_window = LoginWindow()
        login_window.mainloop()

    def validate_login(self, new_text):
        # максимум 32 символа
        if len(new_text) >= 32:
            return False
        if new_text == "":
            return True
        return all(c.isalnum() or c == '_' for c in new_text)

    def back_to_login(self):
        """Возврат к окну входа"""
        self.destroy()
        from logining import LoginWindow
        login_window = LoginWindow()
        login_window.mainloop()
