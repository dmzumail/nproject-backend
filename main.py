from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import httpx

app = FastAPI(
    title="nproject.site — Спортивный секундомер",
    description="Интерактивный спортивный секундомер с погодой, развёрнутый на Kubernetes",
    version="1.5.0"  # Новая версия
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
                0: "☀️ Ясно", 1: " Преим. ясно", 2: "⛅ Переменная облачность",
                3: "️ Пасмурно", 45: "🌫 Туман", 51: "🌦 Слабый дождь",
                61: "🌧 Дождь", 71: "🌨 Снег", 80: "🌧 Ливень", 95: "⛈ Гроза"
            }
            desc = codes.get(code, f"🌡 Код {code}")
            return temp, desc, wind
    except Exception:
        return "—", "⚠️ Нет данных", "—"

def get_moscow_time():
    """Возвращает текущее московское время и дату"""
    try:
        # Получаем текущее время в UTC и конвертируем в московское (UTC+3)
        now_utc = datetime.now(timezone.utc)
        moscow_offset = timezone(datetime.timedelta(hours=3))
        now_moscow = now_utc.astimezone(moscow_offset)
        
        # Форматируем дату и время
        date_str = now_moscow.strftime("%d.%m.%Y")
        time_str = now_moscow.strftime("%H:%M:%S")
        day_name = now_moscow.strftime("%A")
        
        # Перевод дней недели на русский
        days_ru = {
            "Monday": "Понедельник",
            "Tuesday": "Вторник",
            "Wednesday": "Среда",
            "Thursday": "Четверг",
            "Friday": "Пятница",
            "Saturday": "Суббота",
            "Sunday": "Воскресенье"
        }
        day_name_ru = days_ru.get(day_name, day_name)
        
        return time_str, date_str, day_name_ru
    except Exception:
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
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>nproject.site — Спортивный секундомер</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f7f6; color: #333; margin: 0; padding: 1rem; }
                .container { max-width: 900px; margin: 0 auto; display: flex; gap: 2rem; flex-wrap: wrap; }
                .stopwatch-section { flex: 2; min-width: 300px; background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
                .sidebar-section { flex: 1; min-width: 250px; display: flex; flex-direction: column; gap: 2rem; }
                .widget { background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
                h1 { text-align: center; color: #2c3e50; margin-top: 0; margin-bottom: 1.5rem; }
                .display { font-size: 3rem; text-align: center; font-family: monospace; margin: 1.5rem 0; padding: 0.5rem; background: #f8f9fa; border-radius: 8px; border: 1px solid #eee; }
                .controls { text-align: center; margin: 1.5rem 0; }
                button { font-size: 1.1rem; padding: 0.6rem 1.2rem; margin: 0 0.4rem; border: none; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
                .start { background: #28a745; color: white; }
                .lap { background: #17a2b8; color: white; }
                .reset { background: #6c757d; color: white; }
                button:disabled { opacity: 0.6; cursor: not-allowed; }
                .laps { margin-top: 2rem; }
                .laps h2 { color: #495057; }
                .lap-header, .lap-item { display: flex; justify-content: space-between; padding: 0.5rem 0; font-family: monospace; }
                .lap-header { font-weight: bold; border-bottom: 2px solid #ddd; background: #f8f9fa; }
                .lap-col { width: 32%; text-align: right; }
                .lap-col:first-child { text-align: left; }
                .lap-item { border-bottom: 1px solid #eee; }
                
                /* Weather Widget */
                .widget h2 { text-align: center; margin-top: 0; color: #2c3e50; }
                .weather-card { text-align: center; }
                .temp { font-size: 3.5rem; font-weight: bold; color: #2c3e50; margin: 0.5rem 0; }
                .desc { font-size: 1.2rem; color: #555; margin-bottom: 0.5rem; }
                .wind { font-size: 0.9rem; color: #777; }
                .hint { margin-top: 1.5rem; font-style: italic; color: #e67e22; font-weight: 500; font-size: 1rem; }
                
                /* Time Widget */
                .time-card { text-align: center; }
                .time-display { font-size: 2.8rem; font-weight: bold; color: #17a2b8; margin: 0.5rem 0; font-family: monospace; }
                .date-display { font-size: 1.3rem; color: #2c3e50; margin-bottom: 0.3rem; }
                .day-display { font-size: 1rem; color: #555; font-style: italic; }
                .time-hint { margin-top: 1rem; font-size: 0.85rem; color: #777; }
                
                .footer { text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; }
                .footer a { color: #17a2b8; text-decoration: none; font-weight: 500; }
                .footer a:hover { text-decoration: underline; }
                
                /* Стили для инструкции */
                .instructions {
                    margin-top: 2rem;
                    padding: 1.5rem;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid #17a2b8;
                }
                .instructions h2 {
                    margin: 0 0 1rem 0;
                    color: #2c3e50;
                    font-size: 1.3rem;
                }
                .instruction-steps {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 0.8rem;
                    margin-bottom: 1rem;
                }
                .step {
                    display: flex;
                    align-items: flex-start;
                    gap: 0.5rem;
                    font-size: 0.95rem;
                    color: #444;
                }
                .step-num {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 24px;
                    height: 24px;
                    background: #17a2b8;
                    color: white;
                    border-radius: 50%;
                    font-weight: bold;
                    font-size: 0.85rem;
                    flex-shrink: 0;
                }
                .instruction-note {
                    margin: 0;
                    font-size: 0.9rem;
                    color: #666;
                    font-style: normal;
                }
                .instruction-note kbd {
                    background: #eee;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 0.85rem;
                    border: 1px solid #ccc;
                }
                @media (max-width: 600px) {
                    .instruction-steps { grid-template-columns: 1fr; }
                    .step { font-size: 0.9rem; }
                    .container { flex-direction: column; }
                    .sidebar-section { flex-direction: column; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="stopwatch-section">
                    <h1>Спортивный секундомер</h1>
                    <div class="display" id="display">00:00:00.000</div>
                    <div class="controls">
                        <button id="startBtn" class="start">▶️ Старт</button>
                        <button id="lapBtn" class="lap" disabled>🏁 Новый круг</button>
                        <button id="resetBtn" class="reset">↺ Сброс</button>
                    </div>
                    <div class="laps">
                        <h2>Круги</h2>
                        <div class="lap-header">
                            <span class="lap-col">Круг</span>
                            <span class="lap-col">Время круга</span>
                            <span class="lap-col">Общее время</span>
                        </div>
                        <div id="lapsList"></div>
                    </div>
                    
                    <!-- Инструкция по использованию -->
                    <div class="instructions">
                        <h2>📖 Как пользоваться</h2>
                        <div class="instruction-steps">
                            <div class="step">
                                <span class="step-num">1</span>
                                <p>Нажми <strong>▶️ Старт</strong> для начала отсчёта</p>
                            </div>
                            <div class="step">
                                <span class="step-num">2</span>
                                <p>Нажми <strong>🏁 Новый круг</strong> чтобы зафиксировать время круга</p>
                            </div>
                            <div class="step">
                                <span class="step-num">3</span>
                                <p>Нажми <strong>⏸️ Пауза</strong> для временной остановки</p>
                            </div>
                            <div class="step">
                                <span class="step-num">4</span>
                                <p>Нажми <strong>↺ Сброс</strong> чтобы начать заново</p>
                            </div>
                        </div>
                        <p class="instruction-note">
                            💡 Горячие клавиши: <kbd>Пробел</kbd> Старт/Пауза · 
                            <kbd>L</kbd> Круг · <kbd>R</kbd> Сброс
                        </p>
                    </div>
                </div>

                <div class="sidebar-section">
                    <!-- Weather Widget -->
                    <div class="widget">
                        <h2>🌤 Погода в Москве</h2>
                        <div class="weather-card">
                            <div class="temp">{{TEMP}}°C</div>
                            <div class="desc">{{DESC}}</div>
                            <div class="wind">💨 Ветер: {{WIND}} м/с</div>
                            <p class="hint">Посмотри погоду перед пробежкой</p>
                        </div>
                    </div>

                    <!-- Time Widget -->
                    <div class="widget">
                        <h2>🕐 Сверим часы</h2>
                        <div class="time-card">
                            <div class="time-display">{{TIME}}</div>
                            <div class="date-display">{{DATE}}</div>
                            <div class="day-display">{{DAY}}</div>
                            <p class="time-hint">Московское время</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="footer">
                <a href="/about">👍 О проекте</a>
            </div>

            <script>
                let startTime = null;
                let lapStartTime = null;
                let interval = null;
                let laps = [];

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
                    return (hours ? String(hours).padStart(2, '0') + ':' : '') +
                           String(minutes).padStart(2, '0') + ':' +
                           String(seconds).padStart(2, '0') + '.' +
                           String(milliseconds).padStart(3, '0');
                }

                function updateDisplay() {
                    if (startTime !== null) {
                        const elapsed = Date.now() - startTime;
                        display.textContent = formatTime(elapsed);
                    }
                }

                startBtn.addEventListener('click', () => {
                    if (startBtn.textContent.includes('Старт')) {
                        startTime = Date.now();
                        lapStartTime = Date.now();
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
                        const currentTime = Date.now();
                        const lapTime = currentTime - lapStartTime;
                        const totalTime = currentTime - startTime;
                        laps.push({ lap: lapTime, total: totalTime });
                        lapStartTime = currentTime;

                        const lapEl = document.createElement('div');
                        lapEl.className = 'lap-item';
                        lapEl.innerHTML = `
                            <span class="lap-col">${laps.length}</span>
                            <span class="lap-col">${formatTime(lapTime)}</span>
                            <span class="lap-col">${formatTime(totalTime)}</span>
                        `;
                        lapsList.prepend(lapEl);
                    }
                });

                resetBtn.addEventListener('click', () => {
                    clearInterval(interval);
                    startTime = null;
                    lapStartTime = null;
                    laps = [];
                    display.textContent = '00:00:00.000';
                    lapsList.innerHTML = '';
                    startBtn.textContent = '▶️ Старт';
                    lapBtn.disabled = true;
                });
                
                // Горячие клавиши
                document.addEventListener('keydown', (e) => {
                    // Игнорируем, если пользователь печатает в поле ввода
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                    
                    if (e.code === 'Space' || e.key === ' ') {
                        e.preventDefault();
                        startBtn.click();  // Пробел = Старт/Пауза
                    }
                    if (e.key === 'l' || e.key === 'L') {
                        e.preventDefault();
                        lapBtn.click();  // L = Новый круг
                    }
                    if (e.key === 'r' || e.key === 'R') {
                        e.preventDefault();
                        resetBtn.click();  // R = Сброс
                    }
                });
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
        return {
            "message": "Hello from nproject.site!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ok"
        }

@app.get("/about")
async def about_page(request: Request):
    if wants_html(request):
        html = """<!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>О проекте — nproject.site</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; background: #f4f7f6; color: #333; }
                .card { background: #fff; padding: 2.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; }
                h1 { color: #2c3e50; margin-bottom: 1rem; font-size: 2rem; }
                .subtitle { color: #555; font-size: 1.2rem; margin-bottom: 2rem; line-height: 1.6; }
                .features { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin: 2rem 0; text-align: left; }
                .feature { background: #f8f9fa; padding: 1.5rem; border-radius: 12px; }
                .feature h3 { margin-top: 0; color: #17a2b8; display: flex; align-items: center; gap: 0.5rem; }
                .feature p { margin: 0; color: #444; line-height: 1.5; }
                .tech-note { background: #e3f2fd; color: #1565c0; padding: 1rem; border-radius: 8px; margin-top: 2rem; font-size: 0.95rem; }
                .nav-link { display: inline-block; margin-top: 2rem; padding: 0.8rem 1.5rem; background: #28a745; color: white; text-decoration: none; border-radius: 8px; font-weight: 500; transition: background 0.2s; }
                .nav-link:hover { background: #218838; }
                @media (max-width: 600px) { .features { grid-template-columns: 1fr; } }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🏃‍♂️ О проекте</h1>
                <p class="subtitle">nproject.site — ваш цифровой помощник для тренировок.<br>Выходите бегать уверенно, зная погоду и свой темп.</p>
                
                <div class="features">
                    <div class="feature">
                        <h3>🌤 Погода перед стартом</h3>
                        <p>Актуальная температура, ветер и состояние неба в Москве. Планируйте пробежку без сюрпризов: одевайтесь по погоде и выбирайте оптимальное время.</p>
                    </div>
                    <div class="feature">
                        <h3>⏱ Секундомер для кругов</h3>
                        <p>Удобный таймер с функцией кругов. Засекайте время каждого отрезка, следите за прогрессом и улучшайте свои результаты на каждой тренировке.</p>
                    </div>
                </div>

                <a href="/" class="nav-link">🏁 К секундомеру</a>
            </div>
        </body>
        </html>"""
        return HTMLResponse(html)
    return {
        "message": "About nproject.site",
        "version": "1.5.0"
    }

@app.get("/healthz")
def health_check():
    return {"status": "healthy"}

# --- Мониторинг: экспорт метрик Prometheus ---
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)