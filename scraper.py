"""네이버 금융에서 5개 종목 데이터를 수집해 game_data.json을 갱신합니다."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대차",
    "035420": "NAVER",
    "051910": "LG화학",
}

PRICE_PAGES = 10
REPORT_PAGES = 4
OUTPUT_PATH = Path(__file__).resolve().parent / "game_data.json"
REQUEST_DELAY_SECONDS = float(os.getenv("NAVER_REQUEST_DELAY", "0.35"))


def make_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
            ),
            "Referer": "https://finance.naver.com/",
        }
    )
    return session


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=20)
    response.raise_for_status()
    # 네이버 금융의 기존 페이지는 EUC-KR로 제공됩니다. 자동 추정에 맡기면
    # 일부 실행 환경에서 한글이 깨질 수 있으므로 명시적으로 지정합니다.
    response.encoding = "euc-kr"
    time.sleep(REQUEST_DELAY_SECONDS)
    return BeautifulSoup(response.text, "html.parser")


def fetch_prices(session: requests.Session, code: str) -> list[dict]:
    prices: dict[str, int] = {}
    for page in range(1, PRICE_PAGES + 1):
        soup = get_soup(
            session,
            f"https://finance.naver.com/item/sise_day.naver?code={code}&page={page}",
        )
        for row in soup.select("table.type2 tr"):
            date_cell = row.select_one("td span.tah.p10.gray03")
            cells = row.select("td")
            if date_cell is None or len(cells) < 2:
                continue
            date_text = date_cell.get_text(strip=True)
            close_text = cells[1].get_text(strip=True).replace(",", "")
            if date_text and close_text.isdigit():
                prices[date_text] = int(close_text)

    result = [
        {"date": datetime.strptime(date, "%Y.%m.%d"), "price": price}
        for date, price in prices.items()
    ]
    result.sort(key=lambda item: item["date"])
    if len(result) < 2:
        raise RuntimeError(f"{code}: 주가 데이터를 충분히 수집하지 못했습니다.")
    return result


def fetch_reports(session: requests.Session, code: str) -> list[dict]:
    reports: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for page in range(1, REPORT_PAGES + 1):
        url = (
            "https://finance.naver.com/research/company_list.naver"
            f"?searchType=itemCode&itemCode={code}&page={page}"
        )
        soup = get_soup(session, url)
        table = soup.select_one("table.type_1")
        if table is None:
            continue
        for row in table.select("tr"):
            cells = row.select("td")
            if len(cells) != 6:
                continue
            title = cells[1].get_text(" ", strip=True)
            date_text = cells[4].get_text(strip=True)
            key = (title, date_text)
            if not title or key in seen:
                continue
            try:
                report_date = datetime.strptime(date_text, "%y.%m.%d")
            except ValueError:
                continue
            seen.add(key)
            reports.append({"title": title, "date": report_date})
    return reports


def build_stock_data(prices: list[dict], reports: list[dict]) -> list[dict]:
    game_data: list[dict] = []
    for index in range(len(prices) - 1):
        current = prices[index]
        next_day = prices[index + 1]
        if index == 0:
            titles: list[str] = []
        else:
            previous_date = prices[index - 1]["date"]
            titles = [
                report["title"]
                for report in reports
                if previous_date < report["date"] <= current["date"]
            ]
        game_data.append(
            {
                "date": current["date"].strftime("%Y.%m.%d"),
                "price": current["price"],
                "nextDate": next_day["date"].strftime("%Y.%m.%d"),
                "nextPrice": next_day["price"],
                "reports": titles,
            }
        )
    return game_data


def main() -> None:
    session = make_session()
    all_game_data: dict[str, dict] = {}
    for code, company_name in STOCKS.items():
        print(f"{company_name}({code}) 수집 중...")
        prices = fetch_prices(session, code)
        reports = fetch_reports(session, code)
        data = build_stock_data(prices, reports)
        all_game_data[code] = {"name": company_name, "code": code, "data": data}
        print(f"  완료: {len(data)}문제, 리포트 {len(reports)}개")

    temporary_path = OUTPUT_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(all_game_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(OUTPUT_PATH)
    print(f"전체 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
