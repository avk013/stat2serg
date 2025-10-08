import logging
import time
import os
import re
from date_selector import DateSelector
from email_sender import EmailSender
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from config import (
    LOGIN_URL, USERNAME, PASSWORD, USERNAME_FIELD_ID,
    PASSWORD_FIELD_ID, SUBMIT_BUTTON_ID, CHROME_PROFILE_PATH, LOGGER_NAME, FILE_FORMAT_TEXT,
    EXPORT_BUTTON_TEXT, OK_BUTTON_ID_PREFIX,
    EMAIL_ACCOUNT_OUT, EMAIL_PASSWORD_OUT, SMTP_SERVER_OUT, EMAIL_RECEIVER
)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(LOGGER_NAME)

OK_BUTTON_ID_PREFIX = "editForm"
#FILE_FORMAT_TEXT = "CSV"

class AuthWorker:
    def __init__(self):
        self.driver = None
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "My_Exports")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"Создана папка для загрузок: {self.download_dir}")

    def login(self):
        try:
            logger.info("Инициализация браузера Chrome...")
            chrome_options = Options()
            if CHROME_PROFILE_PATH:
                chrome_options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
            chrome_options.add_argument("--start-maximized")

            prefs = {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_argument('--ignore-certificate-errors')
           # если нужно присмотреть бракзер
            chrome_options.add_argument("--headless=new")


            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.get(LOGIN_URL + "?lang=ru_RU")
            logger.info("Переход на страницу входа с языком ru_RU.")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, USERNAME_FIELD_ID))
            )
            logger.info("Страница загружена. Вводим данные.")
            self.driver.find_element(By.ID, USERNAME_FIELD_ID).send_keys(USERNAME)
            self.driver.find_element(By.ID, PASSWORD_FIELD_ID).send_keys(PASSWORD)
            submit_button = self.driver.find_element(By.ID, SUBMIT_BUTTON_ID)
            submit_button.click()
            time.sleep(5)
            if self.driver.current_url != LOGIN_URL:
                logger.info("Авторизация успешна.")
                return True
            else:
                logger.error("Авторизация не удалась. Проверьте логин и пароль.")
                return False
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Ошибка во время авторизации: {e}")
            return False
        except WebDriverException as e:
            logger.error(f"Ошибка веб-драйвера: {e}")
            return False

    def get_driver(self):
        return self.driver

    def cleanup(self):
        if self.driver:
            logger.info("Закрываем браузер.")
            self.driver.quit()

