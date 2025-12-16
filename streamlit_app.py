"""Streamlit app voor specificatie-uren naar bewakingscode conversie
Refactored version with improved structure and maintainability
"""

import streamlit as st
import pandas as pd
import io
import warnings
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

warnings.filterwarnings('ignore')


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class AppConfig:
    """Application configuration and constants"""
    PAGE_TITLE = "Specificatie Uren naar Bewakingscode"
    PAGE_ICON = "📊"
    VERSION = "2.0 - Refactored - 16-12-2025"
    
    # CSV parsing settings
    CSV_SEPARATOR = ';'
    DECIMAL_SEPARATOR = ','
    SKIP_ROWS = 3
    # Not sure of exact encodings needed, but these worked before
    ENCODINGS = ['cp1252', 'latin-1', 'iso-8859-1', 'utf-8']
    
    # Project code extraction (text that precedes the code)
    PROJECT_PREFIX = 'SPECIFICATIE UREN van project: '
    
    # Column names
    COL_DESCRIPTION = 'Omschrijving'
    COL_SPECIFICATION = 'specificatiecode'
    COL_PROJECT = 'project'
    COL_PROJECT_CODE = 'projectcode'
    COL_MONITORING_CODE = 'bewakingscode'
    COL_MONITORING_DESC = 'bewakingomschrijving'


@dataclass
class ProcessingResult:
    """Result of file processing operation"""
    success: bool
    filename: str
    message: str
    data: Optional[pd.DataFrame] = None
    project_code: Optional[str] = None


# ============================================================================
# TRANSLATION TABLE
# ============================================================================

# Vertaaltabel specificatiecode -> bewakingscode

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
# FILE PROCESSING
# ============================================================================

