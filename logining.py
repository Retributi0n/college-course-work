import customtkinter
import hashlib
from databases.app_database import search_user
from main_content import MainApp
from databases.app_database import get_user_group
from theme_manager import theme_manager


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

class LoginWindow(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Domovoy - Вход в аккаунт")
        self.geometry("1280x720")
        self.configure(fg_color=theme_manager.main_frame_color)
        set_window_icon(self)

        custom_font = customtkinter.CTkFont(
            size=14
        )

        self.grid_columnconfigure(0, weight=1)
        for i in range(6):  # Добавил еще одну строку для заголовка
            self.grid_rowconfigure(i, weight=1 if i in [0, 5] else 0)

        center_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=1, column=0, rowspan=4, sticky="nsew")
        center_frame.grid_columnconfigure(0, weight=1)

        self.title_label = customtkinter.CTkLabel(center_frame,
                                                  text="Вход в аккаунт",
                                                  text_color=theme_manager.text_color,
                                                  font=("Arial", 24, "bold")  # Можно настроить шрифт
                                                  )
        self.title_label.grid(row=0, column=0, padx=20, pady=(0, 30))

        self.login = customtkinter.CTkEntry(center_frame,
                                            placeholder_text="Логин",
                                            fg_color=theme_manager.house_frame_color,
                                            text_color=theme_manager.text_color,
                                            placeholder_text_color=theme_manager.text_color_secondary,
                                            border_color=theme_manager.text_color_secondary,
                                            width=300,
                                            height=40,
                                            validate="key",
                                            validatecommand=(self.register(self.validate_login), '%P'),
                                            font=custom_font
                                            )

        self.login.grid(row=1, column=0, padx=20, pady=10)

        self.password = customtkinter.CTkEntry(center_frame,
                                               placeholder_text="Пароль",
                                               fg_color=theme_manager.house_frame_color,
                                               text_color=theme_manager.text_color,
                                               placeholder_text_color=theme_manager.text_color_secondary,
                                               border_color=theme_manager.text_color_secondary,
                                               width=300,
                                               height=40,
                                               show="✱︎",
                                               font=custom_font
                                               )

        self.password.grid(row=2, column=0, padx=20, pady=10)

        button_frame = customtkinter.CTkFrame(center_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=20, pady=20)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.auth = customtkinter.CTkButton(button_frame,
                                            text="Вход",
                                            command=self.auth_button_callback,
                                            fg_color=theme_manager.button_primary,
                                            text_color="#111318",
                                            height=40,
                                            font=custom_font
                                            )

        self.auth.grid(row=3, column=0, padx=(0, 5), sticky="ew")

        self.registration = customtkinter.CTkButton(button_frame,
                                                    text="Регистрация",
                                                    command=self.reg_button_callback,
                                                    fg_color=theme_manager.button_primary,
                                                    text_color="#111318",
                                                    height=40,
                                                    font=custom_font
                                                    )

        self.registration.grid(row=3, column=1, padx=(5, 0), sticky="ew")

        self.countdown_label = customtkinter.CTkLabel(center_frame,
                                                      text="",
                                                      text_color="#111318",
                                                      font=("Arial", 16)
                                                      )
        self.countdown_label.grid(row=4, column=0, padx=20, pady=10)

    def validate_login(self, new_text):
        # максимум 32 символа
        if len(new_text) >= 32:
            return False
        if new_text == "":
            return True
        return all(c.isalnum() or c == '_' for c in new_text)

    def reg_button_callback(self):
        self.destroy()
        from registration import RegisterWindow
        register_window = RegisterWindow()
        register_window.mainloop()

    def auth_button_callback(self):
        # Сохраняем значения ДО уничтожения окна
        username = self.login.get()
        password = self.password.get()

        if not all([username, password]):
            self.countdown_label.configure(text="Заполните все поля!", text_color='#EF4444')
            return

        hash_object = hashlib.sha256(password.encode())
        hex_digest = hash_object.hexdigest()

        if search_user(username, hex_digest) == True:
            print('Вход')
            self.countdown_label.configure(text=" ")

            # Получаем группу пользователя
            user_group = get_user_group(username)

            # Уничтожаем окно входа
            self.destroy()

            # Запускаем главное приложение
            MainApp(username, user_group).mainloop()

        else:
            self.countdown_label.configure(text="Неправильный логин или пароль!", text_color="#EF4444")
