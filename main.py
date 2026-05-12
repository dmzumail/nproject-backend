from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import httpx

app = FastAPI(
    title="nproject.site — Спортивный секундомер",
    description="Интерактивный спортивный секундомер с погодой, развёрнутый на Kubernetes",
    version="1.1.0"
)

def wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept

async def get_moscow_weather():
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
                61: " Дождь", 71: "️ Снег", 80: " Ливень", 95: " Гроза"
            }
            desc = codes.get(code, f"🌡 Код {code}")
            return temp, desc, wind
    except Exception:
        return "—", "️ Нет данных", "—"

@app.get("/")
async def read_root(request: Request):
    if wants_html(request):
        temp, desc, wind = await get_moscow_weather()

        html = """<!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>nproject.site — Спортивный секундомер</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f4f7f6;
                    color: #333;
                    margin: 0;
                    padding: 1rem;
                }
                .container {
                    max-width: 900px;
                    margin: 0 auto;
                    display: flex;
                    gap: 2rem;
                    flex-wrap: wrap;
                }
                .stopwatch-section {
                    flex: 2;
                    min-width: 300px;
                    background: #fff;
                    padding: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                }
                .weather-section {
                    flex: 1;
                    min-width: 250px;
                    background: #fff;
                    padding: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                h1 { text-align: center; color: #2c3e50; margin-top: 0; margin-bottom: 1.5rem; }
                .display {
                    font-size: 3rem;
                    text-align: center;
                    font-family: monospace;
                    margin: 1.5rem 0;
                    padding: 0.5rem;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border: 1px solid #eee;
                }
                .controls { text-align: center; margin: 1.5rem 0; }
                button {
                    font-size: 1.1rem; padding: 0.6rem 1.2rem; margin: 0 0.4rem;
                    border: none; border-radius: 6px; cursor: pointer; transition: background 0.2s;
                }
                .start { background: #28a745; color: white; }
                .stop { background: #dc3545; color: white; }
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
                
                /* Погодный виджет */
                .weather-section h2 { text-align: center; margin-top: 0; color: #2c3e50; }
                .weather-card { text-align: center; }
                .temp { font-size: 3.5rem; font-weight: bold; color: #2c3e50; margin: 0.5rem 0; }
                .desc { font-size: 1.2rem; color: #555; margin-bottom: 0.5rem; }
                .wind { font-size: 0.9rem; color: #777; }
                .hint { margin-top: 1.5rem; font-style: italic; color: #e67e22; font-weight: 500; font-size: 1rem; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="stopwatch-section">
                    <h1>Спортивный секундомер</h1>
                    <div class="display" id="display">00:00:00.000</div>
                    <div class="controls">
                        <button id="startBtn" class="start">▶️ Старт</button>
                        <button id="lapBtn" class="lap" disabled>⏱️ Новый круг</button>
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
                </div>

                <div class="weather-section">
                    <h2>🌤 Погода в Москве</h2>
                    <div class="weather-card">
                        <div class="temp">{{TEMP}}°C</div>
                        <div class="desc">{{DESC}}</div>
                        <div class="wind">💨 Ветер: {{WIND}} м/с</div>
                        <p class="hint">Посмотри погоду перед пробежкой</p>
                    </div>
                </div>
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
            </script>
        </body>
        </html>"""

        html = (html.replace("{{TEMP}}", str(temp))
                    .replace("{{DESC}}", desc)
                    .replace("{{WIND}}", str(wind)))
        
        return HTMLResponse(html)
    else:
        return {
            "message": "Hello from nproject.site!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ok"
        }

@app.get("/healthz")
def health_check():
    return {"status": "healthy"}

# --- Мониторинг: экспорт метрик Prometheus ---
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)