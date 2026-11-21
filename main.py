import json
import os
import time
import webbrowser as wb
import sounddevice as sd
from faster_whisper import WhisperModel
import ollama
import pyautogui as pya
import pyperclip as pc

#Initializing the model myModel
myModel = WhisperModel("small", device="cpu", compute_type="int8")
llmModel = "qwen2.5:0.5b"

SYSTEM_PROMPT = """
Jestes asystentem sterujacym komputerem. Twoim jedynym zadaniem jest zamiana polecenia glosowego uzytkownika na obiekt JSON.

Dozwolone formaty odpowiedzi:
1. Otwarcie strony lub wyszukiwanie: {"akcja": "przegladarka", "cel": "youtube" lub "google", "szukaj": "wpisana fraza"}
2. Zapisanie notatki: {"akcja": "notatka", "tresc": "tresc notatki"}
3. Otworzenie Spotify i puszczenie ostatniej piosenki: {"akcja": "spotify", "cel": "odtworz ostatnia piosenke"}
4. Obliczenie wartosci wyrazenia matematycznego: {"akcja": "oblicz", "wyrazenie": "2 + 2"}
5. Niezrozumiale polecenie: {"akcja": "niezrozumiale", "tresc": "Nie zrozumialem polecenia."}

Zasady:
- Odpowiadaj WYLACZNIE poprawnym obiektem JSON, bez zadnego dodatkowego tekstu, komentarzy czy wyjasnien.
- Jesli polecenie nie pasuje do zadnej z powyzszych kategorii, zawsze zwroc akcje "niezrozumiale".
- Jesli uzytkownik nie poda konkretnej strony, domyslnie wpisz Google.
- W polu "wyrazenie" podaj TYLKO samo dzialanie matematyczne, NIGDY nie dopisuj znaku "=" ani wyniku.

Przyklady:
Uzytkownik: "Odpal na YouTube muzyke zespolu Queen"
Odpowiedz: {"akcja": "przegladarka", "cel": "youtube", "szukaj": "muzyka zespolu Queen"}

Użytkownik: "Zanotuj sobie, że we wtorek oddajemy projekt"
Odpowiedź: {"akcja": "notatka", "tresc": "We wtorek oddajemy projekt"}

Uzytkownik: "Otworz Spotify i odtworz ostatnia piosenke"
Odpowiedz: {"akcja": "spotify", "cel": "odtworz ostatnia piosenke"}

Uzytkownik: "Oblicz wartosc wyrazenia 2 + 3"
Odpowiedz: {"akcja": "oblicz", "wyrazenie": "2 + 3"}

Użytkownik: "Opowiedz mi kawał"
Odpowiedź: {"akcja": "niezrozumiale", "tresc": "Nie zrozumialem polecenia."}

Uzytkownik: "Oblicz 50 podzielone na 25"
Odpowiedz: {"akcja": "oblicz", "wyrazenie": "50 / 25"}

Uzytkownik: "Wyszukaj w Google jak zrobic jajecznice"
Odpowiedz: {"akcja": "przegladarka", "cel": "google", "szukaj": "jak zrobic jajecznice"}
"""

#Function recording the audio from the user 
def RecordAudio(duration = 4, fs = 16000):
    print("Nagrywam... ")

    #starting the recording
    recording = sd.rec(
        int(duration * fs), samplerate = fs, channels = 1, dtype = "float32"
    )

    #waiting with program for the recording to end
    sd.wait()

    print("Nagrywanie zakonczone i zapisane")

    return recording.flatten()


def TranscribeAudio(audio):

    #changing recorded audio to text 
    segments, info = myModel.transcribe(audio, language = "pl", initial_prompt = "YouTube, Google, Spotify, zanotuj, Notatnik, oblicz")

    #joining the segments into one string
    text = " ".join([segment.text for segment in segments]).strip()
    return text

def GetJSONFromPrompt(text):

    #sending text to myModel and getting response
    response = ollama.chat(
        model = llmModel,
        format = "json",
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
    )

    return response["message"]["content"]


def ExecuteCommand(jsonResponse):

    #getting the json response
    try:
        command = json.loads(jsonResponse)
    except json.JSONDecodeError:
        print("blad! Model zwrocil zly json")
        return

    akcja = command.get("akcja")

    if akcja == "przegladarka":

        target = command.get("cel")
        search = command.get("szukaj")

        if target == "youtube":
            if search:
                wb.open(f"https://www.youtube.com/results?search_query={search}")
            else:
                wb.open("https://www.youtube.com")

        elif target == "google":
            if search:
                wb.open(f"https://www.google.com/search?q={search}")
            else:
                wb.open("https://www.google.com")



    elif akcja == "notatka":

        content = command.get("tresc")

        if content:
            os.system("start notepad")
            time.sleep(3)
            pc.copy(content)
            pya.hotkey("ctrl", "v")

    elif akcja == "spotify":

        os.system("start spotify:")
        time.sleep(3)
        pya.press("playpause")

        pass

    elif akcja == "oblicz":

        equation = command.get("wyrazenie")
        allowedChars = "0123456789+-*/(). "

        if "=" in equation:
            equation = equation.split("=")[0]

        if equation and all(char in allowedChars for char in equation):
            result = eval(equation)
            print(f"wynik dzialania {equation} = {result}")
        else:
            print(f"Nieprawidlowe lub niebezpieczne wyrazenie: {equation}")

        pass

    elif akcja == "niezrozumiale":
        print(command.get("tresc", "Nie zrozumialem polecenia."))

        pass

    else:
        print("Nieznana akcja:", akcja)


if __name__ == "__main__":
    # Initializing the model myModel
    myModel = WhisperModel("small", device="cpu", compute_type="int8")

    try:
        while True:
            input(
                "\nWcisnij ENTER, aby wydac komende glosowe (lub CTRL+C, aby zakonczyc): "
            )

            audioData = RecordAudio()
            tekst = TranscribeAudio(audioData)
            print("Rozpoznany tekst: ", tekst)

            if not tekst:
                print("Nic nie uslyszalem, sprobuj ponownie.")
                continue

            jsonResponse = GetJSONFromPrompt(tekst)
            print("Decyzja: ", jsonResponse)

            ExecuteCommand(jsonResponse)

    except KeyboardInterrupt:
        print("\nDo zobaczenia potem!")
