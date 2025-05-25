from logger import setup_logger
logger = setup_logger()

import pandas as pd
import os
import time
from scraping_lib import scrape_data_for_account
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

MAX_WORKERS = 6

def read_input_file(input_file):
    """Reads the input CSV and returns a DataFrame with username and password."""
    logger.info('Leyendo input...')
    columns = ["RUTF", "Clave"]
    df = pd.read_excel(input_file, sheet_name=0, usecols=columns)
    df = df[columns]
    return df

def write_output_file(output_dir, results_df, month, year):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file_name = f"f29_codes_{month}_{year}_{timestamp}.xlsx"
    output_file = os.path.join(output_dir, output_file_name)
    results_df.to_excel(output_file, index=False)
    return output_file

def process_account(username, password, year, month, target_codes, retries=3):
    """Attempts to scrape data for an account with retry logic."""
    success = False
    scraped_data = None
    for attempt in range(retries):
        try:
            scraped_data = scrape_data_for_account(username, password, year, month, target_codes)
            success = True
            logger.info(f"Datos obtenidos para {username}")
            break
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for account {username}: {e}")
            time.sleep(2)
    if not success:
        logger.error(f"Failed to process account {username} after {retries} attempts.")
        return {"RUTF": username, "NOMBRE": "Error", "DIRECCION": "Error", "CORREO": "Error", "FOLIO": "Error", "RETENCION": "Error", "RETENCION TERCEROS": "Error"}
    return scraped_data

def process_accounts(input_file, output_dir, month, year, target_codes):
    """Processes each account, collects data, and writes to an output file with concurrency."""
    df = read_input_file(input_file)
    logger.info('Input leido...')
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        
        for index, row in df.iterrows():
            username, password = row['RUTF'], row['Clave']
            logger.info(f'Procesando cuenta: {username}')
            
            futures.append(executor.submit(process_account, username, password, year, month, target_codes))
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    columns = ["RUTF", "NOMBRE", "DIRECCION", "CORREO", "FOLIO", "RETENCION", "RETENCION TERCEROS"] + target_codes
    results_df = pd.DataFrame(results)

    for column in columns:
        if column not in results_df.columns:
            results_df[column] = None
    
    results_df = results_df[columns]
    print(results_df)

    output_file = write_output_file(output_dir, results_df, month, year)
    return [output_file]

# if __name__ == "__main__":
#     input_file = r"C:\Users\Camilo Aranda\Desktop\Revisión DDJJ\Input general Socios 12.05.2025.xlsx"
#     output_dir = r"C:\Users\Camilo Aranda\Desktop\Revisión DDJJ"
#     process_accounts(input_file, output_dir, month='Marzo', year='2025', target_codes=['151', '155'])
