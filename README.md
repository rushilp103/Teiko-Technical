# Teiko-Technical
This dashboard visualizes and analyzes the clinical data from the ```cell-count.csv``` file. It provides tools for exploring cell population frequencies, performing statistical comparisons between responders and non-responders, and filtering baseline cohort.

## How to Run the Code
Prerequisites:
* Python 3.12+
* ```cell-count.csv``` must be present in the root directory

Installation & Execution:
1. Install Dependencies: Open your terminal/command prompt and run:
```
pip install -r requirements.txt
```
2. Run the Dashboard: Execute the main interactive dashboard file:
```
python app.py
```
3. Access the Dashboard:
* After running the code, look for the "Ports" tab in the bottom panel of the Codespaces editor.
* Find Port 8050
* Click the "Open in Browser" or the forwarded address link to view the dashboard

(If running locally on your own machine, simply visit: http://127.0.0.1:8050/)

# Database Schema & Rationale
The application incorporates a relational database (SQLite) constructed from the raw CSV input. The data is normalized into three primary tables to reduce redundancy, ensuring data integrity and supporting scalability in the future.
## Schema Design
Table 1: ```projects```
* Columns: ```project``` (Primary Key)
* Purpose: This acts as the root entity, ensuring that every subject is assigned to a valid existing project.

Table 2: ```subjects```
* Columns: ```subject``` (Primary Key), ```project``` (Foreign Key), ```age```, ```sex```, ```condition```, ```response```, ```treatment```
* Purpose: This stores the concrete attributes for a specific patient. For example, a patient's age or sex does not change between samples, so storing it here prevents duplication

Table 3: ```samples```
* Columns: ```sample``` (Primary Key), ```subject``` (Foreign Key), ```time_from_treatment_start```, ```b_cell```, ```cd8_t_cell```, ```cd4_t_cell```, ```nk_cell```, ```monocyte```
* Purpose: This stores all the dynamic biological measurements. Since one subject has multiple samples over time, this table will grow fast.

## Rationale & Scalability
* Normalization: If all the data was kept in one large table, the project name and patient demographics would repeat for every sample. As the database continues to grow to contain hundreds of projects, the ```projects``` table allows us to index and filter distinct cohorts instantly without having to scan millions of rows of data.
* Performance: Questions like "How many female non-responders in project 89?" can be quickly answered by querying the small ```subjects``` table rather than scanning the larger ```samples``` table. The ```samples``` table is optimized for biological data, linking back to the ```subjects``` table only when demographic filtering is required.
* Data Integrity: The Foreign Key constraints ensures that you cannot accidently add a sample for a subject that doesn't exist, or a subject for a project that doesn't exist.

# Code Structure
1. ```backend.py``` (Data Layer): Handles extracting, transforming, and loading the data. By isolating data operations from the dashboard code, we can ensure that statistical calculations can be updated without breaking the user interface.
* ```initialize_database()```: Automatically converts the raw CSV into the normalized SQL structure on startup
* ```load_data(csv_file)```: Parses the raw CSV, cleans the column names, and populates the three database tables
* ```get_frequency()```: Collects cell count data to calculate the relative frequency of each cell type per sample
* ```get_statistics()```: This is the core statistical analysis engine. It filters for Melanoma/Miraclib/PBMC samples, checks for normality using Shapiro-Wilk, and dynamically applies the correct statistical test (Welch's t-test or Mann-Whitney U) to compare Responders vs. Non-Responders
* ```get_specific_subset_data()```: Retrieves the baseline (```time_from_treatment_start``` = 0) cohort data for part 4

2. ```app.py``` (Dashboard): Defines the user interface and interaction. This file focuses solely on the user experience. It uses a modular layout to guide the user through a logical analysis workflow from frequency to statistics to baseline results.
* Modular layout: The dashboard is divided into three distinct tabs to guide the user through the analysis workflow
* Interactive Callbacks: Dropdowns and multi-select filters trigger real-time updates for graphs and tables without reloading the page
* Formatting: Enforces user-friendly display logic while keeping the underlying data precise for calculations