class CSVProcessor:
    """Handles CSV file reading and parsing"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    def read_file(self, file_bytes: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[str]]:
        """
        Attempts to read CSV file with multiple encoding fallbacks
        
        Returns:
            Tuple of (dataframe, project_code, encoding_used)
        """
        for encoding in self.config.ENCODINGS:
            try:
                # Read CSV data
                data = pd.read_csv(
                    io.BytesIO(file_bytes),
                    sep=self.config.CSV_SEPARATOR,
                    decimal=self.config.DECIMAL_SEPARATOR,
                    encoding=encoding,
                    skiprows=self.config.SKIP_ROWS,
                    on_bad_lines='warn'
                )
                
                # Extract project code from first line
                project_code = self._extract_project_code(file_bytes, encoding)
                
                return data, project_code, encoding
                
            except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError):
                continue
        
        return None, None, None
    
    def _extract_project_code(self, file_bytes: bytes, encoding: str) -> str:
        """Extracts project code from first line of file"""
        content = file_bytes.decode(encoding, errors='ignore')
        first_line = content.split('\n')[0] if '\n' in content else content
        
        if ';' in first_line:
            project_code_raw = first_line.strip().split(';')[0]
        else:
            project_code_raw = first_line.strip()
        
        return project_code_raw
    
    def validate_format(self, data: pd.DataFrame) -> bool:
        """Validates that the CSV has the expected format"""
        if data is None or data.empty:
            return False
        
        if len(data.columns) < 2:
            return False
        
        return data.columns[1] == self.config.COL_DESCRIPTION


class FileProcessor:
    """Orchestrates the processing of uploaded files"""
    
    def __init__(self, config: AppConfig, csv_processor: CSVProcessor):
        self.config = config
        self.csv_processor = csv_processor
        self.processed_projects = set()
    
    def process_file(self, uploaded_file) -> ProcessingResult:
        """Processes a single uploaded file"""
        filename = uploaded_file.name
        
        try:
            file_bytes = uploaded_file.getvalue()
            data, project_code_raw, encoding = self.csv_processor.read_file(file_bytes, filename)
            
            if data is None or data.empty:
                return ProcessingResult(
                    success=False,
                    filename=filename,
                    message="Kon CSV niet lezen met ondersteunde encodings of bestand is leeg"
                )
            
            # Validate format
            if not self.csv_processor.validate_format(data):
                col_name = data.columns[1] if len(data.columns) >= 2 else 'geen tweede kolom'
                return ProcessingResult(
                    success=False,
                    filename=filename,
                    message=f"Ongeldig formaat (tweede kolom is niet '{self.config.COL_DESCRIPTION}', gevonden: {col_name})"
                )
            
            # Clean project code and check for duplicates
            project_code_clean = project_code_raw.replace(self.config.PROJECT_PREFIX, '')
            
            if project_code_clean in self.processed_projects:
                return ProcessingResult(
                    success=False,
                    filename=filename,
                    message=f"Projectcode {project_code_clean} is al eerder verwerkt. Bestand wordt overgeslagen."
                )
            
            # Add project code to data
            data[self.config.COL_PROJECT] = project_code_raw
            self.processed_projects.add(project_code_clean)
            
            return ProcessingResult(
                success=True,
                filename=filename,
                message=f"Succesvol verwerkt (Project: {project_code_raw})",
                data=data,
                project_code=project_code_raw
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                filename=filename,
                message=f"Fout - {str(e)}"
            )


# ============================================================================
# DATA TRANSFORMATION
# ============================================================================

class DataTransformer:
    """Handles data transformation and aggregation"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.translation_table = TRANSLATION_TABLE
    
    def transform(self, combined_data: pd.DataFrame) -> pd.DataFrame:
        """Transforms raw data into aggregated monitoring code hours"""
        # Move project column to first position
        cols = [self.config.COL_PROJECT] + [col for col in combined_data.columns if col != self.config.COL_PROJECT]
        data = combined_data[cols].copy()
        
        # Clean project code
        data[self.config.COL_PROJECT_CODE] = data[self.config.COL_PROJECT].str.replace(
            self.config.PROJECT_PREFIX, '', regex=False
        )
        data = data.drop(columns=[self.config.COL_PROJECT])
        
        # Rename first column to specificatiecode
        first_col = data.columns[0]
        if first_col != self.config.COL_SPECIFICATION:
            data = data.rename(columns={first_col: self.config.COL_SPECIFICATION})
        
        # Merge with translation table
        data = pd.merge(
            data,
            self.translation_table,
            on=self.config.COL_SPECIFICATION,
            how='left'
        )
        
        # Find hours column
        hours_col = self._find_hours_column(data)
        if hours_col is None:
            raise ValueError("Geen uren kolom gevonden in de data")
        
        # Aggregate hours
        return self._aggregate_hours(data, hours_col)
    
    def _find_hours_column(self, data: pd.DataFrame) -> Optional[str]:
        """Finds the hours column in the dataframe"""
        for col in data.columns:
            if 'Uren' in col:
                return col
        return None
    
    def _aggregate_hours(self, data: pd.DataFrame, hours_col: str) -> pd.DataFrame:
        """Aggregates hours per monitoring code per project"""
        # Filter rows with monitoring code
        data_with_code = data[data[self.config.COL_MONITORING_CODE].notna()].copy()
        
        # Ensure hours are numeric
        data_with_code[hours_col] = pd.to_numeric(
            data_with_code[hours_col], errors='coerce'
        ).fillna(0)
        
        # Group and aggregate
        hours_per_code = data_with_code.groupby(
            [self.config.COL_MONITORING_DESC, self.config.COL_PROJECT_CODE]
        )[hours_col].sum().reset_index()
        
        # Pivot table
        hours_pivot = hours_per_code.pivot_table(
            index=self.config.COL_PROJECT_CODE,
            columns=self.config.COL_MONITORING_DESC,
            values=hours_col,
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Rename columns to add '_uren' suffix
        new_columns = [self.config.COL_PROJECT_CODE]
        for col in hours_pivot.columns[1:]:
            new_columns.append(f"{col}_uren")
        hours_pivot.columns = new_columns
        
        return hours_pivot


# ============================================================================
# EXPORT UTILITIES
# ============================================================================

class DataExporter:
    """Handles data export in various formats"""
    
    @staticmethod
    def to_csv_dutch(df: pd.DataFrame) -> str:
        """Exports dataframe to Dutch CSV format (semicolon, comma decimal)"""
        return df.to_csv(sep=';', decimal=',', index=False, encoding='utf-8')
    
    @staticmethod
    def to_csv_english(df: pd.DataFrame) -> str:
        """Exports dataframe to English CSV format (comma, dot decimal)"""
        return df.to_csv(sep=',', decimal='.', index=False, encoding='utf-8')
    
    @staticmethod
    def to_excel(df: pd.DataFrame) -> bytes:
        """Exports dataframe to Excel format"""
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Resultaten')
        return buffer.getvalue()


# ============================================================================
# USER INTERFACE
# ============================================================================

class StreamlitUI:
    """Manages Streamlit user interface"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self._setup_page()
    
    def _setup_page(self):
        """Configures page settings"""
        st.set_page_config(
            page_title=self.config.PAGE_TITLE,
            page_icon=self.config.PAGE_ICON,
            layout="wide"
        )
    
    def render_header(self):
        """Renders app header"""
        st.title(f"{self.config.PAGE_ICON} {self.config.PAGE_TITLE} Converter")
        st.markdown("""
        Deze app converteert specificatie-uren CSV-bestanden naar een overzicht per bewakingscode.
        Upload één of meerdere CSV-bestanden met de juiste opmaak.
        """)
    
    def render_sidebar(self) -> str:
        """Renders sidebar and returns selected output format"""
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
            
            return output_format
    
    def render_file_uploader(self):
        """Renders file uploader widget"""
        return st.file_uploader(
            "Upload CSV-bestanden",
            type=['csv', 'CSV'],
            accept_multiple_files=True,
            help="Selecteer één of meerdere CSV-bestanden"
        )
    
    def render_processing_log(self, results: List[ProcessingResult]):
        """Renders processing log"""
        with st.expander("📋 Verwerkingslogboek", expanded=True):
            for result in results:
                status = "[OK]" if result.success else "[ERROR]" if "overgeslagen" not in result.message else "[WAARSCHUWING]"
                st.write(f"{status} {result.filename}: {result.message}")
    
    def render_results(self, df: pd.DataFrame, output_format: str):
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
        self._render_download_buttons(df, output_format)
        
        # Additional statistics
        self._render_statistics(df)
        
        # Visualization
        self._render_visualization(df)
    
    def _render_download_buttons(self, df: pd.DataFrame, output_format: str):
        """Renders download buttons for results"""
        st.subheader("📥 Download Resultaten")
        
        exporter = DataExporter()
        
        col1, col2 = st.columns(2)
        with col1:
            if output_format == "Nederlands (puntkomma)":
                csv_data = exporter.to_csv_dutch(df)
                file_name = "uren_per_bewakingscode.csv"
            else:
                csv_data = exporter.to_csv_english(df)
                file_name = "UK_US_uren_per_bewakingscode.csv"
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=file_name,
                mime="text/csv"
            )
        
        with col2:
            excel_data = exporter.to_excel(df)
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name="uren_per_bewakingscode.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    def _render_statistics(self, df: pd.DataFrame):
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
    
    def _render_visualization(self, df: pd.DataFrame):
        """Renders data visualization"""
        st.subheader("📊 Visualisatie")
        
        # Prepare data for chart
        totals = []
        for col in df.columns[1:]:
            code_name = col.replace('_uren', '')
            totals.append({
                'Bewakingscode': code_name,
                'Totaal Uren': df[col].sum()
            })
        
        totals_df = pd.DataFrame(totals)
        if not totals_df.empty:
            st.bar_chart(totals_df.set_index('Bewakingscode'))
    
    def render_translation_table(self):
        """Renders translation table"""
        with st.expander("🔍 Bekijk Vertaaltabel (Specificatiecode → Bewakingscode)"):
            st.dataframe(TRANSLATION_TABLE, use_container_width=True)
    
    def render_footer(self):
        """Renders app footer"""
        st.markdown("---")
        st.caption(f"Versie {self.config.VERSION}")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    config = AppConfig()
    ui = StreamlitUI(config)
    
    # Render UI components
    ui.render_header()
    output_format = ui.render_sidebar()
    uploaded_files = ui.render_file_uploader()
    
    # Process files if uploaded
    if uploaded_files:
        st.subheader("📁 Geüploade Bestanden")
        st.write(f"Aantal bestanden: {len(uploaded_files)}")
        
        # Initialize processors
        csv_processor = CSVProcessor(config)
        file_processor = FileProcessor(config, csv_processor)
        
        # Process files
        results = []
        valid_data = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Verwerken: {uploaded_file.name} ({i+1}/{len(uploaded_files)})")
            
            result = file_processor.process_file(uploaded_file)
            results.append(result)
            
            if result.success:
                valid_data.append(result.data)
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Verwerking voltooid!")
        
        # Show processing log
        ui.render_processing_log(results)
        
        # Process and display results
        if valid_data:
            success_count = sum(1 for r in results if r.success)
            fail_count = len(results) - success_count
            st.success(f"✅ {success_count} bestand(en) succesvol verwerkt, {fail_count} niet verwerkt")
            
            # Combine and transform data
            combined_data = pd.concat(valid_data, ignore_index=True)
            st.write(f"Totaal aantal rijen: {len(combined_data)}")
            
            with st.spinner("Data aan het verwerken..."):
                transformer = DataTransformer(config)
                result_df = transformer.transform(combined_data)
            
            # Display results
            ui.render_results(result_df, output_format)
        else:
            st.warning("Geen geldige bestanden gevonden om te verwerken.")
            failed_files = [r.filename for r in results if not r.success]
            if failed_files:
                st.error("De volgende bestanden konden niet worden verwerkt:")
                for filename in failed_files:
                    st.write(f"- {filename}")
                st.info("Controleer of de bestanden het juiste formaat hebben (zie instructies in de sidebar).")
    
    # Show translation table
    ui.render_translation_table()
    ui.render_footer()


if __name__ == "__main__":
    main()
