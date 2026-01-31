# Specificatie Uren naar Bewakingscode Converter

Dit project bevat een online tool voor het converteren van specificatie-uren CSV-bestanden uit Groeneveld-software naar een overzicht per bewakingscode. Daarnaast wordt op basis van de loonkosten een feitentabel gemaakt van kostprijsbedrag per bewaking om te gebruiken in Power BI.

## 1. Streamlit Web App

### Bestandsnaam

`streamlit_app.py`

### Gebruik

De app is beschikbaar op de volgende url: https://app-uren-converter.streamlit.app/. Daarnaast kan de app ook op je localhost gerund worden. Typ hiervoor het volgende in je command prompt:

```bash
streamlit run streamlit_app.py
```

### Vereisten

Typ het volgende in je command prompt:

```conda
conda install --file requirements.txt
```

### Functies

- **Web-based interface** voor eenvoudig gebruik
- **Drag-and-drop upload** van CSV-bestanden
- **Real-time verwerking** met voortgangsindicatie
- **Interactieve resultaten** weergave
- **Visualisaties** van uren per bewakingscode
- **Download opties** in CSV en Excel formaat
- **Nederlandse en Engelse** output formaten
- **Export van feitentabel arbeidskosten planning** voor gebruik in data modellen

### Interface

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

### Uren planning Output:

```csv
Projectcode;Machinale;Conturex;Biesse en Select;Opsluiten, Voormontage, Afkort/profiel/contr lat;Spuiten;Afmontage;Glaslatten/Plak Roeden
"255340A";35,94;151,29;4,97;202,96999999999997;33,54;125,03999999999999;0,0
"255437";0,42000000000000004;0,24;0,0;0,58;0,27;0,7;0,0
```

## Power BI feitentabel Output:

```csv
Bewakingscode, Projectcode, Project_Key, Kostprijs
K605, 255340A, 255340, 131.82
K602, 253117, 253117, 13.04
```

## Troubleshooting

### Veelvoorkomende problemen:

1. **Bestand handmatig bewerkt voor verwerking in app**: De kolommen worden niet goed herkent
   wanneer er handmatig gewerkt is in het bestand.
2. **Verkeerd formaat**: Bestanden zonder de juiste header worden genegeerd
3. **Dubbele bestanden**: Het script voorkomt nu dubbele verwerking
