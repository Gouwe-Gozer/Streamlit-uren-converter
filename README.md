# Specificatie Uren naar Bewakingscode Converter

Dit project bevat twee tools voor het converteren van specificatie-uren CSV-bestanden naar een overzicht per bewakingscode.

## 1. Origineel Python Script

### Bestandsnaam
`VanSpecificatieNaarBewakingscodeUren_correct.py`

### Gebruik
```bash
python VanSpecificatieNaarBewakingscodeUren_correct.py
```

### Vereisten
- Python 3.7+
- Vereiste packages:
  ```bash
  pip install pandas numpy
  ```

### Functie
- Leest CSV-bestanden uit de map `specificatieuren/`
- Verwerkt alleen bestanden met het juiste formaat:
  - Eerste regel: `SPECIFICATIE UREN van project: [projectnummer]`
  - Data start op regel 4
  - Tweede kolom moet 'Omschrijving' heten
- Genereert twee output bestanden:
  - `uren_per_bewakingscode.csv` (Nederlands formaat, puntkomma)
  - `eng_uren_per_bewakingscode.csv` (Engels formaat, komma)

## 2. Streamlit Web App

### Bestandsnaam
`streamlit_app.py`

### Gebruik
```bash
streamlit run streamlit_app.py
```

### Vereisten
```bash
pip install -r requirements.txt
```

### Functies
- **Web-based interface** voor eenvoudig gebruik
- **Drag-and-drop upload** van CSV-bestanden
- **Real-time verwerking** met voortgangsindicatie
- **Interactieve resultaten** weergave
- **Visualisaties** van uren per bewakingscode
- **Download opties** in CSV en Excel formaat
- **Nederlandse en Engelse** output formaten

### Screenshots
1. Upload interface met instructies
2. Verwerkingslogboek
3. Resultaten overzicht
4. Visualisatie grafiek
5. Download opties

## Bestandsformaat Vereisten

### Geldig CSV formaat:
```
SPECIFICATIE UREN van project: 225028
[tweede regel]
[derde regel]
;Omschrijving;Minuten;Uren;Toeslag uren (%);Uren;Uurtarief;= Loonkosten
020CAL;Afkorten en calibreren;1.902,85;31,71;-2,20;31,02;35,00;1.085,45
035FRE;Frezen;0,68;0,01;;0,01;39,71;0,45
...
```

### Vertaaltabel (Specificatiecode → Bewakingscode)
| Specificatiecode | Omschrijving | Bewakingscode |
|------------------|--------------|---------------|
| 020CAL | Afkorten en calibreren | K601 |
| 035FRE | Frezen | K601 |
| 040CON | Conturex | K602 |
| 050BIE | Biesse | K601 |
| 055ORD | Opsluite ramen/deuren | K603 |
| 060SEL | Select | K601 |
| 070LAT | Afkort/ProfielContr Lat | K603 |
| 080OPK | opsluiten kozijnen | K603 |
| 090SPU | Spuiten | K604 |
| 100AFM | Afmontage | K605 |
| 110GLZ | Glaszetten (extern) | None |
| AFM | afmonteren | K605 |
| 085VMO | Voormontage/glaslatten | K603 |

## Installatie

1. Clone of download dit project
2. Installeer dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Plaats CSV-bestanden in de map `specificatieuren/` (voor het originele script)
4. Run de gewenste tool:
   - Voor command-line: `python VanSpecificatieNaarBewakingscodeUren_correct.py`
   - Voor web interface: `streamlit run streamlit_app.py`

## Output Voorbeeld

### CSV Output:
```csv
projectcode;K601_uren;K602_uren;K603_uren;K604_uren;K605_uren
225028;77.96;127.78;280.94;78.40;155.62
225310;10.22;28.48;54.18;9.68;24.04
```

## Troubleshooting

### Veelvoorkomende problemen:
1. **Encoding errors**: De app probeert automatisch verschillende encodings (UTF-8, Latin-1, CP1252)
2. **Verkeerd formaat**: Bestanden zonder de juiste header worden genegeerd
3. **Dubbele bestanden**: Het script voorkomt nu dubbele verwerking
4. **Unicode tekens**: Gebruikt nu ASCII-vriendelijke symbolen in plaats van Unicode

## Licentie

Vrij te gebruiken voor intern bedrijfsgebruik.

## Contact

Voor vragen of problemen, raadpleeg de ontwikkelaar van het originele script.
