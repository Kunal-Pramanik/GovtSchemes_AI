import pandas as pd
import numpy as np
import os

def main():
    print("Loading data...")
    # There are two files in the folder: schemes_data.csv and schemes2_data.csv
    # The user was viewing schemes2_data.csv, let's load it if it exists
    input_file = 'schemes2_data.csv' if os.path.exists('schemes2_data.csv') else 'schemes_data.csv'
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows from {input_file}.")
    
    # Drop completely empty rows
    df.dropna(how='all', inplace=True)
    
    # Fill NaN with empty string
    df = df.fillna("")
    
    # Construct combined text
    combined = []
    
    for idx, row in df.iterrows():
        # Clean text by removing excess structural whitespaces
        name = str(row.get('Scheme Name', '')).strip()
        state = str(row.get('State', '')).strip()
        ministry = str(row.get('Nodal Ministry', '')).strip()
        details = str(row.get('Details', '')).strip()
        elig = str(row.get('Eligibility Criteria', '')).strip()
        bens = str(row.get('Benefits', '')).strip()
        app_proc = str(row.get('Application Process', '')).strip()
        
        # Build block
        doc = f"Scheme Name: {name}\n"
        if state and state.lower() != 'nan':
            doc += f"State: {state}\n"
        if ministry and ministry.lower() != 'nan':
            doc += f"Ministry: {ministry}\n"
        if details:
            doc += f"Details: {details}\n"
        if elig:
            doc += f"Eligibility Criteria: {elig}\n"
        if bens:
            doc += f"Benefits: {bens}\n"
        if app_proc:
            doc += f"Application Process: {app_proc}\n"
            
        combined.append(doc)
        
    df['combined_text'] = combined
    
    # Save cleaned file
    output_file = 'myscheme_cleaned.csv'
    df.to_csv(output_file, index=False)
    print(f"Data successfully cleaned and saved to {output_file}.")

if __name__ == "__main__":
    main()