class Exporter:
    def __init__(self, driver):
        self.driver = driver

    def click_export_button_sequentially(self):
        try:
            logger.info("Поиск и клик по кнопке 'Экспорт'...")
            export_button_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//div[text()='{EXPORT_BUTTON_TEXT}']"))
            )
            export_button_div.click()
            logger.info("Кнопка 'Экспорт' нажата. Ожидаем всплывающее окно...")
            return True
        except Exception as e:
            logger.error(f"Не удалось кликнуть по кнопке 'Экспорт': {e}")
            return False

    def interact_with_export_popup(self):
        logger.info("Начинаем комплексную диагностику модального окна... [%s]", datetime.now().strftime("%Y-%m-%d %H:%M:%S EEST"))
        try:
            logger.info("Ожидаем появления кнопки 'ОК' во всплывающем окне...")
            ok_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[starts-with(@id, '{OK_BUTTON_ID_PREFIX}') and text()='ОК']"))
            )
            logger.info("Кнопка 'ОК' найдена.")

            try:
                self.driver.execute_script("document.querySelector('.dhxwin_fr_cover').style.display = 'none';")
                logger.info("Оверлей dhxwin_fr_cover скрыт.")
            except Exception as e:
                logger.warning(f"Не удалось скрыть оверлей: {e}")

            logger.info("Шаг 1: Пробуем кликнуть по опции 'Нет'...")
            try:
                no_radio_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "no"))
                )
                logger.info("Элемент 'Нет' по ID найден. Пробуем кликнуть через JavaScript.")
                self.driver.execute_script(
                    """
                    var input = arguments[0];
                    input.checked = true;
                    var event = new Event('change', { bubbles: true });
                    input.dispatchEvent(event);
                    """, no_radio_input
                )
                logger.info("Успешный клик по опции 'Нет' через JavaScript (ID).")
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Не удалось кликнуть по 'Нет' через ID. Причина: {e}")
                logger.info("Пробуем альтернативный вариант.")
                no_label = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Нет')]"))
                )
                logger.info("Элемент 'Нет' по тексту найден. Пробуем кликнуть через JavaScript.")
                self.driver.execute_script("arguments[0].click();", no_label)
                logger.info("Успешный клик по опции 'Нет' через JavaScript (XPATH).")
                time.sleep(1)

            try:
                logger.info("Пробуем найти поле для пароля пользователя...")
                user_password_field = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.ID, "loginPwd"))
                )
                if user_password_field.is_displayed() and user_password_field.is_enabled():
                    logger.info("Поле для пароля найдено и активно. Имитируем ввод.")
                    user_password_field.click()
                    user_password_field.clear()
                    user_password_field.send_keys(PASSWORD)
                    logger.info("Пароль пользователя введен.")
                    time.sleep(5)
                    self.driver.find_element(By.TAG_NAME, "body").click()
                    time.sleep(2)
                else:
                    logger.info("Поле для пароля пользователя не видимо или не активно, пропускаем этот шаг.")
            except (TimeoutException, NoSuchElementException):
                logger.info("Поле для пароля пользователя не найдено, пропускаем этот шаг.")

            logger.info(f"Шаг 3: Пытаемся установить формат '{FILE_FORMAT_TEXT}' через DHTMLX Combo...")
            try:
                combo_container = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'search-combo-box') and contains(@comid, 'reportType')]"))
                )
                combo_id = combo_container.get_attribute('comid')
                logger.info(f"Найден combo-box с comid: {combo_id}")

                self.driver.execute_script(
                    f'ZKUI.Combo.get("#{combo_id}").combo.setComboValue("{FILE_FORMAT_TEXT}");'
                )
                time.sleep(1)

                selected_value = self.driver.find_element(By.CSS_SELECTOR, "input[name='reportType']").get_attribute("value")
                logger.info(f"Значение reportType после установки через Combo: {selected_value}")
                if selected_value.lower() != FILE_FORMAT_TEXT.lower():
                    raise Exception(f"Формат не изменился на {FILE_FORMAT_TEXT}")

                self.driver.execute_script(
                    'document.querySelector("input[name=\'reportType_new_value\']").value = "true";'
                )
                new_value_flag = self.driver.find_element(By.CSS_SELECTOR, "input[name='reportType_new_value']").get_attribute("value")
                logger.info(f"reportType_new_value установлено: {new_value_flag}")
            except Exception as e:
                logger.warning(f"Не удалось установить формат через DHTMLX Combo: {e}. Пробуем через скрытые поля...")

                self.driver.execute_script(
                    """
                    var input = document.querySelector("input[name='reportType']");
                    input.value = arguments[0];
                    var event = new Event('change', { bubbles: true });
                    input.dispatchEvent(event);
                    """, FILE_FORMAT_TEXT
                )
                self.driver.execute_script(
                    'document.querySelector("input[name=\'reportType_new_value\']").value = "true";'
                )
                time.sleep(1)
                selected_value = self.driver.find_element(By.CSS_SELECTOR, "input[name='reportType']").get_attribute("value")
                new_value_flag = self.driver.find_element(By.CSS_SELECTOR, "input[name='reportType_new_value']").get_attribute("value")
                logger.info(f"Формат установлен через скрытые поля: reportType={selected_value}, reportType_new_value={new_value_flag}")

            logger.info("Шаг 4: Проверяем данные формы перед отправкой...")
            try:
                export_form = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dhxwin_active')]//form[contains(@id, 'editForm')]"))
                )
                form_id = export_form.get_attribute("id")
                logger.info(f"Найдена форма с ID: {form_id}")
                form_data = self.driver.execute_script(f"return $('#{form_id}').serialize();")
                logger.info(f"Данные формы перед отправкой: {form_data}")
            except Exception as e:
                logger.warning(f"Не удалось найти форму динамически: {e}. Используем резервный вариант.")
                form_data = self.driver.execute_script("return $('form').serialize();")
                logger.info(f"Данные формы (резервный вариант): {form_data}")

            logger.info("Шаг 5: Нажимаем кнопку 'ОК' через JavaScript...")
            self.driver.execute_script("arguments[0].removeAttribute('disabled');", ok_button)
            self.driver.execute_script("arguments[0].click();", ok_button)
            logger.info("Кнопка 'ОК' нажата. Начинается загрузка файла.")

            try:
                WebDriverWait(self.driver, 30).until(
                    EC.staleness_of(ok_button)
                )
                logger.info("Модальное окно закрылось.")
            except TimeoutException:
                logger.warning("Модальное окно не закрылось автоматически в течение 30 секунд.")

            return True
        except Exception as e:
            logger.error(f"Критическая ошибка при работе со всплывающим окном: {e}")
            time.sleep(30)
            return False

