from logger import setup_logger
logger = setup_logger(name='script2_logger', log_file='logs/script2.log')

import pandas as pd
import os
import time
from scraping_lib import check_password_account
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 5

def read_input_file(input_file):
    logger.info('Reading input file...')
    columns = ["RUTF", "Clave"]
    df = pd.read_excel(input_file, sheet_name=0, usecols=columns)
    return df[columns]

def write_output_file(output_dir, results_df):
    logger.info('Writing output file...')
    output_file_name = "check_passwords.xlsx"
    output_path = os.path.join(output_dir, output_file_name)
    results_df.to_excel(output_path, index=False)
    logger.info(f"Output written to {output_path}")

def check_account(username, password, retries=3):
    for attempt in range(retries):
        try:
            result = check_password_account(username, password)
            logger.info(f"Data retrieved for {username}")
            return result
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {username}: {e}")
            time.sleep(2)
    logger.error(f"Failed to retrieve data for {username} after {retries} attempts.")
    return {"RUTF": username, "ESTADO": "Error"}

def process_accounts(input_file, output_dir):
    df = read_input_file(input_file)
    logger.info('Starting account processing...')
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(check_account, row['RUTF'], row['Clave'])
            for _, row in df.iterrows()
        ]
        for future in as_completed(futures):
            results.append(future.result())

    columns = ["RUTF", "ESTADO"]
    results_df = pd.DataFrame(results)

    for column in columns:
        if column not in results_df.columns:
            results_df[column] = None
    results_df = results_df[columns]

    logger.info("All accounts processed. Writing results...")
    write_output_file(output_dir, results_df)
