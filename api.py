from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
import asyncio
import json
import os

app = FastAPI(title="Skype Üzenet Statisztika API")

class SkypeCredentials(BaseModel):
    email: str
    password: str

class SkypeStats(BaseModel):
    email: str
    total_messages: int
    unread_messages: int
    oldest_unread_date: Optional[str] = None
    error: Optional[str] = None

class AsyncSkypeReader:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    async def setup(self):
        try:
            self.playwright = await async_playwright().start()
            
            # Böngésző útvonalának ellenőrzése
            browser_path = os.path.join(os.getenv('PLAYWRIGHT_BROWSERS_PATH', ''), 'chromium-1105/chrome-linux/chrome')
            print(f"Böngésző útvonala: {browser_path}")
            
            if not os.path.exists(browser_path):
                print("Böngésző telepítése...")
                import subprocess
                subprocess.run(['playwright', 'install', 'chromium'], check=True)
            
            # Böngésző indítása headless módban
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-notifications',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--disable-setuid-sandbox',
                    '--single-process',
                    '--no-zygote',
                    '--disable-accelerated-2d-canvas',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            # Új kontextus létrehozása
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                ignore_https_errors=True,
                java_script_enabled=True,
                bypass_csp=True,
                extra_http_headers={
                    'Accept-Language': 'hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7'
                }
            )
            
            # Új oldal létrehozása
            self.page = await self.context.new_page()
            await self.page.set_default_timeout(120000)
            
            # JavaScript kód injektálása
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
        except Exception as e:
            print(f"Hiba a böngésző inicializálása során: {str(e)}")
            raise
    
    async def login(self, username, password):
        try:
            print("Skype weboldal betöltése...")
            await self.page.goto("https://web.skype.com", wait_until="networkidle", timeout=120000)
            await asyncio.sleep(10)
            
            print("Várakozás a bejelentkezési mezőre...")
            await self.page.wait_for_selector('input[name="loginfmt"]', timeout=120000)
            print("Email cím megadása...")
            await self.page.fill('input[name="loginfmt"]', username)
            await asyncio.sleep(2)
            
            print("Következő gomb kattintása...")
            await self.page.click('#idSIButton9')
            await asyncio.sleep(5)
            
            print("Várakozás a jelszó mezőre...")
            await self.page.wait_for_selector('input[name="passwd"]', timeout=120000)
            print("Jelszó megadása...")
            await self.page.fill('input[name="passwd"]', password)
            await asyncio.sleep(2)
            
            print("Bejelentkezés gomb kattintása...")
            await self.page.click('#idSIButton9')
            await asyncio.sleep(5)
            
            print("Várakozás a 'Bejelentkezve maradás' ablakra...")
            try:
                await asyncio.sleep(10)
                checkbox = await self.page.wait_for_selector('[name="DontShowAgain"]', timeout=30000)
                if checkbox:
                    print("Checkbox megtalálva, kattintás...")
                    await checkbox.click()
                    await asyncio.sleep(2)
                    await self.page.keyboard.press('Enter')
                    await asyncio.sleep(10)
            except:
                print("Nem található 'Bejelentkezve maradás' ablak")
            
            print("Várakozás a főoldal betöltésére...")
            await asyncio.sleep(30)
            
            # Várjuk meg, hogy a chat lista megjelenjen
            print("Chat lista keresése...")
            chat_list = None
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    chat_list = await self.page.wait_for_selector('div[role="list"]', timeout=60000)
                    if chat_list:
                        print("Chat lista megtalálva")
                        break
                except:
                    print(f"Chat lista nem található, újrapróbálkozás ({retry_count + 1}/{max_retries})...")
                    await self.page.reload(wait_until="networkidle", timeout=120000)
                    await asyncio.sleep(20)
                    retry_count += 1
            
            if not chat_list:
                print("Nem található chat lista")
                return False
            
            print("Oldal frissítése és várakozás a chat elemekre...")
            await self.page.reload(wait_until="networkidle", timeout=120000)
            await asyncio.sleep(20)
            
            # Várjuk meg, hogy legalább egy chat elem megjelenjen
            try:
                print("Chat elemek keresése...")
                chat_items = await self.page.wait_for_selector('div[role="listitem"]', timeout=60000)
                if chat_items:
                    print("Chat elemek megtalálva")
                    await asyncio.sleep(10)
            except:
                print("Nem találhatók chat elemek")
                return False
            
            return True
            
        except Exception as e:
            print(f"Hiba történt a bejelentkezés során: {str(e)}")
            return False
    
    async def get_message_stats(self):
        try:
            print("Várakozás a beszélgetések betöltésére...")
            await asyncio.sleep(20)
            
            # Próbáljuk meg többször is lekérni a chat elemeket
            retry_count = 0
            max_retries = 3
            debug_info = None
            
            while retry_count < max_retries:
                # HTML tartalom mentése debuggoláshoz
                html_content = await self.page.content()
                with open(f'debug_page_{retry_count}.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"HTML tartalom elmentve a debug_page_{retry_count}.html fájlba")
                
                # JavaScript kód futtatása
                print(f"JavaScript kód futtatása (próbálkozás {retry_count + 1}/{max_retries})...")
                debug_info = await self.page.evaluate(self.get_messages_js_code())
                
                # Debug információk mentése fájlba
                with open(f'debug_info_{retry_count}.json', 'w', encoding='utf-8') as f:
                    f.write(str(debug_info))
                print(f"Debug információk elmentve a debug_info_{retry_count}.json fájlba")
                
                if debug_info and debug_info['totalChats'] > 0:
                    print(f"Sikeresen találtunk {debug_info['totalChats']} chat elemet")
                    break
                
                print("Nem találtunk chat elemeket, újrapróbálkozás...")
                await self.page.reload(wait_until="networkidle", timeout=120000)
                await asyncio.sleep(20)
                retry_count += 1
            
            if not debug_info or debug_info['totalChats'] == 0:
                print("Nem sikerült chat elemeket találni")
                return None
            
            return {
                "total_messages": debug_info['totalChats'],
                "unread_messages": debug_info['unreadCount'],
                "oldest_unread_date": debug_info['oldestUnreadDate']
            }
            
        except Exception as e:
            print(f"Hiba történt az üzenetek lekérdezése során: {str(e)}")
            return None
    
    def get_messages_js_code(self):
        return """
        () => {
            // Keressük a chat elemeket
            const chatItems = Array.from(document.querySelectorAll('div[role="listitem"]'));
            console.log('Talált chat elemek száma:', chatItems.length);
            
            let unreadCount = 0;
            let oldestUnreadDate = null;
            const results = [];
            
            // Vizsgáljuk meg az elemeket
            chatItems.forEach((item, index) => {
                const itemInfo = {
                    index,
                    classes: item.className,
                    text: item.textContent,
                    hasUnread: false,
                    unreadCount: 0,
                    date: null,
                    fullDate: null
                };
                
                // Keressük a dátumot az aria-label attribútumból
                const ariaLabel = item.getAttribute('aria-label');
                if (ariaLabel) {
                    console.log('Aria label:', ariaLabel);
                    
                    // Először próbáljuk megtalálni a teljes dátumot
                    const fullDateMatch = ariaLabel.match(/(\d{4}\.\d{2}\.\d{2}\.)/);
                    const timeMatch = ariaLabel.match(/(\d{1,2}:\d{2})/);
                    
                    // Keressük a mai/tegnapi/stb. jelzőket is
                    const dayMatch = ariaLabel.match(/(ma|tegnap|tegnapelőtt)/i);
                    
                    if (fullDateMatch) {
                        // Ha van teljes dátum
                        itemInfo.date = fullDateMatch[1];
                        const [year, month, day] = fullDateMatch[1].split('.').map(Number);
                        itemInfo.fullDate = new Date(year, month - 1, day);
                        if (timeMatch) {
                            const [hours, minutes] = timeMatch[1].split(':').map(Number);
                            itemInfo.fullDate.setHours(hours, minutes, 0, 0);
                            itemInfo.date = `${fullDateMatch[1]} ${timeMatch[1]}`;
                        }
                    } else if (dayMatch && timeMatch) {
                        // Ha van relatív nap (ma/tegnap) és időpont
                        const today = new Date();
                        const [hours, minutes] = timeMatch[1].split(':').map(Number);
                        
                        switch(dayMatch[1].toLowerCase()) {
                            case 'tegnap':
                                today.setDate(today.getDate() - 1);
                                break;
                            case 'tegnapelőtt':
                                today.setDate(today.getDate() - 2);
                                break;
                        }
                        
                        today.setHours(hours, minutes, 0, 0);
                        itemInfo.fullDate = today;
                        
                        // Formázott dátum string létrehozása
                        const year = today.getFullYear();
                        const month = String(today.getMonth() + 1).padStart(2, '0');
                        const day = String(today.getDate()).padStart(2, '0');
                        itemInfo.date = `${year}.${month}.${day}. ${timeMatch[1]}`;
                    } else if (timeMatch) {
                        // Ha csak időpont van, feltételezzük, hogy mai
                        const today = new Date();
                        const [hours, minutes] = timeMatch[1].split(':').map(Number);
                        today.setHours(hours, minutes, 0, 0);
                        itemInfo.fullDate = today;
                        
                        // Formázott dátum string létrehozása
                        const year = today.getFullYear();
                        const month = String(today.getMonth() + 1).padStart(2, '0');
                        const day = String(today.getDate()).padStart(2, '0');
                        itemInfo.date = `${year}.${month}.${day}. ${timeMatch[1]}`;
                    }
                    
                    if (itemInfo.date) {
                        console.log('Talált dátum:', {
                            text: itemInfo.date,
                            ariaLabel,
                            fullDate: itemInfo.fullDate
                        });
                    }
                }
                
                // Keressük az olvasatlan üzenet jelzőket
                const unreadIndicators = [
                    '.css-1dbjc4n.r-1awozwy.r-1mlx99i.r-1867qdf.r-1yadl64.r-1777fci.r-285fr0.r-s1qlax',
                    '.css-901oao.r-jwli3a.r-1bhw0zn.r-10x49cs.r-b88u0q.r-1cwl3u0',
                    '[role="status"]'
                ];
                
                // Keressük az olvasatlan üzenet jelzőket
                for (const selector of unreadIndicators) {
                    const indicators = item.querySelectorAll(selector);
                    indicators.forEach(indicator => {
                        const style = window.getComputedStyle(indicator);
                        
                        // Ellenőrizzük, hogy látható-e és nem átlátszó
                        if (style.display !== 'none' && 
                            style.visibility !== 'hidden' && 
                            style.opacity !== '0' &&
                            indicator.offsetParent !== null) {
                            
                            // Ellenőrizzük a szöveget
                            const text = indicator.textContent.trim();
                            if (text && /^\\d+$/.test(text)) {
                                const count = parseInt(text);
                                if (count > 0) {
                                    itemInfo.hasUnread = true;
                                    itemInfo.unreadCount = count;
                                    unreadCount = Math.max(unreadCount, count);
                                    
                                    // Ha van dátum és olvasatlan üzenet, frissítjük a legrégebbi dátumot
                                    if (itemInfo.date) {
                                        if (!oldestUnreadDate || 
                                            (itemInfo.fullDate && (!oldestUnreadDate.fullDate || itemInfo.fullDate < oldestUnreadDate.fullDate))) {
                                            oldestUnreadDate = {
                                                text: itemInfo.date,
                                                fullDate: itemInfo.fullDate
                                            };
                                        }
                                    }
                                    
                                    console.log('Talált olvasatlan üzenet:', {
                                        selector,
                                        text,
                                        count,
                                        date: itemInfo.date,
                                        element: indicator.outerHTML
                                    });
                                }
                            }
                        }
                    });
                }
                
                results.push(itemInfo);
            });
            
            return {
                totalChats: chatItems.length,
                unreadCount,
                oldestUnreadDate,
                details: results
            };
        }
        """
    
    async def close(self):
        print("Böngésző bezárása...")
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

@app.post("/check-messages", response_model=List[SkypeStats])
async def check_messages(credentials: List[SkypeCredentials]):
    results = []
    
    for cred in credentials:
        try:
            print(f"Bejelentkezés a következő fiókkal: {cred.email}")
            reader = AsyncSkypeReader()
            await reader.setup()
            
            if await reader.login(cred.email, cred.password):
                stats = await reader.get_message_stats()
                if stats:
                    oldest_date = None
                    if stats['oldest_unread_date']:
                        if isinstance(stats['oldest_unread_date'], dict):
                            oldest_date = stats['oldest_unread_date']['text']
                        else:
                            oldest_date = stats['oldest_unread_date']
                    
                    results.append(SkypeStats(
                        email=cred.email,
                        total_messages=stats['total_messages'],
                        unread_messages=stats['unread_messages'],
                        oldest_unread_date=oldest_date
                    ))
                else:
                    results.append(SkypeStats(
                        email=cred.email,
                        total_messages=0,
                        unread_messages=0,
                        error="Nem sikerült lekérni a statisztikákat"
                    ))
            else:
                results.append(SkypeStats(
                    email=cred.email,
                    total_messages=0,
                    unread_messages=0,
                    error="Sikertelen bejelentkezés"
                ))
            
            await reader.close()
            
        except Exception as e:
            results.append(SkypeStats(
                email=cred.email,
                total_messages=0,
                unread_messages=0,
                error=str(e)
            ))
    
    return results

@app.get("/health")
async def health_check():
    return {"status": "ok"} 