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
    && rm -rf /var/lib/apt/lists/*

# Munkamappa létrehozása
WORKDIR /app

# Függőségek másolása és telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright böngésző telepítése
RUN playwright install chromium --with-deps
RUN playwright install-deps

# Alkalmazás fájlok másolása
COPY . .

# Környezeti változók beállítása
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers

# Xvfb és alkalmazás indítása
RUN mkdir -p /app/pw-browsers
COPY start.sh /app/
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"] 