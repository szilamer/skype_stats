# Python alapkép használata
FROM python:3.11-slim

# Rendszer függőségek telepítése
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Munkamappa létrehozása
WORKDIR /app

# Függőségek másolása és telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright böngésző telepítése
RUN playwright install chromium
RUN playwright install-deps chromium

# Alkalmazás fájlok másolása
COPY . .

# Környezeti változók beállítása
ENV PYTHONUNBUFFERED=1

# Alkalmazás futtatása
CMD ["python", "skype_reader.py"] 