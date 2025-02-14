#!/bin/bash

# Xvfb indítása
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &

# Várakozás az Xvfb elindulására
sleep 5

# Ellenőrizzük és telepítsük újra a böngészőt, ha szükséges
if [ ! -d "/app/pw-browsers/chromium-1105" ]; then
    echo "Chromium böngésző telepítése..."
    playwright install chromium
fi

# Python alkalmazás indítása
python skype_reader.py 