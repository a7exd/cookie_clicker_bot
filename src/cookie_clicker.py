import datetime
import time

from selenium import webdriver
from selenium.common import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
from logging import Logger, FileHandler, StreamHandler, Formatter


def get_game_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--ignore-certificate-errors")

    time.sleep(50)  # ChromeDriver can't start immediately

    drvr = webdriver.Remote(
        command_executor="http://selenium-grid:4444", options=options
    )

    drvr.set_window_size("1400", "900")
    drvr.get("https://orteil.dashnet.org/cookieclicker/")
    time.sleep(4)
    return drvr


class Bot:
    def __init__(
        self, driver: WebDriver, logger: Logger, report_timeout: int = 1
    ):

        self.drvr = driver
        self.log = logger
        self.actions = ActionChains(self.drvr, duration=500)
        self.counter_to_buy_upgrade = 1000
        self.counter_to_buy_building = 100
        self.cookies_count = 0.0
        self.report_timeout = datetime.timedelta(minutes=report_timeout)
        self.start_time_to_report = datetime.datetime.now()
        self.units = ""

        change_lang = driver.find_element(By.ID, "changeLanguage")
        change_lang.click()
        change_lang_close = driver.find_element(By.ID, "promptClose")
        change_lang_close.click()

    def run(self):

        while True:
            self.click_cookie()

            self.check_flying_cookie()
            self.check_cookies_count()
            self.check_time_to_report()

    def click_cookie(self):
        try:
            self.get_cookie_click()
        except ElementClickInterceptedException:
            print("Error was excepted!")
            WebDriverWait(
                self.drvr,
                20,
                ignored_exceptions=(
                    StaleElementReferenceException,
                    ElementClickInterceptedException,
                ),
            ).until(self.get_cookie_click)

    def check_time_to_report(self):
        time_now = datetime.datetime.now()
        if time_now > self.start_time_to_report + self.report_timeout:
            speed = self.get_speed()
            self.log.info(
                f"Cookies count: {self.cookies_count}, " f"speed: {speed}\n"
            )
            self.start_time_to_report = time_now

    def buy_building(self, building: WebElement):
        self.actions.move_to_element(building).click().perform()
        self.move_to_locked_building()
        self.counter_to_buy_building += 200

    def move_to_locked_building(self):
        """This method is responsible for the most expensive
        available building being in the viewport"""
        locked_buildings = self.drvr.find_elements(
            By.CSS_SELECTOR, "div .product.locked.disabled"
        )
        if len(locked_buildings) > 1:
            self.actions.move_to_element(locked_buildings[1]).perform()
        else:
            self.actions.move_to_element(
                self.drvr.find_element(By.ID, "div #support")
            ).perform()

    def buy_upgrade(self, upgrade: WebElement):
        self.actions.move_to_element(upgrade).click().perform()

        # This equation is responsible for buying upgrades more often than
        # buildings, if other conditions are equal.
        self.counter_to_buy_upgrade = 1000 + int(
            self.counter_to_buy_building * 0.8
        )

    def get_active_building(self) -> WebElement:
        if buildings := self.drvr.find_elements(
            By.CSS_SELECTOR, value="div .product.unlocked.enabled"
        ):
            return buildings[-1]

    def get_active_upgrade(self) -> WebElement:
        if upgrades := self.drvr.find_elements(
            By.CSS_SELECTOR, value="div .crate.upgrade.enabled"
        ):
            return upgrades[-1]

    def check_cookies_count(self):
        cookies, self.units = self.drvr.find_element(
            By.ID, "cookies"
        ).text.split()[:2]
        cookies = cookies.replace(",", "_")

        units_multiplier = self.get_units_multiplier()
        self.cookies_count = float(cookies) * units_multiplier

        active_building = self.get_active_building()
        active_upgrade = self.get_active_upgrade()
        if (
            self.cookies_count > self.counter_to_buy_building
            and active_building
        ):
            self.buy_building(active_building)
        elif (
            self.cookies_count > self.counter_to_buy_upgrade and active_upgrade
        ):
            self.buy_upgrade(active_upgrade)

    def get_speed(self) -> str:
        speed = WebDriverWait(
            self.drvr,
            40,
            ignored_exceptions=(StaleElementReferenceException,),
        ).until(self._find_speed_element)
        return speed

    def _find_speed_element(self, driver: WebDriver) -> str | bool:
        speed = driver.find_elements(By.ID, "cookiesPerSecond")
        if speed:
            return speed[-1].text
        else:
            return False

    def check_flying_cookie(self):
        if flying_cookies := self.drvr.find_elements(
            By.XPATH, "/html/body/div/div[2]/div[5]/div"
        ):
            self.actions.move_to_element(flying_cookies[-1]).click().perform()

    def get_cookie_click(self, driver: WebDriver | None = None) -> bool | None:
        driver = driver if driver is not None else self.drvr
        cookie = driver.find_element(By.ID, value="bigCookie")
        if cookie:
            return cookie.click()
        else:
            return False

    def get_units_multiplier(self) -> int:
        if "million" in self.units:
            return 10**6
        elif "billion" in self.units:
            return 10**9
        else:
            return 1


if __name__ == "__main__":
    log = Logger(__name__, level="INFO")
    file_handler = FileHandler(
        "./logs/cookie_clicker_bot.log", mode="w", encoding="utf-8"
    )

    formatter = Formatter("[%(asctime)s: %(levelname)s] - %(message)s")
    file_handler.setFormatter(formatter)

    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)

    log.addHandler(file_handler)
    log.addHandler(stream_handler)

    bot = Bot(driver=get_game_driver(), logger=log)
    bot.run()
