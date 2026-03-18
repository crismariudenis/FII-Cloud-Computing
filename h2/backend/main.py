from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
import os
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NoteSchema(BaseModel):
    text: str

notes_db = {
    "tokyo": ["Best sushi at Tsukiji", "Visit Shibuya crossing"],
    "iasi": ["Visit the Palace of Culture", "Walk in Copou Park"],
    "paris": ["Eiffel tower at night is must", "Croissants are amazing"],
    "london": ["Mind the gap", "Visit British Museum"]
}

@app.get("/api/notes/{city}", response_model=List[str])
def get_notes(city: str):
    city_key = city.lower()
    return notes_db.get(city_key, [])

@app.post("/api/notes/{city}")
def add_note(city: str, note: NoteSchema):
    city_key = city.lower()
    if city_key not in notes_db:
        notes_db[city_key] = []
    notes_db[city_key].append(note.text)
    return {"message": "Note added successfully"}

# -----------------------------------------------

@app.get("/api/dashboard/{city}")
async def get_dashboard_data(city: str):
    """
    Orchestrates data from 3 different Web Services.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            hw1_base = os.getenv('HW1_API_URL', 'http://localhost:8000/api').rstrip('/')
            hw1_url = f"{hw1_base}/notes/{city}"
            
            weather_key = os.getenv('WEATHER_API_KEY', '').strip()
            news_key = os.getenv('NEWS_API_KEY', '').strip()

            weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_key}&units=metric"
            news_url = f"https://newsapi.org/v2/everything?q={city}&apiKey={news_key}&pageSize=3"

            print(f"DEBUG: Calling HW1: {hw1_url}")
            hw1_response = await client.get(hw1_url)
            
            print(f"DEBUG: Calling Weather: {weather_url}")
            weather_response = await client.get(weather_url)
            
            print(f"DEBUG: Calling News: {news_url}")
            news_response = await client.get(news_url)

            # --- Error Handling ---
            if weather_response.status_code != 200:
                print(f"Weather Error: {weather_response.text}")
                raise HTTPException(status_code=502, detail=f"Weather API failed: {weather_response.status_code}")
            
            if news_response.status_code != 200:
                if news_response.status_code == 401:
                    raise HTTPException(status_code=502, detail="News API Key Invalid")
                print(f"News Error: {news_response.text}")
                raise HTTPException(status_code=502, detail=f"News API failed: {news_response.status_code}")

            hw1_data = []
            if hw1_response.status_code == 200:
                try:
                    hw1_data = hw1_response.json()
                except ValueError:
                    hw1_data = ["Error decoding notes data"]
            else:
                hw1_data = [] 

            return {
                "city": city.capitalize(),
                "local_notes": hw1_data,
                "weather": weather_response.json(),
                "news": news_response.json().get("articles", [])
            }

        except httpx.RequestError as exc:
            print(f"Connection Error: {exc}")
            raise HTTPException(status_code=503, detail=f"Error communicating with external service: {str(exc)}")
        except HTTPException:
            raise
        except Exception as e:
            print(f"Internal Error: {e}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")