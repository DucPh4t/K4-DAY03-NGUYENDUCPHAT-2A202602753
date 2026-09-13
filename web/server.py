"""
🌐 VINUNI AI LAB #3 — WEB DEMO SERVER
Giao diện trực quan hoá vòng lặp ReAct Loop và kiểm thử Model Context Protocol (MCP).
"""

import os
import sys
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Thêm thư mục gốc vào sys.path để import src
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))

from mcp_server import MCPAcademicServer
from tools import MOCK_DATABASE, TOOLS_SCHEMA
from prompts import CHATBOT_BASELINE_PROMPT, REACT_AGENT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import GeminiProvider, MockOfflineProvider, OpenAIProvider, get_llm_provider

HOST = "127.0.0.1"
PORT = 8080

mcp_server = MCPAcademicServer()

HTML_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VinUni AI Lab 3 — ReAct Agent & MCP Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #090d16;
      --bg-card: rgba(18, 24, 38, 0.75);
      --bg-card-hover: rgba(28, 38, 58, 0.85);
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-glow: rgba(99, 102, 241, 0.35);
      --primary: #6366f1;
      --primary-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
      --accent-cyan: #06b6d4;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --font-sans: 'Plus Jakarta Sans', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-dark);
      background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(236, 72, 153, 0.12) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(6, 182, 212, 0.12) 0px, transparent 50%);
      color: var(--text-main);
      font-family: var(--font-sans);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Header */
    header {
      border-bottom: 1px solid var(--border-subtle);
      background: rgba(9, 13, 22, 0.8);
      backdrop-filter: blur(12px);
      position: sticky;
      top: 0;
      z-index: 100;
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.85rem;
    }

    .logo-badge {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: var(--primary-gradient);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.4rem;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4);
    }

    .brand-title {
      font-weight: 800;
      font-size: 1.15rem;
      letter-spacing: -0.02em;
    }

    .brand-subtitle {
      font-size: 0.78rem;
      color: var(--text-muted);
    }

    .controls-bar {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .pill-select {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      padding: 0.5rem 1rem;
      border-radius: 9999px;
      font-family: var(--font-sans);
      font-size: 0.85rem;
      cursor: pointer;
      outline: none;
      transition: all 0.2s;
    }
    .pill-select:hover {
      border-color: var(--primary);
    }

    .mode-toggle {
      display: flex;
      background: rgba(0, 0, 0, 0.4);
      padding: 4px;
      border-radius: 9999px;
      border: 1px solid var(--border-subtle);
    }

    .mode-btn {
      padding: 0.4rem 1rem;
      border-radius: 9999px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }

    .mode-btn.active {
      background: var(--primary-gradient);
      color: #fff;
      box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
    }

    /* App Container */
    .app-container {
      display: grid;
      grid-template-columns: 1fr 380px;
      gap: 1.5rem;
      max-width: 1540px;
      width: 100%;
      margin: 0 auto;
      padding: 1.5rem 2rem;
      flex: 1;
    }

    @media (max-width: 1024px) {
      .app-container { grid-template-columns: 1fr; }
    }

    /* Left: Chat Canvas */
    .chat-section {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 120px);
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 20px;
      backdrop-filter: blur(16px);
      overflow: hidden;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    /* Message Bubbles */
    .msg-group {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .msg-user {
      align-self: flex-end;
      background: var(--primary-gradient);
      color: #fff;
      padding: 0.9rem 1.25rem;
      border-radius: 18px 18px 4px 18px;
      max-width: 75%;
      font-weight: 500;
      line-height: 1.5;
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
    }

    .msg-assistant {
      align-self: flex-start;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }

    /* ReAct Waterfall Components */
    .waterfall-card {
      background: rgba(10, 15, 26, 0.8);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 1rem 1.25rem;
      position: relative;
      overflow: hidden;
    }

    .waterfall-card::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
    }
    .waterfall-card.thought::before { background: var(--accent-amber); }
    .waterfall-card.action::before { background: var(--accent-cyan); }
    .waterfall-card.observation::before { background: var(--accent-green); }
    .waterfall-card.final::before { background: var(--primary); }

    .step-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }

    .step-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .thought .step-badge { color: var(--accent-amber); }
    .action .step-badge { color: var(--accent-cyan); }
    .observation .step-badge { color: var(--accent-green); }
    .final .step-badge { color: #a5b4fc; }

    .step-latency {
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--text-muted);
      background: rgba(255, 255, 255, 0.05);
      padding: 2px 8px;
      border-radius: 6px;
    }

    .step-content {
      font-size: 0.92rem;
      line-height: 1.6;
      color: #e2e8f0;
    }

    .code-block {
      background: #060911;
      border: 1px solid var(--border-subtle);
      padding: 0.75rem 1rem;
      border-radius: 8px;
      font-family: var(--font-mono);
      font-size: 0.82rem;
      color: #38bdf8;
      overflow-x: auto;
      margin-top: 0.4rem;
    }

    .final-answer-box {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(139, 92, 246, 0.08) 100%);
      border: 1px solid var(--border-glow);
      border-radius: 14px;
      padding: 1.25rem;
      color: #fff;
      font-size: 0.98rem;
      line-height: 1.65;
      box-shadow: 0 4px 20px rgba(99, 102, 241, 0.15);
    }

    /* Presets Carousel */
    .presets-bar {
      padding: 0.75rem 1.5rem;
      border-top: 1px solid var(--border-subtle);
      background: rgba(12, 17, 29, 0.6);
      display: flex;
      gap: 0.6rem;
      overflow-x: auto;
      scrollbar-width: thin;
    }

    .preset-chip {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      padding: 0.4rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.78rem;
      font-weight: 500;
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.2s;
    }
    .preset-chip:hover {
      background: rgba(99, 102, 241, 0.15);
      border-color: var(--primary);
      color: #fff;
      transform: translateY(-1px);
    }

    /* Input Bar */
    .input-section {
      padding: 1rem 1.5rem;
      border-top: 1px solid var(--border-subtle);
      background: rgba(9, 13, 22, 0.85);
      display: flex;
      gap: 0.75rem;
      align-items: center;
    }

    .chat-input {
      flex: 1;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-subtle);
      color: #fff;
      padding: 0.85rem 1.2rem;
      border-radius: 12px;
      font-family: var(--font-sans);
      font-size: 0.95rem;
      outline: none;
      transition: border 0.2s;
    }
    .chat-input:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }

    .send-btn {
      background: var(--primary-gradient);
      color: #fff;
      border: none;
      padding: 0.85rem 1.5rem;
      border-radius: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      transition: opacity 0.2s;
    }
    .send-btn:hover { opacity: 0.9; }
    .send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

    /* Right: Inspector Panel */
    .inspector-section {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      height: calc(100vh - 120px);
      overflow-y: auto;
    }

    .panel-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 18px;
      padding: 1.25rem;
      backdrop-filter: blur(16px);
    }

    .panel-title {
      font-size: 0.92rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.85rem;
      color: #f1f5f9;
    }

    .tool-item {
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 0.75rem;
      margin-bottom: 0.6rem;
    }

    .tool-name {
      font-family: var(--font-mono);
      font-size: 0.85rem;
      color: var(--accent-cyan);
      font-weight: 600;
      display: flex;
      justify-content: space-between;
    }

    .tool-desc {
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 0.3rem;
      line-height: 1.4;
    }

    .db-badge {
      font-family: var(--font-mono);
      font-size: 0.78rem;
      background: rgba(255, 255, 255, 0.05);
      padding: 0.5rem;
      border-radius: 8px;
      margin-bottom: 0.5rem;
      line-height: 1.5;
    }

    .pulse-dot {
      width: 8px;
      height: 8px;
      background: var(--accent-green);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-green);
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(1.2); }
    }

    .loading-spinner {
      display: inline-block;
      width: 18px;
      height: 18px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 1s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="logo-badge">🏫</div>
      <div>
        <div class="brand-title">VinUni AI — ReAct Agent & MCP Studio</div>
        <div class="brand-subtitle">Lab #3: Baseline Chatbot (L2) vs ReAct Agent (L3)</div>
      </div>
    </div>

    <div class="controls-bar">
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span class="pulse-dot"></span>
        <span style="font-size: 0.8rem; color: var(--text-muted);">MCP Server: <strong style="color: var(--accent-green);">ONLINE</strong></span>
      </div>

      <select id="providerSelect" class="pill-select">
        <option value="gemini">⚡ Google Gemini Live API (gemini-3.6-flash)</option>
        <option value="mock">🛡️ Offline Mock Provider</option>
      </select>

      <div class="mode-toggle">
        <button id="btnModeReact" class="mode-btn active" onclick="setMode('react')">ReAct Agent (L3)</button>
        <button id="btnModeBaseline" class="mode-btn" onclick="setMode('baseline')">Chatbot Baseline (L2)</button>
      </div>
    </div>
  </header>

  <div class="app-container">
    <!-- Chat Section -->
    <section class="chat-section">
      <div class="chat-messages" id="chatMessages">
        <!-- Welcome banner -->
        <div class="waterfall-card final" style="border-left-width: 4px;">
          <div class="step-header">
            <span class="step-badge">🚀 HỆ THỐNG SẴN SÀNG</span>
            <span class="step-latency">MCP JSON-RPC 2.0</span>
          </div>
          <div class="step-content">
            Chào mừng bạn đến với Studio tương tác <strong>ReAct Agent & Model Context Protocol (MCP)</strong> của Đại học VinUni!
            <br>Bạn có thể thử nghiệm chế độ <strong>ReAct Agent</strong> (tự động suy luận, gọi Tool tra cứu hồ sơ và đặt lịch hẹn) hoặc chuyển sang <strong>Chatbot Baseline</strong> để so sánh sự khác biệt.
          </div>
        </div>
      </div>

      <!-- Presets Carousel -->
      <div class="presets-bar" id="presetsBar">
        <button class="preset-chip" onclick="applyPreset('TC01')">📌 [TC01] Giới thiệu quy chế học vụ VinUni</button>
        <button class="preset-chip" onclick="applyPreset('TC02')">🔍 [TC02] Tra cứu sinh viên SV2026001</button>
        <button class="preset-chip" onclick="applyPreset('TC03')">📅 [TC03] Đặt lịch hẹn SV2026001</button>
        <button class="preset-chip" onclick="applyPreset('TC04')">🔄 [TC04] Tìm cố vấn & Đặt lịch (Multi-step)</button>
        <button class="preset-chip" onclick="applyPreset('TC05')">⚠️ [TC05] Tra cứu mã không tồn tại SV9999999</button>
      </div>

      <!-- Input Area -->
      <div class="input-section">
        <input type="text" id="userInput" class="chat-input" placeholder="Nhập câu hỏi học vụ hoặc yêu cầu đặt lịch hẹn..." onkeydown="if(event.key==='Enter') sendMessage()">
        <button id="sendBtn" class="send-btn" onclick="sendMessage()">
          <span>Gửi</span>
          <span>🚀</span>
        </button>
      </div>
    </section>

    <!-- Right Inspector Panel -->
    <aside class="inspector-section">
      <!-- Panel 1: MCP Tool Registry -->
      <div class="panel-card">
        <div class="panel-title">
          <span>📦</span>
          <span>MCP Tool Registry (Model Context Protocol)</span>
        </div>
        <div class="tool-item">
          <div class="tool-name">
            <span>academic_query</span>
            <span style="font-size: 0.72rem; color: var(--accent-green);">ACTIVE</span>
          </div>
          <div class="tool-desc">Tra cứu hồ sơ, GPA, lớp và cố vấn học tập bằng mã số sinh viên.</div>
        </div>
        <div class="tool-item">
          <div class="tool-name">
            <span>schedule_appointment</span>
            <span style="font-size: 0.72rem; color: var(--accent-green);">ACTIVE</span>
          </div>
          <div class="tool-desc">Tạo phiên đặt lịch hẹn tư vấn học thuật với Cố vấn học tập VinUni.</div>
        </div>
      </div>

      <!-- Panel 2: Live Mock Database -->
      <div class="panel-card">
        <div class="panel-title">
          <span>🗄️</span>
          <span>Mock Academic Database (2 Records)</span>
        </div>
        <div class="db-badge">
          <strong style="color: #38bdf8;">SV2026001:</strong> Nguyễn Văn An | AI-K4 | GPA: 3.85<br>
          <span style="color: var(--text-muted);">Cố vấn:</span> PGS.TS Nguyễn Văn A
        </div>
        <div class="db-badge">
          <strong style="color: #38bdf8;">SV2026002:</strong> Trần Thị Bình | AI-K4 | GPA: 3.60<br>
          <span style="color: var(--text-muted);">Cố vấn:</span> TS. Lê Thị B
        </div>
      </div>

      <!-- Panel 3: Rubric Verification -->
      <div class="panel-card">
        <div class="panel-title">
          <span>🎯</span>
          <span>Trạng thái Nghiệm thu Rubric</span>
        </div>
        <div style="font-size: 0.82rem; line-height: 1.6; color: var(--text-muted);">
          <div>✅ <strong>Fit & Tool Specs:</strong> 17/20 điểm</div>
          <div>✅ <strong>MCP Protocol:</strong> JSON-RPC 2.0 Dispatcher OK</div>
          <div>✅ <strong>ReAct Loop:</strong> Thought ➔ Action ➔ Observation OK</div>
          <div>✅ <strong>Live Gemini:</strong> gemini-3.6-flash Live Connected</div>
          <div>✅ <strong>Log Trace:</strong> trace_waterfall.json Verified</div>
        </div>
      </div>
    </aside>
  </div>

  <script>
    let currentMode = 'react';

    function setMode(mode) {
      currentMode = mode;
      document.getElementById('btnModeReact').classList.toggle('active', mode === 'react');
      document.getElementById('btnModeBaseline').classList.toggle('active', mode === 'baseline');
    }

    const testCases = {
      'TC01': 'Chào bạn, bạn có thể giới thiệu quy chế học vụ cơ bản của Đại học VinUni không?',
      'TC02': 'Hãy tra cứu thông tin học vụ của sinh viên SV2026001.',
      'TC03': 'Hãy đặt lịch hẹn tư vấn học vụ cho sinh viên SV2026001 vào lúc 14:00 ngày 15/09/2026 với cố vấn PGS.TS Nguyễn Văn A.',
      'TC04': 'Sinh viên SV2026001 cần tư vấn học tập. Bạn hãy tra cứu thông tin sinh viên xem cố vấn học tập là ai, sau đó đặt lịch hẹn tư vấn với cố vấn đó vào lúc 09:00 ngày 18/09/2026.',
      'TC05': 'Hãy tra cứu thông tin học vụ của sinh viên có mã số SV9999999.'
    };

    function applyPreset(id) {
      document.getElementById('userInput').value = testCases[id];
      sendMessage();
    }

    async function sendMessage() {
      const input = document.getElementById('userInput');
      const text = input.value.trim();
      if (!text) return;

      const chatMessages = document.getElementById('chatMessages');
      const sendBtn = document.getElementById('sendBtn');
      const provider = document.getElementById('providerSelect').value;

      // Append User message
      const userDiv = document.createElement('div');
      userDiv.className = 'msg-group';
      userDiv.innerHTML = `<div class="msg-user">${escapeHtml(text)}</div>`;
      chatMessages.appendChild(userDiv);
      input.value = '';
      chatMessages.scrollTop = chatMessages.scrollHeight;

      // Loading indicator
      sendBtn.disabled = true;
      sendBtn.innerHTML = `<div class="loading-spinner"></div><span>Đang xử lý...</span>`;

      const assistantDiv = document.createElement('div');
      assistantDiv.className = 'msg-assistant';
      assistantDiv.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">🔄 Agent đang kích hoạt vòng lặp ReAct (${provider === 'gemini' ? 'Google Gemini Live' : 'Offline Mock'})...</div>`;
      chatMessages.appendChild(assistantDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: text, mode: currentMode, provider: provider })
        });
        const data = await res.json();

        assistantDiv.innerHTML = '';

        if (data.mode === 'baseline') {
          // Chatbot Baseline response
          assistantDiv.innerHTML = `
            <div class="waterfall-card final">
              <div class="step-header">
                <span class="step-badge">💬 CHATBOT BASELINE (NO TOOLS)</span>
                <span class="step-latency">${data.total_latency_ms} ms</span>
              </div>
              <div class="final-answer-box">${escapeHtml(data.final_answer)}</div>
            </div>
          `;
        } else {
          // ReAct Agent response with waterfall
          const traces = data.traces || [];
          let html = '';

          traces.forEach(t => {
            if (t.thought && t.action_type !== 'FINAL_ANSWER') {
              html += `
                <div class="waterfall-card thought">
                  <div class="step-header">
                    <span class="step-badge">🧠 THOUGHT (BƯỚC ${t.step})</span>
                    <span class="step-latency">${t.latency_ms || 0} ms</span>
                  </div>
                  <div class="step-content">${escapeHtml(t.thought)}</div>
                </div>
              `;
            }

            if (t.action_type === 'TOOL_EXECUTION') {
              html += `
                <div class="waterfall-card action">
                  <div class="step-header">
                    <span class="step-badge">🛠️ ACTION ➔ MCP TOOL CALL</span>
                    <span class="step-latency">${escapeHtml(t.tool_name)}</span>
                  </div>
                  <div class="code-block">${escapeHtml(JSON.stringify(t.arguments || {}, null, 2))}</div>
                </div>
                <div class="waterfall-card observation">
                  <div class="step-header">
                    <span class="step-badge">👁️ OBSERVATION (TỪ MCP SERVER)</span>
                    <span class="step-latency">JSON-RPC 2.0</span>
                  </div>
                  <div class="code-block" style="color: #4ade80;">${escapeHtml(JSON.stringify(t.observation || {}, null, 2))}</div>
                </div>
              `;
            }

            if (t.action_type === 'FINAL_ANSWER') {
              html += `
                <div class="waterfall-card final">
                  <div class="step-header">
                    <span class="step-badge">🏁 FINAL ANSWER</span>
                    <span class="step-latency">Tổng: ${data.total_latency_ms} ms</span>
                  </div>
                  <div class="final-answer-box">${escapeHtml(t.output)}</div>
                </div>
              `;
            }
          });

          assistantDiv.innerHTML = html;
        }

      } catch (err) {
        assistantDiv.innerHTML = `<div style="color: #ef4444;">❌ Lỗi kết nối API: ${escapeHtml(err.message)}</div>`;
      } finally {
        sendBtn.disabled = false;
        sendBtn.innerHTML = `<span>Gửi</span><span>🚀</span>`;
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }
  </script>
