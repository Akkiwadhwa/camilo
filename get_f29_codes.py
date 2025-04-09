from logger import setup_logger
logger = setup_logger()

import pandas as pd
import os
import time
from scraping_lib import scrape_data_for_account
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

MAX_WORKERS = 5

def read_input_file(input_file):
    logger.info('Reading input file...')
    df = pd.read_excel(input_file, sheet_name=0, usecols=["RUTF", "Clave"])
    return df

def write_output_file(output_dir, results_df, month, year):
    logger.info('Writing output file...')
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = os.path.join(output_dir, f"data_{month}_{year}_{timestamp}.xlsx")
    results_df.to_excel(output_file, index=False)

def process_account(username, password, year, month, target_codes, retries=3):
    for attempt in range(retries):
        try:
            data = scrape_data_for_account(username, password, year, month, target_codes)
            logger.info(f"Scraped successfully for {username}")
            return data
        except Exception as e:
            logger.warning(f"Retry {attempt+1} failed for {username}: {e}")
            time.sleep(2)
    logger.error(f"Failed for {username}")
    return {"RUTF": username, "NOMBRE": "Error", "DIRECCION": "Error", "CORREO": "Error", "FOLIO": "Error", "RETENCION": "Error"}

def process_accounts(input_file, output_dir, month, year, target_codes):
    df = read_input_file(input_file)
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_account, row['RUTF'], row['Clave'], year, month, target_codes)
                   for _, row in df.iterrows()]
        for future in as_completed(futures):
            results.append(future.result())

    base_columns = ["RUTF", "NOMBRE", "DIRECCION", "CORREO", "FOLIO", "RETENCION"]
    results_df = pd.DataFrame(results)
    for col in base_columns + target_codes:
        if col not in results_df.columns:
            results_df[col] = None
    results_df = results_df[base_columns + target_codes]

    logger.info("Script 4 processing done.")
    write_output_file(output_dir, results_df, month, year)
