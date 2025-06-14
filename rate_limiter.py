
import time # Bruges til at måle tid og sætte programmet til at sove i et antal sekunder.
from threading import Lock # Bruges til at sikre, at kode, der bruger fælles data, ikke bliver kørt af flere tråde på samme tid.

# RateLimiter klasse til at begrænse antallet af kald over en given periode
class RateLimiter:

    # Konstruktør, der initialiserer RateLimiter med maksimalt antal kald og periode i sekunder
    def __init__(self, max_calls: int, period_sec: float):
        self.max_calls = max_calls # Maksimalt antal kald, der er tilladt inden for perioden
        self.period_sec = period_sec # Tidsperiode i sekunder, hvor kald tælles
        self.call_timestamps = [] # Liste til at gemme tidsstempler for de seneste kald
        self.lock = Lock() # Lås for at sikre trådsikker adgang til call_timestamps
   
   # metode kaldes ved hvert API-kald - tjekker om man gar overskredet "rate limit" og venter (hvis det er nødvendigt)
    def wait_if_needed(self):

        # Sikrer, at kun én tråd ad gangen kan ændre call_timestamps
        with self.lock:
            now = time.time()
           
           # Fjerner tidsstempler, der er ældre end den angivne periode
            self.call_timestamps = [t for t in self.call_timestamps if now - t < self.period_sec]

            # Hvis antallet af kald overstiger det maksimale antal, venter vi
            if len(self.call_timestamps) >= self.max_calls:
                earliest = self.call_timestamps[0] # Det ældste kald i listen
                to_wait = self.period_sec - (now - earliest) # Beregner, hvor længe vi skal vente for at respektere rate limit
                if to_wait > 0: # Hvis vi skal vente, udskriver vi en besked og sover i det nødvendige antal sekunder
                    print(f"RateLimiter: Sleeping for {to_wait:.2f} seconds to respect rate limit")
                
                # Sover i det nødvendige antal sekunder
                time.sleep(to_wait)

                # Tilføjer det nuværende tidsstempel til listen over kald
            self.call_timestamps.append(time.time())
