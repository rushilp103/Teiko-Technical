import sqlite3
import pandas as pd
import os

DB_name = 'clinical_trial.db'
csv_file = 'cell-count.csv'

# Part 1
def initialize_database():
    with sqlite3.connect(DB_name) as con:
        cursor = con.cursor()

        # Clean up existing tables if they exist to avoid conflicts
        cursor.execute("DROP TABLE IF EXISTS projects")
        cursor.execute("DROP TABLE IF EXISTS subjects")
        cursor.execute("DROP TABLE IF EXISTS samples")

        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute('''
            CREATE TABLE projects (
                project TEXT PRIMARY KEY
            )
        ''')

        cursor.execute('''
            CREATE TABLE subjects (
                subject TEXT PRIMARY KEY,
                project TEXT,
                condition TEXT,
                age INTEGER,
                sex TEXT,
                treatment TEXT,
                response TEXT,
                sample_type TEXT,
                FOREIGN KEY (project) REFERENCES projects(project)
            )
        ''')

        cursor.execute('''
            CREATE TABLE samples (
                sample TEXT PRIMARY KEY,
                subject TEXT,
                time_from_treatment_start INTEGER,
                b_cell INTEGER,
                cd8_t_cell INTEGER,
                cd4_t_cell INTEGER,
                nk_cell INTEGER,
                monocyte INTEGER,
                FOREIGN KEY (subject) REFERENCES subjects(subject)
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

        projects_cols = ['project']
        projects_cols = df[projects_cols].drop_duplicates()
       
        subjects_cols = ['subject', 'project', 'condition', 'age', 'sex', 'treatment', 'response', 'sample_type']
        subjects_cols = df[subjects_cols].drop_duplicates(subset=['subject'])

        samples_cols = ['sample', 'subject', 'time_from_treatment_start', 'b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']
        samples_cols = df[samples_cols].drop_duplicates(subset=['sample'])

        try:
            projects_cols.to_sql('projects', con, if_exists='append', index=False)
            subjects_cols.to_sql('subjects', con, if_exists='append', index=False)
            samples_cols.to_sql('samples', con, if_exists='append', index=False)
            print("Data loaded successfully into the database.")
        except sqlite3.IntegrityError as ie:
            print(f"Integrity error: {ie}")
        except Exception as e:
            print(f"Error loading data into database: {e}")

# Part 2
def get_frequency():
    with sqlite3.connect(DB_name) as con:
        query = '''
            SELECT 
                samples.sample, samples.b_cell, samples.cd8_t_cell, samples.cd4_t_cell, samples.nk_cell, samples.monocyte,
                subjects.subject, subjects.condition, subjects.treatment, subjects.response, subjects.sample_type
            FROM samples
            JOIN subjects ON samples.subject = subjects.subject
        '''
        df = pd.read_sql_query(query, con)

        population_cols = ['b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']
        df['total_count'] = df[population_cols].sum(axis=1)

        metadata_cols = ['sample', 'subject', 'condition', 'treatment', 'response', 'sample_type']

        df_long = df.melt(
            id_vars = metadata_cols + ['total_count'],
            value_vars = population_cols,
            var_name = 'population',
            value_name = 'count'
        )

        df_long['percentage'] = (df_long['count'] / df_long['total_count']) * 100

        return df_long

# Part 3

if __name__ == "__main__":
    initialize_database()
    load_data(csv_file)
    get_frequency()