# date_selector.py
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from datetime import datetime

logger = logging.getLogger("stat2serg_logger")

class DateSelector:
    def __init__(self, driver):
        self.driver = driver

    def select_date_and_time(self, title, date_time_str):
        """
        Метод для выбора даты в dhtmlx-календаре.
        :param title: Заголовок поля ввода ('Время с' или 'Время до').
        :param date_time_str: Строка с датой и временем в формате 'YYYY-MM-DD HH:MM:SS'.
        """
        try:
            target_dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
            logger.info(f"Начинаем процесс выбора даты: {target_dt.strftime('%Y-%m-%d')} для поля с заголовком '{title}'")

            # 1. Поиск поля ввода по заголовку (title)
            input_field_xpath = f"//input[@title='{title}']"

            input_field = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, input_field_xpath))
            )
            logger.info(f"✅ Поле ввода найдено. ID: {input_field.get_attribute('id')}.")

            # 2. Клик по полю через JavaScript для вызова календаря
            logger.info("Клик на поле ввода через JavaScript...")
            self.driver.execute_script("arguments[0].click();", input_field)
            time.sleep(5)

            # 3. Ожидание появления и видимости календаря
            calendar_xpath = "//div[contains(@class, 'dhtmlxcalendar_dhx_web')]"
            visible_calendar = None
            try:
                calendars = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, calendar_xpath))
                )
                for calendar in calendars:
                    if calendar.is_displayed():
                        visible_calendar = calendar
                        logger.info("✅ Окно календаря загрузилось и стало видимым.")
                        break
            except TimeoutException:
                logger.error("❌ Окно календаря не появилось или не стало видимым.")
                return False

            if not visible_calendar:
                logger.error("❌ Не удалось найти видимый календарь среди всех элементов.")
                return False

            # 4. Навигация по месяцам и годам
            # Словарь для маппинга русских месяцев на английские
            month_map = {
                "Январь": "January",
                "Февраль": "February",
                "Март": "March",
                "Апрель": "April",
                "Май": "May",
                "Июнь": "June",
                "Июль": "July",
                "Август": "August",
                "Сентябрь": "September",
                "Октябрь": "October",
                "Ноябрь": "November",
                "Декабрь": "December"
            }

            while True:
                try:
                    month_element = visible_calendar.find_element(By.XPATH, ".//span[contains(@class, 'dhtmlxcalendar_month_label_month')]")
                    year_element = visible_calendar.find_element(By.XPATH, ".//span[contains(@class, 'dhtmlxcalendar_month_label_year')]")

                    current_month_str = month_element.text.strip()
                    current_year_str = year_element.text.strip()

                except NoSuchElementException as e:
                    logger.error(f"❌ Не удалось найти или считать месяц/год внутри контейнера календаря. Ошибка: {e}")
                    return False

                if not current_month_str or not current_year_str:
                    logger.error("❌ Элементы месяца или года найдены, но их текст пуст. Возможно, они еще не прогрузились.")
                    time.sleep(1)
                    continue

                # Преобразуем русский месяц в английский для парсинга
                current_month_eng = month_map.get(current_month_str, current_month_str)
                try:
                    current_month_dt = datetime.strptime(current_month_eng, '%B')
                except ValueError:
                    logger.error(f"Не удалось распознать название месяца: '{current_month_str}' (английский: '{current_month_eng}'). Проверьте словарь month_map.")
                    return False

                current_year_int = int(current_year_str)

                logger.info(f"Текущий месяц: {current_month_str} {current_year_int}. Целевой: {target_dt.strftime('%B %Y')}")

                if current_year_int > target_dt.year or (current_year_int == target_dt.year and current_month_dt.month > target_dt.month):
                    arrow_locators = [
                        ".//div[contains(@class, 'dhtmlxcalendar_month_arrow_left')]",
                        ".//div[contains(@class, 'dhtmlxcalendar_month_arrow_left')]/parent::div"
                    ]
                    logger.info("Переход на предыдущий месяц...")
                elif current_year_int < target_dt.year or (current_year_int == target_dt.year and current_month_dt.month < target_dt.month):
                    arrow_locators = [
                        ".//div[contains(@class, 'dhtmlxcalendar_month_arrow_right')]",
                        ".//div[contains(@class, 'dhtmlxcalendar_month_arrow_right')]/parent::div"
                    ]
                    logger.info("Переход на следующий месяц...")
                else:
                    logger.info("✅ Найден нужный месяц и год.")
                    time.sleep(5)
                    break

                arrow_element = None
                for locator in arrow_locators:
                    try:
                        arrow_element = WebDriverWait(visible_calendar, 5).until(
                            EC.element_to_be_clickable((By.XPATH, locator))
                        )
                        logger.info(f"✅ Стрелка найдена по XPath: {locator}")
                        break
                    except TimeoutException:
                        logger.warning(f"❌ Стрелка не найдена по XPath: {locator}.")
                        continue

                if not arrow_element:
                    if (current_year_int < target_dt.year or (current_year_int == target_dt.year and current_month_dt.month < target_dt.month)):
                        logger.error("❌ Целевой месяц находится в будущем, но стрелка 'вперед' неактивна. Возможно, это максимальная дата.")
                    elif (current_year_int > target_dt.year or (current_year_int == target_dt.year and current_month_dt.month > target_dt.month)):
                        logger.error("❌ Целевой месяц находится в прошлом, но стрелка 'назад' неактивна. Возможно, это минимальная дата.")
                    else:
                        logger.error("❌ Не удалось найти стрелку для навигации по месяцам.")
                    return False

                self.driver.execute_script("arguments[0].click();", arrow_element)
                time.sleep(5)

            # 5. Выбор дня
            target_day_xpath = f".//li[contains(@class, 'dhtmlxcalendar_cell_month')]/div[@class='dhtmlxcalendar_label' and text()='{target_dt.day}']"
            logger.info(f"Поиск и выбор дня: {target_dt.day}. XPath: {target_day_xpath}")
            day_element = WebDriverWait(visible_calendar, 10).until(
                EC.element_to_be_clickable((By.XPATH, target_day_xpath))
            )
            self.driver.execute_script("arguments[0].click();", day_element)
            logger.info(f"✅ Выбран день: {target_dt.day}")
            time.sleep(5)

            return True

        except Exception as e:
            logger.error(f"❌ Произошла непредвиденная ошибка: {e}")
            return False
