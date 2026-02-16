# AGENTS.md — K-Pedia (스낵 데이터 파이프라인)

## 0) 프로젝트 목적
NyamNyam 크롤링 → 데이터 전처리 → DB 저장 → API/Streamlit → 자동 리포트

## 1) 최우선 안전 규칙
- **터미널/쉘 커맨드 실행 전 사용자 승인**
- 파일 삭제/대량 변경은 계획+영향 범위 보고 후 승인
- `.env`/API키 절대 하드코딩 금지
- 크롤링은 **타임아웃+재시도+User-Agent 로테이션**
- 멱등성 보장: 동일 날짜 데이터 중복 생성 방지

## 2) 프로젝트 구조 (고정)
kpedia/
├── AGENTS.md
├── src/
│ ├── crawler.py # 데이터 수집
│ ├── processor.py # 전처리/DB
│ └── api.py # FastAPI
├── app.py # Streamlit UI
├── tests/
└── requirements.txt

text

## 3) 자주 쓰는 엔트리포인트
pytest tests/
streamlit run app.py
python src/crawler.py --date=20260216

text

## 4) 출력 규칙
data/YYYYMMDD_snack_prices.csv
reports/YYYYMMDD_kpedia_report.md
logs/YYYYMMDD.log

text

## 5) 코딩 표준
- 함수: `fetch_snack_prices()`, `save_to_db()`
- 로그: `logging.info()` 사용
- 설정: `.env` + config.json
- 변경 최소 범위 (폴더/파일 지정)

## 6) 에이전트 작업 방식
1. "계획 → 대상 파일 → 변경 요약(diff)" 제시
2. 지정 폴더만 수정
3. 테스트 제안 → 승인 후 실행

## 에이전트 팀
|@planner|ulw 목표→plan.md|✅ plan.md, ⚠️ git, 🚫 삭제|
|@coder|plan.md 구현|✅ pytest, ⚠️ selenium, 🚫 pip|
|@deploy|streamlit 배포|✅ run, ⚠️ prod|