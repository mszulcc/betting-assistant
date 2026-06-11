# Teoria Obstawiania Piłkarskiego — Baza Wiedzy

## 1. FORMATY KURSÓW

### Kursy dziesiętne (europejskie) — używane przez football-data.co.uk
- Zysk = Stawka × Kurs
- Przykład: £10 × 3.50 = £35 (w tym zwrot stawki), zysk netto = £25
- Minimum = 1.0 (zdarzenie pewne)
- Kurs = 1 / prawdopodobieństwo_implicite

### Kursy ułamkowe (brytyjskie)
- Zysk = Stawka × (licznik/mianownik)
- Przykład: 5/1 → zysk £50 od stawki £10

### Kursy moneyline (amerykańskie)
- Ujemne: wymagana stawka do wygrania $100
- Dodatnie: wygrana od stawki $100

### Przelicznik: dziesiętne → implicite prawdopodobieństwo
```
P = 1 / kurs_dziesietny
```
Przykład: kurs 2.50 → P = 1/2.50 = 40%

---

## 2. MARŻA BUKMACHERA (OVERROUND)

Suma implicite prawdopodobieństw dla wszystkich wyników zawsze przekracza 1.0.
Nadwyżka = marża bukmachera.

### Wzór
```
Overround = (1/KursH + 1/KursD + 1/KursA) - 1
```

### Przykład
- Kurs H=2.10, D=3.40, A=3.60
- 1/2.10 + 1/3.40 + 1/3.60 = 0.476 + 0.294 + 0.278 = 1.048
- Marża = 4.8%

### Normalizacja prawdopodobieństw
```
P_norm(i) = P_raw(i) / suma_wszystkich_P_raw
```
Usuwa marżę i daje "czyste" prawdopodobieństwa rynkowe.

### Typowe marże wg bukmachera
| Bukmacher | Typowa marża |
|-----------|-------------|
| Pinnacle | ~2–3% (najniższa) |
| Betfair Exchange | ~2–5% (prowizja) |
| Bet365 | ~5–7% |
| Więksi bukmacherzy UK | ~7–10% |
| Mniejsi bukmacherzy | ~10–15% |

---

## 3. VALUE BETTING — OBSTAWIANIE Z WARTOŚCIĄ

### Definicja wartości (value)
Zakład ma wartość (value), gdy rzeczywiste prawdopodobieństwo zdarzenia > implicite prawdopodobieństwo kursu.

```
Value = (P_rzeczywiste × Kurs) - 1
```
- Value > 0 → zakład z wartością (opłacalny długoterminowo)
- Value < 0 → zakład bez wartości (niekorzystny)
- Value = 0 → zakład sprawiedliwy (break-even)

### Przykład
- Kurs bukmachera: 2.50 → P_impl = 40%
- Twoja ocena: P = 50%
- Value = (0.50 × 2.50) - 1 = 0.25 → +25% value

### Oczekiwana wartość (EV)
```
EV = (P_wygranej × zysk_netto) - (P_przegranej × stawka)
```

---

## 4. EFEKTYWNOŚĆ RYNKU KURSÓW

### Kursy Pinnacle jako benchmark
Pinnacle jest uznawany za najbardziej efektywny rynek — przyjmuje wysokie limity, wygrani gracze nie są blokowani. Kursy Pinnacle są powszechnie stosowane jako wzorzec "prawdziwego" prawdopodobieństwa.

### Closing Line Value (CLV)
Kurs zamknięcia (tuż przed meczem) zawiera więcej informacji niż kurs otwarcia. Gracze bijący kurs zamknięcia (CLV) długoterminowo wykazują prawdziwą przewagę.

```
CLV = kurs_postawiony / kurs_zamknięcia
```
- CLV > 1.0 → postawiono kurs lepszy niż rynek zamknięcia → dobry sygnał

### Kolumny kursów zamknięcia w football-data.co.uk
Format: dodaj "C" po prefixie bukmachera
- `B365CH` = Bet365 closing home odds
- `PSCH` = Pinnacle closing home odds
- `MaxCH`, `AvgCH` = rynkowe maks./średnie zamknięcia

---

## 5. TYPY RYNKÓW ZAKŁADOWYCH

### 1X2 (Match Result)
- 1 = wygrana gospodarzy
- X = remis
- 2 = wygrana gości
Najpopularniejszy rynek. Kolumny: H, D, A.

