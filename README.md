# Skype Üzenet Olvasó

Ez a program automatikusan bejelentkezik a Skype webes felületére és ellenőrzi az olvasatlan üzeneteket.

## Telepítés

### Függőségek

- Docker
- Docker Compose

### Környezeti változók beállítása

Hozz létre egy `.env` fájlt a következő tartalommal:

```env
SKYPE_USERNAME=your_email@example.com
SKYPE_PASSWORD=your_password
```

### Konténer építése és futtatása

```bash
# Konténer építése
docker-compose build

# Konténer futtatása
docker-compose up

# Konténer futtatása háttérben
docker-compose up -d

# Logok megtekintése
docker-compose logs -f

# Konténer leállítása
docker-compose down
```

## Működés

A program a következő műveleteket végzi:

1. Bejelentkezik a megadott Skype fiókba
2. Ellenőrzi az olvasatlan üzeneteket
3. Kiírja az eredményeket:
   - Összes üzenet száma
   - Olvasatlan üzenetek száma
   - Legrégebbi olvasatlan üzenet időpontja

## Debug információk

A program két debug fájlt hoz létre:

- `debug_page.html`: A Skype oldal HTML tartalma
- `debug_info.json`: Részletes információk az üzenetekről

## Hibaelhárítás

Ha a program nem működik megfelelően:

1. Ellenőrizd a környezeti változókat
2. Nézd meg a konténer logjait: `docker-compose logs -f`
3. Ellenőrizd a debug fájlokat 