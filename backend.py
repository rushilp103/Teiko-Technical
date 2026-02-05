import sqlite3
import pandas as pd
import numpy as np
import os
import scipy.stats as stats

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
def get_statistics():
    df = get_frequency()

    subset = df[
        (df['condition'].str.lower() == 'melanoma') &
        (df['treatment'].str.lower() == 'miraclib') &
        (df['sample_type'].str.upper() == 'PBMC')
    ]

    statistical_results = []
    num_tests = len(subset['population'].unique())

    for population in subset['population'].unique():
        population_data = subset[subset['population'] == population]

        responders = population_data[population_data['response'].str.lower() == 'yes']['percentage']
        non_responders = population_data[population_data['response'].str.lower() == 'no']['percentage']

        num_responders, num_non_responders = len(responders), len(non_responders)

        # Calculate means and medians
        if num_responders > 0 and num_non_responders > 0:
            responder_mean = np.mean(responders)
            responder_median = np.median(responders)
            non_responder_mean = np.mean(non_responders)
            non_responder_median = np.median(non_responders)
        else:
            responder_mean = responder_median = non_responder_mean = non_responder_median = 0

        # Normality test
        is_normal = False
        if num_responders >= 3 and num_non_responders >= 3:
            _, p_responders = stats.shapiro(responders)
            _, p_non_responders = stats.shapiro(non_responders)
            is_normal = (p_responders > 0.05) and (p_non_responders > 0.05)

        p_value = None
        test_used = "N/A"

        if num_responders > 1 and num_non_responders > 1:
            if is_normal:
                _, p_value = stats.ttest_ind(responders, non_responders, equal_var=False)
                test_used = "t-test"
            else:
                _, p_value = stats.mannwhitneyu(responders, non_responders, alternative='two-sided')
                test_used = "Mann-Whitney U"
        
        if p_value is not None:
            adjusted_p_value = min(p_value * num_tests, 1.0)
        else:
            adjusted_p_value = None

        if adjusted_p_value is not None:
            significance = adjusted_p_value < 0.05
        else:
            significance = False

        statistical_results.append({
            'population': population,
            'test used': test_used,
            'p-value': p_value,
            'adjusted p-value': adjusted_p_value,
            'significant': significance,
            'responder mean': round(responder_mean, 2),
            'responder median': round(responder_median, 2),
            'non-responder mean': round(non_responder_mean, 2),
            'non-responder median': round(non_responder_median, 2)
        })
    
    return subset, pd.DataFrame(statistical_results)


if __name__ == "__main__":
    initialize_database()
    load_data(csv_file)
    get_frequency()
    get_statistics()