### Over/Under 2.5 gola
- Over 2.5 = 3 lub więcej goli w meczu
- Under 2.5 = 0, 1 lub 2 gole
Kolumny: `>2.5`, `<2.5`
Inne linie: 1.5, 3.5, 4.5 (rzadziej w danych historycznych)

### Asian Handicap (AH)
Eliminuje remis przez przyznanie wirtualnej przewagi słabszej drużynie.
- AH = 0: remis = zwrot stawki
- AH = -0.5: drużyna musi wygrać (brak remisu)
- AH = +0.5: drużyna może przegrać o 1 gol
- AH z 0.25/0.75: stawka dzielona na dwa zakłady
Kolumny: `AHH`, `AHA`, `AHh` (wielkość handicapu)

### Both Teams to Score (BTTS)
Czy obie drużyny strzelą gola? (Tak/Nie)
Nie jest dostępny w standardowych plikach CSV football-data.co.uk, ale można obliczyć z danych historycznych.

### Handicap europejski
Podobny do AH, ale remis jest możliwy — trzy wyniki.

---

## 6. PRZEWAGA DRUŻYNY DOMOWEJ (HOME ADVANTAGE)

Historycznie w europejskiej piłce nożnej:
- ~45% meczów wygrywa gospodarz
- ~27% kończy się remisem
- ~28% wygrywa gość

Czynniki wpływające na przewagę domową:
- Wsparcie kibiców
- Brak podróży / zmęczenia
- Znajomość boiska
- Efekty sędziowania (nieświadome uprzedzenia)
- Spadek przewagi przy meczach bez kibiców (COVID-19 potwierdził wpływ)

---

## 7. SYSTEMY OCENY DRUŻYN (RATING SYSTEMS)

### Metoda Elo
- Każda drużyna ma ocenę numeryczną
- Po meczu oceny są aktualizowane na podstawie wyniku vs oczekiwań
- Oczekiwana wygrana: `E = 1 / (1 + 10^((R_oponent - R_druzyna)/400))`
- K-factor określa szybkość dostosowania oceny

### Metoda Least Squares (MLS)
- Modeluje liczbę goli jako sumę siły ataku i słabości obrony
- `Gole_H = atak_H - obrona_A + stała_domowa`

### Metoda Poissona
- Liczba goli w meczu ma rozkład Poissona
- Lambda (średnia oczekiwana liczba goli) wyznaczana z historii
- Pozwala obliczyć prawdopodobieństwo każdego dokładnego wyniku

```
P(k goli) = (e^(-λ) × λ^k) / k!
```

---

## 8. ZARZĄDZANIE BANKROLLEM

### Kelly Criterion
Optymalny rozmiar stawki maksymalizujący długoterminowy wzrost bankrolla:

```
f = (b × p - q) / b
```
Gdzie:
- f = frakcja bankrolla do postawienia
- b = kurs - 1 (zysk netto na jednostkę)
- p = szacowane prawdopodobieństwo wygranej
- q = 1 - p

### Frakcjonalne Kelly
Stosowanie 1/4 lub 1/2 wartości Kelly redukuje wariancję przy zachowaniu pozytywnego EV.

### Flat staking
Stała stawka na każdy zakład — prosta, bezpieczna, ale nie optymalna matematycznie.

### Level staking
Procent bieżącego bankrolla (np. 1–3%) jako stawka.

---

## 9. KLUCZOWE METRYKI OCENY SKUTECZNOŚCI

| Metryka | Opis |
|---------|------|
| ROI | (Zysk / Łączne stawki) × 100% |
| Yield | Jak ROI, standard w UK |
| Strike Rate | % wygranych zakładów |
| P&L | Profit & Loss — łączny wynik |
| AKO | Average Killing Odds — średni kurs postawionych zakładów |
| CLV | Closing Line Value — jakość wejścia w rynek |
| EV | Expected Value — oczekiwana wartość |

---

## 10. BŁĘDY POZNAWCZE W OBSTAWIANIU

- **Gambler's Fallacy** — przekonanie, że po serii porażek wygrana jest "należna"
- **Recency Bias** — nadmierne znaczenie ostatnich wyników
- **Confirmation Bias** — szukanie informacji potwierdzających istniejące przekonanie
- **Overconfidence** — przecenianie własnej dokładności prognoz
- **Loss Aversion** — asymetryczna wrażliwość na straty vs zyski (teoria Kahnemana)
- **Hot Hand Fallacy** — błędne przypisywanie "passy" drużynie lub zawodnikowi
