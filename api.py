from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from skype_reader import SkypeReader
import asyncio
import json

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

@app.post("/check-messages", response_model=List[SkypeStats])
async def check_messages(credentials: List[SkypeCredentials]):
    results = []
    
    for cred in credentials:
        try:
            print(f"Bejelentkezés a következő fiókkal: {cred.email}")
            reader = SkypeReader()
            
            if reader.login(cred.email, cred.password):
                stats = reader.get_message_stats()
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
            
            reader.close()
            
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