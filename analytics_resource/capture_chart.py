import base64
import io
import logging
import os
import time

from datetime import datetime
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return chrome_options

def create_driver():
    logging.info("ChromeDriver 설정 중 ....")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=setup_chrome_options())
    return driver

def click_element_by_xpath(driver, xpath, element_name, wait_time=10):
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()
        logger.info(f"{element_name} 클릭 완료")
        time.sleep(2) # 클릭 후 잠시 대기
    except TimeoutException:
        logger.error(f"{element_name} 요소를 찾는데 시간이 초과되었습니다.")
    except ElementClickInterceptedException:
        logger.error(f"{element_name} 요소를 클릭할 수 없습니다. 다른 요소에 가려져 있을 수 있습니다.")
    except Exception as ex:
        logger.error(f"{element_name} 클릭 중 오류 발생 : {ex}")

def perform_chart_action(driver):
    # 시간 메뉴 클릭
    click_element_by_xpath(
        driver=driver,
        xpath="/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]",
        element_name="시간 메뉴"
    )

    # 1시간 옵션 선택
    click_element_by_xpath(
        driver=driver,
        xpath="/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]/cq-menu-dropdown/cq-item[8]",
        element_name="1시간 옵션"
    )

    # 지표 메뉴 클릭
    click_element_by_xpath(
        driver=driver,
        xpath="/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]",
        element_name="지표 메뉴"
    )

    # 볼린저 밴드 옵션 선택
    click_element_by_xpath(
        driver=driver,
        xpath="/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]/cq-menu-dropdown/cq-scroll/cq-studies/cq-studies-content/cq-item[15]",
        element_name="볼린저 밴드 옵션"
    )

def capture_and_encode_screenshot(driver):
    try:
        # 스크린샷 캡처
        png = driver.get_screenshot_as_png()

        # PIL Image로 변환
        img = Image.open(io.BytesIO(png))

        # 이미지 리사이즈 (OpenAI 제한에 맞춤)
        img.thumbnail((2000, 2000))

        # 현재 시간을 파일명에 포함
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upbit_chart_ETH_{current_time}.png"

        # 현재 스크립트의 경로를 가져옴
        script_path = os.path.dirname(os.path.abspath(__file__))

        # 파일 저장 경로 설정
        file_path = os.path.join(f"{script_path}/captures", filename)

        # 이미지 파일로 저장
        img.save(file_path)
        logger.info(f"스크린샷이 저장되었습니다.: {file_path}")

        # 이미지를 바이트로 변환
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")

        # Base64로 인코딩
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return base64_image, file_path

    except Exception as ex:
        logger.error(f"스크린샷 캡처 및 인코딩 중 오류 발생: {ex}")
        return None, None

def run_capture():
    driver = None

    try:
        driver = create_driver()

        driver.get("https://upbit.com/full_chart?code=CRIX.UPBIT.KRW-ETH")
        logger.info("> 페이지 로드 완료")
        time.sleep(30) # 페이지 로딩 대기 시간 증가

        logger.info("> 차트 작업 시작")
        perform_chart_action(driver=driver)
        logger.info("> 차트 작업 완료")

        chart_image, saved_file_path = capture_and_encode_screenshot(driver=driver)
        logger.info(f"> 스크린샷 캡처 완료. 저장된 파일 경로: {saved_file_path}")

    except WebDriverException as ex:
        logger.error(f"WebDriver 오류 발생: {ex}")
        chart_image, saved_file_path = None, None

    except Exception as ex:
        logger.error(f"차트 캡처 중 오류 발생: {ex}")
        chart_image, saved_file_path = None, None

    finally:
        if driver:
            driver.quit()

    return chart_image, saved_file_path
