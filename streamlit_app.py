"""Streamlit app voor specificatie-uren naar bewakingscode conversie
Gebaseerd op VanSpecificatieNaarBewakingscodeUren_correct.py
"""

import streamlit as st
import pandas as pd
import io
import warnings
warnings.filterwarnings('ignore')


# Set page config
st.set_page_config(
    page_title="Specificatie Uren naar Bewakingscode",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 Specificatie Uren naar Bewakingscode Converter")
st.markdown("""
Deze app converteert specificatie-uren CSV-bestanden naar een overzicht per bewakingscode.
Upload één of meerdere CSV-bestanden met de juiste opmaak.
""")

# Sidebar for instructions
with st.sidebar:
    st.header("📋 Instructies")
    st.markdown("""
    **Bestandsformaat:**
    - CSV-bestand met puntkomma als scheidingsteken
    - Eerste regel: `SPECIFICATIE UREN van project: [projectnummer]`
    - Data start op regel 4
    - Kolommen: specificatiecode, Omschrijving, Minuten, Uren, etc.
    
    **Voorbeeld:**
    ```
    SPECIFICATIE UREN van project: 225028
    [tweede regel]
    [derde regel]
    ;Omschrijving;Minuten;Uren;...
    020CAL;Afkorten en calibreren;1.902,85;31,71;...
    ```
    """)
    
    st.header("⚙️ Instellingen")
    output_format = st.radio(
        "Uitvoerformaat voor CSV:",
        ["Nederlands (puntkomma)", "Engels/Amerikaans (komma)"],
        index=0
    )

# Vertaaltabel (bewakingscode mapping)
vertaaltabel = pd.DataFrame({
    'specificatiecode': [
        "020CAL", "035FRE", "040CON", "050BIE", 
        "055ORD", "060SEL", "070LAT", "080OPK", 
        "090SPU", "100AFM", "110GLZ", "AFM", 
        "085VMO"
    ],
    'Omschrijving': [
        "Afkorten en calibreren", "Frezen", "Conturex", "Biesse", 
        "Opsluite ramen/deuren", "Select", "Afkort/ProfielContr Lat", "opsluiten kozijnen",
        "Spuiten", "Afmontage", "Glaszetten (extern)", "afmonteren", 
        "Voormontage/glaslatten"
    ],
    'bewakingscode': [
        "K601", "K601", "K602", "K608", 
        "K603", "K608", "K603", "K603", 
        "K604", "K605", None, "K605",
        "K603"
    ],
    'bewakingomschrijving': [
        "Machinale", "Machinale","Conturex","Biesse en Select", 
        "Opsluiten, Voormontage, Afkort/profiel/contr lat","Biesse en Select", "Opsluiten, Voormontage, Afkort/profiel/contr lat","Opsluiten, Voormontage, Afkort/profiel/contr lat", 
        "Spuiten","Afmontage",None,"Afmontage",
        "Opsluiten, Voormontage, Afkort/profiel/contr lat"
    ]
})


# File uploader
uploaded_files = st.file_uploader(
    "Upload CSV-bestanden",
    type=['csv', 'CSV'],
    accept_multiple_files=True,
    help="Selecteer één of meerdere CSV-bestanden"
)


# Lijst die projectcodes bijhoudt om duplicaten te detecteren
processed_project_codes = []

if uploaded_files:
    st.subheader("📁 Geüploade Bestanden")
    st.write(f"Aantal bestanden: {len(uploaded_files)}")
    
    # Initialize lists for data
    alle_data_lijst = []
    niet_behandeld = []
    verwerkings_log = []
    # Duplicate detection
    processed_project_codes = []

    # Process each file
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Verwerken: {uploaded_file.name} ({i+1}/{len(uploaded_files)})")
        
        try:
            # Get the raw bytes
            file_bytes = uploaded_file.getvalue()
            
            # Try different encodings to read the file
            encodings_to_try = ['cp1252', 'latin-1', 'iso-8859-1', 'utf-8']
            data = None
            project_code_vlak = None
            used_encoding = None
            
            for encoding in encodings_to_try:
                try:
                    # Read file bytes directly with skiprows
                    data = pd.read_csv(
                        io.BytesIO(file_bytes),
                        sep=';',
                        decimal=',',
                        encoding=encoding,
                        skiprows=3,
                        on_bad_lines='warn'
                    )
                    used_encoding = encoding
                    
                    # Extract project code from first line
                    content = file_bytes.decode(encoding, errors='ignore')
                    first_line = content.split('\n')[0] if '\n' in content else content
                    if ';' in first_line:
                        project_code_vlak = first_line.strip().split(';')[0]
                    else:
                        project_code_vlak = first_line.strip()
                    
                    
                    project_code_clean = project_code_vlak.replace('SPECIFICATIE UREN van project: ', '')
                
                    if project_code_clean in processed_project_codes:
                        verwerkings_log.append(f"[WAARSCHUWING] {uploaded_file.name}: Projectcode {project_code_clean} is al eerder verwerkt. Bestand wordt overgeslagen.")
                        niet_behandeld.append(uploaded_file.name)
                        # Skip naar volgend bestand
                        data = None  # Zorg dat data None blijft
                        break  # Break uit de encoding-loop
                    break
                except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError):
                    continue
            
            if data is None or data.empty:
                raise ValueError("Kon CSV niet lezen met ondersteunde encodings of bestand is leeg")

            
            # Check if second column is 'Omschrijving'
            if len(data.columns) >= 2 and data.columns[1] == 'Omschrijving':
                # Add project code as column
                data['project'] = project_code_vlak

                # Add to project names list for duplicate detection
                processed_project_codes.append(project_code_clean)
                
                # Process immediately to reduce memory usage
                if len(alle_data_lijst) > 0 and len(data.columns) != len(alle_data_lijst[0].columns):
                    # Ensure column consistency
                    st.warning(f"Kolommen verschillen in {uploaded_file.name}")
                
                # Add to list
                alle_data_lijst.append(data)
                verwerkings_log.append(f"[OK] {uploaded_file.name}: Succesvol verwerkt (Project: {project_code_vlak})")
            else:
                niet_behandeld.append(uploaded_file.name)
                verwerkings_log.append(f"[ERROR] {uploaded_file.name}: Ongeldig formaat (tweede kolom is niet 'Omschrijving', gevonden: {list(data.columns)[1] if len(data.columns) >= 2 else 'geen tweede kolom'})")
                
        except Exception as e:
            niet_behandeld.append(uploaded_file.name)
            verwerkings_log.append(f"[ERROR] {uploaded_file.name}: Fout - {str(e)}")
        
        # Update progress
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    status_text.text("Verwerking voltooid!")
    
    # Show processing log
    with st.expander("📋 Verwerkingslogboek", expanded=True):
        for log_entry in verwerkings_log:
            st.write(log_entry)
    
    # Combine all dataframes if we have valid data
    if alle_data_lijst:
        alle_data = pd.concat(alle_data_lijst, ignore_index=True)
        
        # Move 'project' column to first position
        cols = ['project'] + [col for col in alle_data.columns if col != 'project']
        alle_data = alle_data[cols]
        
        st.success(f"[OK] {len(alle_data_lijst)} bestand(en) succesvol verwerkt, {len(niet_behandeld)} niet verwerkt")
        st.write(f"Totaal aantal rijen: {len(alle_data)}")
        
        # Process the data
        with st.spinner("Data aan het verwerken..."):
            # Clean data
            data_opgeschoond = alle_data.copy()
            
            # Remove prefix from project code
            data_opgeschoond['projectcode'] = data_opgeschoond['project'].str.replace(
                'SPECIFICATIE UREN van project: ', '', regex=False
            )
            
            # Remove old project column
            data_opgeschoond = data_opgeschoond.drop(columns=['project'])
            
            # Rename first column to specificatiecode
            if len(data_opgeschoond.columns) > 0:
                first_col = data_opgeschoond.columns[0]
                if first_col != 'specificatiecode':
                    data_opgeschoond = data_opgeschoond.rename(columns={first_col: 'specificatiecode'})
            
            # Link bewakingscode to specificatiecode
            data_opgeschoond = pd.merge(
                data_opgeschoond,
                vertaaltabel,
                on='specificatiecode',
                how='left'
            )
            
            # Identify the hours column
            uren_kolom = None
            for col in data_opgeschoond.columns:
                if 'Uren' in col:
                    uren_kolom = col
                    break
            
            if uren_kolom is None:
                st.error("Geen uren kolom gevonden in de data.")
                st.stop()
            
            # Aggregate hours per bewakingscode per project
            data_met_bewakingscode = data_opgeschoond[data_opgeschoond['bewakingscode'].notna()].copy()
            
            # Ensure hours are numeric
            data_met_bewakingscode[uren_kolom] = pd.to_numeric(
                data_met_bewakingscode[uren_kolom], errors='coerce'
            ).fillna(0)
            
            # Group and aggregate
            uren_per_bewakingscode = data_met_bewakingscode.groupby(
                ['bewakingomschrijving', 'projectcode']
            )[uren_kolom].sum().reset_index()
            
            # Pivot the table
            uren_pivot = uren_per_bewakingscode.pivot_table(
                index='projectcode',
                columns='bewakingomschrijving',
                values=uren_kolom,
                aggfunc='sum',
                fill_value=0
            ).reset_index()
            
            # Rename columns to add '_uren'
            nieuwe_kolomnamen = ['projectcode']
            for col in uren_pivot.columns[1:]:  # Skip projectcode
                nieuwe_kolomnamen.append(f"{col}_uren")
            
            uren_pivot.columns = nieuwe_kolomnamen
        
        # Display results
        st.subheader("📊 Resultaten")
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Aantal projecten", len(uren_pivot))
        with col2:
            st.metric("Aantal bewakingscodes", len(uren_pivot.columns) - 1)
        with col3:
            totaal_uren = uren_pivot.iloc[:, 1:].sum().sum()
            st.metric("Totaal aantal uren", f"{totaal_uren:.2f}")
        
        # Show the data
        st.dataframe(uren_pivot, use_container_width=True)
        
        # Download buttons
        st.subheader("📥 Download Resultaten")
        
        # Convert to CSV strings
        if output_format == "Nederlands (puntkomma)":
            csv_data = uren_pivot.to_csv(sep=';', decimal=',', index=False, encoding='utf-8')
            file_name = "uren_per_bewakingscode.csv"
            mime_type = "text/csv"
        else:
            csv_data = uren_pivot.to_csv(sep=',', decimal='.', index=False, encoding='utf-8')
            file_name = "UK_US_uren_per_bewakingscode.csv"
            mime_type = "text/csv"
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=file_name,
                mime=mime_type
            )
        
        with col2:
            # Also provide Excel format
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                uren_pivot.to_excel(writer, index=False, sheet_name='Resultaten')
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name="uren_per_bewakingscode.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        
        # Show hours per bewakingscode
        st.subheader("📈 Uren per Bewakingscode (Totaal)")
        
        # Calculate totals per bewakingscode
        totaal_per_code = []
        for col in uren_pivot.columns[1:]:  # Skip projectcode
            totaal_uren = uren_pivot[col].sum()
            bewakingscode = col.replace('_uren', '')
            totaal_per_code.append({
                'Bewakingscode': bewakingscode,
                'Totaal Uren': totaal_uren
            })
        
        totaal_df = pd.DataFrame(totaal_per_code)
        st.dataframe(totaal_df, use_container_width=True)
        
        # Visualization
        st.subheader("📊 Visualisatie")
        
        # Bar chart of hours per bewakingscode
        if not totaal_df.empty:
            st.bar_chart(totaal_df.set_index('Bewakingscode'))
        
    else:
        st.warning("Geen geldige bestanden gevonden om te verwerken.")
        
        if niet_behandeld:
            st.error("De volgende bestanden konden niet worden verwerkt:")
            for bestand in niet_behandeld:
                st.write(f"- {bestand}")
            st.info("Controleer of de bestanden het juiste formaat hebben (zie instructies in de sidebar).")

# Show vertaaltabel
with st.expander("🔍 Bekijk Vertaaltabel (Specificatiecode → Bewakingscode)"):
    st.dataframe(vertaaltabel, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Versie 1.03 - duplicate detectie toegevoegd - 16-12-2025")
