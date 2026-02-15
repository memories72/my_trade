import sys
import os
import time
import json
import logging
import requests
import datetime
import threading
import csv
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. HTML UI Content (Load from external file)
# -----------------------------------------------------------------------------
try:
    with open("stock_trade_ui.html", "r", encoding="utf-8") as f:
        HTML_CONTENT = f.read()
except FileNotFoundError:
    HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QUANTUM TRADER PRO</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=JetBrains+Mono:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'JetBrains Mono', monospace;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1628 100%);
            color: #e0e6ed;
            overflow-x: hidden;
            min-height: 100vh;
        }
        /* 배경 효과 */
        .bg-pattern {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-image: radial-gradient(circle at 20% 30%, rgba(0, 255, 255, 0.05) 0%, transparent 50%),
                              radial-gradient(circle at 80% 70%, rgba(255, 0, 255, 0.05) 0%, transparent 50%);
            pointer-events: none; z-index: -1;
        }
        .container { max-width: 1920px; margin: 0 auto; padding: 2rem; position: relative; z-index: 1; }
        
        /* 폰트 및 텍스트 효과 */
        .neon-text {
            font-family: 'Orbitron', sans-serif;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        }
        
        /* 카드 스타일 */
        .glass-card {
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        .glass-card:hover { border-color: rgba(0, 255, 255, 0.3); transform: translateY(-2px); }

        /* 버튼 */
        .btn-primary {
            background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
            color: #0a0e27; font-weight: 600; font-family: 'Orbitron', sans-serif;
            padding: 0.75rem 2rem; border-radius: 12px; transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 30px rgba(0, 212, 255, 0.5); }
        .btn-danger { background: linear-gradient(135deg, #ff0080 0%, #cc0066 100%); box-shadow: 0 4px 20px rgba(255, 0, 128, 0.3); color: white;}
        
        /* 상태 배지 */
        .status-badge {
            display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem;
            border-radius: 20px; font-size: 0.85rem; font-weight: 600; font-family: 'Orbitron', sans-serif;
        }
        .status-running { background: rgba(0, 255, 0, 0.1); color: #00ff00; border: 1px solid rgba(0, 255, 0, 0.3); }
        .status-stopped { background: rgba(255, 0, 0, 0.1); color: #ff4444; border: 1px solid rgba(255, 0, 0, 0.3); }
        
        /* 테이블 */
        .table-container { overflow-x: auto; border-radius: 12px; }
        table { width: 100%; border-collapse: collapse; }
        th { padding: 1rem; text-align: left; font-family: 'Orbitron', sans-serif; color: #00ffff; font-size: 0.8rem; background: rgba(0, 255, 255, 0.05); }
        td { padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); font-size: 0.9rem; }
        
        /* 통계 카드 */
        .stat-card {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.05), rgba(0, 100, 200, 0.05));
            padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(0, 212, 255, 0.2);
        }
        .stat-label { font-size: 0.75rem; color: #00d4ff; font-family: 'Orbitron', sans-serif; margin-bottom: 0.5rem; }
        .stat-value { font-size: 1.8rem; font-weight: 700; font-family: 'Orbitron', sans-serif; color: #fff; }
        
        /* RSI 게이지 */
        .rsi-track { width: 100%; height: 8px; background: #374151; border-radius: 4px; position: relative; margin-top: 10px; overflow: hidden; }
        .rsi-bar { height: 100%; background: linear-gradient(90deg, #ef4444 0%, #eab308 50%, #22c55e 100%); width: 100%; opacity: 0.6; }
        .rsi-cursor { width: 4px; height: 14px; background: white; position: absolute; top: 50%; transform: translateY(-50%); box-shadow: 0 0 8px rgba(255,255,255,0.8); transition: left 0.5s ease; border-radius: 2px; }

        /* 유틸리티 */
        .text-profit { color: #00ff88; }
        .text-loss { color: #ff4466; }
        .log-container { height: 300px; overflow-y: auto; font-size: 0.85rem; padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 12px; }
        .log-entry { margin-bottom: 4px; }
        
        /* 모드 토글 */
        .mode-btn { padding: 0.5rem 1rem; border-radius: 8px; font-family: 'Orbitron', sans-serif; font-size: 0.8rem; transition: all 0.2s; }
        .mode-active { background: #00d4ff; color: #000; box-shadow: 0 0 10px rgba(0, 212, 255, 0.5); }
        .mode-inactive { background: transparent; color: #666; border: 1px solid #333; }
    </style>
</head>
<body>
    <div class="bg-pattern"></div>
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect } = React;

        function App() {
            const [status, setStatus] = useState({
                isRunning: false,
                mode: 'paper',
                balance: 0,
                totalBuyAmount: 0,
                stocks: {},
                target_info: {},
                logs: [],
                summary: { dailyProfit: 0, tradeCount: 0, winCount: 0 },
                config: { market: 'SIDEWAYS', rsi: 50, reason: '분석 대기중', targetProfit: 3.0, stopLoss: -3.0 }
            });

            useEffect(() => {
                fetchStatus();
                const interval = setInterval(fetchStatus, 2000);
                return () => clearInterval(interval);
            }, []);

            const fetchStatus = async () => {
                try {
                    const res = await fetch('/api/status');
                    const data = await res.json();
                    setStatus(data);
                } catch (err) { console.error(err); }
            };

            const handleStart = async () => await fetch('/api/start', { method: 'POST' });
            const handleStop = async () => await fetch('/api/stop', { method: 'POST' });
            const handleMode = async (mode) => {
                await fetch('/api/mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode })
                });
                fetchStatus();
            };

            const fmtNum = (n) => new Intl.NumberFormat('ko-KR').format(n || 0);
            
            const calcRatio = () => {
                const total = (status.totalBuyAmount || 0) + (status.balance || 0);
                return total === 0 ? 0 : (status.totalBuyAmount / total) * 100;
            };

            return (
                <div className="container">
                    {/* Header */}
                    <header className="flex justify-between items-center mb-8 flex-wrap gap-4">
                        <div>
                            <h1 className="text-4xl font-bold neon-text text-white">QUANTUM TRADER</h1>
                            <p className="text-gray-400 text-sm mt-1">AI-Powered Algorithmic Trading System</p>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className={`status-badge ${status.isRunning ? 'status-running' : 'status-stopped'}`}>
                                <div className={`w-2 h-2 rounded-full ${status.isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                                {status.isRunning ? 'RUNNING' : 'STOPPED'}
                            </div>
                            <div className="flex bg-gray-800 rounded-lg p-1">
                                <button onClick={() => handleMode('paper')} className={`mode-btn ${status.mode === 'paper' ? 'mode-active' : 'mode-inactive'}`}>PAPER</button>
                                <button onClick={() => handleMode('real')} className={`mode-btn ${status.mode === 'real' ? 'mode-active' : 'mode-inactive'}`}>REAL</button>
                            </div>
                            <div className="flex bg-gray-800 rounded-lg p-1">
                                <button onClick={() => handleMarket('domestic')} className={`mode-btn ${status.marketType === 'domestic' ? 'mode-active' : 'mode-inactive'}`}>🇰🇷 국내</button>
                                <button onClick={() => handleMarket('overseas')} className={`mode-btn ${status.marketType === 'overseas' ? 'mode-active' : 'mode-inactive'}`}>🇺🇸 해외</button>
                            </div>
                            <button 
                                onClick={status.isRunning ? handleStop : handleStart}
                                className={`btn-primary ${status.isRunning ? 'btn-danger' : ''}`}
                            >
                                {status.isRunning ? '■ STOP SYSTEM' : '▶ START SYSTEM'}
                            </button>
                        </div>
                    </header>

                    {/* Stats Dashboard */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        {/* 자산 현황 */}
                        <div className="stat-card">
                            <div className="stat-label">ASSET ALLOCATION</div>
                            <div className="flex flex-col gap-2 mt-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-400">Stocks (Used)</span>
                                    <span className="text-white font-bold">{status.currency === 'KRW' ? fmtNum(status.totalBuyAmount) + '원' : '$' + fmtNum(status.totalBuyAmount)}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-400">Cash (Free)</span>
                                    <span className="text-cyan-300 font-bold">{status.currency === 'KRW' ? fmtNum(status.balance) + '원' : '$' + fmtNum(status.balance)}</span>
                                </div>
                                <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden mt-1 relative">
                                    <div className="bg-cyan-500 h-full transition-all duration-500 absolute top-0 left-0" style={{width: `${calcRatio()}%`}}></div>
                                </div>
                            </div>
                        </div>

                        {/* 손익 */}
                        <div className="stat-card">
                            <div className="stat-label">DAILY P&L</div>
                            <div className={`stat-value ${status.summary.dailyProfit >= 0 ? 'text-profit' : 'text-loss'}`}>
                                {status.summary.dailyProfit > 0 ? '+' : ''}{status.currency === 'KRW' ? fmtNum(status.summary.dailyProfit) + '원' : '$' + fmtNum(status.summary.dailyProfit)}
                            </div>
                        </div>

                        {/* 승률 */}
                        <div className="stat-card">
                            <div className="stat-label">WIN RATE</div>
                            <div className="stat-value">
                                {status.summary.tradeCount > 0 ? ((status.summary.winCount / status.summary.tradeCount) * 100).toFixed(1) : 0}%
                            </div>
                            <div className="text-xs text-gray-500 mt-1">{status.summary.tradeCount} Trades Executed</div>
                        </div>

                        {/* 시장 상태 */}
                        <div className="stat-card border-l-4" style={{borderColor: status.config.market === 'BULL' ? '#22c55e' : status.config.market === 'BEAR' ? '#ef4444' : '#eab308'}}>
                            <div className="stat-label">MARKET SENTIMENT</div>
                            <div className="text-2xl font-bold" style={{color: status.config.market === 'BULL' ? '#22c55e' : status.config.market === 'BEAR' ? '#ef4444' : '#eab308'}}>
                                {status.config.market}
                            </div>
                            <div className="text-xs text-gray-400 mt-1 truncate">{status.config.reason.split(':')[0]}</div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* 보유 종목 */}
                        <div className="lg:col-span-2 glass-card p-6">
                            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <span className="text-cyan-400">●</span> HOLDINGS PORTFOLIO
                            </h2>
                            {Object.keys(status.stocks).length === 0 ? (
                                <div className="text-center py-10 text-gray-600">No active positions</div>
                            ) : (
                                <div className="table-container">
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>SYMBOL</th>
                                                <th>AVG PRICE</th>
                                                <th>CURRENT</th>
                                                <th>QTY</th>
                                                <th>P&L %</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {Object.entries(status.stocks).map(([code, stock]) => {
                                                const currentPrice = status.target_info[code]?.price || 0;
                                                const profit = currentPrice ? ((currentPrice - stock.buy_price) / stock.buy_price * 100).toFixed(2) : 0;
                                                return (
                                                    <tr key={code} className={stock.suspended ? 'opacity-50' : ''}>
                                                        <td>
                                                            <div className="font-bold text-white">{stock.name}</div>
                                                            <div className="text-xs text-gray-500">{code} {stock.suspended && '(정지)'}</div>
                                                        </td>
                                                        <td>{fmtNum(stock.buy_price)}</td>
                                                        <td>{currentPrice ? fmtNum(currentPrice) : '-'}</td>
                                                        <td>{stock.qty}</td>
                                                        <td className={profit >= 0 ? 'text-profit' : 'text-loss'}>{profit}%</td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>

                        {/* 전략 패널 (MARKET STRATEGY) */}
                        <div className="glass-card p-6">
                            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <span className="text-cyan-400">●</span> MARKET STRATEGY
                            </h2>
                            
                            {/* RSI Gauge */}
                            <div className="mb-6">
                                <div className="flex justify-between text-xs text-gray-400 mb-1">
                                    <span>Weak</span>
                                    <span className="text-white font-mono font-bold">RSI: {status.config.rsi ? status.config.rsi.toFixed(1) : 0}</span>
                                    <span>Strong</span>
                                </div>
                                <div className="rsi-track">
                                    <div className="rsi-bar"></div>
                                    <div className="rsi-cursor" style={{left: `${status.config.rsi || 50}%`}}></div>
                                </div>
                                <div className="flex justify-between text-[10px] text-gray-600 mt-1">
                                    <span>Oversold</span>
                                    <span>Neutral</span>
                                    <span>Overbought</span>
                                </div>
                            </div>

                            {/* TP/SL Display */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gray-800 p-4 rounded-xl border border-green-900 bg-opacity-50">
                                    <div className="text-xs text-green-400 mb-1 font-bold">TAKE PROFIT</div>
                                    <div className="text-2xl font-bold text-white">+{status.config.targetProfit}%</div>
                                    <div className="text-[10px] text-gray-500 mt-1">
                                        {status.config.market === 'BULL' ? '▲ Aggressive' : status.config.market === 'BEAR' ? '▼ Conservative' : '- Standard'}
                                    </div>
                                </div>
                                <div className="bg-gray-800 p-4 rounded-xl border border-red-900 bg-opacity-50">
                                    <div className="text-xs text-red-400 mb-1 font-bold">STOP LOSS</div>
                                    <div className="text-2xl font-bold text-white">{status.config.stopLoss}%</div>
                                    <div className="text-[10px] text-gray-500 mt-1">
                                        {status.config.market === 'BULL' ? '▲ Wide' : status.config.market === 'BEAR' ? '▼ Tight' : '- Standard'}
                                    </div>
                                </div>
                            </div>

                            {/* Analysis Reason */}
                            <div className="mt-4 bg-gray-800 p-3 rounded-lg border border-gray-700">
                                <div className="text-xs text-cyan-400 font-bold mb-1">MARKET ANALYSIS</div>
                                <div className="text-xs text-gray-300 leading-relaxed">
                                    {status.config.reason || "Waiting for market data..."}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 로그 */}
                    <div className="glass-card p-6 mt-6">
                        <h2 className="text-lg font-bold text-white mb-4">SYSTEM LOGS</h2>
                        <div className="log-container">
                            {status.logs.map((log, i) => (
                                <div key={i} className="log-entry text-gray-300">
                                    <span className="text-gray-500 text-xs mr-2">[{log.time}]</span>
                                    <span className={log.type === 'BUY' ? 'text-profit' : log.type === 'SELL' ? 'text-loss' : ''}>{log.msg}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Footer */}
                    <footer className="mt-8 text-center text-xs text-gray-600">
                        <p>⚠️ 투자에 대한 모든 책임은 투자자 본인에게 있습니다</p>
                    </footer>
                </div>
            );
        }
        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>
"""
if not HTML_CONTENT or HTML_CONTENT.startswith('<!DOCTYPE'):
    pass  # Successfully loaded from file
else:
    print("[WARN] Failed to load stock_trade_ui.html, using embedded fallback")

# -----------------------------------------------------------------------------
# 2. Python Backend Logic
# -----------------------------------------------------------------------------

# Internal helper for stock names (Fallback if module missing)
def internal_get_stock_name(code):
    stock_map = {
        "005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER", 
        "035720": "카카오", "005380": "현대차", "051910": "LG화학",
        "000270": "기아", "006400": "삼성SDI", "068270": "셀트리온",
        "069500": "KODEX 200"
    }
    return stock_map.get(code, code)

try:
    from stock_names import get_stock_name
except ImportError:
    get_stock_name = internal_get_stock_name

# All required modules are now in the same directory
# No need for external sys.path additions

# .env 로드 (명시적 로드)
try:
    from dotenv import load_dotenv
    # 현재 파일 위치를 기준으로 .env 로드 시도
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"[INFO] .env loaded from {env_path}")
    else:
        # 파일이 없다면 기본 로드 시도 (작업 디렉토리 기준)
        load_dotenv()
        print("[INFO] .env loaded from CWD")
except ImportError:
    print("[WARN] python-dotenv not installed. Using system env vars.")

# 환경변수 로드
KIS_APP_KEY = os.environ.get("KIS_APP_KEY", "")
KIS_APP_SECRET = os.environ.get("KIS_APP_SECRET", "")
KIS_ACCOUNT_NO = os.environ.get("KIS_ACCOUNT_NO", "") 
KIS_ACCOUNT_PROD = os.environ.get("KIS_ACCOUNT_PROD", "01")
KIS_HTS_ID = os.environ.get("KIS_HTS_ID", "") 

# 모의투자 계좌 정보
PAPER_ACCOUNT_NO = os.environ.get("PAPER_ACCOUNT_NO", KIS_ACCOUNT_NO)  # 기본값: 실전계좌
PAPER_ACCOUNT_PROD = os.environ.get("PAPER_ACCOUNT_PROD", "01")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

# 해외주식 설정
OVERSEAS_EXCHANGE = os.environ.get("OVERSEAS_EXCHANGE", "NASD")  # NASD (미국전체), NAS (나스닥), NYSE (뉴욕)
DEFAULT_MARKET = os.environ.get("DEFAULT_MARKET", "domestic")  # domestic 또는 overseas

# 계좌 정보 로드 확인 로그
if not KIS_ACCOUNT_NO:
    print("[CRITICAL ERROR] KIS_ACCOUNT_NO is empty! Check your .env file.")
else:
    masked_acc = KIS_ACCOUNT_NO[:4] + "****" if len(KIS_ACCOUNT_NO) > 4 else "****"
    print(f"[INFO] Account loaded: {masked_acc}")

def update_kis_config():
    config_path = os.path.join(os.path.expanduser("~"), "KIS", "config", "kis_devlp.yaml")
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        content = f"""
my_app: "{KIS_APP_KEY}"
my_sec: "{KIS_APP_SECRET}"
paper_app: "{KIS_APP_KEY}"
paper_sec: "{KIS_APP_SECRET}"
my_htsid: "{KIS_HTS_ID}"
my_acct_stock: "{KIS_ACCOUNT_NO}"
my_paper_stock: "{PAPER_ACCOUNT_NO}"
my_prod: "{KIS_ACCOUNT_PROD}"
my_agent: "Mozilla/5.0"
prod: "https://openapi.koreainvestment.com:9443"
vps: "https://openapivts.koreainvestment.com:29443"
ops: "ws://ops.koreainvestment.com:21000"
vops: "ws://ops.koreainvestment.com:31000"
"""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    except Exception as e:
        print(f"Config Error: {e}")

try:
    update_kis_config() 
    import kis_auth as ka
    from domestic_stock_functions import inquire_price, inquire_daily_price, order_cash, inquire_balance, inquire_investor
except ImportError as e:
    print(f"KIS Open API 모듈 로드 실패 (의존성 파일 확인 필요): {e}")
    pass

# 해외주식 모듈 import
try:
    from overseas_stock_functions import price as overseas_price, inquire_balance as overseas_inquire_balance, order as overseas_order
    OVERSEAS_AVAILABLE = True
    print("[INFO] Overseas stock module loaded successfully")
except ImportError as e:
    print(f"[WARN] 해외주식 모듈 로드 실패 (기능 제한): {e}")
    OVERSEAS_AVAILABLE = False 

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ModeChange(BaseModel):
    mode: str 

class StockBot:
    def __init__(self):
        self.is_running = False
        self.mode = "paper"
        
        # 시장 타입 (domestic 또는 overseas)
        self.market_type = DEFAULT_MARKET  # "domestic" 또는 "overseas"
        self.overseas_exchange = OVERSEAS_EXCHANGE  # "NASD", "NYSE", "AMEX" 등
        self.currency = "KRW" if self.market_type == "domestic" else "USD"
        
        self.target_profit = 3.0
        self.stop_loss = -3.0
        self.max_stock_count = 5
        
        # 국내주식 종목 리스트
        self.domestic_target_stocks = ["005930", "000660", "035420", "035720", "005380"]
        # 해외주식 종목 리스트 (미국 주식)
        self.overseas_target_stocks = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN"]
        
        # 현재 시장에 맞는 종목 리스트 설정
        self.target_stocks = self.domestic_target_stocks if self.market_type == "domestic" else self.overseas_target_stocks
        
        self.target_stock_info = {} 
        self.bought_stocks = {} 
        self.balance = 0 # 예수금
        self.total_buy_amount = 0 # 총 매입금액 추가
        self.entry_amount = 100000 
        self.logs = []
        
        # 시장 분석 상태
        self.market_status = "SIDEWAYS"
        self.market_rsi = 50.0
        self.market_reason = "Initializing..."
        
        self.daily_profit = 0
        self.daily_loss_limit = -500000 
        self.trade_count = 0
        self.win_count = 0
        
        self.csv_file = "trade_log.csv"
        self.init_csv()
        self.auth()
        # 초기 실행 시 계좌 정보 동기화
        self.update_account_info()

    def init_csv(self):
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Time", "Type", "Code", "Price", "Qty", "ProfitRate", "Reason"])

    def save_trade_log(self, type, code, price, qty, profit_rate, reason):
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), type, code, price, qty, f"{profit_rate:.2f}%", reason])

    def auth(self):
        try:
            svr = "prod" if self.mode == "real" else "vps"
            if 'ka' in globals():
                ka.auth(svr=svr, product=KIS_ACCOUNT_PROD)
                self.log(f"KIS API 인증 성공 ({self.mode.upper()})", "SYSTEM")
            else:
                self.log("KIS 모듈 없음 - 시뮬레이션 모드로 동작 불가", "ERROR")
        except Exception as e:
            self.log(f"인증 실패: {e}", "ERROR")

    def change_mode(self, mode):
        self.mode = mode
        self.auth()
        self.log(f"모드 변경 완료: {mode.upper()}", "SYSTEM")
        # 모드 변경 시 계좌 정보 재동기화
        self.update_account_info()
    
    def change_market(self, market_type):
        """시장 타입 변경 (domestic <-> overseas)"""
        if market_type not in ["domestic", "overseas"]:
            self.log(f"잘못된 시장 타입: {market_type}", "ERROR")
            return
        
        if market_type == "overseas" and not OVERSEAS_AVAILABLE:
            self.log("해외주식 모듈이 로드되지 않아 해외 시장으로 전환할 수 없습니다", "ERROR")
            return
        
        self.market_type = market_type
        self.currency = "KRW" if market_type == "domestic" else "USD"
        self.target_stocks = self.domestic_target_stocks if market_type == "domestic" else self.overseas_target_stocks
        
        # 기존 데이터 초기화 (시장 전환 시)
        self.bought_stocks = {}
        self.target_stock_info = {}
        
        market_name = "국내" if market_type == "domestic" else "해외"
        self.log(f"시장 변경 완료: {market_name} ({self.currency})", "SYSTEM")
        
        # 시장 변경 시 계좌 정보 재동기화
        self.update_account_info()

    def check_is_suspended(self, code):
        """종목 거래정지 여부 확인 (코드 58: 거래정지)"""
        try:
            if 'inquire_price' not in globals(): return False
            env_dv = "real" if self.mode == "real" else "demo"
            res = inquire_price(env_dv=env_dv, fid_input_iscd=code)
            if res and isinstance(res, dict):
                status_code = res.get('output', {}).get('iscd_stat_cls_code') if 'output' in res else res.get('iscd_stat_cls_code')
                if status_code == '58': return True
            return False
        except: return False

    def update_account_info(self):
        """계좌 잔고 및 보유 종목 동기화 함수 (국내/해외 자동 선택)"""
        try:
            env_dv = "real" if self.mode == "real" else "demo"
            
            if self.market_type == "domestic":
                # 국내주식 잔고 조회
                if 'inquire_balance' not in globals(): return
                
                # kis_auth가 선택한 계좌 사용
                res = inquire_balance(
                    env_dv=env_dv,
                    cano=ka.getTREnv().my_acct,
                    acnt_prdt_cd=ka.getTREnv().my_prod,
                    afhr_flpr_yn="N",
                    inqr_dvsn="02",
                    unpr_dvsn="01",
                    fund_sttl_icld_yn="N",
                    fncg_amt_auto_rdpt_yn="N",
                    prcs_dvsn="00"
                )
                
                if res is None: return

                if isinstance(res, tuple) and len(res) == 2:
                    holdings_data = res[0]
                    summary_data = res[1]
                    
                    if hasattr(summary_data, 'iloc') and not summary_data.empty: 
                        self.balance = float(summary_data.iloc[0]['dnca_tot_amt']) 
                        self.total_buy_amount = float(summary_data.iloc[0].get('pchs_amt_smtl_amt', 0)) 
                    elif isinstance(summary_data, list) and len(summary_data) > 0: 
                        self.balance = float(summary_data[0].get('dnca_tot_amt', 0))
                        self.total_buy_amount = float(summary_data[0].get('pchs_amt_smtl_amt', 0))

                    if hasattr(holdings_data, 'iterrows') and not holdings_data.empty: 
                        for _, row in holdings_data.iterrows():
                            code = row['pdno']
                            qty = int(row['hldg_qty'])
                            if qty > 0:
                                self.bought_stocks[code] = {
                                    "buy_price": float(row['pchs_avg_pric']),
                                    "qty": qty,
                                    "high_price": float(row['prpr']),
                                    "name": row['prdt_name'],
                                    "suspended": False
                                }
                    
                    # 거래정지 상태 업데이트
                    for code in list(self.bought_stocks.keys()):
                        if self.check_is_suspended(code):
                            self.bought_stocks[code]['suspended'] = True

                    # 총 매입금액 수동 계산 (API 미제공 시)
                    if self.total_buy_amount == 0 and self.bought_stocks:
                        self.total_buy_amount = sum(s['buy_price'] * s['qty'] for s in self.bought_stocks.values())

                    self.log(f"계좌 동기화 완료: 예수금 {self.balance:,.0f}원, 매입금 {self.total_buy_amount:,.0f}원", "SYSTEM")
            
            else:  # overseas
                # 해외주식 잔고 조회
                if not OVERSEAS_AVAILABLE or 'overseas_inquire_balance' not in globals():
                    self.log("해외주식 모듈 없음 - 잔고 조회 불가", "ERROR")
                    return
                
                # kis_auth가 선택한 계좌 사용
                holdings, summary = overseas_inquire_balance(
                    cano=ka.getTREnv().my_acct,
                    acnt_prdt_cd=ka.getTREnv().my_prod,
                    ovrs_excg_cd=self.overseas_exchange,
                    tr_crcy_cd="USD",
                    env_dv=env_dv
                )
                
                # 요약 정보에서 예수금 추출
                if not summary.empty:
                    # 해외주식 API의 output2에서 잔고 정보 추출
                    # 필드명이 다를 수 있으므로 여러 가능성 체크
                    if 'frcr_dncl_amt_2' in summary.columns:  # 외화 예수금
                        self.balance = float(summary.iloc[0].get('frcr_dncl_amt_2', 0))
                    elif 'ord_psbl_frcr_amt' in summary.columns:  # 주문가능 외화금액
                        self.balance = float(summary.iloc[0].get('ord_psbl_frcr_amt', 0))
                
                # 보유 종목 정보 추출
                if not holdings.empty:
                    self.total_buy_amount = 0
                    for _, row in holdings.iterrows():
                        code = row.get('ovrs_pdno', '')  # 해외상품번호
                        if not code:
                            continue
                        qty = int(row.get('ovrs_cblc_qty', 0))  # 해외잔고수량
                        if qty > 0:
                            buy_price = float(row.get('pchs_avg_pric', 0))  # 매입평균가격
                            current_price = float(row.get('now_pric2', 0))  # 현재가
                            self.bought_stocks[code] = {
                                "buy_price": buy_price,
                                "qty": qty,
                                "high_price": current_price,
                                "name": row.get('ovrs_item_name', code),  # 해외종목명
                                "suspended": False
                            }
                            self.total_buy_amount += buy_price * qty
                
                self.log(f"계좌 동기화 완료: 예수금 ${self.balance:,.2f}, 매입금 ${self.total_buy_amount:,.2f}", "SYSTEM")

        except Exception as e:
            self.log(f"계좌 동기화 실패: {e}", "ERROR")

    def log(self, msg, type="INFO"):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{self.mode.upper()}] {msg}")
        self.logs.insert(0, {"time": timestamp, "type": type, "msg": msg})
        self.logs = self.logs[:100]
        if type in ["BUY", "SELL", "ERROR", "SYSTEM"]:
            self.send_telegram(f"[{type}] {msg}")

    def send_telegram(self, msg):
        if TELEGRAM_TOKEN and CHAT_ID:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                requests.get(url, params={"chat_id": CHAT_ID, "text": msg})
            except: pass

    def analyze_market(self):
        """시장 지표(KODEX 200) 분석을 통한 추세 파악 및 설정 자동 조정"""
        try:
            if 'inquire_daily_price' not in globals(): return
            
            # KODEX 200 (069500)으로 시장 지수 확인
            res = inquire_daily_price(
                env_dv="real", 
                fid_cond_mrkt_div_code="J",
                fid_input_iscd="069500", 
                fid_period_div_code="D", 
                fid_org_adj_prc="1"
            )
            if res is None or res.empty: return

            df = res.sort_values('stck_bsop_date')
            close = pd.to_numeric(df['stck_clpr'])
            
            # RSI 지표 계산 (14일 기준)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss.replace(0, 1e-9)
            rsi = (100 - (100 / (1 + rs))).iloc[-1]
            self.market_rsi = float(rsi)

            current = float(close.iloc[-1])
            ma20 = float(close.rolling(window=20).mean().iloc[-1])
            
            # 시장 상태 판단 및 매매 조건 자동 조정
            prev_status = self.market_status
            
            if current > ma20 and rsi >= 50:
                self.market_status = "BULL"
                self.target_profit = 6.0
                self.stop_loss = -4.0
                self.market_reason = f"상승장: 주가({current:,.0f}) > 20일선, RSI({rsi:.1f}) 양호"
            elif current < ma20 and rsi < 50:
                self.market_status = "BEAR"
                self.target_profit = 2.0
                self.stop_loss = -2.0
                self.market_reason = f"하락장: 주가({current:,.0f}) < 20일선, RSI({rsi:.1f}) 침체"
            else:
                self.market_status = "SIDEWAYS"
                self.target_profit = 3.0
                self.stop_loss = -3.0
                self.market_reason = f"보합장: 주가 횡보 중, RSI({rsi:.1f}) 중립"
            
            self.log(f"시장 분석 완료 [{self.market_status}]: {self.market_reason}", "SYSTEM")

        except Exception as e:
            self.log(f"시장 분석 오류: {e}", "ERROR")

    def discover_stocks(self):
        try:
            self.log("종목 스캔 중... (거래대금 상위)", "INFO")
            candidates = ["005930", "000660", "035420", "035720", "005380", "051910", "000270", "006400", "068270"]
            self.target_stocks = candidates[:10]
        except: pass

    def get_market_data(self, code):
        try:
            if 'inquire_daily_price' not in globals(): return None, None, None, None, False
            env_dv = "real" if self.mode == "real" else "demo"
            fid_cond_mrkt_div_code = "J"
            
            res = inquire_daily_price(
                env_dv=env_dv,
                fid_cond_mrkt_div_code=fid_cond_mrkt_div_code,
                fid_input_iscd=code, 
                fid_period_div_code="D", 
                fid_org_adj_prc="1"
            )
            
            if res is None or res.empty: return None, None, None, None, False

            df = res.sort_values('stck_bsop_date') 
            close = pd.to_numeric(df['stck_clpr'])
            
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = (100 - (100 / (1 + (gain / loss)))).iloc[-1]

            ma20 = close.rolling(window=20).mean().iloc[-1]
            current_price = close.iloc[-1]

            prev_close = close.iloc[-2]
            is_too_high = (current_price - prev_close) / prev_close * 100 > 20.0

            investor_res = inquire_investor(
                env_dv=env_dv,
                fid_cond_mrkt_div_code=fid_cond_mrkt_div_code,
                fid_input_iscd=code
            )
            
            is_investor_buy = False
            if investor_res is not None and not investor_res.empty:
                try:
                    recent = investor_res.iloc[0]
                    frgn = float(recent.get('frgn_ntby_qty', 0)) 
                    orgn = float(recent.get('orgn_ntby_qty', 0))
                    if frgn > 0 or orgn > 0: is_investor_buy = True
                except: pass

            self.target_stock_info[code] = {
                "rsi": float(rsi), 
                "price": float(current_price), 
                "ma20": float(ma20),
                "investor": is_investor_buy
            }

            return rsi, ma20, current_price, is_too_high, is_investor_buy

        except Exception as e:
            return None, None, None, None, False

    def buy_stock(self, code, price, reason):
        if code in self.bought_stocks: return
        if self.daily_profit <= self.daily_loss_limit:
            self.log("금일 손실 한도 초과로 매수 중단", "ERROR")
            return

        qty = int(self.entry_amount / price)
        if qty < 1: return 
        
        try:
            env_dv = "real" if self.mode == "real" else "demo"
            
            if self.market_type == "domestic":
                # 국내주식 매수
                if 'order_cash' not in globals():
                    self.log("주문 모듈 없음 - 매수 불가", "ERROR")
                    return
                
                name = get_stock_name(code)
                # kis_auth가 선택한 계좌 사용
                res = order_cash(
                    env_dv=env_dv, ord_dv="buy", cano=ka.getTREnv().my_acct, 
                    acnt_prdt_cd=ka.getTREnv().my_prod, pdno=code, ord_dvsn="01", 
                    ord_qty=str(qty), ord_unpr="0", excg_id_dvsn_cd="KRX"
                )
                
                if not res.empty:
                    self.bought_stocks[code] = {"buy_price": price, "qty": qty, "high_price": price, "name": name, "suspended": False}
                    self.log(f"매수: {name}({code}) {qty}주 @ {price:,.0f}원 ({reason})", "BUY")
                    self.save_trade_log("BUY", code, price, qty, 0, reason)
                    self.update_account_info()
                else:
                    self.log(f"매수 실패({name})", "ERROR")
            
            else:  # overseas
                # 해외주식 매수
                if not OVERSEAS_AVAILABLE or 'overseas_order' not in globals():
                    self.log("해외주식 모듈 없음 - 매수 불가", "ERROR")
                    return
                
                name = code  # 해외주식은 티커 사용
                # kis_auth가 선택한 계좌 사용
                res = overseas_order(
                    cano=ka.getTREnv().my_acct,
                    acnt_prdt_cd=ka.getTREnv().my_prod,
                    ovrs_excg_cd=self.overseas_exchange,
                    pdno=code,
                    ord_qty=str(qty),
                    ovrs_ord_unpr="0",  # 시장가
                    ord_dv="buy",
                    env_dv=env_dv
                )
                
                if res is not None and not res.empty:
                    self.bought_stocks[code] = {"buy_price": price, "qty": qty, "high_price": price, "name": name, "suspended": False}
                    self.log(f"매수: {name} {qty}shares @ ${price:.2f} ({reason})", "BUY")
                    self.save_trade_log("BUY", code, price, qty, 0, reason)
                    self.update_account_info()
                else:
                    self.log(f"매수 실패({name})", "ERROR")
                    
        except Exception as e:
            self.log(f"매수 오류: {e}", "ERROR")

    def sell_stock(self, code, price, profit, reason):
        if code not in self.bought_stocks: return
        qty = self.bought_stocks[code]['qty']
        
        try:
            env_dv = "real" if self.mode == "real" else "demo"
            
            if self.market_type == "domestic":
                # 국내주식 매도
                if 'order_cash' not in globals():
                    self.log("주문 모듈 없음 - 매도 불가", "ERROR")
                    return
                
                name = get_stock_name(code)
                # kis_auth가 선택한 계좌 사용
                res = order_cash(
                    env_dv=env_dv, ord_dv="sell", cano=ka.getTREnv().my_acct, 
                    acnt_prdt_cd=ka.getTREnv().my_prod, pdno=code, ord_dvsn="01", 
                    ord_qty=str(qty), ord_unpr="0", excg_id_dvsn_cd="KRX"
                )
                
                if not res.empty:
                    del self.bought_stocks[code]
                    self.log(f"매도: {name}({code}) {qty}주 @ {price:,.0f}원 수익률 {profit:.2f}% ({reason})", "SELL")
                    self.save_trade_log("SELL", code, price, qty, profit, reason)
                    self.daily_profit += (price - self.bought_stocks.get(code, {}).get('buy_price', price)) * qty
                    if profit > 0: self.win_count += 1
                    self.trade_count += 1
                    self.update_account_info()
                else:
                    self.log(f"매도 실패({name})", "ERROR")
            
            else:  # overseas
                # 해외주식 매도
                if not OVERSEAS_AVAILABLE or 'overseas_order' not in globals():
                    self.log("해외주식 모듈 없음 - 매도 불가", "ERROR")
                    return
                
                name = code
                # kis_auth가 선택한 계좌 사용
                res = overseas_order(
                    cano=ka.getTREnv().my_acct,
                    acnt_prdt_cd=ka.getTREnv().my_prod,
                    ovrs_excg_cd=self.overseas_exchange,
                    pdno=code,
                    ord_qty=str(qty),
                    ovrs_ord_unpr="0",  # 시장가
                    ord_dv="sell",
                    env_dv=env_dv
                )
                
                if res is not None and not res.empty:
                    buy_price = self.bought_stocks[code]['buy_price']
                    del self.bought_stocks[code]
                    self.log(f"매도: {name} {qty}shares @ ${price:.2f} 수익률 {profit:.2f}% ({reason})", "SELL")
                    self.save_trade_log("SELL", code, price, qty, profit, reason)
                    self.daily_profit += (price - buy_price) * qty
                    if profit > 0: self.win_count += 1
                    self.trade_count += 1
                    self.update_account_info()
                else:
                    self.log(f"매도 실패({name})", "ERROR")
                    
        except Exception as e:
            self.log(f"매도 오류: {e}", "ERROR")

    def trading_loop(self):
        self.log("주식 자동매매 봇 시작 🚀", "SYSTEM")
        # 봇 시작 시 잔고 한번 더 체크
        self.update_account_info()
        
        loop_count = 0
        while True:
            if not self.is_running:
                time.sleep(1)
                continue

            now = datetime.datetime.now()
            is_market_open = (9 <= now.hour < 15) or (now.hour == 15 and now.minute <= 20)
            
            if self.mode == "real" and not is_market_open:
                if now.minute == 0 and now.second < 10:
                    self.log("장 마감 상태. 대기 중...", "INFO")
                time.sleep(10)
                continue

            try:
                if loop_count % 900 == 0: self.analyze_market()
                if loop_count % 1800 == 0: 
                    self.discover_stocks() 
                    self.update_account_info()
                loop_count += 1

                if len(self.bought_stocks) < self.max_stock_count:
                    for code in self.target_stocks:
                        rsi, ma20, price, is_too_high, is_investor_buy = self.get_market_data(code)
                        if not price: continue
                        if is_too_high: continue 

                        if rsi < 45 and is_investor_buy and price >= ma20:
                            self.buy_stock(code, price, "수급+눌림목💎")
                        elif rsi < 25 and price >= ma20 * 0.98:
                            self.buy_stock(code, price, "과매도 반등📉")
                        time.sleep(0.2)

                for code in list(self.bought_stocks.keys()):
                    info = self.bought_stocks[code]
                    _, _, current_price, _, _ = self.get_market_data(code)
                    if not current_price: continue

                    # 고가 갱신 (트레일링 스탑 기준점)
                    if current_price > info['high_price']: 
                        info['high_price'] = current_price
                    
                    buy_price = info['buy_price']
                    profit_rate = (current_price - buy_price) / buy_price * 100
                    
                    # 고점 대비 하락률 (트레일링 스탑)
                    drop_rate = (current_price - info['high_price']) / info['high_price'] * 100

                    # 1. 초급등 구간 (20% 이상): 수익 확정 우선
                    if profit_rate >= 20.0 and drop_rate <= -1.5:
                        self.sell_stock(code, current_price, profit_rate, "초급등 후 차익실현(TS)")
                    
                    # 2. 급등 구간 (10%~20%): 변동성 일부 허용
                    elif profit_rate >= 10.0 and drop_rate <= -3.0:
                        self.sell_stock(code, current_price, profit_rate, "급등 후 조정매도")
                    
                    # 3. 목표 달성 구간: 기본 익절 기준
                    elif profit_rate >= self.target_profit and drop_rate <= -2.0:
                        self.sell_stock(code, current_price, profit_rate, "목표달성 후 매도")
                    
                    # 4. 손절 구간
                    elif profit_rate <= self.stop_loss:
                        self.sell_stock(code, current_price, profit_rate, "손절매")
                        
                    time.sleep(0.2)

                time.sleep(1) 
            except Exception as e:
                self.log(f"루프 오류: {e}", "ERROR")
                time.sleep(5)

bot = StockBot()

@app.get("/api/status")
def status():
    # Numpy 데이터 타입 변환 (JSON 직렬화 오류 방지)
    def convert_numpy(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(i) for i in obj]
        elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif hasattr(obj, 'item'): # numpy 타입인 경우
            return obj.item()
        else:
            return obj

    response_data = {
        "isRunning": bot.is_running,
        "mode": bot.mode,
        "balance": bot.balance, # 예수금 추가
        "totalBuyAmount": bot.total_buy_amount, # 총 매입금액 추가
        "stocks": bot.bought_stocks,
        "target_info": bot.target_stock_info, 
        "logs": bot.logs,
        "summary": {
            "dailyProfit": bot.daily_profit,
            "tradeCount": bot.trade_count,
            "winCount": bot.win_count
        },
        "config": {
            "market": bot.market_status,
            "rsi": bot.market_rsi,
            "reason": bot.market_reason,
            "targetProfit": bot.target_profit,
            "stopLoss": bot.stop_loss
        },
        "marketType": bot.market_type,
        "currency": bot.currency,
        "overseasExchange": bot.overseas_exchange
    }
    return convert_numpy(response_data)

@app.post("/api/start")
def start(): bot.is_running = True; return {"status": "started"}

@app.post("/api/stop")
def stop(): bot.is_running = False; return {"status": "stopped"}

@app.post("/api/mode")
def change_mode(payload: ModeChange):
    bot.change_mode(payload.mode)
    return {"status": "ok", "mode": bot.mode}

@app.post("/api/market")
def change_market(payload: ModeChange):
    """Change between domestic and overseas markets"""
    bot.change_market(payload.mode)
    return {"status": "ok", "market": bot.market_type, "currency": bot.currency}

# 수정됨: HTML 파일을 읽는 대신 변수에 저장된 HTML 콘텐츠를 반환
@app.get("/", response_class=HTMLResponse)
def read_root():
    return HTML_CONTENT

if __name__ == "__main__":
    t = threading.Thread(target=bot.trading_loop, daemon=True)
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=8002)
