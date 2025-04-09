from logger import setup_logger
logger = setup_logger()

import pandas as pd
import os
import time
from scraping_lib import get_ddjj_table
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

MAX_WORKERS = 5

def read_input_file(input_file):
    logger.info('Reading input file...')
    columns = ["RUTF", "Clave"]
    df = pd.read_excel(input_file, sheet_name=0, usecols=columns)
    return df[columns]

def write_output_file(output_dir, results_df):
    logger.info('Writing output file...')
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file_name = f"ddjj_table_{timestamp}.xlsx"
    output_file = os.path.join(output_dir, output_file_name)
    results_df.to_excel(output_file, index=False)

def get_ddjj_table_from_sii(username, password, retries=3):
    for attempt in range(retries):
        try:
            result = get_ddjj_table(username, password)
            logger.info(f"Data fetched for {username}")
            return result
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed for {username}: {e}")
            time.sleep(2)
    logger.error(f"Failed to fetch data for {username} after {retries} retries.")
    return {"RUTF": username, "ESTADO": "Error"}

def process_accounts(input_file, output_dir):
    df = read_input_file(input_file)
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(get_ddjj_table_from_sii, row['RUTF'], row['Clave']) for _, row in df.iterrows()]
        for future in as_completed(futures):
            results.append(future.result())

    # Collect dynamic keys
    dj_ano_keys = set()
    for r in results:
        for k in r:
            if '-' in k and all(p.isdigit() for p in k.split('-')):
                dj_ano_keys.add(k)

    sorted_keys = sorted(dj_ano_keys, key=lambda x: (x.split("-")[0], -int(x.split("-")[1])))

    columns = ["RUTF", "NOMBRE", "CORREO"] + sorted_keys
    results_df = pd.DataFrame(results)

    for col in columns:
        if col not in results_df.columns:
            results_df[col] = None

    results_df = results_df[columns]
    logger.info("DDJJ results processed.")
    write_output_file(output_dir, results_df)
