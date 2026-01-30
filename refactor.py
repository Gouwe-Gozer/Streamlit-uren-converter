"""Streamlit app voor specificatie-uren naar bewakingscode conversie
"""

import streamlit as st
import pandas as pd
import io
import warnings
from typing import List, Optional

warnings.filterwarnings('ignore')

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

PAGE_TITLE = "Specificatie Uren naar Bewakingscode"
PAGE_ICON = "📊"
VERSION = "2.1 - Reduced abstratction/simplification refactor- 19-12-2025"

# CSV parsing settings
CSV_SEPARATOR = ';'
DECIMAL_SEPARATOR = ','
SKIP_ROWS = 3
ENCODINGS = ['cp1252', 'latin-1', 'iso-8859-1', 'utf-8']
# -- The project code shares its cell with this line of text
PROJECT_PREFIX = 'SPECIFICATIE UREN van project: '

# Column names
COL_DESCRIPTION = 'Omschrijving'
COL_SPECIFICATION = 'specificatiecode'
COL_PROJECT = 'project'
COL_PROJECT_CODE = 'projectcode'
COL_MONITORING_CODE = 'bewakingscode'
COL_MONITORING_DESC = 'bewakingomschrijving'

# Translation table
# -- Regrouping from specificatie- to bewakingscode occurs based on this table
TRANSLATION_TABLE = pd.DataFrame({
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

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def read_csv_file(file_bytes: bytes) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """Attempts to read CSV file with multiple encoding fallbacks as I was unsure of the encoding used"""
    for encoding in ENCODINGS:
        try:
            data = pd.read_csv(
                io.BytesIO(file_bytes),
                sep=CSV_SEPARATOR,
                decimal=DECIMAL_SEPARATOR,
                encoding=encoding,
                skiprows=SKIP_ROWS,
                on_bad_lines='warn'
            )
            
            # Extract project code from first line
            project_code = extract_project_code(file_bytes, encoding)
            
            return data, project_code
            
        except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError):
            continue
    
    return None, None

def extract_project_code(file_bytes: bytes, encoding: str) -> str:
    """Extracts project code from first line of file (Excel cell A1)"""
    # Decode file
    content = file_bytes.decode(encoding, errors='ignore')
    # Get first line (\n separates rows in raw content) ## MWIJNAN 20251219 Unnecessary: split(';')[0] can also be directly applied on content
    first_line = content.split('\n')[0] if '\n' in content else content
    # From first row, get first cell (; separates columns in semicolon CSVs)
    project_code_raw = first_line.strip().split(';')[0]
    
    return project_code_raw

def validate_csv_format(data: pd.DataFrame) -> bool:
    """Validates that the CSV has the expected format"""
    if data is None or data.empty:
        return False
    
    if len(data.columns) < 2:
        return False
    
    return data.columns[1] == COL_DESCRIPTION

def process_uploaded_file(uploaded_file, processed_projects: set) -> dict:
    """Processes a single uploaded file and returns result dictionary"""
    filename = uploaded_file.name
    
    try:
        file_bytes = uploaded_file.getvalue()
        data, project_code_raw = read_csv_file(file_bytes)
        
        if data is None or data.empty:
            return {
                'success': False,
                'filename': filename,
                'message': "Kon CSV niet lezen met ondersteunde encodings of bestand is leeg"
            }
        
        # Validate format
        if not validate_csv_format(data):
            col_name = data.columns[1] if len(data.columns) >= 2 else 'geen tweede kolom'
            return {
                'success': False,
                'filename': filename,
                'message': f"Ongeldig formaat (tweede kolom is niet '{COL_DESCRIPTION}', gevonden: {col_name})"
            }
        
        # Check if project code contains the required prefix
        if not project_code_raw.startswith(PROJECT_PREFIX):
            return {
                'success': False,
                'filename': filename,
                'message': f"Ongeldig formaat. De gevonden waarde '{project_code_raw}' betreft geen projectcode."
            }
        
        # Clean project code and check for duplicates
        project_code_clean = project_code_raw.replace(PROJECT_PREFIX, '')
        
        if project_code_clean in processed_projects:
            return {
                'success': False,
                'filename': filename,
                'message': f"Projectcode {project_code_clean} is al eerder verwerkt. Bestand wordt overgeslagen."
            }
        
        # Add project code to data
        data[COL_PROJECT] = project_code_raw
        processed_projects.add(project_code_clean)
        
        return {
            'success': True,
            'filename': filename,
            'message': f"Succesvol verwerkt (Project: {project_code_raw})",
            'data': data,
            'project_code': project_code_raw
        }
        
    except Exception as e:
        return {
            'success': False,
            'filename': filename,
            'message': f"Fout - {str(e)}"
        }

def transform_data(combined_data: pd.DataFrame) -> pd.DataFrame:
    """Transforms raw data into aggregated monitoring code hours"""
    # Move project column to first position
    cols = [COL_PROJECT] + [col for col in combined_data.columns if col != COL_PROJECT]
    data = combined_data[cols].copy()
    
    # Clean project code
    data[COL_PROJECT_CODE] = data[COL_PROJECT].str.replace(PROJECT_PREFIX, '', regex=False)
    data = data.drop(columns=[COL_PROJECT])
    
    # Rename first column to specificatiecode
    first_col = data.columns[0]
    if first_col != COL_SPECIFICATION:
        data = data.rename(columns={first_col: COL_SPECIFICATION})
    
    # Merge with translation table
    data = pd.merge(
        data,
        TRANSLATION_TABLE,
        on=COL_SPECIFICATION,
        how='left'
    )
    
    # Find hours column
    hours_col = None
    for col in data.columns:
        if 'Uren' in col:
            hours_col = col
            break
    
    if hours_col is None:
        raise ValueError("Geen uren kolom gevonden in de data")
    
    # Filter rows with monitoring code
    data_with_code = data[data[COL_MONITORING_CODE].notna()].copy()
    
    # Ensure hours are numeric
    data_with_code[hours_col] = pd.to_numeric(
        data_with_code[hours_col], errors='coerce'
    ).fillna(0)
    
    # Group and aggregate
    hours_per_code = data_with_code.groupby(
        [COL_MONITORING_DESC, COL_PROJECT_CODE]
    )[hours_col].sum().reset_index()
    
    # Pivot table
    hours_pivot = hours_per_code.pivot_table(
        index=COL_PROJECT_CODE,
        columns=COL_MONITORING_DESC,
        values=hours_col,
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Rename columns to add '_uren' suffix
    new_columns = [COL_PROJECT_CODE]
    for col in hours_pivot.columns[1:]:
        new_columns.append(f"{col}_uren")
    hours_pivot.columns = new_columns
    
    return hours_pivot

def render_sidebar():
    """Renders sidebar and returns selected output format"""
    with st.sidebar:
        st.header("📋 Instructies")
        st.markdown("""
        Het vereiste inputbestandsformaat volgt de conventies van de specificatie-uren export uit Groeneveldsoftware.
                    
        De app ondersteunt export in Excel of CSV-formaat, waarbij de CSV-export zowel een Nederlands (puntkomma) als een Engels/Amerikaans (komma) formaat aanbiedt.
        Voor een Nederlands Office-pakket is het Nederlandse formaat vereist.
        """)

        st.header("⚙️ Instellingen")
        output_format = st.radio(
            "Uitvoerformaat voor CSV:",
            ["Nederlands (puntkomma)", "Engels/Amerikaans (komma)"],
            index=0
        )
        st.markdown("---")
        st.markdown(""" 
                                  
        **Vereist bestandsformaat:**
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
        
        return output_format

def render_processing_log(results: List[dict]):
    """Renders processing log"""
    with st.expander("📋 Verwerkingslogboek", expanded=True):
        for result in results:
            status = "[OK]" if result['success'] else "[ERROR]" if "overgeslagen" not in result['message'] else "[WAARSCHUWING]"
            st.write(f"{status} {result['filename']}: {result['message']}")

def render_results(df: pd.DataFrame, output_format: str):
    """Renders results section with metrics and data"""
    st.subheader("📊 Resultaten")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Aantal projecten", len(df))
    with col2:
        st.metric("Aantal bewakingscodes", len(df.columns) - 1)
    with col3:
        total_hours = df.iloc[:, 1:].sum().sum()
        st.metric("Totaal aantal uren", f"{total_hours:.2f}")
    
    # Data table
    st.dataframe(df, use_container_width=True)
    
    # Download buttons
    render_download_buttons(df, output_format)
    
    # Additional statistics
    render_statistics(df)

def render_download_buttons(df: pd.DataFrame, output_format: str):
    """Renders download buttons for results"""
    st.subheader("📥 Download Resultaten")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if output_format == "Nederlands (puntkomma)":
            csv_data = df.to_csv(sep=';', decimal=',', index=False, encoding='utf-8')
            file_name = "uren_per_bewakingscode.csv"
        else:
            csv_data = df.to_csv(sep=',', decimal='.', index=False, encoding='utf-8')
            file_name = "UK_US_uren_per_bewakingscode.csv"
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=file_name,
            mime="text/csv"
        )
    
    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Resultaten')
        
        st.download_button(
            label="📥 Download Excel",
            data=buffer.getvalue(),
            file_name="uren_per_bewakingscode.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def render_statistics(df: pd.DataFrame):
    """Renders statistics table"""
    st.subheader("📈 Uren per Bewakingscode (Totaal)")
    
    totals = []
    for col in df.columns[1:]:
        total_hours = df[col].sum()
        code_name = col.replace('_uren', '')
        totals.append({
            'Bewakingscode': code_name,
            'Totaal Uren': total_hours
        })
    
    totals_df = pd.DataFrame(totals)
    st.dataframe(totals_df, use_container_width=True)
    
    # Simple visualization
    if not totals_df.empty:
        st.subheader("📊 Visualisatie")
        st.bar_chart(totals_df.set_index('Bewakingscode'))

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application"""
    # Page setup
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout="wide"
    )
    
    # Header
    st.title(f"{PAGE_ICON} {PAGE_TITLE} Converter")
    st.markdown("""
    Deze app converteert Groeneveld specificatie-uren csv-bestanden naar één overzicht met uren per bewakingscode per project.
    Upload één of meerdere CSV-bestanden met de juiste opmaak en download het resultaat in Excel of CSV-formaat.
    Raadpleeg de Vertaaltabel onderaan voor de mapping van specificatiecodes naar bewakingscodes.
    """)
    
    # Sidebar
    output_format = render_sidebar()
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload CSV-bestanden",
        type=['csv'],
        accept_multiple_files=True,
        help="Selecteer één of meerdere CSV-bestanden"
    )
    
    # Process files if uploaded
    if uploaded_files:
        st.subheader("📁 Geüploade Bestanden")
        st.write(f"Aantal bestanden: {len(uploaded_files)}")
        
        # Process files
        results = []
        valid_data = []
        processed_projects = set()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Verwerken: {uploaded_file.name} ({i+1}/{len(uploaded_files)})")
            
            result = process_uploaded_file(uploaded_file, processed_projects)
            results.append(result)
            
            if result['success']:
                valid_data.append(result['data'])
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Verwerking voltooid!")
        
        # Show processing log
        render_processing_log(results)
        
        # Process and display results
        if valid_data:
            success_count = sum(1 for r in results if r['success'])
            fail_count = len(results) - success_count
            st.success(f"✅ {success_count} bestand(en) succesvol verwerkt, {fail_count} niet verwerkt")
            
            # Combine and transform data
            combined_data = pd.concat(valid_data, ignore_index=True)
            st.write(f"Totaal aantal rijen: {len(combined_data)}")
            
            with st.spinner("Data aan het verwerken..."):
                result_df = transform_data(combined_data)
            
            # Display results
            render_results(result_df, output_format)
        else:
            st.warning("Geen geldige bestanden gevonden om te verwerken.")
            failed_files = [r['filename'] for r in results if not r['success']]
            if failed_files:
                st.error("De volgende bestanden konden niet worden verwerkt:")
                for filename in failed_files:
                    st.write(f"- {filename}")
                st.info("Controleer of de bestanden het juiste formaat hebben (zie instructies in de sidebar).")
    
    # Show translation table
    with st.expander("🔍 Bekijk Vertaaltabel (Specificatiecode → Bewakingscode)"):
        st.dataframe(TRANSLATION_TABLE, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.caption(f"Versie {VERSION}")

if __name__ == "__main__":
    main()