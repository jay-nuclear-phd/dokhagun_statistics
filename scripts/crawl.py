from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import time
import json


BASE_URLS = [
    "https://cafe.naver.com/f-e/cafes/30948335/menus/37",
    "https://cafe.naver.com/f-e/cafes/30948335/menus/38",
    "https://cafe.naver.com/f-e/cafes/30948335/menus/39",
    "https://cafe.naver.com/f-e/cafes/30948335/menus/40",
]

TARGET_YEAR = "2026"
TARGET_MONTH = "04"
STOP_MONTH = "03"

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT_JSON = DATA_DIR / "result.json"

options = Options()
options.add_argument("--start-maximized")

# 처음 로그인할 때 사용한 Selenium 전용 크롬 프로필
options.add_argument(r"--user-data-dir=C:\selenium-naver-profile")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)


def wait_board_loaded():
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "table.article-table tbody tr")
        )
    )


def check_login():
    time.sleep(3)

    if "nid.naver.com" in driver.current_url or "login" in driver.current_url:
        input("로그인이 필요합니다. 네이버 로그인하고 카페 게시판이 보이면 Enter를 누르세요...")
    else:
        print("로그인 세션이 유지되어 있습니다.")


def collect_current_page(menu_no, page_no):
    wait_board_loaded()
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select("table.article-table tbody tr")

    results = []
    stop = False

    for row in rows:
        # 필독/공지 제외: 숫자 게시글 번호가 있는 행만 수집
        article_number_el = row.select_one("td.td_normal.type_articleNumber")

        if not article_number_el:
            continue

        article_number = article_number_el.get_text(strip=True)

        if not article_number.isdigit():
            continue

        writer_el = row.select_one("div.ArticleBoardWriterInfo span.nickname")
        date_el = row.select_one("td.td_normal.type_date")
        title_el = row.select_one("a.article")

        if not writer_el or not date_el:
            continue

        writer = writer_el.get_text(strip=True)
        date = date_el.get_text(strip=True)
        title = title_el.get_text(" ", strip=True) if title_el else ""

        clean_date = date.replace(" ", "")

        # 3월이 나오면 해당 메뉴 수집 종료
        if clean_date.startswith(f"{TARGET_YEAR}.{STOP_MONTH}."):
            stop = True
            break

        # 4월 데이터만 저장
        if clean_date.startswith(f"{TARGET_YEAR}.{TARGET_MONTH}."):
            results.append({
                "menu": menu_no,
                "page": page_no,
                "article_number": article_number,
                "date": date,
                "writer": writer,
                "title": title
            })

    return results, stop


def click_page(page_no):
    wait_board_loaded()

    button_xpath = f"//button[contains(@class, 'btn number') and normalize-space()='{page_no}']"

    btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, button_xpath))
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", btn)

    time.sleep(1.5)
    wait_board_loaded()


def collect_menu(menu_url):
    menu_no = menu_url.rstrip("/").split("/")[-1]

    print("=" * 60)
    print(f"메뉴 {menu_no} 수집 시작")
    print("=" * 60)

    driver.get(menu_url + "?viewType=L")
    check_login()
    wait_board_loaded()

    menu_results = []
    page_no = 1

    while True:
        print(f"메뉴 {menu_no} / {page_no}페이지 수집 중...")

        page_results, stop = collect_current_page(menu_no, page_no)
        menu_results.extend(page_results)

        print(f"메뉴 {menu_no} / {page_no}페이지 수집 개수: {len(page_results)}")

        if stop:
            print(f"메뉴 {menu_no}: {STOP_MONTH}월 데이터가 나와서 종료")
            break

        page_no += 1

        try:
            click_page(page_no)
        except Exception as e:
            print(f"메뉴 {menu_no}: {page_no}페이지 버튼을 찾지 못해서 종료")
            print(e)
            break

    return menu_results


all_results = []

try:
    for url in BASE_URLS:
        all_results.extend(collect_menu(url))

    updated_at = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "updated_at": updated_at,
        "target": f"{TARGET_YEAR}-{TARGET_MONTH}",
        "count": len(all_results),
        "items": all_results
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {OUT_JSON}")

finally:
    driver.quit()