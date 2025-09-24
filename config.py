# config.py
import os

# Новые переменные для отправки почты
EMAIL_ACCOUNT_OUT = ""
EMAIL_PASSWORD_OUT = "" # Используйте пароль приложения, а не основной пароль
SMTP_SERVER_OUT = ""
EMAIL_RECEIVER = ""



# --- Настройки авторизации ---
# URL страницы входа
LOGIN_URL = "https://IP:8098/bioLogin.do"

# Учетные данные для входа
USERNAME = ""
PASSWORD = ""

# ID полей на странице входа
USERNAME_FIELD_ID = "username"
PASSWORD_FIELD_ID = "password"
SUBMIT_BUTTON_ID = "test"
OK_BUTTON_ID_PREFIX = "editForm"

# --- Настройки Selenium ---
# Путь к профилю Chrome. Используется для сохранения сессии.
# Рекомендуется использовать уникальный путь для каждого пользователя.
CHROME_PROFILE_PATH = os.path.join(os.path.expanduser("~"), "selenium_profiles", "stat2serg_profile")

# Имя для уникального логгера. Это гарантирует, что логи
# этого проекта не будут смешиваться с другими.
LOGGER_NAME = "stat2serg_logger"


# --- Префиксы для динамических ID элементов ---
START_TIME_FIELD_ID_PREFIX = "startTime" 
END_TIME_FIELD_ID_PREFIX = "endTime"

# --- Текст кнопки "Экспорт" ---
EXPORT_BUTTON_TEXT = "Export"

ENCRYPTION_PASSWORD = None  # Вы сказали, что вам не нужно шифрование.
#FILE_FORMAT_TEXT = "XLS" # Или "CSV", "PDF" и т.д.
FILE_FORMAT_TEXT = "CSV" # Или "CSV", "PDF" и т.д.
