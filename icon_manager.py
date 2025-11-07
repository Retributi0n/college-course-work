from PIL import Image
import tempfile

def set_window_icon(window):
    """Простая версия - используем только относительные пути"""
    try:
        # Пробуем напрямую
        window.iconbitmap("icons/icon.ico")
        print("Иконка установлена через iconbitmap")
        return True
    except:
        try:
            # Пробуем через временный файл
            img = Image.open("icons/icon.png")
            ico_path = tempfile.gettempdir() + "/temp_icon.ico"
            img.save(ico_path)
            window.iconbitmap(ico_path)
            print("Иконка установлена через временный файл")
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False