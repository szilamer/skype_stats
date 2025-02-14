from playwright.sync_api import sync_playwright
from datetime import datetime
import os
from dotenv import load_dotenv
import time
import re

class SkypeReader:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.setup_browser()
        
    def setup_browser(self):
        try:
            # Böngésző indítása headless módban
            self.browser = self.playwright.chromium.launch(
                headless=True,  # Headless mód bekapcsolása
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-notifications',
                    '--disable-gpu',  # GPU kikapcsolása headless módban
                    '--window-size=1920,1080',
                    '--disable-setuid-sandbox',
                    '--single-process',  # Egyetlen folyamat használata
                    '--no-zygote',  # Zygote process kikapcsolása
                    '--disable-accelerated-2d-canvas',  # 2D gyorsítás kikapcsolása
                    '--disable-web-security',  # Biztonsági korlátozások kikapcsolása
                    '--disable-features=IsolateOrigins,site-per-process'  # Process isolation kikapcsolása
                ]
            )
            
            # Új kontextus létrehozása egyedi beállításokkal
            self.context = self.browser.new_context(
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
            self.page = self.context.new_page()
            self.page.set_default_timeout(120000)  # Timeout növelése 120 másodpercre
            
            # JavaScript kód injektálása az automatizálás elrejtéséhez
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
        except Exception as e:
            print(f"Hiba a böngésző inicializálása során: {str(e)}")
            raise
        
    def login(self, username, password):
        try:
            print("Skype weboldal betöltése...")
            self.page.goto("https://web.skype.com", wait_until="networkidle")
            time.sleep(5)
            
            print("Várakozás a bejelentkezési mezőre...")
            self.page.wait_for_selector('input[name="loginfmt"]', timeout=60000)
            print("Email cím megadása...")
            self.page.fill('input[name="loginfmt"]', username)
            time.sleep(1)
            
            print("Következő gomb kattintása...")
            self.page.click('#idSIButton9')
            time.sleep(2)
            
            print("Várakozás a jelszó mezőre...")
            self.page.wait_for_selector('input[name="passwd"]', timeout=60000)
            print("Jelszó megadása...")
            self.page.fill('input[name="passwd"]', password)
            time.sleep(1)
            
            print("Bejelentkezés gomb kattintása...")
            self.page.click('#idSIButton9')
            time.sleep(3)
            
            print("Várakozás a 'Bejelentkezve maradás' ablakra...")
            try:
                time.sleep(5)
                checkbox = self.page.wait_for_selector('[name="DontShowAgain"]', timeout=10000)
                if checkbox:
                    print("Checkbox megtalálva, kattintás...")
                    checkbox.click()
                    time.sleep(1)
                    self.page.keyboard.press('Enter')
                    time.sleep(5)
            except:
                print("Nem található 'Bejelentkezve maradás' ablak")
            
            print("Várakozás a főoldal betöltésére...")
            time.sleep(20)
            
            # Várjuk meg, hogy a chat lista megjelenjen
            chat_list = self.page.wait_for_selector('div[role="list"]', timeout=30000)
            if not chat_list:
                print("Nem található chat lista")
                return False
                
            print("Oldal frissítése...")
            self.page.reload(wait_until="networkidle")
            time.sleep(10)
            
            return True
            
        except Exception as e:
            print(f"Hiba történt a bejelentkezés során: {str(e)}")
            return False
            
    def get_message_stats(self):
        try:
            print("Várakozás a beszélgetések betöltésére...")
            time.sleep(10)
            
            # HTML tartalom mentése debuggoláshoz
            html_content = self.page.content()
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("HTML tartalom elmentve a debug_page.html fájlba")
            
            # JavaScript kód az olvasatlan üzenetek kereséséhez és debug információk gyűjtéséhez
            js_code = """
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
                        console.log('Aria label:', ariaLabel);  // Debug log
                        
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
                    
                    // Keressük az olvasatlan üzenet jelzőket a specifikus osztályokkal
                    const unreadIndicators = [
                        '.css-1dbjc4n.r-1awozwy.r-1mlx99i.r-1867qdf.r-1yadl64.r-1777fci.r-285fr0.r-s1qlax',
                        '.css-901oao.r-jwli3a.r-1bhw0zn.r-10x49cs.r-b88u0q.r-1cwl3u0'
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
            
            # Futtatjuk a JavaScript kódot
            print("JavaScript kód futtatása...")
            debug_info = self.page.evaluate(js_code)
            
            # Debug információk mentése fájlba
            with open('debug_info.json', 'w', encoding='utf-8') as f:
                f.write(str(debug_info))
            print("Debug információk elmentve a debug_info.json fájlba")
            
            return {
                "total_messages": debug_info['totalChats'],
                "unread_messages": debug_info['unreadCount'],
                "oldest_unread_date": debug_info['oldestUnreadDate']
            }
            
        except Exception as e:
            print(f"Hiba történt az üzenetek lekérdezése során: {str(e)}")
            return None
    
    def close(self):
        print("Böngésző bezárása...")
        self.context.close()
        self.browser.close()
        self.playwright.stop()

def main():
    load_dotenv()
    
    username = os.getenv("SKYPE_USERNAME")
    password = os.getenv("SKYPE_PASSWORD")
    
    if not username or not password:
        print("Hiba: A SKYPE_USERNAME és SKYPE_PASSWORD környezeti változók nincsenek beállítva!")
        return
    
    print(f"Bejelentkezés a következő fiókkal: {username}")
    reader = SkypeReader()
    
    if reader.login(username, password):
        print("Üzenetek statisztikáinak lekérése...")
        stats = reader.get_message_stats()
        if stats:
            print("\nEredmények:")
            print(f"Összes üzenet száma: {stats['total_messages']}")
            print(f"Olvasatlan üzenetek száma: {stats['unread_messages']}")
            if stats['oldest_unread_date']:
                if isinstance(stats['oldest_unread_date'], dict):
                    date_text = stats['oldest_unread_date']['text']
                    print(f"Legrégebbi olvasatlan üzenet időpontja: {date_text}")
                else:
                    print(f"Legrégebbi olvasatlan üzenet időpontja: {stats['oldest_unread_date']}")
            else:
                print("Nincs olvasatlan üzenet")
    
    reader.close()

if __name__ == "__main__":
    main() 