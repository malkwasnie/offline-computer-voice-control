import time
import json
import ollama
from main import SYSTEM_PROMPT  # importujemy Twój gotowy prompt bezpośrednio z main.py!

# 1. Lista modeli do porównania (musisz je najpierw pobrać przez: ollama pull <nazwa>)
MODELE = ["qwen2.5:0.5b", "qwen2.5:1.5b", "llama3.2:3b"]

# 2. Stały zestaw testowy: (komenda użytkownika, oczekiwana akcja)
TESTY = [
    ("Odpal na YouTube muzykę do nauki", "przegladarka"),
    ("Wyszukaj w Google jaka jest pogoda w Gdańsku", "przegladarka"),
    ("Zanotuj, że jutro mamy spotkanie zespołu", "notatka"),
    ("Zapisz notatkę kupić mleko i chleb", "notatka"),
    ("Włącz Spotify i puść ostatnią piosenkę", "spotify"),
    ("Odpal muzykę na Spotify", "spotify"),
    ("Oblicz 50 podzielone na 25", "oblicz"),
    ("Ile to jest 14 razy 3", "oblicz"),
    ("Opowiedz mi dowcip o informatykach", "niezrozumiale"),
    ("Jaki dzisiaj dzień tygodnia?", "niezrozumiale"),
]

print("Rozpoczynam test modeli...\n")

for model_name in MODELE:
    poprawne = 0
    calkowity_czas = 0.0

    # Rozgrzewka modelu (pierwsze zapytanie ładuje model do RAM-u, więc nie liczymy go do średniej)
    ollama.chat(model=model_name, messages=[{"role": "user", "content": "test"}])

    for komenda, oczekiwana_akcja in TESTY:
        start = time.perf_counter()
        
        response = ollama.chat(
            model=model_name,
            format="json",
            options={"temperature": 1},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": komenda},
            ],
        )
        
        czas = time.perf_counter() - start
        calkowity_czas += czas

        # Sprawdzamy, czy JSON jest poprawny i czy model trafił w dobrą akcję
        try:
            wynik = json.loads(response["message"]["content"])
            if wynik.get("akcja") == oczekiwana_akcja:
                poprawne += 1
        except json.JSONDecodeError:
            pass

    sredni_czas = calkowity_czas / len(TESTY)
    skutecznosc = (poprawne / len(TESTY)) * 100

    print(f"Model: {model_name:15} | Skuteczność: {skutecznosc:5.1f}% ({poprawne}/{len(TESTY)}) | Śr. czas: {sredni_czas:.2f} s")