import os
from dotenv import load_dotenv

# .env 파일이 있으면 로드 (로컬 개발용)
load_dotenv()

# 업비트 API 키 설정 (환경 변수 또는 여기에 직접 입력 - 권장: .env 사용)
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY", "") 
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY", "")

# 텔레그램 알림 설정 (환경 변수 또는 여기에 직접 입력)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# 매매 기본 설정
TRADE_AMOUNT = int(os.getenv("TRADE_AMOUNT", "100000"))  # 1회 매수 금액
MAX_COIN_COUNT = int(os.getenv("MAX_COIN_COUNT", "3"))     # 최대 보유 종목 수