def find_new_file(download_dir, initial_files, timeout=60, check_interval=1):
    logger.info("Начинаем поиск нового файла в папке загрузок...")
    end_time = time.time() + timeout
    while time.time() < end_time:
        current_files = os.listdir(download_dir)
        new_files = list(set(current_files) - set(initial_files))

        if new_files:
            file_name = new_files[0]
            file_path = os.path.join(download_dir, file_name)

            initial_size = -1
            for _ in range(5):
                try:
                    current_size = os.path.getsize(file_path)
                    if current_size > 0 and current_size == initial_size:
                        logger.info(f"✅ Новый файл найден и полностью скачан: {file_name}")
                        return file_path
                    initial_size = current_size
                except Exception as e:
                    logger.warning(f"Ошибка при проверке размера файла: {e}")
                time.sleep(check_interval)

            logger.warning(f"Найден файл {file_name}, но он, возможно, еще скачивается.")
            return file_path

        time.sleep(check_interval)

    logger.error("❌ Не удалось найти новый файл в папке загрузок в течение установленного таймаута.")
    return None

if __name__ == "__main__":
    auth_worker = AuthWorker()
    if auth_worker.login():
        logger.info("Авторизация прошла успешно. Переходим к экспорту.")
        time.sleep(15)
        driver = auth_worker.get_driver()
        date_selector = DateSelector(driver)

        now = datetime.now()
        days_since_monday = now.weekday()
        current_monday = now - timedelta(days=days_since_monday)
        last_monday = current_monday - timedelta(weeks=1)

        start_date_str = last_monday.strftime("%Y-%m-%d 00:00:00")
        end_date_str = current_monday.strftime("%Y-%m-%d 00:00:00")

        success_start = date_selector.select_date_and_time('Время с', start_date_str)
        success_end = False
        if success_start:
            success_end = date_selector.select_date_and_time('До', end_date_str)

        if success_start and success_end:
            logger.info("Обе даты установлены. Нажимаем на кнопку 'Поиск'.")
            search_button_xpath = "//div[contains(@class, 'search_button_new') and @title='Поиск']"
            try:
                search_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, search_button_xpath))
                )
                search_button.click()
                logger.info("✅ Кнопка 'Поиск' нажата.")
                time.sleep(5)

                initial_files = os.listdir(auth_worker.download_dir)

                exporter = Exporter(driver)
                if exporter.click_export_button_sequentially():
                    if exporter.interact_with_export_popup():
                        logger.info("Взаимодействие с всплывающим окном завершено. Ожидаем скачивания файла...")

                        downloaded_file_path = find_new_file(auth_worker.download_dir, initial_files)

                        if downloaded_file_path:
                            logger.info(f"Готов к отправке файл: {downloaded_file_path}")

                            email_sender = EmailSender(SMTP_SERVER_OUT, EMAIL_ACCOUNT_OUT, EMAIL_PASSWORD_OUT)
                            email_subject = "отчет за указанный период"
                            email_body = f"Здравствуйте,\n\nВ приложении находится отчет за период с {last_monday.strftime('%d.%m.%Y')} по {current_monday.strftime('%d.%m.%Y')}."

# Получаем имя файла и его директорию
                            file_dir = os.path.dirname(downloaded_file_path)
                            file_name = os.path.basename(downloaded_file_path)
# Создаём безопасное имя файла (только латинские буквы, цифры и дефис)
                            safe_file_name = re.sub(r'[^a-zA-Z0-9\.\-]', '', file_name)  # Удаляем всё, кроме латинских букв, цифр и дефиса
#                            if not safe_file_name:  # Если имя стало пустым, добавляем базовое имя
#                               safe_file_name = "file" + str(int(time.time())) + ".csv"  # Используем timestamp как уникальное имя
                            new_file_path = os.path.join(file_dir, safe_file_name)

# Переименовываем файл
                            os.rename(downloaded_file_path, new_file_path)
                            downloaded_file_path = new_file_path  # Обновляем путь для отправки

# Теперь отправляем переименованный файл
                            if email_sender.send_email_with_attachment(EMAIL_RECEIVER, email_subject, email_body, downloaded_file_path):


#                            if email_sender.send_email_with_attachment(EMAIL_RECEIVER, email_subject, email_body, downloaded_file_path):
                                logger.info("✅ Файл успешно отправлен по электронной почте.")
                            else:
                                logger.error("❌ Не удалось отправить файл по электронной почте.")
                        else:
                            logger.error("❌ Не удалось найти скачанный файл для отправки.")
                    else:
                        logger.error("Не удалось завершить взаимодействие с всплывающим окном.")
                else:
                    logger.error("Клик на кнопку 'Экспорт' не удался.")
            except TimeoutException:
                logger.error("❌ Не удалось найти или нажать на кнопку 'Поиск' по заданному XPath.")
            except Exception as e:
                logger.error(f"❌ Произошла непредвиденная ошибка при клике на 'Поиск': {e}")
        else:
            logger.error("❌ Тест провален. Не удалось установить одну или обе даты.")
    else:
        logger.error("❌ Не удалось авторизоваться.")

    auth_worker.cleanup()