#!/bin/bash

# Xvfb indítása
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &

# Várakozás az Xvfb elindulására
sleep 5

# Python alkalmazás indítása
python skype_reader.py 