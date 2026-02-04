import sqlite3
import pandas as pd
import os

DB_name = 'clinical_trial.db'
csv_file = 'cell-count.csv'

def initialize_database():
    with sqlite3.connect(DB_name) as con:
        cursor = con.cursor()

        # Clean up existing tables if they exist to avoid conflicts
        cursor.execute("DROP TABLE IF EXISTS cell_counts")
        cursor.execute("DROP TABLE IF EXISTS samples")

        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute('''
            CREATE TABLE samples (
                sample TEXT PRIMARY KEY,
                project TEXT,
                subject TEXT,
                condition TEXT,
                age INTEGER,
                sex TEXT,
                treatment TEXT,
                response TEXT,
                sample_type TEXT,
                time_from_treatment_start INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE cell_counts (
                sample TEXT PRIMARY KEY,
                b_cell INTEGER,
                cd8_t_cell INTEGER,
                cd4_t_cell INTEGER,
                nk_cell INTEGER,
                monocyte INTEGER,
                FOREIGN KEY (sample) REFERENCES samples(sample)
            )
        ''')
    
    print(f"Database '{DB_name}' initialized.")

def load_data(csv_file):
    if not os.path.exists(csv_file):
        print(f"CSV file '{csv_file}' not found.")
        return

    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    with sqlite3.connect(DB_name) as con:
        con.execute("PRAGMA foreign_keys = ON;")

        samples_cols = ['sample', 'project', 'subject', 'condition', 'age', 'sex', 'treatment', 'response', 'sample_type', 'time_from_treatment_start']
        df_samples = df[samples_cols].drop_duplicates(subset=['sample'])
       
        cell_counts_cols = ['sample', 'b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']
        df_cell_counts = df[cell_counts_cols].drop_duplicates(subset=['sample'])

        try:
            df_samples.to_sql('samples', con, if_exists='append', index=False)
            df_cell_counts.to_sql('cell_counts', con, if_exists='append', index=False)
            print("Data loaded successfully into the database.")
        except sqlite3.IntegrityError as ie:
            print(f"Integrity error: {ie}")
        except Exception as e:
            print(f"Error loading data into database: {e}")

if __name__ == "__main__":
    initialize_database()
    load_data(csv_file)