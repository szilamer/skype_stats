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
            print("\n=== SETUP KEZDÉSE ===")
            print(f"Környezeti változók:")
            print(f"DISPLAY: {os.getenv('DISPLAY')}")
            print(f"PLAYWRIGHT_BROWSERS_PATH: {os.getenv('PLAYWRIGHT_BROWSERS_PATH')}")
            print(f"PWD: {os.getenv('PWD')}")
            
            print("\n=== PLAYWRIGHT INICIALIZÁLÁSA ===")
            try:
                self.playwright = await async_playwright().start()
                print(f"Playwright objektum típusa: {type(self.playwright)}")
                print(f"Playwright objektum: {self.playwright}")
                print("Elérhető böngészők:")
                print(f"- Chromium: {self.playwright.chromium}")
                print(f"- Firefox: {self.playwright.firefox}")
                print(f"- Webkit: {self.playwright.webkit}")
            except Exception as e:
                print(f"HIBA a Playwright inicializálása során: {str(e)}")
                print(f"Hiba típusa: {type(e)}")
                print(f"Hiba részletek: {e.__dict__}")
                raise
            
            print("\n=== BÖNGÉSZŐ INDÍTÁSA ===")
            try:
                print("Böngésző indítási paraméterek:")
                launch_args = {
                    'headless': True,
                    'args': [
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-software-rasterizer',
                        '--disable-features=VizDisplayCompositor'
                    ]
                }
                print(f"Launch args: {json.dumps(launch_args, indent=2)}")
                
                print("Chromium böngésző indítása...")
                self.browser = await self.playwright.chromium.launch(**launch_args)
                print(f"Böngésző objektum típusa: {type(self.browser)}")
                print(f"Böngésző objektum: {self.browser}")
                
                if not self.browser:
                    print("HIBA: A böngésző objektum None értékű!")
                    return False
                    
                print("Böngésző verzió információk:")
                version = await self.browser.version()
                print(f"- Verzió: {version}")
                
                contexts = self.browser.contexts
                print(f"Aktív kontextusok száma: {len(contexts)}")
                
            except Exception as e:
                print(f"HIBA a böngésző indítása során: {str(e)}")
                print(f"Hiba típusa: {type(e)}")
                print(f"Hiba részletek: {e.__dict__}")
                if self.playwright:
                    await self.playwright.stop()
                return False
            
            print("\n=== KONTEXTUS LÉTREHOZÁSA ===")
            try:
                print("Kontextus paraméterek:")
                context_args = {
                    'viewport': {'width': 1920, 'height': 1080},
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'bypass_csp': True,
                    'ignore_https_errors': True
                }
                print(f"Context args: {json.dumps(context_args, indent=2)}")
                
                print("Új kontextus létrehozása...")
                self.context = await self.browser.new_context(**context_args)
                print(f"Kontextus objektum típusa: {type(self.context)}")
                print(f"Kontextus objektum: {self.context}")
                
                if not self.context:
                    print("HIBA: A kontextus objektum None értékű!")
                    return False
                
                pages = await self.context.pages()
                print(f"Aktív oldalak száma a kontextusban: {len(pages)}")
                
            except Exception as e:
                print(f"HIBA a kontextus létrehozása során: {str(e)}")
                print(f"Hiba típusa: {type(e)}")
                print(f"Hiba részletek: {e.__dict__}")
                await self.browser.close()
                await self.playwright.stop()
                return False
            
            print("\n=== ÚJ OLDAL LÉTREHOZÁSA ===")
            try:
                print("Oldal létrehozásának megkísérlése...")
                try:
                    print("Új oldal létrehozása a kontextusban...")
                    self.page = await self.context.new_page()
                    print(f"Oldal objektum típusa: {type(self.page)}")
                    print(f"Oldal objektum: {self.page}")
                    
                    print("Oldal tulajdonságok:")
                    url = self.page.url
                    print(f"- URL: {url}")
                    viewport = await self.page.viewport_size()
                    print(f"- Viewport: {viewport}")
                    
                except Exception as page_error:
                    print(f"HIBA az oldal létrehozása során (belső): {str(page_error)}")
                    print(f"Hiba típusa: {type(page_error)}")
                    print(f"Hiba részletek: {page_error.__dict__}")
                    raise
                
                if not self.page:
                    print("HIBA: Az oldal objektum None értékű!")
                    return False
                
                print("Timeout beállítása...")
                await self.page.set_default_timeout(120000)
                print("Oldal sikeresen létrehozva és konfigurálva")
                
                print("\n=== SETUP BEFEJEZVE ===")
                return True
                
            except Exception as e:
                print(f"HIBA az oldal létrehozása során (külső): {str(e)}")
                print(f"Hiba típusa: {type(e)}")
                print(f"Hiba részletek: {e.__dict__}")
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()
                return False
            
        except Exception as e:
            print(f"\n=== VÉGZETES HIBA A SETUP SORÁN ===")
            print(f"Hiba üzenet: {str(e)}")
            print(f"Hiba típusa: {type(e)}")
            print(f"Hiba részletek: {e.__dict__}")
            if self.playwright:
                await self.playwright.stop()
            return False
    
    async def login(self, username, password):
        try:
            print("\n=== BEJELENTKEZÉS KEZDÉSE ===")
            print(f"Bejelentkezési adatok:")
            print(f"- Email: {username}")
            print(f"- Jelszó: {'*' * len(password)}")
            
            print("\n=== SKYPE WEBOLDAL BETÖLTÉSE ===")
            try:
                print("Oldal betöltése: https://web.skype.com")
                response = await self.page.goto("https://web.skype.com", wait_until="networkidle", timeout=120000)
                print(f"Válasz státusz: {response.status if response else 'Nincs válasz'}")
                print(f"Jelenlegi URL: {self.page.url}")
                await asyncio.sleep(10)
            except Exception as e:
                print(f"HIBA az oldal betöltése során: {str(e)}")
                print(f"Hiba típusa: {type(e)}")
                print(f"Hiba részletek: {e.__dict__}")
                return False
            
            print("\n=== BEJELENTKEZÉSI ŰRLAP KITÖLTÉSE ===")
            try:
                print("Várakozás a bejelentkezési mezőre...")
                email_input = await self.page.wait_for_selector('input[name="loginfmt"]', timeout=120000)
                print(f"Email mező megtalálva: {email_input}")
                
                print("Email cím megadása...")
                await self.page.fill('input[name="loginfmt"]', username)
                print("Email cím sikeresen megadva")
                await asyncio.sleep(2)
                
                print("Következő gomb keresése...")
                next_button = await self.page.wait_for_selector('#idSIButton9')
                print(f"Következő gomb megtalálva: {next_button}")
                
                print("Következő gomb kattintása...")
                await self.page.click('#idSIButton9')
                print("Következő gomb sikeresen megnyomva")
                await asyncio.sleep(5)
                
                print("Várakozás a jelszó mezőre...")
                password_input = await self.page.wait_for_selector('input[name="passwd"]', timeout=120000)
                print(f"Jelszó mező megtalálva: {password_input}")
                
                print("Jelszó megadása...")
                await self.page.fill('input[name="passwd"]', password)
                print("Jelszó sikeresen megadva")
                await asyncio.sleep(2)
                
                print("Bejelentkezés gomb kattintása...")
                await self.page.click('#idSIButton9')
                print("Bejelentkezés gomb sikeresen megnyomva")
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"HIBA a bejelentkezési űrlap kitöltése során: {str(e)}")
                print(f"Hiba típusa: {type(e)}")
                print(f"Hiba részletek: {e.__dict__}")
                print(f"Jelenlegi URL: {self.page.url}")
                return False
            
            print("\n=== BEJELENTKEZÉS UTÁNI FOLYAMAT ===")
            try:
                print("Várakozás a 'Bejelentkezve maradás' ablakra...")
                try:
                    await asyncio.sleep(10)
                    checkbox = await self.page.wait_for_selector('[name="DontShowAgain"]', timeout=30000)
                    if checkbox:
                        print("Checkbox megtalálva, kattintás...")
                        await checkbox.click()
                        print("Checkbox sikeresen bepipálva")
                        await asyncio.sleep(2)
                        await self.page.keyboard.press('Enter')
                        print("Enter billentyű lenyomva")
                        await asyncio.sleep(10)
                except Exception as e:
                    print(f"Megjegyzés: 'Bejelentkezve maradás' ablak nem található: {str(e)}")
                
                print("\n=== CHAT LISTA BETÖLTÉSE ===")
                print("Várakozás a főoldal betöltésére...")
                await asyncio.sleep(30)
                print(f"Jelenlegi URL: {self.page.url}")
                
                print("Chat lista keresése...")
                chat_list = None
                retry_count = 0
                max_retries = 3
                
                while retry_count < max_retries:
                    try:
                        print(f"\nPróbálkozás {retry_count + 1}/{max_retries}...")
                        chat_list = await self.page.wait_for_selector('div[role="list"]', timeout=60000)
                        if chat_list:
                            print("Chat lista megtalálva")
                            print(f"Chat lista elem: {chat_list}")
                            break
                    except Exception as e:
                        print(f"Chat lista nem található ebben a próbálkozásban: {str(e)}")
                        print("Oldal újratöltése...")
                        await self.page.reload(wait_until="networkidle", timeout=120000)
                        print(f"Oldal újratöltve, jelenlegi URL: {self.page.url}")
                        await asyncio.sleep(20)
                        retry_count += 1
                
                if not chat_list:
                    print("HIBA: Nem található chat lista több próbálkozás után sem")
                    return False
                
                print("\n=== CHAT ELEMEK ELLENŐRZÉSE ===")
                print("Oldal frissítése és várakozás a chat elemekre...")
                await self.page.reload(wait_until="networkidle", timeout=120000)
                await asyncio.sleep(20)
                
                try:
                    print("Chat elemek keresése...")
                    chat_items = await self.page.wait_for_selector('div[role="listitem"]', timeout=60000)
                    if chat_items:
                        print("Chat elemek megtalálva")
                        print(f"Chat elem: {chat_items}")
                        await asyncio.sleep(10)
                except Exception as e:
                    print(f"HIBA: Nem találhatók chat elemek: {str(e)}")
                    print(f"Hiba típusa: {type(e)}")
                    print(f"Hiba részletek: {e.__dict__}")
                    return False
                
                print("\n=== BEJELENTKEZÉS BEFEJEZVE ===")
                return True
                
            except Exception as e:
                print(f"HIBA a bejelentkezés utáni folyamat során: {str(e)}")
                print(f"Hiba típusa: {type(e)}")
                print(f"Hiba részletek: {e.__dict__}")
                print(f"Jelenlegi URL: {self.page.url}")
                return False
            
        except Exception as e:
            print(f"\n=== VÉGZETES HIBA A BEJELENTKEZÉS SORÁN ===")
            print(f"Hiba üzenet: {str(e)}")
            print(f"Hiba típusa: {type(e)}")
            print(f"Hiba részletek: {e.__dict__}")
            print(f"Jelenlegi URL: {self.page.url if self.page else 'Nincs oldal'}")
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
        try:
            print("Böngésző bezárása...")
            if self.context:
                try:
                    await self.context.close()
                    print("Kontextus sikeresen bezárva")
                except Exception as e:
                    print(f"Hiba a kontextus bezárása során: {str(e)}")
            
            if self.browser:
                try:
                    await self.browser.close()
                    print("Böngésző sikeresen bezárva")
                except Exception as e:
                    print(f"Hiba a böngésző bezárása során: {str(e)}")
            
            if self.playwright:
                try:
                    await self.playwright.stop()
                    print("Playwright sikeresen leállítva")
                except Exception as e:
                    print(f"Hiba a Playwright leállítása során: {str(e)}")
        except Exception as e:
            print(f"Általános hiba a bezárás során: {str(e)}")

@app.post("/check-messages", response_model=List[SkypeStats])
async def check_messages(credentials: List[SkypeCredentials]):
    results = []
    
    for cred in credentials:
        reader = None
        try:
            print(f"Bejelentkezés a következő fiókkal: {cred.email}")
            reader = AsyncSkypeReader()
            setup_success = await reader.setup()
            
            if not setup_success:
                results.append(SkypeStats(
                    email=cred.email,
                    total_messages=0,
                    unread_messages=0,
                    error="Nem sikerült inicializálni a böngészőt"
                ))
                continue
            
            login_success = await reader.login(cred.email, cred.password)
            if login_success:
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
            
        except Exception as e:
            print(f"Hiba történt: {str(e)}")
            results.append(SkypeStats(
                email=cred.email,
                total_messages=0,
                unread_messages=0,
                error=str(e)
            ))
        finally:
            if reader:
                try:
                    await reader.close()
                except Exception as e:
                    print(f"Hiba a böngésző bezárása során: {str(e)}")
    
    return results

@app.get("/health")
async def health_check():
    return {"status": "ok"} 