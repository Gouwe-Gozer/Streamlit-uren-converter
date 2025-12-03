"""Script om specificatie-uren te koppelen aan bewakingscodes en te aggregeren per project.
Python equivalent van het R-script 'VanSpecificatieNaarBewakingscodeUren.R'
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import sys
warnings.filterwarnings('ignore')

def main():
    print("=== Python Script Gestart ===")
    
    # Pad naar folder met CSV-bestanden
    current_dir = Path.cwd()
    input_folder = current_dir / "specificatieuren"
    
    print(f"Current directory: {current_dir}")
    print(f"Input folder: {input_folder}")
    
    # Controleer of de folder bestaat
    if not input_folder.exists():
        print(f"FOUT: Input folder niet gevonden: {input_folder}")
        print("Controleer of de folder 'specificatieuren' bestaat.")
        return
    
    # Vertaaltabel die specificatiecode koppelt aan een bewakingscode
    vertaaltabel = pd.DataFrame({
        'specificatiecode': [
            "020CAL", "035FRE", "040CON", "050BIE", "055ORD", 
            "060SEL", "070LAT", "080OPK", "090SPU", "100AFM", 
            "110GLZ", "AFM", "085VMO"
        ],
        'Omschrijving': [
            "Afkorten en calibreren", "Frezen", "Conturex", "Biesse", 
            "Opsluite ramen/deuren", "Select", "Afkort/ProfielContr Lat", 
            "opsluiten kozijnen", "Spuiten", "Afmontage", 
            "Glaszetten (extern)", "afmonteren", "Voormontage/glaslatten"
        ],
        'bewakingscode': [
            "K601", "K601", "K602", "K601", "K603", "K601", "K603", 
            "K603", "K604", "K605", None, "K605", "K603"
        ]
    })
    
    # Zoek alle CSV-bestanden in de input folder
    csv_bestanden = list(input_folder.glob("*.csv"))
    
    print(f"\nAantal CSV-bestanden gevonden: {len(csv_bestanden)}")
    
    if not csv_bestanden:
        print("Geen CSV-bestanden gevonden in:", input_folder)
        return
    
    # Initialiseer lijsten voor data
    alle_data_lijst = []
    niet_behandeld = []
    
    print("\n" + "=" * 60)
    print("VERWERKEN VAN BESTANDEN:")
    print("=" * 60)
    
    # Loop door alle bestanden
    for bestand in csv_bestanden:
        print(f"Verwerk: {bestand.name}")
        
        try:
            # Probeer verschillende encodings voor het lezen van de eerste regel
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            project_code_vlak = None
            
            for encoding in encodings_to_try:
                try:
                    with open(bestand, 'r', encoding=encoding) as f:
                        first_line = f.readline().strip()
                        # Splits op puntkomma en neem eerste element
                        project_code_vlak = first_line.split(';')[0] if ';' in first_line else first_line
                    break  # Stop als een encoding werkt
                except UnicodeDecodeError:
                    continue
            
            if project_code_vlak is None:
                raise UnicodeDecodeError("Kon geen geschikte encoding vinden voor het bestand")
            
            # Probeer verschillende encodings voor het lezen van de CSV data
            data = None
            for encoding in encodings_to_try:
                try:
                    data = pd.read_csv(
                        bestand,
                        sep=';',
                        skiprows=3,
                        decimal=',',
                        encoding=encoding
                    )
                    break  # Stop als een encoding werkt
                except UnicodeDecodeError:
                    continue
            
            if data is None:
                raise UnicodeDecodeError("Kon geen geschikte encoding vinden voor CSV data")
            
            # Check of tweede kolom 'Omschrijving' is
            if len(data.columns) >= 2 and data.columns[1] == 'Omschrijving':
                print(f"  [OK] Geldig bestand | Cel 1A: {project_code_vlak}")
                
                # Voeg project_code toe als kolom
                data['project'] = project_code_vlak
                
                # Voeg toe aan lijst
                alle_data_lijst.append(data)
            else:
                print(f"  [ERROR] Ongeldig: tweede kolom is niet 'Omschrijving'")
                print(f"    Gevonden kolommen: {list(data.columns)}")
                niet_behandeld.append(bestand.name)
                
        except Exception as e:
            print(f"  [ERROR] Fout bij inlezen: {str(e)}")
            niet_behandeld.append(bestand.name)
        
        print("-" * 40)
    
    # Combineer alle geldige dataframes
    if alle_data_lijst:
        alle_data = pd.concat(alle_data_lijst, ignore_index=True)
        
        # Verplaats 'project' kolom naar eerste positie
        cols = ['project'] + [col for col in alle_data.columns if col != 'project']
        alle_data = alle_data[cols]
        
        print(f"\nTotaal aantal rijen in gecombineerde data: {len(alle_data)}")
    else:
        print("Geen geldige bestanden gevonden.")
        alle_data = pd.DataFrame()  # lege dataframe
    
    # Toon niet-behandelde bestanden
    if niet_behandeld:
        print("\n" + "=" * 60)
        print("NIET BEHANDELDE BESTANDEN:")
        print("=" * 60)
        print(f"Aantal: {len(niet_behandeld)}")
        print("Bestanden:")
        for bestand in niet_behandeld:
            print(f"- {bestand}")
    else:
        print("\n" + "=" * 60)
        print("ALLES SUCCESVOL BEHANDELD")
        print("=" * 60)
        print("Alle CSV-bestanden zijn correct ingelezen.")
    
    # Verwerk de data als er data is
    if not alle_data.empty:
        # Data opschonen
        data_opgeschoond = alle_data.copy()
        
        # Verwijder prefix uit projectcode
        data_opgeschoond['projectcode'] = data_opgeschoond['project'].str.replace(
            'SPECIFICATIE UREN van project: ', '', regex=False
        )
        
        # Verwijder oude project kolom
        data_opgeschoond = data_opgeschoond.drop(columns=['project'])
        
        # Hernoem eerste kolom naar specificatiecode
        if len(data_opgeschoond.columns) > 0:
            first_col = data_opgeschoond.columns[0]
            if first_col != 'specificatiecode':
                data_opgeschoond = data_opgeschoond.rename(columns={first_col: 'specificatiecode'})
        
        # Link bewakingscode aan specificatiecode
        data_opgeschoond = pd.merge(
            data_opgeschoond,
            vertaaltabel,
            on='specificatiecode',
            how='left'
        )
        
        # Identificeer de uren kolom (zoek kolom met 'Uren' in de naam)
        uren_kolom = None
        for col in data_opgeschoond.columns:
            if 'Uren' in col:
                uren_kolom = col
                break
        
        if uren_kolom is None:
            print("\nFOUT: Geen uren kolom gevonden in de data.")
            print("Beschikbare kolommen:", list(data_opgeschoond.columns))
            return
        
        print(f"\nGebruik uren kolom: {uren_kolom}")
        
        # Aggregateer uren per bewakingscode per project
        data_met_bewakingscode = data_opgeschoond[data_opgeschoond['bewakingscode'].notna()].copy()
        
        # Zorg ervoor dat uren numeriek zijn
        data_met_bewakingscode[uren_kolom] = pd.to_numeric(
            data_met_bewakingscode[uren_kolom], errors='coerce'
        ).fillna(0)
        
        # Groepeer en aggregeer
        uren_per_bewakingscode = data_met_bewakingscode.groupby(
            ['bewakingscode', 'projectcode']
        )[uren_kolom].sum().reset_index()
        
        # Pivot de tabel: bewakingscodes worden kolommen
        uren_pivot = uren_per_bewakingscode.pivot_table(
            index='projectcode',
            columns='bewakingscode',
            values=uren_kolom,
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Hernoem kolommen om '_uren' toe te voegen
        nieuwe_kolomnamen = ['projectcode']
        for col in uren_pivot.columns[1:]:  # Skip projectcode
            nieuwe_kolomnamen.append(f"{col}_uren")
        
        uren_pivot.columns = nieuwe_kolomnamen
        
        # Toon samenvatting
        print("\n" + "=" * 60)
        print("RESULTATEN SAMENVATTING:")
        print("=" * 60)
        print(f"Aantal projecten: {len(uren_pivot)}")
        print(f"Aantal bewakingscodes: {len(uren_pivot.columns) - 1}")
        print(f"Totaal aantal uren: {uren_pivot.iloc[:, 1:].sum().sum():.2f}")
        
        # Toon eerste paar rijen
        print("\nEerste 5 rijen van resultaat:")
        print(uren_pivot.head())
        
        # Sla resultaten op
        # Nederlandse versie (puntkomma als scheidingsteken)
      
        # Engelse versie (komma als scheidingsteken)
        uren_pivot.to_csv('eng_uren_per_bewakingscode.csv', index=False, encoding='utf-8')
        
        print("\n" + "=" * 60)
        print("BESTANDEN OPGESLAGEN:")
        print("=" * 60)
        print("1. uren_per_bewakingscode.csv (Nederlands formaat, puntkomma)")
        print("2. eng_uren_per_bewakingscode.csv (Engels formaat, komma)")
        
        # Toon ook statistieken per bewakingscode
        print("\n" + "=" * 60)
        print("UREN PER BEWAKINGSCODE (TOTAAL):")
        print("=" * 60)
        
        # Bereken totaal per bewakingscode
        for col in uren_pivot.columns[1:]:  # Skip projectcode
            totaal_uren = uren_pivot[col].sum()
            bewakingscode = col.replace('_uren', '')
            print(f"{bewakingscode}: {totaal_uren:.2f} uren")
    
    else:
        print("\nGeen data om te verwerken.")

if __name__ == "__main__":
    main()
