import pyupbit
import time
import json
import os
import threading
import uvicorn
import requests
import asyncio
from datetime import datetime, date
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
import config

# ============================================================
# ✅ 프론트(index.html) : QUANTUM TRADER UI + Settings Modal
# ============================================================
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>QUANTUM TRADER</title>

  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>

  <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&display=swap');

    body {
      background-color: #0f172a;
      color: #e2e8f0;
      font-family: 'Rajdhani', sans-serif;
      overflow-x: hidden;
    }

    .custom-scrollbar::-webkit-scrollbar { width: 6px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: #0f172a; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }

    .neon-text-cyan { text-shadow: 0 0 10px rgba(6, 182, 212, 0.5); }
    .neon-border-cyan { box-shadow: 0 0 15px rgba(6, 182, 212, 0.15); border-color: rgba(6, 182, 212, 0.5); }
    .neon-text-pink { text-shadow: 0 0 10px rgba(244, 63, 94, 0.5); }
    .neon-border-pink { box-shadow: 0 0 15px rgba(244, 63, 94, 0.15); border-color: rgba(244, 63, 94, 0.5); }
    .neon-text-green { text-shadow: 0 0 10px rgba(34, 197, 94, 0.5); }
    .neon-border-green { box-shadow: 0 0 15px rgba(34, 197, 94, 0.15); border-color: rgba(34, 197, 94, 0.5); }

    .glass-panel {
      background: rgba(17, 24, 39, 0.7);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(51, 65, 85, 0.5);
    }

    .modal-overlay {
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(5px);
    }
  </style>
</head>

<body>
  <div id="root"></div>

  <script type="text/babel">
    const { useState, useEffect } = React;

    const Icon = ({ name, size = 16, className = "" }) => {
      useEffect(() => { if (window.lucide) lucide.createIcons(); }, [name]);
      return <i data-lucide={name} className={className} style={{ width: size, height: size }}></i>;
    };

    const ProgressBar = ({ value, colorClass }) => (
      <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2">
        <div className={`h-1.5 rounded-full transition-all duration-500 ${colorClass}`} style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}></div>
      </div>
    );

    const SettingsModal = ({ isOpen, onClose, config, onSave }) => {
      const [formData, setFormData] = useState({
        black_list: "",
        stop_tickers: "",
        protect_tickers: "",
        max_hold_minutes: 60
      });

      useEffect(() => {
        if (isOpen && config) {
          setFormData({
            black_list: config.blackList?.join(", ") || "",
            stop_tickers: config.stopTickers?.join(", ") || "",
            protect_tickers: config.protectTickers?.join(", ") || "",
            max_hold_minutes: config.maxHoldMinutes || 60
          });
        }
      }, [isOpen]);

      if (!isOpen) return null;

      const handleSave = () => {
        const parse = (str) => str.split(",").map(s => s.trim()).filter(s => s);
        onSave({
          black_list: parse(formData.black_list),
          stop_tickers: parse(formData.stop_tickers),
          protect_tickers: parse(formData.protect_tickers),
          max_hold_minutes: Number(formData.max_hold_minutes)
        });
      };

      return (
        <div className="fixed inset-0 z-50 flex items-center justify-center modal-overlay p-4">
          <div className="glass-panel w-full max-w-2xl rounded-xl border border-cyan-500/50 shadow-[0_0_30px_rgba(6,182,212,0.2)] flex flex-col max-h-[90vh]">
            <div className="p-6 border-b border-slate-700 flex justify-between items-center">
              <h2 className="text-xl font-bold text-cyan-400 tracking-widest flex items-center gap-2">
                <Icon name="settings" /> SYSTEM CONFIGURATION
              </h2>
              <button onClick={onClose} className="text-slate-400 hover:text-white"><Icon name="x" size={24} /></button>
            </div>

            <div className="p-6 space-y-6 overflow-y-auto">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase mb-2">Max Hold Time (Minutes)</label>
                <input
                  type="number"
                  className="w-full bg-slate-900/80 border border-slate-700 rounded p-3 text-sm text-cyan-300 font-mono focus:border-cyan-500 focus:outline-none"
                  value={formData.max_hold_minutes}
                  onChange={e => setFormData({...formData, max_hold_minutes: e.target.value})}
                />
                <p className="text-[10px] text-slate-500 mt-1">Maximum time to hold a position before time-based exit.</p>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase mb-2">Blacklist (Trading Forbidden)</label>
                <textarea
                  className="w-full bg-slate-900/80 border border-slate-700 rounded p-3 text-sm text-red-300 font-mono focus:border-red-500 focus:outline-none"
                  rows="3"
                  value={formData.black_list}
                  onChange={e => setFormData({...formData, black_list: e.target.value})}
                  placeholder="KRW-ADA, KRW-TRX..."
                />
                <p className="text-[10px] text-slate-500 mt-1">Comma separated list of tickers to never trade.</p>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase mb-2">Stop Tickers (Temporary Halt)</label>
                <textarea
                  className="w-full bg-slate-900/80 border border-slate-700 rounded p-3 text-sm text-amber-300 font-mono focus:border-amber-500 focus:outline-none"
                  rows="2"
                  value={formData.stop_tickers}
                  onChange={e => setFormData({...formData, stop_tickers: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase mb-2">Protect Tickers (Long Term / Safe Re-entry)</label>
                <textarea
                  className="w-full bg-slate-900/80 border border-slate-700 rounded p-3 text-sm text-green-300 font-mono focus:border-green-500 focus:outline-none"
                  rows="3"
                  value={formData.protect_tickers}
                  onChange={e => setFormData({...formData, protect_tickers: e.target.value})}
                  placeholder="KRW-BTC, KRW-ETH..."
                />
                <p className="text-[10px] text-slate-500 mt-1">These assets use "Dip Buying" strategy and have wider stop losses.</p>
              </div>
            </div>

            <div className="p-6 border-t border-slate-700 flex justify-end gap-3 bg-slate-900/50">
              <button onClick={onClose} className="px-4 py-2 rounded text-sm font-bold text-slate-400 hover:text-white transition-colors">CANCEL</button>
              <button onClick={handleSave} className="px-6 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-bold shadow-lg transition-all neon-border-cyan border border-cyan-400">
                SAVE CONFIGURATION
              </button>
            </div>
          </div>
        </div>
      );
    };

    const App = () => {
      const [status, setStatus] = useState({
        isRunning: false,
        mode: 'paper',
        balance: 0,
        start_balance: 0,
        positions: [],
        logs: [],
        config: {}
      });

      const [market, setMarket] = useState([]);
      const [trending, setTrending] = useState([]);
      const [sellBusy, setSellBusy] = useState({});
      const [panicBusy, setPanicBusy] = useState(false);
      const [showConfig, setShowConfig] = useState(false);

      const fetchData = async () => {
        try {
          const origin = window.location.origin;
          const [resStatus, resMarket, resTrending] = await Promise.all([
            fetch(`${origin}/api/status`).then(r => r.json()),
            fetch(`${origin}/api/market`).then(r => r.json()),
            fetch(`${origin}/api/trending`).then(r => r.json())
          ]);
          setStatus(resStatus);
          setMarket(resMarket);
          setTrending(resTrending);
        } catch (e) { }
      };

      useEffect(() => {
        fetchData();
        const timer = setInterval(fetchData, 3000);
        return () => clearInterval(timer);
      }, []);

      const toggleBot = async (cmd) => {
        try {
          await fetch(`${window.location.origin}/api/${cmd}`, { method: 'POST' });
        } finally { fetchData(); }
      };

      const changeMode = async (m) => {
        try {
          await fetch(`${window.location.origin}/api/mode`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: m })
          });
        } finally { fetchData(); }
      };

      const postJSON = async (url, payload) => {
        const r = await fetch(url, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      };

      const saveConfig = async (newConfig) => {
        try {
          await postJSON(`${window.location.origin}/api/config/system`, newConfig);
          setShowConfig(false);
          alert("Configuration Saved!");
          fetchData();
        } catch(e) { alert("Save failed: " + e.message); }
      };

      const sellAll = async (ticker) => {
        if(!window.confirm(`${ticker} 매도하시겠습니까?`)) return;
        setSellBusy(prev => ({ ...prev, [ticker]: true }));
        try {
          await postJSON(`${window.location.origin}/api/sell_one`, { ticker });
          await fetchData();
        } catch (e) { alert(e.message); }
        finally { setSellBusy(prev => ({ ...prev, [ticker]: false })); }
      };

      const panicSell = async () => {
        if(!window.confirm("🚨 SYSTEM WARNING: EMERGENCY STOP & SELL ALL?")) return;
        setPanicBusy(true);
        try {
          await postJSON(`${window.location.origin}/api/panic_sell`, {});
          alert("EMERGENCY PROTOCOL INITIATED.");
          await fetchData();
        } catch(e) { alert(e.message); }
        finally { setPanicBusy(false); }
      };

      // --- Calculations ---
      const totalAsset = status.positions.reduce((acc, p) => acc + (p.cur_price * p.amount), status.balance);
      const usedAsset = totalAsset - status.balance;
      const investRatio = totalAsset > 0 ? (usedAsset / totalAsset) * 100 : 0;
      const dailyPnL = totalAsset - (status.start_balance || 1000000);
      const dailyPnLPercent = status.start_balance > 0 ? (dailyPnL / status.start_balance) * 100 : 0;

      const isBull = status.config?.market === 'BULL';
      const isBear = status.config?.market === 'BEAR';

      return (
        <div className="min-h-screen p-4 md:p-8">
          <SettingsModal
            isOpen={showConfig}
            onClose={() => setShowConfig(false)}
            config={status.config}
            onSave={saveConfig}
          />

          {/* HEADER */}
          <div className="flex flex-col md:flex-row justify-between items-center mb-8 border-b border-slate-800 pb-6">
            <div>
              <h1 className="text-4xl font-bold tracking-tighter text-white neon-text-cyan flex items-center gap-2">
                QUANTUM TRADER <span className="text-xs bg-cyan-900/30 text-cyan-400 px-2 py-1 rounded border border-cyan-500/30">V.2.1 (SAFE)</span>
              </h1>
              <p className="text-slate-500 text-sm tracking-widest mt-1">AI-POWERED ALGORITHMIC TRADING SYSTEM</p>
            </div>

            <div className="flex gap-4 mt-4 md:mt-0">
              <div className={`px-4 py-2 rounded-lg border font-bold flex items-center gap-2 ${status.isRunning ? 'bg-green-900/20 border-green-500/50 text-green-400 neon-border-green' : 'bg-slate-800 border-slate-700 text-slate-500'}`}>
                <div className={`w-2 h-2 rounded-full ${status.isRunning ? 'bg-green-400 animate-pulse' : 'bg-slate-500'}`}></div>
                {status.isRunning ? 'RUNNING' : 'STOPPED'}
              </div>

              <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-700">
                <button onClick={() => changeMode('paper')} className={`px-4 py-1.5 rounded text-sm font-bold transition-all ${status.mode === 'paper' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}>PAPER</button>
                <button onClick={() => changeMode('real')} className={`px-4 py-1.5 rounded text-sm font-bold transition-all ${status.mode === 'real' ? 'bg-amber-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}>REAL</button>
              </div>

              <button onClick={() => setShowConfig(true)} className="px-4 py-2 rounded-lg border border-slate-600 bg-slate-800 text-slate-300 font-bold hover:bg-slate-700 transition-all flex items-center gap-2">
                <Icon name="settings" size={16} /> SETTINGS
              </button>

              <button onClick={status.isRunning ? () => toggleBot('stop') : () => toggleBot('start')} className={`px-6 py-2 rounded-lg font-bold border transition-all ${status.isRunning ? 'bg-red-600 hover:bg-red-500 border-red-400 text-white neon-border-pink' : 'bg-cyan-600 hover:bg-cyan-500 border-cyan-400 text-white neon-border-cyan'}`}>
                {status.isRunning ? 'STOP SYSTEM' : 'START SYSTEM'}
              </button>

              <button onClick={panicSell} disabled={panicBusy} className="px-4 py-2 rounded-lg bg-red-900/50 border border-red-500/50 text-red-400 font-bold hover:bg-red-900 hover:text-white transition-all" title="Emergency Sell">
                {panicBusy ? '!!!' : '🚨'}
              </button>
            </div>
          </div>

          {/* DASHBOARD GRID */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">

            {/* Asset Allocation */}
            <div className="glass-panel p-5 rounded-xl border-l-4 border-l-cyan-500 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity"><Icon name="pie-chart" size={48} /></div>
              <h3 className="text-cyan-400 text-xs font-bold tracking-widest uppercase mb-4">Asset Allocation</h3>
              <div className="space-y-2 font-mono text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Stocks (Used)</span>
                  <span className="text-white font-bold">{Math.round(usedAsset).toLocaleString()}원</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Cash (Free)</span>
                  <span className="text-cyan-300 font-bold">{Math.round(status.balance).toLocaleString()}원</span>
                </div>
              </div>
              <ProgressBar value={investRatio} colorClass="bg-cyan-500" />
            </div>

            {/* Daily P&L */}
            <div className="glass-panel p-5 rounded-xl border-l-4 border-l-blue-500 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity"><Icon name="bar-chart-2" size={48} /></div>
              <h3 className="text-blue-400 text-xs font-bold tracking-widest uppercase mb-2">Daily P&L</h3>
              <div className={`text-3xl font-black font-mono mt-2 ${dailyPnL >= 0 ? 'text-green-400 neon-text-green' : 'text-red-400 neon-text-pink'}`}>
                {dailyPnL > 0 ? '+' : ''}{Math.round(dailyPnL).toLocaleString()}원
              </div>
              <p className={`text-xs font-bold mt-1 ${dailyPnLPercent >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {dailyPnLPercent.toFixed(2)}% Today
              </p>
            </div>

            {/* Win Rate (Placeholder logic) */}
            <div className="glass-panel p-5 rounded-xl border-l-4 border-l-purple-500 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity"><Icon name="target" size={48} /></div>
              <h3 className="text-purple-400 text-xs font-bold tracking-widest uppercase mb-2">Total Equity</h3>
              <div className="text-3xl font-black text-white font-mono mt-2">
                 {Math.round(totalAsset).toLocaleString()}
              </div>
              <p className="text-xs text-slate-500 mt-1 uppercase">Total Estimated Assets</p>
            </div>

            {/* Market Sentiment */}
            <div className={`glass-panel p-5 rounded-xl border-l-4 relative overflow-hidden group ${isBull ? 'border-l-green-500 neon-border-green' : isBear ? 'border-l-red-500 neon-border-pink' : 'border-l-slate-500'}`}>
              <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity"><Icon name="activity" size={48} /></div>
              <h3 className="text-slate-400 text-xs font-bold tracking-widest uppercase mb-2">Market Sentiment</h3>
              <div className={`text-4xl font-black uppercase tracking-tighter ${isBull ? 'text-green-400 neon-text-green' : isBear ? 'text-red-500 neon-text-pink' : 'text-slate-300'}`}>
                {status.config?.market || 'SIDEWAYS'}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {isBull ? 'Strong Uptrend Detected' : isBear ? 'Downtrend - Caution' : 'Low Volatility'}
              </p>
            </div>
          </div>

          {/* MAIN CONTENT SPLIT */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">

            {/* LEFT: HOLDINGS PORTFOLIO */}
            <div className="lg:col-span-2 glass-panel rounded-xl overflow-hidden flex flex-col h-[400px]">
              <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <h3 className="text-cyan-400 font-bold tracking-widest text-sm flex items-center gap-2">
                  <span className="w-2 h-2 bg-cyan-400 rounded-full"></span> HOLDINGS PORTFOLIO
                </h3>
                <span className="text-xs text-slate-500 font-mono">COUNT: {status.positions.length}</span>
              </div>

              <div className="overflow-auto custom-scrollbar flex-1 bg-[#0B0E14]">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-900 text-slate-500 text-[10px] uppercase font-bold sticky top-0 z-10">
                    <tr>
                      <th className="p-4">Symbol</th>
                      <th className="p-4 text-right">Avg Price</th>
                      <th className="p-4 text-right">Current</th>
                      <th className="p-4 text-right">Qty</th>
                      <th className="p-4 text-right">P&L %</th>
                      <th className="p-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono">
                    {status.positions.map((p, i) => (
                      <tr key={i} className="hover:bg-slate-800/30 transition-colors group">
                        <td className="p-4 font-bold text-slate-200">
                          {p.ticker.split('-')[1]}
                          {p.is_protect && <span className="ml-2 text-[9px] bg-amber-500/20 text-amber-400 px-1 rounded border border-amber-500/30">PROT</span>}
                        </td>
                        <td className="p-4 text-right text-slate-400">{Math.round(p.buy_price).toLocaleString()}</td>
                        <td className="p-4 text-right text-slate-300">{Math.round(p.cur_price).toLocaleString()}</td>
                        <td className="p-4 text-right text-cyan-600">{Number(p.amount).toFixed(4)}</td>
                        <td className={`p-4 text-right font-bold ${p.profit_rate >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {p.profit_rate > 0 ? '+' : ''}{Number(p.profit_rate).toFixed(2)}%
                        </td>
                        <td className="p-4 text-right">
                          <button onClick={() => sellAll(p.ticker)} disabled={sellBusy[p.ticker]} className="opacity-0 group-hover:opacity-100 transition-opacity bg-red-900/30 hover:bg-red-600 text-red-500 hover:text-white px-3 py-1 rounded text-xs border border-red-500/30">
                            SELL
                          </button>
                        </td>
                      </tr>
                    ))}
                    {status.positions.length === 0 && (
                      <tr><td colSpan="6" className="p-20 text-center text-slate-600 font-mono text-sm">NO ACTIVE POSITIONS</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* RIGHT: MARKET STRATEGY */}
            <div className="glass-panel rounded-xl p-6 flex flex-col justify-between h-[400px]">
              <div>
                <h3 className="text-cyan-400 font-bold tracking-widest text-sm mb-6 flex items-center gap-2">
                  <span className="w-2 h-2 bg-cyan-400 rounded-full"></span> MARKET STRATEGY
                </h3>

                {/* RSI Visualization */}
                <div className="mb-8">
                  <div className="flex justify-between text-xs font-bold text-slate-400 mb-1">
                    <span>Weak</span>
                    <span className="text-white">RSI Threshold: {status.config?.rsiThreshold}</span>
                    <span>Strong</span>
                  </div>
                  <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 w-full opacity-30"></div>
                    <div className="absolute top-0 bottom-0 bg-white w-1 shadow-[0_0_10px_white]" style={{ left: `${status.config?.rsiThreshold}%` }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-600 mt-1 uppercase">
                    <span>Oversold</span>
                    <span>Neutral</span>
                    <span>Overbought</span>
                  </div>
                </div>

                {/* TP / SL Cards */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-[#0B0E14] border border-green-900/50 p-4 rounded-lg text-center relative overflow-hidden">
                    <div className="text-[10px] text-green-600 uppercase font-bold mb-1">Take Profit</div>
                    <div className="text-3xl font-black text-green-400 neon-text-green">+{status.config?.targetProfit}%</div>
                    <div className="text-[9px] text-slate-500 mt-1">Aggressive Scaling</div>
                  </div>
                  <div className="bg-[#0B0E14] border border-red-900/50 p-4 rounded-lg text-center relative overflow-hidden">
                    <div className="text-[10px] text-red-600 uppercase font-bold mb-1">Stop Loss</div>
                    <div className="text-3xl font-black text-red-400 neon-text-pink">{status.config?.stopLoss}%</div>
                    <div className="text-[9px] text-slate-500 mt-1">Trailing Safety</div>
                  </div>
                </div>
              </div>

              {/* Analysis Text */}
              <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700">
                <div className="text-xs text-cyan-500 font-bold mb-1 uppercase">System Analysis</div>
                <p className="text-sm text-slate-300 leading-relaxed">
                  Market Condition: <span className="font-bold text-white">{status.config?.market}</span>.
                  Currently scanning top {20} assets by volume.
                  Auto-tuning enabled: <span className={status.config?.autoTune ? 'text-green-400' : 'text-red-400'}>{String(status.config?.autoTune)}</span>.
                  Protected Assets: {status.config?.protectTickers?.length}
                </p>
              </div>
            </div>

            {/* RIGHT 2: TRENDING CRYPTO */}
            <div className="glass-panel rounded-xl overflow-hidden flex flex-col h-[400px]">
              <div className="p-4 border-b border-slate-800 bg-slate-900/50">
                <h3 className="text-pink-400 font-bold tracking-widest text-sm flex items-center gap-2">
                  <span className="w-2 h-2 bg-pink-400 rounded-full animate-pulse"></span> TRENDING CRYPTO
                </h3>
              </div>

              <div className="overflow-auto custom-scrollbar flex-1 bg-[#0B0E14] p-4 space-y-3">
                {trending.length === 0 ? (
                  <div className="text-center text-slate-600 py-8">Loading trends...</div>
                ) : (
                  trending.map((coin) => {
                    const isPositive = coin.change_rate >= 0;
                    const changeColor = isPositive ? 'text-green-400' : 'text-red-400';
                    const bgColor = isPositive ? 'bg-green-900/20 border-green-500/30' : 'bg-red-900/20 border-red-500/30';
                    
                    return (
                      <div key={coin.ticker} className={`glass-panel p-3 rounded-lg border ${bgColor} hover:scale-[1.02] transition-transform`}>
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="font-bold text-white text-sm">{coin.name}</div>
                            <div className="text-[10px] text-slate-500 font-mono">{coin.ticker}</div>
                          </div>
                          <div className="text-right">
                            <div className={`text-lg font-black ${changeColor}`}>
                              {isPositive ? '+' : ''}{coin.change_rate}%
                            </div>
                            <div className="text-[9px] text-slate-600 uppercase font-bold">{coin.trend}</div>
                          </div>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-slate-400">Price</span>
                          <span className="text-white font-mono">
                            {coin.price >= 1000 ? `${(coin.price / 1000).toFixed(1)}K` : coin.price.toFixed(2)}₩
                          </span>
                        </div>
                        {coin.rsi && (
                          <div className="flex justify-between items-center text-xs mt-1">
                            <span className="text-slate-400">RSI</span>
                            <span className={`font-mono font-bold ${
                              coin.rsi > 70 ? 'text-red-400' : coin.rsi < 30 ? 'text-green-400' : 'text-slate-300'
                            }`}>{coin.rsi}</span>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* BOTTOM: SYSTEM LOGS */}
          <div className="glass-panel rounded-xl overflow-hidden flex flex-col h-[250px]">
            <div className="p-3 border-b border-slate-800 bg-slate-900/80">
              <h3 className="text-slate-400 font-bold tracking-widest text-xs uppercase">System Logs</h3>
            </div>
            <div className="flex-1 overflow-auto p-4 font-mono text-xs space-y-1 bg-black custom-scrollbar">
              {status.logs.map((log, i) => (
                <div key={i} className="flex gap-3 hover:bg-slate-900/30 p-0.5 rounded">
                  <span className="text-slate-600">[{log.timestamp}]</span>
                  <span className={`${log.type === 'BUY' ? 'text-green-400' : log.type === 'SELL' ? 'text-red-400' : log.type === 'RISK' ? 'text-amber-400 font-bold' : 'text-slate-300'}`}>
                    {log.message}
                  </span>
                </div>
              ))}
            </div>
          </div>

        </div>
      );
    };
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (if any)
    yield
    # Shutdown logic
    global shutting_down
    shutting_down = True

# ====== FastAPI 설정 ======
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

shutting_down = False

@app.middleware("http")
async def handle_cancelled(request: Request, call_next):
    if shutting_down:
        return JSONResponse({"detail": "shutting down"}, status_code=503)
    try:
        return await call_next(request)
    except asyncio.CancelledError:
        return JSONResponse({"detail": "request cancelled"}, status_code=503)

class ModeChange(BaseModel):
    mode: str
class SellOne(BaseModel):
    ticker: str
class ConfigUpdate(BaseModel):
    targetProfit: float
    stopLoss: float
    rsiThreshold: float
    maxHoldMinutes: Optional[int] = None
    holdMinProfit: Optional[float] = None
    dailyMaxLossPct: Optional[float] = None
    watchTopN: Optional[int] = None
    maxTradeCoinCount: Optional[int] = None
    autoTune: Optional[bool] = None

class SystemConfig(BaseModel):
    black_list: List[str]
    stop_tickers: List[str]
    protect_tickers: List[str]
    max_hold_minutes: int

# ====== 유틸 ======
class PriceCache:
    def __init__(self, ttl_sec=3):
        self.ttl = ttl_sec
        self.data = {}
        self.lock = threading.Lock()
    def get(self, ticker):
        now = time.time()
        with self.lock:
            v = self.data.get(ticker)
            if not v: return None
            ts, price = v
            if now - ts > self.ttl: return None
            return price
    def set(self, ticker, price):
        with self.lock:
            self.data[ticker] = (time.time(), price)

price_cache = PriceCache(ttl_sec=3)

def safe_sleep(sec: float):
    time.sleep(sec)

def get_current_price_safe(ticker: str, retries=3, base_delay=0.15):
    cached = price_cache.get(ticker)
    if cached is not None: return cached
    delay = base_delay
    for _ in range(retries):
        try:
            price = pyupbit.get_current_price(ticker)
            if isinstance(price, list): price = price[0]
            if isinstance(price, dict): price = price.get("trade_price")
            if price is not None:
                price = float(price)
                price_cache.set(ticker, price)
                return price
        except: pass
        safe_sleep(delay)
        delay *= 2
    return None

def get_ohlcv_safe(ticker: str, interval="minute3", count=50, retries=3):
    delay = 0.2
    for _ in range(retries):
        try:
            df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
            if df is not None and len(df) >= 20: return df
        except: pass
        safe_sleep(delay)
        delay *= 2
    return None

def fetch_top_markets_by_trade_price(top_n=20):
    try:
        markets = pyupbit.get_tickers(fiat="KRW")
        if not markets: return []
        url = "https://api.upbit.com/v1/ticker"
        chunks = [markets[i:i + 100] for i in range(0, len(markets), 100)]
        rows = []
        for ch in chunks:
            r = requests.get(url, params={"markets": ",".join(ch)}, timeout=3)
            if r.status_code == 200: rows.extend(r.json())
            safe_sleep(0.05)
        rows.sort(key=lambda x: float(x.get("acc_trade_price_24h", 0) or 0), reverse=True)
        return [x["market"] for x in rows[:top_n] if "market" in x]
    except: return []

def fetch_orderbook(ticker: str):
    try:
        url = "https://api.upbit.com/v1/orderbook"
        r = requests.get(url, params={"markets": ticker}, timeout=3)
        if r.status_code == 200:
            j = r.json()
            if j: return j[0]
    except: pass
    return None

def fetch_recent_trades(ticker: str, count=30):
    try:
        url = "https://api.upbit.com/v1/trades/ticks"
        r = requests.get(url, params={"market": ticker, "count": count}, timeout=3)
        if r.status_code == 200: return r.json()
    except: pass
    return None

def get_major_crypto_trends():
    """
    주요 암호화폐의 실시간 추세 데이터를 반환
    Returns: List of dicts with ticker, name, price, change_rate, volume_24h, rsi, trend
    """
    major_coins = [
        ("KRW-BTC", "Bitcoin"),
        ("KRW-ETH", "Ethereum"),
        ("KRW-XRP", "Ripple"),
        ("KRW-ADA", "Cardano"),
        ("KRW-SOL", "Solana"),
        ("KRW-DOGE", "Dogecoin")
    ]
    
    results = []
    try:
        # Upbit API로 가격 정보 조회
        tickers = [coin[0] for coin in major_coins]
        url = "https://api.upbit.com/v1/ticker"
        r = requests.get(url, params={"markets": ",".join(tickers)}, timeout=3)
        
        if r.status_code != 200:
            return []
        
        price_data = {item["market"]: item for item in r.json()}
        
        for ticker, name in major_coins:
            if ticker not in price_data:
                continue
                
            data = price_data[ticker]
            price = data.get("trade_price", 0)
            change_rate = data.get("signed_change_rate", 0) * 100  # Convert to percentage
            volume_24h = data.get("acc_trade_price_24h", 0)
            
            # RSI 계산
            rsi, ma, px, pump, ma5, open_p = get_indicators(ticker)
            
            # 추세 판단
            if pump:
                trend = "급등"
            elif change_rate > 3:
                trend = "강세"
            elif change_rate > 0:
                trend = "상승"
            elif change_rate > -3:
                trend = "하락"
            else:
                trend = "급락"
            
            results.append({
                "ticker": ticker,
                "name": name,
                "price": price,
                "change_rate": round(change_rate, 2),
                "volume_24h": int(volume_24h),
                "rsi": round(rsi, 1) if rsi else None,
                "trend": trend
            })
    except Exception as e:
        print(f"[ERROR] get_major_crypto_trends: {e}")
    
    return results

# ====== 봇 상태 ======
class BotState:
    def __init__(self):
        self.lock = threading.RLock()
        self.is_running = False
        self.mode = "paper"
        self.target_profit = 1.5
        self.stop_loss = -3.0
        self.rsi_threshold = 50.0
        self.max_trade_coin_count = 6
        self.watch_top_n = 20
        self.trailing_after_tp_drop = -1.0
        self.trailing_general_drop = -2.5
        self.max_hold_minutes = 60 # 기본값
        self.hold_min_profit = 0.9
        self.daily_max_loss_pct = -3.0
        self.last_risk_warn_time = 0

        self.load_system_config()

        self.market_status = "SIDEWAYS"
        self.real_bought_coins = {}
        self.real_balance = 0.0
        self.paper_bought_coins = {}
        self.paper_balance = 1_000_000.0
        self.balance_history = []
        self.logs = []
        self.target_tickers = []
        self.last_report_time = time.time()
        self.day_key = date.today().isoformat()
        self.day_start_balance_real = None
        self.day_start_balance_paper = 1_000_000.0
        self.upbit = pyupbit.Upbit(config.ACCESS_KEY, config.SECRET_KEY)
        self.protect_last_alert = {}
        self.buy_fail_cooldown = {}
        self.buy_fail_cooldown_sec = 60
        self.last_insufficient_warn = 0

        self.sell_cooldown = {} # ticker -> timestamp
        self.sell_cooldown_sec = 1800

        # [수정] 작전주 필터 완화 (매수 기회 확대)
        self.risky_spread_max = 0.006
        self.risky_depth10_min = 10_000_000
        self.risky_top_trades_ratio = 0.75
        self.risky_wick_ratio = 0.70
        self.risky_wick_count = 6

        self.risky_check_ttl = 10
        self.risky_cache = {}
        self.risky_last_log = {}
        self.exit_confirm = {}
        self.exit_confirm_ttl = 12
        self.exit_confirm_need_sl = 2
        self.exit_confirm_need_drop = 2
        self.exit_confirm_need_tpdrop = 2
        self.auto_tune = True
        self.regime_interval_sec = 60
        self.last_regime_ts = 0

        self.bull_enter = 0.005
        self.bull_exit  = 0.002
        self.bear_enter = -0.005
        self.bear_exit  = -0.002

        self.exit_confirm_need_sl = 3
        self.exit_confirm_need_drop = 3
        self.exit_confirm_need_tpdrop = 2

        self.protect_sell_info = {}
        self.protect_stop_loss = -5.0

        self.load_state()
        self.sanitize_positions()

    def load_system_config(self):
        defaults = {
            "black_list": ["KRW-ADA", "KRW-TRX", "KRW-USD1", "KRW-BOUNTY", "KRW-CTC", "KRW-USDT"],
            "stop_tickers": ["KRW-XCORE"],
            "protect_tickers": ["KRW-BTC", "KRW-ETH", "KRW-XRP"],
            "max_hold_minutes": 60
        }
        if os.path.exists("tickers.json"):
            try:
                with open("tickers.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.black_list = data.get("black_list", defaults["black_list"])
                    self.stop_tickers = data.get("stop_tickers", defaults["stop_tickers"])
                    self.protect_tickers = data.get("protect_tickers", defaults["protect_tickers"])
                    self.max_hold_minutes = data.get("max_hold_minutes", defaults["max_hold_minutes"])
            except:
                self.black_list = defaults["black_list"]
                self.stop_tickers = defaults["stop_tickers"]
                self.protect_tickers = defaults["protect_tickers"]
                self.max_hold_minutes = defaults["max_hold_minutes"]
        else:
            self.black_list = defaults["black_list"]
            self.stop_tickers = defaults["stop_tickers"]
            self.protect_tickers = defaults["protect_tickers"]
            self.max_hold_minutes = defaults["max_hold_minutes"]
            self.save_system_config()

    def save_system_config(self):
        data = {
            "black_list": self.black_list,
            "stop_tickers": self.stop_tickers,
            "protect_tickers": self.protect_tickers,
            "max_hold_minutes": self.max_hold_minutes
        }
        try:
            with open("tickers.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except: pass

    def send_telegram(self, msg):
        if config.TELEGRAM_TOKEN and config.CHAT_ID:
            try:
                requests.get(f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage", params={"chat_id": config.CHAT_ID, "text": msg}, timeout=3)
            except: pass

    def log(self, msg, type="INFO"):
        ts = datetime.now().strftime('%H:%M:%S')
        log_entry = {"id": f"{ts}-{len(self.logs)}", "timestamp": ts, "type": type, "message": str(msg)}
        print(f"[{ts}] [{self.mode.upper()}] {str(msg)}")
        with self.lock:
            self.logs.insert(0, log_entry)
            self.logs = self.logs[:150]
        if type in ["BUY", "SELL", "ERROR", "SYSTEM", "REPORT", "RISK"]:
            self.send_telegram(f"[{type}] {msg}")

    def load_state(self):
        with self.lock:
            if os.path.exists("bot_state.json"):
                try:
                    with open("bot_state.json", 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if "coins" in data: self.real_bought_coins = data["coins"]
                        else: self.real_bought_coins = data
                except: pass

                try:
                    if os.path.exists("protect_state.json"):
                        with open("protect_state.json", 'r', encoding='utf-8') as f:
                            self.protect_sell_info = json.load(f)
                except: pass

            if os.path.exists("paper_state.json"):
                try:
                    with open("paper_state.json", 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.paper_bought_coins = data.get('coins', {})
                        self.paper_balance = float(data.get('balance', 1000000))
                except: pass

    def sanitize_positions(self):
        try:
            valid = set(pyupbit.get_tickers(fiat="KRW") or [])
            if not valid:
                self.log("⚠️ 티커 목록 조회 실패: 기존 포지션 유지 (네트워크 오류 가능성)", "SYSTEM")
                return

            with self.lock:
                self.paper_bought_coins = {k: v for k, v in self.paper_bought_coins.items() if k in valid}
                self.real_bought_coins = {k: v for k, v in self.real_bought_coins.items() if k in valid}
            self.save_state()
        except: pass

    def save_state(self):
        with self.lock:
            try:
                with open("bot_state.json", 'w', encoding='utf-8') as f: json.dump(self.real_bought_coins, f, indent=4)
                with open("paper_state.json", 'w', encoding='utf-8') as f: json.dump({"coins": self.paper_bought_coins, "balance": self.paper_balance}, f, indent=4)
                with open("protect_state.json", 'w', encoding='utf-8') as f: json.dump(self.protect_sell_info, f, indent=4)
            except: pass

    def update_balance(self):
        today = date.today().isoformat()
        if today != self.day_key:
            self.day_key = today
            self.day_start_balance_real = None
            self.day_start_balance_paper = self.paper_balance
        if self.mode == "real":
            try:
                bal = float(self.upbit.get_balance("KRW") or 0)
                with self.lock: self.real_balance = bal
                if self.day_start_balance_real is None: self.day_start_balance_real = bal
            except: pass
        else:
            if self.day_start_balance_paper is None: self.day_start_balance_paper = self.paper_balance

        current = self.real_balance if self.mode == "real" else self.paper_balance
        now = datetime.now().strftime('%H:%M')
        with self.lock:
            if not self.balance_history or self.balance_history[-1]['time'] != now:
                self.balance_history.append({"time": now, "balance": current})
                self.balance_history = self.balance_history[-60:]

    def send_periodic_report(self):
        if time.time() - self.last_report_time > 3600:
            cur = self.real_balance if self.mode == "real" else self.paper_balance
            msg = f"📊 정기 보고: 잔고 {cur:,.0f}원"
            self.log(msg, "REPORT")
            self.last_report_time = time.time()

    def check_daily_risk(self):
        start = self.day_start_balance_real if self.mode == "real" else self.day_start_balance_paper
        if not start or start <= 0: return
        cur = self.real_balance if self.mode == "real" else self.paper_balance
        dd = (cur - start) / start * 100
        if dd <= self.daily_max_loss_pct:
            now = time.time()
            if now - self.last_risk_warn_time >= 600:
                self.last_risk_warn_time = now
                self.log(f"⚠️ 일일 손실 한도 경고: {dd:.2f}%", "RISK")

bot = BotState()

# 필터 및 로직 함수들
def _should_log_risky(ticker: str) -> bool:
    now = time.time()
    with bot.lock:
        if now - bot.risky_last_log.get(ticker, 0) >= 30:
            bot.risky_last_log[ticker] = now
            return True
    return False

def is_risky_market(ticker: str):
    now = time.time()
    with bot.lock:
        cached = bot.risky_cache.get(ticker)
        if cached and (now - cached[0] < bot.risky_check_ttl): return cached[1], cached[2]
    reasons = []
    ob = fetch_orderbook(ticker)
    if ob and ob["orderbook_units"]:
        units = ob["orderbook_units"]
        ask = float(units[0].get("ask_price", 0))
        bid = float(units[0].get("bid_price", 0))
        if ask and bid:
            spread = (ask - bid) / ((ask+bid)/2)
            if spread > bot.risky_spread_max: reasons.append("SPREAD")
        depth = sum([u["ask_price"]*u["ask_size"] + u["bid_price"]*u["bid_size"] for u in units[:10]])
        if depth < bot.risky_depth10_min: reasons.append("DEPTH")
    else: reasons.append("OB_FAIL")

    trades = fetch_recent_trades(ticker)
    if trades:
        vals = sorted([t["trade_price"]*t["trade_volume"] for t in trades], reverse=True)
        if sum(vals) > 0 and sum(vals[:3])/sum(vals) > bot.risky_top_trades_ratio: reasons.append("WHALE")
    else: reasons.append("TRADES_FAIL")

    df = get_ohlcv_safe(ticker, count=25)
    if df is not None and len(df) >= 20:
        bad = 0
        for _, r in df.tail(20).iterrows():
            rng = r["high"] - r["low"]
            if rng > 0 and (r["high"]-max(r["open"],r["close"]))/rng >= bot.risky_wick_ratio: bad += 1
        if bad >= bot.risky_wick_count: reasons.append("WICK")
    else: reasons.append("OHLCV_FAIL")

    res = (len(reasons)>0, ",".join(reasons) if reasons else "OK")
    with bot.lock: bot.risky_cache[ticker] = (now, res[0], res[1])
    return res

def exit_confirm_hit(ticker, key):
    now = time.time()
    with bot.lock:
        d = bot.exit_confirm.get(ticker, {"ts": 0})
        if now - d["ts"] > bot.exit_confirm_ttl: d = {"sl":0, "drop":0, "tpdrop":0, "ts":now}
        d["ts"] = now
        d[key] = d.get(key, 0) + 1
        bot.exit_confirm[ticker] = d
        threshold = {"sl": bot.exit_confirm_need_sl, "drop": bot.exit_confirm_need_drop, "tpdrop": bot.exit_confirm_need_tpdrop}.get(key, 2)
        return d[key] >= threshold

def exit_confirm_reset(ticker, key):
    with bot.lock:
        if ticker in bot.exit_confirm:
            bot.exit_confirm[ticker][key] = 0
            bot.exit_confirm[ticker]["ts"] = time.time()

def exit_confirm_clear(ticker):
    with bot.lock: bot.exit_confirm.pop(ticker, None)

def wait_order_fill_or_cancel(uuid: str, ticker: str, side: str, max_wait=5):
    end = time.time() + max_wait
    while time.time() < end:
        try:
            od = bot.upbit.get_order(uuid)
            if od and od.get("state") in ("done", "cancel"): return od
        except: pass
        safe_sleep(0.5)

    try:
        bot.log(f"⏰ 주문 미체결로 인한 취소 시도: {ticker} ({side})", "SYSTEM")
        bot.upbit.cancel_order(uuid)
        safe_sleep(1)
        return bot.upbit.get_order(uuid)
    except Exception as e:
        bot.log(f"주문 취소 실패({ticker}): {e}", "ERROR")
    return None

def sync_positions_from_exchange():
    if bot.mode != "real": return
    try:
        bals = bot.upbit.get_balances()
        if not bals: return
        holdings = {}
        for b in bals:
            cur = b.get("currency")
            if cur == "KRW": continue
            bal = float(b.get("balance") or 0)
            if bal <= 0: continue
            ticker = f"KRW-{cur}"

            with bot.lock: prev = bot.real_bought_coins.get(ticker, {})
            avg = float(b.get("avg_buy_price") or 0)
            if avg <= 0: avg = float(prev.get("buy_price") or get_current_price_safe(ticker) or 0)

            holdings[ticker] = {
                "ticker": ticker, "buy_price": avg,
                "buy_time": prev.get("buy_time", time.time()),
                "profit_rate": prev.get("profit_rate", 0),
                "high_price": max(float(prev.get("high_price", 0)), avg),
                "amount": bal
            }
        with bot.lock: bot.real_bought_coins = holdings
        bot.save_state()
    except Exception as e: bot.log(f"동기화 오류: {e}", "ERROR")

def monitor_protect_tickers():
    if bot.mode != "real": return
    for t in bot.protect_tickers:
        if t in bot.real_bought_coins:
            info = bot.real_bought_coins[t]
            buy = float(info.get("buy_price", 0))
            if buy > 0:
                cur = get_current_price_safe(t)
                if cur:
                    p = (cur-buy)/buy*100
                    bk = int(p//5)
                    last = bot.protect_last_alert.get(t, (0, -999))
                    if time.time()-last[0] > 600 or bk != last[1]:
                        bot.protect_last_alert[t] = (time.time(), bk)
                        bot.log(f"🧾 보호코인 {t}: {p:.2f}%", "REPORT")

def analyze_market_condition():
    try:
        now = time.time()
        with bot.lock:
            if not bot.auto_tune or now - bot.last_regime_ts < bot.regime_interval_sec: return
            bot.last_regime_ts = now
        df = get_ohlcv_safe("KRW-BTC", interval="minute15", count=60)
        if df is None: return
        close = float(df["close"].iloc[-1])
        ma20 = float(df["close"].rolling(20).mean().iloc[-1])
        diff = (close - ma20) / ma20

        with bot.lock:
            st = bot.market_status
            nxt = st
            if st == "BULL" and diff < bot.bull_exit: nxt = "SIDEWAYS"
            elif st == "BEAR" and diff > bot.bear_exit: nxt = "SIDEWAYS"
            else:
                if diff >= bot.bull_enter: nxt = "BULL"
                elif diff <= bot.bear_enter: nxt = "BEAR"

            if nxt != st:
                bot.market_status = nxt
                if nxt == "BULL":
                    bot.target_profit, bot.stop_loss, bot.rsi_threshold = 2.0, -3.0, 60.0
                    bot.max_hold_minutes, bot.hold_min_profit = 90, 0.6
                elif nxt == "BEAR":
                    bot.target_profit, bot.stop_loss, bot.rsi_threshold = 1.0, -2.0, 30.0
                    bot.max_hold_minutes, bot.hold_min_profit = 45, 0.3
                else:
                    bot.target_profit, bot.stop_loss, bot.rsi_threshold = 1.5, -3.0, 50.0
                    bot.max_hold_minutes, bot.hold_min_profit = 60, 0.9
                bot.log(f"시장상태 변경: {nxt} (이격도 {diff*100:.2f}%)", "SYSTEM")
    except: pass

def get_indicators(ticker):
    try:
        df = get_ohlcv_safe(ticker, count=60)
        if df is None: return None, None, None, None, None, None

        close = df['close']
        cur = float(close.iloc[-1])

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain/loss
        rsi = float((100 - (100/(1+rs))).iloc[-1])

        # MA
        ma20 = float(close.rolling(20).mean().iloc[-1])
        ma5  = float(close.rolling(5).mean().iloc[-1]) # 단기

        # PUMP (거래량 폭증 + 양봉 + 윗꼬리 체크)
        vol_avg = float(df['volume'].iloc[-20:-1].mean())
        curr_vol = float(df['volume'].iloc[-1])

        open_p = float(df['open'].iloc[-1])
        high_p = float(df['high'].iloc[-1])

        is_pump = False
        # 거래량이 5배 이상이고, 양봉이며
        if vol_avg > 0 and curr_vol > vol_avg * 5 and cur > open_p:
            # 윗꼬리가 몸통의 2배를 넘지 않아야 함 (설거지 방지)
            body = cur - open_p
            wick = high_p - cur
            if body > 0 and wick < body * 2:
                is_pump = True

        return round(rsi,1), ma20, cur, is_pump, ma5, open_p
    except: return None, None, None, None, None, None

def execute_buy(ticker, price, rsi, reason):
    now = time.time()
    if ticker in bot.black_list: return

    with bot.lock:
        if now < bot.buy_fail_cooldown.get(ticker, 0): return
        if now < bot.sell_cooldown.get(ticker, 0): return

        cur_coins = bot.real_bought_coins if bot.mode == "real" else bot.paper_bought_coins
        if ticker in cur_coins: return

        if ticker not in bot.protect_tickers:
             if len(cur_coins) >= bot.max_trade_coin_count: return

    if bot.mode == "real":
        try:
            krw = float(bot.upbit.get_balance("KRW") or 0)
            if krw < float(config.TRADE_AMOUNT) * 1.01:
                with bot.lock: bot.buy_fail_cooldown[ticker] = now + 60
                return

            res = bot.upbit.buy_market_order(ticker, config.TRADE_AMOUNT)
            if res and 'uuid' in res:
                bot.log(f"매수 시도: {ticker} ({reason})", "BUY")
                od = wait_order_fill_or_cancel(res['uuid'], ticker, "BUY")
                
                # [수정] 체결 여부 판단 로직 개선
                is_done = False
                if od:
                    if od.get("state") == "done": is_done = True
                    elif float(od.get("executed_volume", 0) or 0) > 0: is_done = True
                    elif len(od.get("trades", [])) > 0: is_done = True

                if is_done:
                    real_price = float(od.get("price", price))
                    if od.get("trades"):
                        total_vol = sum([float(t["volume"]) for t in od["trades"]])
                        total_price = sum([float(t["price"])*float(t["volume"]) for t in od["trades"]])
                        if total_vol > 0: real_price = total_price / total_vol

                    with bot.lock:
                        bot.real_bought_coins[ticker] = {
                            "ticker": ticker, "buy_price": real_price, "buy_time": now,
                            "profit_rate": 0, "high_price": real_price, "amount": 0
                        }
                        if ticker in bot.protect_sell_info: del bot.protect_sell_info[ticker]

                    sync_positions_from_exchange()
                else:
                    bot.log(f"매수 미체결 취소됨: {ticker}", "SYSTEM")
            else:
                with bot.lock: bot.buy_fail_cooldown[ticker] = now + 60
        except Exception as e:
            bot.log(f"매수 에러({ticker}): {e}", "ERROR")
            with bot.lock: bot.buy_fail_cooldown[ticker] = now + 60
    else:
        with bot.lock:
            if bot.paper_balance >= config.TRADE_AMOUNT:
                bot.paper_balance -= config.TRADE_AMOUNT
                bot.paper_bought_coins[ticker] = {
                    "ticker": ticker, "buy_price": float(price), "buy_time": now,
                    "profit_rate": 0, "high_price": float(price), "amount": float(config.TRADE_AMOUNT)
                }
                if ticker in bot.protect_sell_info: del bot.protect_sell_info[ticker]
                bot.log(f"가상 매수: {ticker}", "BUY")
                bot.save_state()

def execute_sell(ticker, price, profit, reason):
    is_protect = ticker in bot.protect_tickers

    with bot.lock:
        bot.sell_cooldown[ticker] = time.time() + bot.sell_cooldown_sec

    if bot.mode == "real":
        try:
            coin = ticker.split("-")[1]
            bal = bot.upbit.get_balance(coin)
            if bal and float(bal) > 0:
                res = bot.upbit.sell_market_order(ticker, bal)
                if res and 'uuid' in res:
                    bot.log(f"매도 시도: {ticker} ({reason})", "SELL")
                    exit_confirm_clear(ticker)
                    od = wait_order_fill_or_cancel(res['uuid'], ticker, "SELL")

                    # [수정] 체결 여부 판단 로직 개선
                    is_done = False
                    if od:
                        if od.get("state") == "done": is_done = True
                        elif float(od.get("executed_volume", 0) or 0) > 0: is_done = True
                        elif len(od.get("trades", [])) > 0: is_done = True

                    if is_done:
                        if is_protect:
                            real_fill = float(od.get("price", price)) if od else price
                            with bot.lock:
                                 bot.protect_sell_info[ticker] = {
                                     "price": real_fill, "time": time.time(), "amount": float(bal)
                                 }
                                 bot.save_state()

                    sync_positions_from_exchange()
                else: bot.log(f"매도 실패: {res}", "ERROR")
            else:
                sync_positions_from_exchange()
        except Exception as e: bot.log(f"매도 에러({ticker}): {e}", "ERROR")
    else:
        with bot.lock:
            if ticker in bot.paper_bought_coins:
                info = bot.paper_bought_coins[ticker]
                amt = float(info.get("amount", config.TRADE_AMOUNT))
                ret = amt * (1 + profit/100)
                bot.paper_balance += ret

                if is_protect:
                    bot.protect_sell_info[ticker] = {
                        "price": float(price), "time": time.time(), "amount": amt
                    }

                del bot.paper_bought_coins[ticker]
                exit_confirm_clear(ticker)
                bot.log(f"가상 매도: {ticker} ({profit:.2f}%)", "SELL")
                bot.save_state()

def sell_all_position(ticker):
    ticker = ticker.upper()
    if ticker in bot.protect_tickers: return {"status":"blocked"}

    if bot.mode == "real":
        try:
            coin = ticker.split("-")[1]
            bal = bot.upbit.get_balance(coin)
            if bal and float(bal) > 0:
                res = bot.upbit.sell_market_order(ticker, bal)
                if res and "uuid" in res:
                    bot.log(f"강제 매도: {ticker}", "SELL")
                    wait_order_fill_or_cancel(res['uuid'], ticker, "SELL")
                    sync_positions_from_exchange()
                    return {"status":"ok"}
        except: pass
        return {"status":"fail"}
    else:
        with bot.lock:
            if ticker in bot.paper_bought_coins:
                info = bot.paper_bought_coins[ticker]
                px = get_current_price_safe(ticker) or info['buy_price']
                profit = (px - info['buy_price'])/info['buy_price']*100
                ret = float(info.get("amount", config.TRADE_AMOUNT)) * (1 + profit/100)
                bot.paper_balance += ret
                del bot.paper_bought_coins[ticker]
                bot.log(f"가상 강제 매도: {ticker}", "SELL")
                bot.save_state()
                return {"status":"ok"}
    return {"status":"fail"}

def panic_sell_all():
    bot.is_running = False
    bot.log("🚨 비상 탈출(PANIC SELL) 발동! 봇을 정지하고 전량 매도를 시도합니다.", "RISK")

    if bot.mode == "real":
        try:
            bals = bot.upbit.get_balances()
            for b in bals:
                cur = b.get("currency")
                if cur == "KRW": continue
                ticker = f"KRW-{cur}"
                if ticker in bot.protect_tickers: continue

                vol = float(b.get("balance") or 0)
                if vol > 0:
                    try:
                        res = bot.upbit.sell_market_order(ticker, vol)
                        bot.log(f"🚨 비상 매도 주문: {ticker}", "RISK")
                        if res and "uuid" in res: wait_order_fill_or_cancel(res["uuid"], ticker, "SELL")
                        safe_sleep(0.2)
                    except: pass
            sync_positions_from_exchange()
        except Exception as e: bot.log(f"비상 탈출 중 오류: {e}", "ERROR")
    else:
        with bot.lock:
            tickers = list(bot.paper_bought_coins.keys())
        for t in tickers: sell_all_position(t)
        bot.save_state()

@app.post("/api/start")
def api_start():
    bot.is_running = True
    bot.log("봇 시작", "SYSTEM")
    return {"status":"ok"}

@app.post("/api/stop")
def api_stop():
    bot.is_running = False
    bot.log("봇 정지", "SYSTEM")
    return {"status":"ok"}

@app.post("/api/mode")
def api_mode(p: ModeChange):
    bot.mode = p.mode
    bot.log(f"모드 변경: {p.mode}", "SYSTEM")
    return {"status":"ok"}

@app.post("/api/sell_one")
def api_sell_one(p: SellOne):
    return sell_all_position(p.ticker)

@app.post("/api/panic_sell")
def api_panic():
    threading.Thread(target=panic_sell_all).start()
    return {"status":"ok"}

@app.post("/api/config/system")
def api_update_system(p: SystemConfig):
    with bot.lock:
        bot.black_list = p.black_list
        bot.stop_tickers = p.stop_tickers
        bot.protect_tickers = p.protect_tickers
        bot.max_hold_minutes = p.max_hold_minutes
        bot.save_system_config()
    bot.log("시스템 설정 업데이트 완료", "SYSTEM")
    return {"status": "ok"}

@app.get("/api/status")
def api_status():
    with bot.lock:
        is_real = bot.mode == "real"
        coins = bot.real_bought_coins if is_real else bot.paper_bought_coins

        pos_list = []
        now_ts = time.time()

        for t, info in coins.items():
            cur = get_current_price_safe(t) or info.get("buy_price", 0)
            buy = float(info.get("buy_price", 0) or 0)
            if buy <= 0 or not cur: continue

            profit_rate = (cur - buy) / buy * 100
            amt = float(info.get("amount", 0) or 0)
            buy_time = float(info.get("buy_time", now_ts) or now_ts)
            held_min = (now_ts - buy_time) / 60
            high = float(info.get("high_price", buy) or buy)
            dd_from_high = (cur - high) / high * 100
            cd_left = max(0, int((bot.sell_cooldown.get(t, 0) or 0) - now_ts))

            pos_list.append({
                "ticker": t, "buy_price": buy, "cur_price": float(cur), "profit_rate": float(profit_rate),
                "amount": float(amt), "held_min": float(held_min), "high_price": float(high),
                "dd_from_high": float(dd_from_high), "cooldown_left_sec": cd_left,
                "is_protect": (t in bot.protect_tickers),
            })

        start_bal = bot.day_start_balance_real if is_real else bot.day_start_balance_paper

        return {
            "isRunning": bot.is_running, "mode": bot.mode,
            "balance": bot.real_balance if is_real else bot.paper_balance,
            "start_balance": start_bal, "positions": pos_list,
            "history": list(bot.balance_history), "logs": list(bot.logs),
            "config": {
                "market": bot.market_status, "targetProfit": bot.target_profit, "stopLoss": bot.stop_loss,
                "rsiThreshold": bot.rsi_threshold, "autoTune": bot.auto_tune,
                "protectTickers": bot.protect_tickers, "blackList": bot.black_list,
                "stopTickers": bot.stop_tickers, "maxHoldMinutes": bot.max_hold_minutes
            }
        }

@app.get("/api/market")
def api_market():
    res = []
    with bot.lock: targets = bot.target_tickers[:8]
    for t in targets:
        rsi, ma, px, pump, ma5, open_p = get_indicators(t)
        if rsi:
            risky, why = is_risky_market(t)
            trend = "급등" if pump else ("상승세" if px>ma else "하락세")
            res.append({"ticker":t, "rsi":rsi, "trend":trend, "risky":risky, "why":why})
    return res

@app.get("/api/trending")
def api_trending():
    """주요 암호화폐 추세 데이터 반환"""
    return get_major_crypto_trends()

@app.get("/")
def index():
    try:
        with open("stock_ui_korean.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading UI: {e}</h1>")

def trading_loop():
    bot.log("시스템 가동", "SYSTEM")
    step = 0
    while True:
        if bot.is_running:
            try:
                if step % 10 == 0: analyze_market_condition()
                if step % 20 == 0: bot.update_balance()
                if step % 30 == 0: bot.check_daily_risk()
                if step % 60 == 0: bot.send_periodic_report()
                if bot.mode == "real" and step % 20 == 0: sync_positions_from_exchange()
                if bot.mode == "real" and step % 60 == 0: monitor_protect_tickers()

                if step % 300 == 0:
                    top = fetch_top_markets_by_trade_price(bot.watch_top_n)
                    if top:
                        with bot.lock: bot.target_tickers = [t for t in top if t not in bot.black_list and t not in bot.stop_tickers]
                        bot.log(f"감시 종목 갱신({len(bot.target_tickers)}개): {', '.join(bot.target_tickers[:5])}...", "SYSTEM")

                with bot.lock: reentry_candidates = list(bot.protect_sell_info.keys())
                for t in reentry_candidates:
                    cur_coins = bot.real_bought_coins if bot.mode == "real" else bot.paper_bought_coins
                    if t in cur_coins:
                        with bot.lock: del bot.protect_sell_info[t]
                        continue

                    rsi, ma, px, pump, ma5, open_p = get_indicators(t)
                    if not px or not ma: continue

                    last_info = bot.protect_sell_info.get(t)
                    if not last_info: continue
                    sell_price = last_info["price"]

                    is_bull_trend = (px > ma)
                    is_recovered = (px >= sell_price * 1.01)

                    if is_bull_trend or is_recovered:
                         bot.log(f"🔄 보호코인 재진입 시도: {t}", "BUY")
                         execute_buy(t, px, rsi, "보호코인/재진입")
                         safe_sleep(1)

                with bot.lock:
                    coins = bot.real_bought_coins if bot.mode == "real" else bot.paper_bought_coins
                    targets = list(bot.target_tickers)
                    slots = bot.max_trade_coin_count - sum(1 for c in coins if c not in bot.protect_tickers)

                if slots > 0:
                    for t in targets:
                        if t in coins or t in bot.protect_tickers: continue

                        rsi, ma, px, pump, ma5, open_p = get_indicators(t)
                        if not rsi: continue

                        risky, why = is_risky_market(t)
                        if risky:
                            if _should_log_risky(t): bot.log(f"스킵(위험): {t} {why}", "INFO")
                            continue

                        # [수정] 매수 조건 대폭 강화 (손실 방지 핵심 로직)
                        cond_pump = (pump and ma5 > ma and px > ma)
                        cond_rsi = (rsi <= bot.rsi_threshold and ma5 > ma and px > ma and px > open_p)

                        if cond_pump:
                             execute_buy(t, px, rsi, "급등/정배열")
                             safe_sleep(0.5)
                             slots -= 1
                             if slots <= 0: break
                        elif cond_rsi:
                             execute_buy(t, px, rsi, "RSI/저점")
                             safe_sleep(0.5)
                             slots -= 1
                             if slots <= 0: break

                cur_coins = list(coins.items())
                now_ts = time.time()
                for t, info in cur_coins:
                    is_protect = t in bot.protect_tickers

                    px = get_current_price_safe(t)
                    if not px: continue

                    buy = info['buy_price']
                    if buy <= 0: continue

                    high = max(info.get('high_price', buy), px)
                    if bot.mode == "real": bot.real_bought_coins[t]['high_price'] = high
                    else: bot.paper_bought_coins[t]['high_price'] = high

                    profit = (px - buy)/buy * 100
                    drop = (px - high)/high * 100
                    held = (now_ts - info['buy_time'])/60

                    if is_protect:
                        if drop <= bot.protect_stop_loss:
                             execute_sell(t, px, profit, "보호코인 급락")
                        continue

                    if held >= bot.max_hold_minutes and profit < bot.hold_min_profit:
                        execute_sell(t, px, profit, f"시간경과({held:.0f}분)")
                        continue

                    if profit >= bot.target_profit:
                        if drop <= bot.trailing_after_tp_drop:
                            if exit_confirm_hit(t, "tpdrop"): execute_sell(t, px, profit, "익절(트레일링)")
                        else: exit_confirm_reset(t, "tpdrop")
                        continue

                    if profit <= bot.stop_loss:
                        if exit_confirm_hit(t, "sl"): execute_sell(t, px, profit, "손절")
                        continue
                    else: exit_confirm_reset(t, "sl")

                    if drop <= bot.trailing_general_drop:
                        if exit_confirm_hit(t, "drop"): execute_sell(t, px, profit, "급락감지")
                        continue
                    else: exit_confirm_reset(t, "drop")

            except Exception as e:
                bot.log(f"루프 오류: {e}", "ERROR")
                safe_sleep(5)

            step += 1
            safe_sleep(1)
        else:
            safe_sleep(1)

if __name__ == "__main__":
    t = threading.Thread(target=trading_loop, daemon=True)
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=8001)
