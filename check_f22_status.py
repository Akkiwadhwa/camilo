from logger import setup_logger
logger = setup_logger()

import pandas as pd
import os
import time
from scraping_lib import check_f22_status
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

MAX_WORKERS = 12

def read_input_file(input_file):
    logger.info('Reading input file...')
    columns = ["RUTF", "Clave"]
    df = pd.read_excel(input_file, sheet_name=0, usecols=columns)
    return df[columns]

def write_output_file(output_dir, results_df, year):
    logger.info('Writing output file...')
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file_name = f"f22_status_{year}_{timestamp}.xlsx"
    output_file = os.path.join(output_dir, output_file_name)
    results_df.to_excel(output_file, index=False)

def process_account(username, password, year, retries=3):
    for attempt in range(retries):
        try:
            data = check_f22_status(username, password, year)
            logger.info(f"Data retrieved for {username}")
            return data
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {username}: {e}")
            time.sleep(2)
    logger.error(f"Failed to retrieve data for {username} after {retries} attempts.")
    return {
        "RUTF": username, 
        "NOMBRE": "Error", 
        "SITUACION": "Error", 
        "FOLIO": "Error", 
        "MONTO DEVOLUCION": "Error", 
        "MONTO A PAGAR": "Error"
    }

def process_accounts(input_file, output_dir, year):
    df = read_input_file(input_file)
    logger.info('Starting processing of accounts...')
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_account, row['RUTF'], row['Clave'], year)
                   for _, row in df.iterrows()]
        for future in as_completed(futures):
            results.append(future.result())

    columns = ["RUTF", "NOMBRE", "SITUACION", "FOLIO", "MONTO DEVOLUCION", "MONTO A PAGAR"]
    results_df = pd.DataFrame(results)

    for col in columns:
        if col not in results_df.columns:
            results_df[col] = None
    results_df = results_df[columns]

    logger.info("All accounts processed. Writing results...")
    write_output_file(output_dir, results_df, year)
