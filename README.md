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

## API Használata Külső Alkalmazásból

Az API a `http://localhost:10000` címen érhető el. A következő végpontok állnak rendelkezésre:

### 1. Üzenetek Ellenőrzése

**Végpont:** `/check-messages`
**Metódus:** POST
**Content-Type:** application/json

#### Kérés formátuma:
```json
{
    "email": "your_email@example.com",
    "password": "your_password"
}
```

#### Válasz formátuma:
```json
{
    "email": "your_email@example.com",
    "total_messages": 42,
    "unread_messages": 5,
    "oldest_unread_date": "2024.02.24. 10:30",
    "error": null
}
```

### Implementációs Példák

#### Python (requests könyvtárral):
```python
import requests

def check_skype_messages(email, password):
    url = "http://localhost:10000/check-messages"
    payload = {
        "email": email,
        "password": password
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Használat:
result = check_skype_messages("your_email@example.com", "your_password")
print(f"Olvasatlan üzenetek száma: {result['unread_messages']}")
```

#### JavaScript/TypeScript (fetch API):
```javascript
async function checkSkypeMessages(email, password) {
    const url = 'http://localhost:10000/check-messages';
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            password: password
        })
    });
    
    return await response.json();
}

// Használat:
checkSkypeMessages('your_email@example.com', 'your_password')
    .then(result => {
        console.log(`Olvasatlan üzenetek száma: ${result.unread_messages}`);
    })
    .catch(error => {
        console.error('Hiba történt:', error);
    });
```

#### C# (.NET):
```csharp
using System.Net.Http;
using System.Text;
using System.Text.Json;

public class SkypeStats
{
    public string Email { get; set; }
    public int TotalMessages { get; set; }
    public int UnreadMessages { get; set; }
    public string OldestUnreadDate { get; set; }
    public string Error { get; set; }
}

public async Task<SkypeStats> CheckSkypeMessages(string email, string password)
{
    using var client = new HttpClient();
    var payload = JsonSerializer.Serialize(new
    {
        email = email,
        password = password
    });

    var content = new StringContent(payload, Encoding.UTF8, "application/json");
    var response = await client.PostAsync("http://localhost:10000/check-messages", content);
    
    var jsonResponse = await response.Content.ReadAsStringAsync();
    return JsonSerializer.Deserialize<SkypeStats>(jsonResponse);
}

// Használat:
var result = await CheckSkypeMessages("your_email@example.com", "your_password");
Console.WriteLine($"Olvasatlan üzenetek száma: {result.UnreadMessages}");
```

#### PHP:
```php
function checkSkypeMessages($email, $password) {
    $url = 'http://localhost:10000/check-messages';
    $data = array(
        'email' => $email,
        'password' => $password
    );

    $options = array(
        'http' => array(
            'method'  => 'POST',
            'header'  => 'Content-Type: application/json',
            'content' => json_encode($data)
        )
    );

    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);
    return json_decode($result, true);
}

// Használat:
$result = checkSkypeMessages('your_email@example.com', 'your_password');
echo "Olvasatlan üzenetek száma: " . $result['unread_messages'];
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

### Gyakori Hibakódok

- "Sikertelen bejelentkezés" - Helytelen email vagy jelszó
- "Nem sikerült lekérni az üzeneteket" - A bejelentkezés sikeres volt, de az üzenetek lekérése közben hiba történt
- Egyéb hibák esetén a válasz `error` mezője tartalmazza a részletes hibaüzenetet 