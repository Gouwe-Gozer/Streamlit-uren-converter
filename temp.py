def extract_project_code(file_bytes: bytes, encoding: str) -> str:
    """Extracts project code from first line of file"""

    content = file_bytes.decode(encoding, errors='ignore')
    project_code_raw = content.strip().split(';')[0]
    
    return project_code_raw


def extract_project_code(file_bytes: bytes, encoding: str) -> str:
    """Extracts project code value from first line of the csv file (Excel cell A1)"""
    # Decode file
    content = file_bytes.decode(encoding, errors='ignore')
    # Get first line (\n separates rows in raw content) ## MWIJNAN 20251219 Unnecessary: split(';')[0] can also be directly applied on content
    first_line = content.split('\n')[0] if '\n' in content else content

    # From the file get the first cell (; separates columns in semicolon CSVs)
    # Separating the first line (column) from the rest is not necessary, as the first cell is located there
    project_code_raw = first_line.strip().split(';')[0]
    
    return project_code_raw