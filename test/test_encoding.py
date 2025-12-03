import pandas as pd
import tempfile
import os

# Test what the Streamlit app does
with open('specificatieuren/225028.CSV', 'rb') as f:
    content_bytes = f.read()
    
# Decode with errors='ignore' like Streamlit app does
content = content_bytes.decode('utf-8', errors='ignore')

# Write to temp file with UTF-8 encoding
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp_file:
    tmp_file.write(content)
    tmp_path = tmp_file.name

try:
    # Try to read with UTF-8
    data = pd.read_csv(tmp_path, sep=';', skiprows=3, decimal=',', encoding='utf-8')
    print('UTF-8 reading:')
    print('  Columns:', list(data.columns))
    print('  Second column:', data.columns[1] if len(data.columns) >= 2 else 'N/A')
    print('  Is second column "Omschrijving"?', data.columns[1] == 'Omschrijving' if len(data.columns) >= 2 else 'N/A')
except Exception as e:
    print(f'UTF-8 error: {e}')

# Now try with cp1252 like original script does
try:
    data2 = pd.read_csv('specificatieuren/225028.CSV', sep=';', skiprows=3, decimal=',', encoding='cp1252')
    print('\nCP1252 reading (original script):')
    print('  Columns:', list(data2.columns))
    print('  Second column:', data2.columns[1] if len(data2.columns) >= 2 else 'N/A')
    print('  Is second column "Omschrijving"?', data2.columns[1] == 'Omschrijving' if len(data2.columns) >= 2 else 'N/A')
except Exception as e:
    print(f'CP1252 error: {e}')

finally:
    # Clean up
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)