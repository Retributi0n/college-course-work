import customtkinter


def create_date_selectors(self):
    """Поля для ввода дат вручную"""
    date_frame = customtkinter.CTkFrame(self)
    date_frame.pack(pady=20)

    # Дата заезда
    start_frame = customtkinter.CTkFrame(date_frame, fg_color="transparent")
    start_frame.pack(pady=10)

    customtkinter.CTkLabel(start_frame, text="📅 Заезд:").pack(side="left", padx=5)

    self.start_day = customtkinter.CTkEntry(start_frame, width=40, placeholder_text="ДД")
    self.start_day.pack(side="left", padx=2)

    self.start_month = customtkinter.CTkEntry(start_frame, width=40, placeholder_text="ММ")
    self.start_month.pack(side="left", padx=2)

    self.start_year = customtkinter.CTkEntry(start_frame, width=60, placeholder_text="ГГГГ")
    self.start_year.pack(side="left", padx=2)

    # Кнопка "Сегодня"
    today_btn = customtkinter.CTkButton(
        start_frame,
        text="Сегодня",
        width=80,
        command=self.set_today_start
    )
    today_btn.pack(side="left", padx=10)

    # Аналогично для даты выезда...

    # Кнопка рассчитать
    calc_btn = customtkinter.CTkButton(
        date_frame,
        text="🔄 Рассчитать",
        command=self.calculate_total
    )
    calc_btn.pack(pady=10)