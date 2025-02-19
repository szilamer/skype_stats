# Python alapkép használata
FROM python:3.11-slim

# Rendszer függőségek telepítése
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    xvfb \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    # Új függőségek
    libxtst6 \
    libxss1 \
    libgtk-3-0 \
    libnss3-tools \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Munkamappa létrehozása
WORKDIR /app

# Függőségek másolása és telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Környezeti változók beállítása
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Playwright böngésző telepítése előre
RUN mkdir -p /app/pw-browsers && \
    playwright install chromium && \
    playwright install-deps chromium

# Alkalmazás fájlok másolása
COPY . .

# Port beállítása
ENV PORT=10000

# Xvfb és alkalmazás indítása jobb konfigurációval
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset > /dev/null 2>&1 & sleep 5 && uvicorn api:app --host 0.0.0.0 --port $PORT"] 