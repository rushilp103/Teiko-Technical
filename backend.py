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

        projects_cols = df[['project']].drop_duplicates()
        subjects_cols = df[['subject', 'project', 'condition', 'age', 'sex', 'treatment', 'response', 'sample_type']].drop_duplicates(subset=['subject'])
        samples_cols = df[['sample', 'subject', 'time_from_treatment_start', 'b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']].drop_duplicates(subset=['sample'])

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

        df_long['percentage'] = ((df_long['count'] / df_long['total_count']) * 100).round(2)

        df_long = df_long.sort_values(by=['sample', 'population'])

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
    populations = subset['population'].unique()
    num_tests = len(populations)

    for population in populations:
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

        # Normality test using Shapiro-Wilk
        is_normal = False
        if num_responders >= 3 and num_non_responders >= 3:
            _, p_responders = stats.shapiro(responders)
            _, p_non_responders = stats.shapiro(non_responders)
            is_normal = (p_responders > 0.05) and (p_non_responders > 0.05)

        p_value = None
        test_used = "N/A"
        effect_size = None

        if num_responders > 1 and num_non_responders > 1:
            if is_normal:
                # If normal, use Welch's t-test
                t_stat, p_value = stats.ttest_ind(responders, non_responders, equal_var=False)
                test_used = "Welch's t-test"

                # Calculate Cohen's d
                n1, n2 = num_responders, num_non_responders
                var1 = np.var(responders, ddof=1)
                var2 = np.var(non_responders, ddof=1)
                std_pooled = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
                effect_size = (responder_mean - non_responder_mean) / std_pooled if std_pooled > 0 else 0
            else:
                # If not normal, use Mann-Whitney U test
                u_stat, p_value = stats.mannwhitneyu(responders, non_responders, alternative='two-sided')
                test_used = "Mann-Whitney U"

                # Calculate rank-biserial correlation
                effect_size = 1 - (2 * u_stat) / (num_responders * num_non_responders) if (num_responders * num_non_responders) > 0 else 0
        
        if p_value is not None:
            adjusted_p_value = min(p_value * num_tests, 1.0)
        else:
            adjusted_p_value = None

        if adjusted_p_value is not None:
            significant = adjusted_p_value < 0.05
        else:
            significant = False

        statistical_results.append({
            'population': population,
            'test used': test_used,
            'p-value': round(p_value, 4) if p_value is not None else None,
            'adjusted p-value': round(adjusted_p_value, 4) if adjusted_p_value is not None else None,
            'significant': significant,
            'effect size': round(effect_size, 4) if effect_size is not None else None,
            'responder mean': round(responder_mean, 2),
            'responder median': round(responder_median, 2),
            'non-responder mean': round(non_responder_mean, 2),
            'non-responder median': round(non_responder_median, 2)
        })
    
    return subset, pd.DataFrame(statistical_results)

# Part 4
def get_specific_subset_data():
    with sqlite3.connect(DB_name) as con:
        query = '''
            SELECT subjects.project, subjects.response, subjects.sex, samples.sample
            FROM samples
            JOIN subjects ON samples.subject = subjects.subject
            WHERE subjects.condition = 'melanoma'
              AND subjects.sample_type = 'PBMC'
              AND subjects.treatment = 'miraclib'
              AND samples.time_from_treatment_start = 0
        '''
        df = pd.read_sql_query(query, con)
    return df

# Average b-cell question
def get_average_b_cell():
    with sqlite3.connect(DB_name) as con:
        query = '''
            SELECT AVG(samples.b_cell)
            FROM samples
            JOIN subjects ON samples.subject = subjects.subject
            WHERE subjects.condition = 'melanoma'
              AND subjects.sex = 'M'
              AND subjects.response = 'yes'
              AND samples.time_from_treatment_start = 0
        '''
        result = pd.read_sql_query(query, con)
    return result.iloc[0, 0]

if __name__ == "__main__":
    initialize_database()
    load_data(csv_file)
    print(get_frequency())
    print(get_statistics())
    print(get_specific_subset_data())
    print(f"Average b_cell count: {get_average_b_cell()}")