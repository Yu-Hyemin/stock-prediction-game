# 주식 맞추기 게임 자동 업데이트 파일

이 폴더의 **내용 전체**를 GitHub 저장소 최상단에 올리면 됩니다. `.github` 폴더도 빠뜨리지 마세요.

## 파일 구조

```text
index.html
game_data.json
scraper.py
requirements.txt
.github/
  workflows/
    update.yml
```

- `index.html`: 기존 디자인과 게임 로직을 유지하며 `game_data.json`을 불러옵니다.
- `game_data.json`: 게임에서 사용하는 5개 종목 데이터입니다.
- `scraper.py`: 네이버 금융의 최근 일별 시세 10페이지와 기업 리포트 4페이지를 수집합니다.
- `update.yml`: 기본적으로 평일 KST 18:00에 자동 실행하고, 데이터가 바뀐 경우에만 커밋합니다.

## GitHub에 올린 뒤 확인

1. 저장소의 **Actions** 탭에서 `Update stock game data`를 엽니다.
2. `Run workflow`로 한 번 수동 실행합니다.
3. 초록색 체크가 뜨고 `game_data.json`이 갱신되면 자동화가 정상입니다.
4. 저장소 **Settings → Pages**는 기존처럼 `main` 브랜치의 `/ (root)`를 사용합니다.

## 실행 시간 바꾸기

`.github/workflows/update.yml`의 `cron` 한 줄을 수정합니다. GitHub cron은 UTC이므로 **KST 시각에서 9시간을 빼야** 합니다.

```yaml
# 평일 KST 18:00
- cron: '0 9 * * 1-5'

# 매일 KST 20:30
- cron: '30 11 * * *'
```

형식은 `분 시 일 월 요일`입니다. 요일의 `1-5`는 월~금이며, `*`는 매일입니다. 예약 실행은 GitHub 사정에 따라 몇 분 늦게 시작될 수 있습니다.

## 로컬에서 확인할 때

`index.html`은 외부 JSON을 읽으므로 파일을 직접 더블클릭하지 말고 간단한 웹 서버로 열어야 합니다.

```bash
python -m http.server 8000
```

그 다음 브라우저에서 `http://localhost:8000`을 엽니다. GitHub Pages에서는 별도 설정 없이 동작합니다.