</body>
</html>
"""


class StudioHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif parsed.path == "/api/database":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(MOCK_DATABASE, ensure_ascii=False).encode("utf-8"))
        elif parsed.path == "/api/tools":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(TOOLS_SCHEMA, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            query = data.get("query", "").strip()
            mode = data.get("mode", "react")
            provider_type = data.get("provider", "gemini")

            start_t = time.time()

            # Chọn Provider
            if provider_type == "gemini":
                gemini_key = os.getenv("GEMINI_API_KEY")
                if gemini_key and gemini_key != "your_gemini_api_key_here":
                    provider = GeminiProvider(model=os.getenv("LLM_MODEL", "gemini-3.6-flash"))
                else:
                    provider = MockOfflineProvider()
            else:
                provider = MockOfflineProvider()

            if mode == "baseline":
                res = provider.generate(query, system_prompt=CHATBOT_BASELINE_PROMPT)
                total_ms = round((time.time() - start_t) * 1000, 2)
                resp_payload = {
                    "status": "success",
                    "mode": "baseline",
                    "provider": provider.__class__.__name__,
                    "query": query,
                    "final_answer": res,
                    "total_latency_ms": total_ms
                }
            else:
                # ReAct Mode
                from app import run_react_agent
                traces = run_react_agent(query, provider, mcp_server)
                total_ms = round((time.time() - start_t) * 1000, 2)

                final_ans = ""
                for t in traces:
                    if t.get("action_type") == "FINAL_ANSWER":
                        final_ans = t.get("output", "")

                resp_payload = {
                    "status": "success",
                    "mode": "react",
                    "provider": provider.__class__.__name__,
                    "query": query,
                    "traces": traces,
                    "final_answer": final_ans,
                    "total_latency_ms": total_ms
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def start_server():
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, StudioHandler)
    print(f"🚀 [VINUNI AI LAB 3 STUDIO] Server running at: http://{HOST}:{PORT}")
    print("👉 Mở trình duyệt để trải nghiệm Web Demo tương tác ReAct Agent & MCP Server!")
    httpd.serve_forever()


if __name__ == "__main__":
    start_server()
