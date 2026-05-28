from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(
    title="nproject.site — Спортивный секундомер",
    description="Интерактивный спортивный секундомер с погодой, развёрнутый на Kubernetes",
    version="1.5.4"
)

# 🔹 CORS для мобильного приложения
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept

async def get_moscow_weather():
    """Получает погоду в Москве через Open-Meteo"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast?latitude=55.75&longitude=37.62&current_weather=true"
            )
            resp.raise_for_status()
            data = resp.json()
            cw = data.get("current_weather", {})
            temp = cw.get("temperature", "—")
            wind = cw.get("windspeed", "—")
            code = cw.get("weathercode", 0)

            codes = {
                0: "☀️ Ясно", 1: "🌤 Преим. ясно", 2: "⛅ Переменная облачность",
                3: "☁️ Пасмурно", 45: "🌫 Туман", 51: "🌦 Слабый дождь",
                61: "🌧 Дождь", 71: "🌨 Снег", 80: "🌧 Ливень", 95: "⛈ Гроза"
            }
            desc = codes.get(code, f"🌡 Код {code}")
            return temp, desc, wind
    except Exception:
        return "—", "⚠️ Нет данных", "—"

def get_moscow_time():
    """Возвращает текущее московское время и дату"""
    try:
        now_utc = datetime.now(timezone.utc)
        moscow_offset = timezone(timedelta(hours=3))
        now_moscow = now_utc.astimezone(moscow_offset)

        date_str = now_moscow.strftime("%d.%m.%Y")
        time_str = now_moscow.strftime("%H:%M:%S")
        day_name = now_moscow.strftime("%A")

        days_ru = {
            "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
            "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
        }
        day_name_ru = days_ru.get(day_name, day_name)
        return time_str, date_str, day_name_ru
    except Exception as e:
        print(f"Error getting Moscow time: {e}")
        return "—", "—", "—"

@app.get("/")
async def read_root(request: Request):
    if wants_html(request):
        temp, desc, wind = await get_moscow_weather()
        time_str, date_str, day_name = get_moscow_time()

        html = """<!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
            <meta name="apple-mobile-web-app-capable" content="yes">
            <meta name="mobile-web-app-capable" content="yes">
            <meta name="theme-color" content="#17a2b8">
            <title>nproject.site — Спортивный секундомер</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
                html { scroll-behavior: smooth; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
                    color: #333;
                    line-height: 1.5;
                    min-height: 100vh;
                    padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
                }
                
                /* Контейнер */
                .container {
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 16px;
                    display: flex;
                    gap: 20px;
                    flex-wrap: wrap;
                }
                
                /* Секции */
                .stopwatch-section {
                    flex: 2;
                    min-width: 300px;
                    background: #fff;
                    padding: 24px;
                    border-radius: 20px;
                    box-shadow: 0 8px 30px rgba(0,0,0,0.08);
                }
                
                .sidebar-section {
                    flex: 1;
                    min-width: 280px;
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                }
                
                .widget {
                    background: #fff;
                    padding: 20px;
                    border-radius: 16px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
                }
                
                /* Заголовки */
                h1 {
                    text-align: center;
                    color: #1a252f;
                    margin-bottom: 20px;
                    font-size: 1.75rem;
                    font-weight: 700;
                }
                
                h2 {
                    text-align: center;
                    color: #2c3e50;
                    margin-bottom: 16px;
                    font-size: 1.25rem;
                    font-weight: 600;
                }
                
                /* Дисплей секундомера */
                .display {
                    font-size: 2.8rem;
                    text-align: center;
                    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                    margin: 20px 0;
                    padding: 16px;
                    background: linear-gradient(145deg, #f8f9fa, #e9ecef);
                    border-radius: 12px;
                    border: 1px solid #dee2e6;
                    font-weight: 600;
                    letter-spacing: 1px;
                }
                
                /* Кнопки */
                .controls {
                    text-align: center;
                    margin: 24px 0;
                    display: flex;
                    gap: 12px;
                    justify-content: center;
                    flex-wrap: wrap;
                }
                
                button {
                    font-size: 1rem;
                    padding: 14px 20px;
                    min-width: 48px;
                    min-height: 48px;
                    border: none;
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-weight: 600;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                }
                
                button:active { transform: scale(0.98); }
                button:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }
                
                .start { background: linear-gradient(135deg, #28a745, #20c997); color: white; }
                .start:hover { background: linear-gradient(135deg, #218838, #1e9e8c); }
                
                .lap { background: linear-gradient(135deg, #17a2b8, #138496); color: white; }
                .lap:hover { background: linear-gradient(135deg, #138496, #117a8b); }
                
                .reset { background: linear-gradient(135deg, #6c757d, #5a6268); color: white; }
                .reset:hover { background: linear-gradient(135deg, #5a6268, #545b62); }
                
                /* Круги */
                .laps { margin-top: 24px; }
                .laps h2 { text-align: left; color: #495057; font-size: 1.1rem; }
                
                .lap-header, .lap-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 12px;
                    font-family: 'SF Mono', monospace;
                    font-size: 0.9rem;
                }
                
                .lap-header {
                    font-weight: 600;
                    border-bottom: 2px solid #dee2e6;
                    background: #f8f9fa;
                    border-radius: 8px 8px 0 0;
                }
                
                .lap-col { width: 32%; text-align: right; }
                .lap-col:first-child { text-align: left; }
                .lap-item { border-bottom: 1px solid #eee; }
                .lap-item:last-child { border-bottom: none; }
                
                /* Виджет погоды */
                .weather-card { text-align: center; }
                .temp {
                    font-size: 3rem;
                    font-weight: 700;
                    color: #1a252f;
                    margin: 8px 0;
                    line-height: 1;
                }
                .desc { font-size: 1.1rem; color: #495057; margin-bottom: 8px; }
                .wind { font-size: 0.95rem; color: #6c757d; }
                .hint {
                    margin-top: 16px;
                    font-style: italic;
                    color: #e67e22;
                    font-weight: 500;
                    font-size: 0.95rem;
                }
                
                /* Виджет времени */
                .time-card { text-align: center; }
                .time-display {
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: #17a2b8;
                    margin: 8px 0;
                    font-family: monospace;
                    line-height: 1;
                }
                .date-display { font-size: 1.2rem; color: #2c3e50; margin-bottom: 4px; font-weight: 500; }
                .day-display { font-size: 1rem; color: #6c757d; font-style: italic; }
                .time-hint { margin-top: 12px; font-size: 0.85rem; color: #6c757d; }
                
                /* Инструкция */
                .instructions {
                    margin-top: 24px;
                    padding: 16px;
                    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                    border-radius: 12px;
                    border-left: 4px solid #17a2b8;
                }
                .instructions h2 {
                    text-align: left;
                    margin: 0 0 12px 0;
                    color: #1a252f;
                    font-size: 1.1rem;
                }
                .instruction-steps {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                    gap: 10px;
                    margin-bottom: 12px;
                }
                .step {
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                    font-size: 0.9rem;
                    color: #444;
                }
                .step-num {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 22px;
                    height: 22px;
                    background: #17a2b8;
                    color: white;
                    border-radius: 50%;
                    font-weight: 600;
                    font-size: 0.8rem;
                    flex-shrink: 0;
                }
                .instruction-note {
                    margin: 0;
                    font-size: 0.85rem;
                    color: #6c757d;
                    font-style: normal;
                }
                .instruction-note kbd {
                    background: #e9ecef;
                    padding: 3px 8px;
                    border-radius: 6px;
                    font-family: monospace;
                    font-size: 0.8rem;
                    border: 1px solid #dee2e6;
                    box-shadow: inset 0 -2px 0 rgba(0,0,0,0.1);
                }
                
                /* Футер */
                .footer {
                    text-align: center;
                    margin-top: 24px;
                    padding-top: 16px;
                    border-top: 1px solid #dee2e6;
                }
                .footer a {
                    color: #17a2b8;
                    text-decoration: none;
                    font-weight: 500;
                    padding: 8px 16px;
                    display: inline-block;
                    border-radius: 8px;
                    transition: background 0.2s;
                }
                .footer a:hover { background: rgba(23, 162, 184, 0.1); }
                
                /* === МОБИЛЬНАЯ АДАПТАЦИЯ === */
                @media (max-width: 768px) {
                    .container {
                        flex-direction: column;
                        padding: 12px;
                    }
                    
                    .stopwatch-section, .sidebar-section {
                        min-width: 100%;
                        width: 100%;
                    }
                    
                    .stopwatch-section {
                        padding: 20px 16px;
                        border-radius: 16px;
                    }
                    
                    h1 { font-size: 1.5rem; }
                    h2 { font-size: 1.1rem; }
                    
                    .display {
                        font-size: 2.2rem;
                        padding: 12px;
                    }
                    
                    .controls {
                        flex-direction: row;
                        flex-wrap: wrap;
                        gap: 10px;
                    }
                    
                    button {
                        flex: 1;
                        min-width: 100px;
                        font-size: 0.95rem;
                        padding: 12px 16px;
                    }
                    
                    .temp { font-size: 2.5rem; }
                    .time-display { font-size: 2rem; }
                    
                    .instruction-steps {
                        grid-template-columns: 1fr;
                    }
                    
                    .lap-header, .lap-item {
                        font-size: 0.85rem;
                        padding: 8px 10px;
                    }
                }
                
                @media (max-width: 480px) {
                    body { padding: 8px; }
                    
                    .stopwatch-section, .widget {
                        padding: 16px 12px;
                        border-radius: 12px;
                    }
                    
                    h1 { font-size: 1.3rem; margin-bottom: 16px; }
                    
                    .display {
                        font-size: 1.8rem;
                        padding: 10px;
                        margin: 16px 0;
                    }
                    
                    button {
                        font-size: 0.9rem;
                        padding: 12px;
                        min-height: 44px;
                    }
                    
                    .temp { font-size: 2.2rem; }
                    .time-display { font-size: 1.8rem; }
                    .date-display { font-size: 1.1rem; }
                    
                    .controls { gap: 8px; }
                    
                    .step { font-size: 0.85rem; }
                    .step-num { width: 20px; height: 20px; font-size: 0.75rem; }
                }
                
                /* Landscape на очень маленьких экранах */
                @media (max-height: 500px) and (orientation: landscape) {
                    .container { padding: 8px; }
                    .stopwatch-section { padding: 12px; }
                    h1 { font-size: 1.2rem; margin-bottom: 12px; }
                    .display { font-size: 1.5rem; margin: 10px 0; padding: 8px; }
                    .controls { margin: 12px 0; }
                    button { padding: 10px 14px; font-size: 0.85rem; }
                }
                
                /* Тёмная тема (опционально) */
                @media (prefers-color-scheme: dark) {
                    body {
                        background: linear-gradient(135deg, #1a252f 0%, #2c3e50 100%);
                        color: #f8f9fa;
                    }
                    .stopwatch-section, .widget {
                        background: #2c3e50;
                        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
                    }
                    h1, h2 { color: #f8f9fa; }
                    .display {
                        background: linear-gradient(145deg, #34495e, #2c3e50);
                        border-color: #495057;
                        color: #f8f9fa;
                    }
                    .lap-header { background: #34495e; border-color: #495057; }
                    .lap-item { border-color: #495057; }
                    .instructions {
                        background: linear-gradient(135deg, #34495e, #2c3e50);
                        border-left-color: #17a2b8;
                    }
                    .step, .instruction-note { color: #adb5bd; }
                    .footer { border-color: #495057; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="stopwatch-section">
                    <h1>🏃‍♂️ Спортивный секундомер</h1>
                    <div class="display" id="display">00:00:00.000</div>
                    <div class="controls">
                        <button id="startBtn" class="start">▶️ Старт</button>
                        <button id="lapBtn" class="lap" disabled>🏁 Круг</button>
                        <button id="resetBtn" class="reset">↺ Сброс</button>
                    </div>
                    <div class="laps">
                        <h2>📋 Круги</h2>
                        <div class="lap-header">
                            <span class="lap-col">№</span>
                            <span class="lap-col">Круг</span>
                            <span class="lap-col">Всего</span>
                        </div>
                        <div id="lapsList"></div>
                    </div>

                    <div class="instructions">
                        <h2>📖 Как пользоваться</h2>
                        <div class="instruction-steps">
                            <div class="step"><span class="step-num">1</span><p>Нажми <strong>▶️</strong> для старта</p></div>
                            <div class="step"><span class="step-num">2</span><p>Нажми <strong>🏁</strong> для круга</p></div>
                            <div class="step"><span class="step-num">3</span><p>Нажми <strong>⏸️</strong> для паузы</p></div>
                            <div class="step"><span class="step-num">4</span><p>Нажми <strong>↺</strong> для сброса</p></div>
                        </div>
                        <p class="instruction-note">
                            ⌨️ <kbd>Пробел</kbd> Старт/Пауза · <kbd>L</kbd> Круг · <kbd>R</kbd> Сброс
                        </p>
                    </div>
                </div>

                <div class="sidebar-section">
                    <div class="widget">
                        <h2>🌤 Погода в Москве</h2>
                        <div class="weather-card">
                            <div class="temp">{{TEMP}}°C</div>
                            <div class="desc">{{DESC}}</div>
                            <div class="wind">💨 {{WIND}} м/с</div>
                            <p class="hint">Планируй тренировку с умом</p>
                        </div>
                    </div>

                    <div class="widget">
                        <h2>🕐 Московское время</h2>
                        <div class="time-card">
                            <div class="time-display">{{TIME}}</div>
                            <div class="date-display">{{DATE}}</div>
                            <div class="day-display">{{DAY}}</div>
                            <p class="time-hint">Точное время для старта</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="footer">
                <a href="/about">ℹ️ О проекте</a>
            </div>

            <script>
                let startTime = null, lapStartTime = null, interval = null, laps = [];
                const display = document.getElementById('display');
                const startBtn = document.getElementById('startBtn');
                const lapBtn = document.getElementById('lapBtn');
                const resetBtn = document.getElementById('resetBtn');
                const lapsList = document.getElementById('lapsList');

                function formatTime(ms) {
                    let totalSeconds = Math.floor(ms / 1000);
                    let hours = Math.floor(totalSeconds / 3600);
                    let minutes = Math.floor((totalSeconds % 3600) / 60);
                    let seconds = totalSeconds % 60;
                    let milliseconds = ms % 1000;
                    return (hours ? String(hours).padStart(2,'0')+':' : '') +
                           String(minutes).padStart(2,'0') + ':' +
                           String(seconds).padStart(2,'0') + '.' +
                           String(milliseconds).padStart(3,'0');
                }

                function updateDisplay() {
                    if (startTime !== null) {
                        display.textContent = formatTime(Date.now() - startTime);
                    }
                }

                startBtn.addEventListener('click', () => {
                    if (startBtn.textContent.includes('Старт') || startBtn.textContent.includes('Продолжить')) {
                        if (!startTime) { startTime = Date.now(); lapStartTime = Date.now(); }
                        else { startTime = Date.now() - (parseInt(display.textContent.split(':')[2]) * 1000 + parseInt(display.textContent.split(':')[1]) * 60000 + (display.textContent.split(':')[0].includes(':') ? parseInt(display.textContent.split(':')[0].split(':')[1]) : 0) * 3600000); }
                        interval = setInterval(updateDisplay, 10);
                        startBtn.textContent = '⏸️ Пауза';
                        lapBtn.disabled = false;
                    } else {
                        clearInterval(interval);
                        startBtn.textContent = '▶️ Продолжить';
                        lapBtn.disabled = true;
                    }
                });

                lapBtn.addEventListener('click', () => {
                    if (startTime !== null) {
                        const now = Date.now();
                        laps.push({ lap: now - lapStartTime, total: now - startTime });
                        lapStartTime = now;
                        const lapEl = document.createElement('div');
                        lapEl.className = 'lap-item';
                        lapEl.innerHTML = `<span class="lap-col">${laps.length}</span><span class="lap-col">${formatTime(laps[laps.length-1].lap)}</span><span class="lap-col">${formatTime(laps[laps.length-1].total)}</span>`;
                        lapsList.prepend(lapEl);
                    }
                });

                resetBtn.addEventListener('click', () => {
                    clearInterval(interval);
                    startTime = lapStartTime = null;
                    laps = [];
                    display.textContent = '00:00:00.000';
                    lapsList.innerHTML = '';
                    startBtn.textContent = '▶️ Старт';
                    lapBtn.disabled = true;
                });

                document.addEventListener('keydown', (e) => {
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                    if (e.code === 'Space' || e.key === ' ') { e.preventDefault(); startBtn.click(); }
                    if (e.key === 'l' || e.key === 'L') { e.preventDefault(); lapBtn.click(); }
                    if (e.key === 'r' || e.key === 'R') { e.preventDefault(); resetBtn.click(); }
                });

                // Prevent zoom on double-tap
                let lastTouchEnd = 0;
                document.addEventListener('touchend', (e) => {
                    const now = Date.now();
                    if (now - lastTouchEnd <= 300) e.preventDefault();
                    lastTouchEnd = now;
                }, false);
            </script>
        </body>
        </html>"""

        html = (html.replace("{{TEMP}}", str(temp))
                    .replace("{{DESC}}", desc)
                    .replace("{{WIND}}", str(wind))
                    .replace("{{TIME}}", time_str)
                    .replace("{{DATE}}", date_str)
                    .replace("{{DAY}}", day_name))
        return HTMLResponse(html)
    else:
        return {"message": "Hello from nproject.site!", "timestamp": datetime.now(timezone.utc).isoformat(), "status": "ok"}

@app.get("/about")
async def about_page(request: Request):
    if wants_html(request):
        html = """<!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="theme-color" content="#17a2b8">
            <title>О проекте — nproject.site</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 16px;
                    background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
                    color: #333;
                    line-height: 1.6;
                }
                .card {
                    background: #fff;
                    padding: 24px;
                    border-radius: 20px;
                    box-shadow: 0 8px 30px rgba(0,0,0,0.08);
                    text-align: center;
                }
                h1 { color: #1a252f; margin-bottom: 12px; font-size: 1.75rem; font-weight: 700; }
                .subtitle { color: #555; font-size: 1.1rem; margin-bottom: 24px; line-height: 1.6; }
                .features {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 16px;
                    margin: 24px 0;
                    text-align: left;
                }
                .feature {
                    background: #f8f9fa;
                    padding: 16px;
                    border-radius: 12px;
                    transition: transform 0.2s;
                }
                .feature:hover { transform: translateY(-2px); }
                .feature h3 {
                    margin: 0 0 8px 0;
                    color: #17a2b8;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 1.1rem;
                }
                .feature p { margin: 0; color: #444; font-size: 0.95rem; line-height: 1.5; }
                .nav-link {
                    display: inline-block;
                    margin-top: 24px;
                    padding: 14px 28px;
                    background: linear-gradient(135deg, #28a745, #20c997);
                    color: white;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 1rem;
                    min-height: 48px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                .nav-link:active { transform: scale(0.98); }
                
                @media (max-width: 600px) {
                    body { padding: 12px; }
                    .card { padding: 20px 16px; border-radius: 16px; }
                    h1 { font-size: 1.5rem; }
                    .subtitle { font-size: 1rem; }
                    .features { grid-template-columns: 1fr; }
                    .feature { padding: 14px; }
                }
                
                @media (prefers-color-scheme: dark) {
                    body { background: linear-gradient(135deg, #1a252f 0%, #2c3e50 100%); color: #f8f9fa; }
                    .card { background: #2c3e50; }
                    h1 { color: #f8f9fa; }
                    .subtitle { color: #adb5bd; }
                    .feature { background: #34495e; }
                    .feature p { color: #dee2e6; }
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🏃‍♂️ О проекте</h1>
                <p class="subtitle">nproject.site — ваш цифровой помощник для тренировок.<br>Бегайте уверенно, зная погоду, время и свой темп.</p>
                <div class="features">
                    <div class="feature">
                        <h3>🌤 Погода</h3>
                        <p>Актуальная температура и ветер в Москве. Планируйте пробежку без сюрпризов.</p>
                    </div>
                    <div class="feature">
                        <h3>⏱ Секундомер</h3>
                        <p>Удобный таймер с кругами. Засекайте отрезки и улучшайте результаты.</p>
                    </div>
                    <div class="feature">
                        <h3>🕐 Время</h3>
                        <p>Точное московское время. Синхронизируйтесь перед стартом.</p>
                    </div>
                </div>
                <a href="/" class="nav-link">🏁 К секундомеру</a>
            </div>
        </body>
        </html>"""
        return HTMLResponse(html)
    return {"message": "About nproject.site", "version": "1.5.4"}

@app.get("/healthz")
def health_check():
    return {"status": "healthy"}

# Prometheus metrics
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
