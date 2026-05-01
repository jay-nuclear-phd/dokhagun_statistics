from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import time
import pandas as pd
import json

START_DATE = "2026-03-30"
END_DATE = "2026-04-26"

CSV_PATH  = "data/result.csv"
JSON_PATH = "data/result.json"
JS_PATH   = "data/result.js"

base_urls = [
    "https://cafe.naver.com/f-e/cafes/30948335/menus/37",
    "https://cafe.naver.com/f-e/cafes/30948335/menus/38",
    "https://cafe.naver.com/f-e/cafes/30948335/menus/39",
    "https://cafe.naver.com/f-e/cafes/30948335/menus/40",
    "https://cafe.naver.com/f-e/cafes/30948335/menus/61",
]

start_dt = datetime.strptime(START_DATE, "%Y-%m-%d").date()
end_dt = datetime.strptime(END_DATE, "%Y-%m-%d").date()

if start_dt > end_dt:
    raise ValueError("START_DATE는 END_DATE보다 늦을 수 없습니다.")

def parse_naver_date(date_text):
    clean = date_text.strip().replace(" ", "")

    try:
        return datetime.strptime(clean, "%Y.%m.%d.").date()
    except ValueError:
        return None

options = Options()
options.add_argument("--start-maximized")
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
        date_text = date_el.get_text(strip=True)
        title = title_el.get_text(" ", strip=True) if title_el else ""

        post_date = parse_naver_date(date_text)

        if post_date is None:
            continue

        if post_date > end_dt:
            continue

        if post_date < start_dt:
            stop = True
            break

        results.append({
            "menu": menu_no,
            "page": page_no,
            "article_number": article_number,
            "date": date_text,
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
    print(menu_url)
    print("=" * 60)

    target_url = menu_url + "?viewType=L"

    driver.get(target_url)

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
            print(f"메뉴 {menu_no}: {START_DATE}보다 과거 데이터가 나와서 이 메뉴 수집을 종료합니다.")
            break

        page_no += 1

        try:
            click_page(page_no)
        except Exception as e:
            print(f"메뉴 {menu_no}: {page_no}페이지 버튼을 찾지 못했습니다. 이 메뉴 수집 종료.")
            print(e)
            break

    return menu_results


all_results = []

try:
    for url in base_urls:
        menu_results = collect_menu(url)
        all_results.extend(menu_results)

finally:
    df = pd.DataFrame(all_results)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"CSV 저장 완료: {CSV_PATH}")

    updated_at = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "updated_at": updated_at,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "count": len(all_results),
        "items": all_results
    }

    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"JSON 저장 완료: {JSON_PATH}")

    # result.js 저장 (로컬 CORS 회피용)
    with Path(JS_PATH).open("w", encoding="utf-8") as f:
        f.write(f"window.naverCafeData = {json.dumps(payload, ensure_ascii=False, indent=2)};")
    print(f"JS 저장 완료: {JS_PATH}")

    driver.quit()