import customtkinter
import sqlite3
import os
from tkinter import messagebox, filedialog
from PIL import Image
from main_content_database import add_object, change_object_info, delete_object, verify_object


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
        self.title("Domovoy - Аренда домов")
        self.geometry("1280x720")
        self.configure(fg_color="#FFFFFF")
        set_window_icon(self)

        # Настройка сетки
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_content()
        self.load_houses()

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

    def setup_sidebar(self):
        # Боковая панель для фильтров
        sidebar = customtkinter.CTkFrame(self, fg_color="#F1F3F4", width=300, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        sidebar.grid_propagate(False)

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

        # Кнопка просмотра непроверенных (только для админа)
        if self.user_group == 'admin':
            unverified_button = customtkinter.CTkButton(sidebar,
                                                        text="Непроверенные объекты",
                                                        command=self.show_unverified,
                                                        fg_color="#F59E0B",
                                                        text_color="#FFFFFF",
                                                        height=40)
            unverified_button.grid(row=9, column=0, padx=20, pady=5, sticky="ew")

    def setup_main_content(self):
        # Основная область контента
        main_frame = customtkinter.CTkFrame(self, fg_color="#FFFFFF")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Заголовок
        title_label = customtkinter.CTkLabel(main_frame,
                                             text="Доступные дома для аренды",
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

        # Загружаем данные из БД
        conn = sqlite3.connect('premises.db')
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
                # Преобразуем текстовую цену в число для сравнения
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
        self.load_houses(show_unverified=True)

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
                                                         fg_color="transparent")  # прозрачный фон
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

        # Кнопка "Купить" для всех пользователей
        buy_btn = customtkinter.CTkButton(button_frame,
                                          text="🛒 Купить",
                                          width=100,
                                          height=30,
                                          fg_color="#10B981",
                                          text_color="#FFFFFF",
                                          command=lambda h=house: self.buy_house(h))
        buy_btn.pack(side="right", padx=(5, 0))

        # Кнопки админа
        if self.user_group == 'admin':
            if not verified:
                verify_btn = customtkinter.CTkButton(button_frame,
                                                     text="✓ Верифицировать",
                                                     width=120,
                                                     height=30,
                                                     fg_color="#10B981",
                                                     text_color="#FFFFFF",
                                                     command=lambda hid=house_id: self.verify_house(hid))
                verify_btn.pack(side="right", padx=(5, 0))

            edit_btn = customtkinter.CTkButton(button_frame,
                                               text="✏ Редактировать",
                                               width=120,
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

    def buy_house(self, house):
        """Функция покупки дома"""
        house_id, address, area, floor, rooms, price, image_path, verified, created_by = house
        messagebox.showinfo("Покупка", f"Вы приобрели дом по адресу: {address}\nЦена: {price}")

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
        dialog = AddEditDialog(self, "Добавить объект", self.username)
        self.after(100, self.check_dialog_closed, dialog)

    def show_edit_dialog(self, house):
        dialog = AddEditDialog(self, "Редактировать объект", self.username, house)
        self.after(100, self.check_dialog_closed, dialog)

    def check_dialog_closed(self, dialog):
        """Проверяет, закрыт ли диалог и обновляет список"""
        if not dialog.winfo_exists():
            self.load_houses()
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

        # Центрируем диалог
        self.transient(parent)
        self.after(100, self._setup_dialog)

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

    def create_form_field_with_label(self, label_text, field_name, row, placeholder=None):
        """Создает label и поле ввода"""
        # Label
        label = customtkinter.CTkLabel(self,
                                       text=label_text,
                                       text_color="#111318",
                                       font=("Arial", 12, "bold"),
                                       anchor="w")
        label.grid(row=row, column=0, padx=20, pady=(5, 0), sticky="w")

        # Entry field
        if placeholder is None:
            placeholder = label_text

        entry = customtkinter.CTkEntry(self,
                                       placeholder_text=placeholder,
                                       fg_color="#F0F0F0",
                                       text_color="#111318",
                                       placeholder_text_color="#6B7280",
                                       border_color="#F0F0F0",
                                       height=40)
        entry.grid(row=row + 1, column=0, padx=20, pady=(2, 10), sticky="ew")

        # Сохраняем поле как атрибут
        setattr(self, f"{field_name}_entry", entry)
        return entry

    def select_image(self):
        """Выбор изображения"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )
        if file_path:
            self.image_path = file_path
            self.image_path_label.configure(
                text=f"Выбрано: {os.path.basename(file_path)}",
                text_color="#111318"
            )

    def remove_image(self):
        """Удаление выбранного изображения"""
        self.image_path = None
        self.image_path_label.configure(
            text="Изображение не выбрано",
            text_color="#6B7280"
        )

    def _setup_dialog(self):
        """Настройка диалога после полной инициализации"""
        self.grab_set()
        self.focus_set()

        # Центрируем относительно родительского окна
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - self.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - self.winfo_height()) // 2
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
        conn = sqlite3.connect('users.db')
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