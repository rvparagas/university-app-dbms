import os
import datetime
import getpass
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse
import oracledb

app = FastAPI()

# Database connection
ORACLE_USER = os.environ.get("ORACLE_USER")
if ORACLE_USER is None:
    ORACLE_USER = input("Enter Oracle DB username: ")
    os.environ["ORACLE_USER"] = ORACLE_USER
ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD")
if ORACLE_PASSWORD is None:
    ORACLE_PASSWORD = getpass.getpass("Enter Oracle DB password: ")
    os.environ["ORACLE_PASSWORD"] = ORACLE_PASSWORD
ORACLE_DSN = "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(Host=localhost)(Port=1521))(CONNECT_DATA=(SID=orcl12c)))"
conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)

ALLOWED_TABLES = {
    'institutions': 'INSTITUTION',
    'programs': 'PROGRAM',
    'applicants': 'APPLICANT',
    'applications': 'APPLICATION',
    'application_documents': 'APPLICATION_DOCUMENT'
}

PREPARED_QUERIES = {
    '1': """
SELECT DISTINCT Name AS Institution_Name, Accreditation_Status
FROM Institution
ORDER BY Name
""",
    '2': """
SELECT Name AS Program_Name, Minimum_GPA, Duration_Years, Enrollment_Status
FROM Program
WHERE Enrollment_Status = 'Open'
GROUP BY Name, Minimum_GPA, Duration_Years, Enrollment_Status
ORDER BY Name
""",
    '3': """
SELECT DISTINCT First_Name, Last_Name, GPA
FROM Applicant
ORDER BY GPA DESC
""",
    '4': """
SELECT ID AS Application_ID, Applicant_ID, Program_ID, Submission_Date, Status
FROM Application
GROUP BY ID, Applicant_ID, Program_ID, Submission_Date, Status
ORDER BY Submission_Date
""",
    '5': """
SELECT DISTINCT Application_ID, Document_Type, Document_File
FROM Application_Document
ORDER BY Application_ID, Document_Type
""",
    '6': """
SELECT Name AS Program_Name, Minimum_GPA, Enrollment_Status
FROM Program
WHERE Minimum_GPA >= 3.5
GROUP BY Name, Minimum_GPA, Enrollment_Status
ORDER BY Minimum_GPA DESC
""",
    '7': """
SELECT DISTINCT First_Name, Last_Name, GPA
FROM Applicant
WHERE GPA > (SELECT AVG(GPA) FROM Applicant)
ORDER BY GPA DESC
""",
    '8': """
SELECT Status, COUNT(*) AS Application_Count
FROM Application
GROUP BY Status
ORDER BY Application_Count DESC
""",
    '9': """
SELECT i.Name AS Institution_Name,
    ROUND(AVG(a.GPA), 2) AS Avg_GPA,
    MIN(a.GPA) AS Min_GPA,
    MAX(a.GPA) AS Max_GPA,
    ROUND(STDDEV(a.GPA), 2) AS StdDev_GPA
FROM Applicant a
JOIN Institution i ON a.Institution_ID = i.ID
GROUP BY i.Name
ORDER BY Avg_GPA DESC
""",
    '10': """
SELECT p.Name AS Program_Name, ROUND(AVG(a.GPA), 2) AS Program_Avg_GPA
FROM Program p
JOIN Application ap ON p.ID = ap.Program_ID
JOIN Applicant a ON ap.Applicant_ID = a.ID
GROUP BY p.Name
HAVING AVG(a.GPA) > (SELECT AVG(GPA) FROM Applicant)
ORDER BY Program_Avg_GPA DESC
""",
    '11': """
SELECT ap.First_Name, ap.Last_Name, ap.Email
FROM Applicant ap
WHERE NOT EXISTS (
    SELECT 1
    FROM Application a
    JOIN Application_Document d ON a.ID = d.Application_ID
    WHERE d.Document_Type = 'Transcript'
      AND a.Applicant_ID = ap.ID)
ORDER BY ap.Last_Name
""",
    '12': """
SELECT p.Name AS Program_Name, COUNT(a.ID) AS Accepted_Applications
FROM Program p
JOIN Application a ON p.ID = a.Program_ID
WHERE a.Outcome = 'Accepted'
GROUP BY p.Name
HAVING COUNT(a.ID) > 0
ORDER BY Accepted_Applications DESC
""",
    '13': """
SELECT DISTINCT ap.First_Name, ap.Last_Name, p.Name AS Program_Name, a.Status, a.Outcome
FROM Application a
JOIN Applicant ap ON a.Applicant_ID = ap.ID
JOIN Program p ON a.Program_ID = p.ID
WHERE p.Enrollment_Status = 'Open'
  AND a.Outcome IN ('Pending', 'Waitlisted')
ORDER BY ap.Last_Name, p.Name
""",
    '14': """
(SELECT ap.First_Name, ap.Last_Name, ap.Email, p.Name AS Program_Name
FROM Applicant ap
JOIN Application a ON ap.ID = a.Applicant_ID
JOIN Program p ON a.Program_ID = p.ID
WHERE p.Name = 'Computer Science'
    AND a.Outcome = 'Accepted')
MINUS
(SELECT ap.First_Name, ap.Last_Name, ap.Email, p.Name AS Program_Name
FROM Applicant ap
JOIN Application a ON ap.ID = a.Applicant_ID
JOIN Program p ON a.Program_ID = p.ID
WHERE p.Name = 'Business Admin'
    AND a.Outcome = 'Accepted')
ORDER BY Last_Name
""",
    '15': """
SELECT 
    asv.First_Name,
    asv.Last_Name,
    asv.GPA AS Applicant_GPA,
    pov.Program_Name,
    pov.Avg_Applicant_GPA AS Program_Avg_GPA,
    (asv.GPA - pov.Avg_Applicant_GPA) AS GPA_Difference
FROM Applicant_Summary_View asv
JOIN Application a ON asv.Applicant_ID = a.Applicant_ID
JOIN Program_Outcome_View pov ON a.Program_ID = pov.Program_ID
ORDER BY GPA_Difference DESC
""",
    '16': """
SELECT DISTINCT
    asv.First_Name,
    asv.Last_Name,
    adv.Program_Name,
    adv.Document_Type,
    adv.Document_File
FROM Applicant_Summary_View asv
JOIN Application_Document_View adv 
    ON asv.First_Name = adv.First_Name 
   AND asv.Last_Name = adv.Last_Name
JOIN Program_Outcome_View pov 
    ON adv.Program_Name = pov.Program_Name
WHERE pov.Accepted > 0
ORDER BY asv.Last_Name, adv.Program_Name
""",
    '17': """
SELECT 
    pov.Program_Name,
    pov.Total_Applications,
    pov.Accepted,
    ROUND((pov.Accepted / NULLIF(pov.Total_Applications, 0)) * 100, 2) AS Acceptance_Rate,
    pov.Avg_Applicant_GPA
FROM Program_Outcome_View pov
WHERE pov.Total_Applications > 0
ORDER BY Acceptance_Rate DESC, pov.Avg_Applicant_GPA DESC
""",
    '18': """
SELECT 
    asv.Institution_Name,
    COUNT(DISTINCT asv.Applicant_ID) AS Total_Applicants,
    SUM(asv.Accepted_Count) AS Total_Accepted,
    COUNT(DISTINCT adv.Document_File) AS Total_Documents,
    ROUND(COUNT(DISTINCT adv.Document_File) / NULLIF(COUNT(DISTINCT asv.Applicant_ID), 0), 2) AS Avg_Documents_Per_Applicant
FROM Applicant_Summary_View asv
JOIN Application_Document_View adv 
    ON asv.First_Name = adv.First_Name
   AND asv.Last_Name = adv.Last_Name
JOIN Program_Outcome_View pov 
    ON adv.Program_Name = pov.Program_Name
GROUP BY asv.Institution_Name
ORDER BY Total_Accepted DESC
""",
    '19': """
SELECT DISTINCT
    asv.First_Name,
    asv.Last_Name,
    asv.GPA,
    adv.Program_Name,
    pov.Pending
FROM Applicant_Summary_View asv
JOIN Application_Document_View adv 
    ON asv.First_Name = adv.First_Name 
   AND asv.Last_Name = adv.Last_Name
JOIN Program_Outcome_View pov 
    ON adv.Program_Name = pov.Program_Name
WHERE asv.GPA >= 3.7
  AND pov.Pending > 0
ORDER BY asv.GPA DESC, adv.Program_Name
"""
}

RESET_SCRIPT = """
BEGIN EXECUTE IMMEDIATE 'DROP TABLE Application_Document CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE Application CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE Applicant CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE Program CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE Institution CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP VIEW Applicant_Summary_View'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP VIEW Application_Document_View'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP VIEW Program_Outcome_View'; EXCEPTION WHEN OTHERS THEN NULL; END;
/

CREATE OR REPLACE FUNCTION is_date_not_future (
    p_date IN DATE
) RETURN VARCHAR2 DETERMINISTIC IS
BEGIN
    RETURN CASE WHEN p_date > TRUNC(SYSDATE) THEN 'N' ELSE 'Y' END;
END;
/

CREATE TABLE Institution (
    ID NUMBER(10,0) PRIMARY KEY,
    Name VARCHAR2(100) NOT NULL,
    City VARCHAR2(50) NOT NULL,
    State_Province VARCHAR2(50),
    Country VARCHAR2(50) NOT NULL,
    Accreditation_Status VARCHAR2(20) NOT NULL CHECK (Accreditation_Status IN ('Accredited','Provisional','Unaccredited'))
)
/

CREATE TABLE Program (
    ID NUMBER(10,0) PRIMARY KEY,
    Name VARCHAR2(100) NOT NULL,
    Minimum_GPA NUMBER(3,2) NOT NULL CHECK (Minimum_GPA BETWEEN 0.0 AND 4.0),
    Duration_Years NUMBER(2,0) NOT NULL CHECK (Duration_Years > 0),
    Enrollment_Status VARCHAR2(10) NOT NULL CHECK (Enrollment_Status IN ('Open', 'Closed'))
)
/

CREATE TABLE Applicant (
    ID NUMBER(10,0) PRIMARY KEY,
    First_Name VARCHAR2(50) NOT NULL,
    Last_Name VARCHAR2(50) NOT NULL,
    Date_of_Birth DATE NOT NULL,
    Email VARCHAR2(100) NOT NULL UNIQUE,
    Institution_ID NUMBER(10,0) NOT NULL,
    GPA NUMBER(3,2) NOT NULL CHECK (GPA BETWEEN 0.0 AND 4.0),
    not_future_birth_ind VARCHAR2(1) GENERATED ALWAYS AS (CAST(is_date_not_future(Date_of_Birth) AS VARCHAR2(1))) VIRTUAL,
    CONSTRAINT ck_birth_not_future CHECK (not_future_birth_ind = 'Y'),
    CONSTRAINT fk_applicant_institution FOREIGN KEY (Institution_ID) REFERENCES Institution(ID)
)
/

CREATE TABLE Application (
    ID NUMBER(10,0) PRIMARY KEY,
    Applicant_ID NUMBER(10,0) NOT NULL,
    Program_ID NUMBER(10,0) NOT NULL,
    Submission_Date DATE DEFAULT SYSDATE NOT NULL,
    Status VARCHAR2(20) DEFAULT 'Submitted' NOT NULL CHECK (Status IN ('Submitted', 'Under Review', 'Completed')),
    Decision_Date DATE,
    Outcome VARCHAR2(20) NOT NULL CHECK (Outcome IN ('Accepted', 'Rejected', 'Pending', 'Waitlisted')),
    Outcome_Notes VARCHAR2(1000),
    not_future_sub_ind VARCHAR2(1) GENERATED ALWAYS AS (CAST(is_date_not_future(Submission_Date) AS VARCHAR2(1))) VIRTUAL,
    CONSTRAINT ck_sub_not_future CHECK (not_future_sub_ind = 'Y'),
    CONSTRAINT fk_application_applicant FOREIGN KEY (Applicant_ID) REFERENCES Applicant(ID),
    CONSTRAINT fk_application_program FOREIGN KEY (Program_ID) REFERENCES Program(ID),
    CONSTRAINT ck_application_decision_logic CHECK (
        (Outcome IN ('Accepted','Rejected','Waitlisted') AND Status='Completed' AND Decision_Date IS NOT NULL AND Decision_Date >= Submission_Date)
        OR
        (Outcome='Pending' AND Decision_Date IS NULL AND Status IN ('Submitted','Under Review'))
    )
)
/

CREATE TABLE Application_Document (
    ID NUMBER(10,0) PRIMARY KEY,
    Application_ID NUMBER(10,0) NOT NULL,
    Institution_ID NUMBER(10,0),
    Document_Type VARCHAR2(50) NOT NULL CHECK (Document_Type IN ('Transcript', 'Essay', 'Recommendation', 'Certificate', 'English Test')),
    Document_File VARCHAR2(255) NOT NULL,
    CONSTRAINT fk_document_application FOREIGN KEY (Application_ID) REFERENCES Application(ID) ON DELETE CASCADE,
    CONSTRAINT fk_document_institution FOREIGN KEY (Institution_ID) REFERENCES Institution(ID),
    CONSTRAINT chk_transcript_institution CHECK (Document_Type != 'Transcript' OR Institution_ID IS NOT NULL)
)
/

CREATE OR REPLACE VIEW Applicant_Summary_View AS
SELECT 
    ap.ID AS Applicant_ID,
    ap.First_Name,
    ap.Last_Name,
    i.Name AS Institution_Name,
    ap.GPA,
    COUNT(a.ID) AS Total_Applications,
    COUNT(CASE WHEN a.Outcome = 'Accepted' THEN 1 END) AS Accepted_Count
FROM Applicant ap
JOIN Institution i ON ap.Institution_ID = i.ID
LEFT JOIN Application a ON ap.ID = a.Applicant_ID
GROUP BY ap.ID, ap.First_Name, ap.Last_Name, i.Name, ap.GPA
/

CREATE OR REPLACE VIEW Application_Document_View AS
SELECT 
    a.ID AS Application_ID,
    ap.First_Name,
    ap.Last_Name,
    d.Document_Type,
    d.Document_File,
    i.Name AS Institution_Name,
    p.Name AS Program_Name
FROM Application a
JOIN Applicant ap ON a.Applicant_ID = ap.ID
JOIN Program p ON a.Program_ID = p.ID
LEFT JOIN Application_Document d ON a.ID = d.Application_ID
LEFT JOIN Institution i ON ap.Institution_ID = i.ID
/

CREATE OR REPLACE VIEW Program_Outcome_View AS
SELECT 
    p.ID AS Program_ID,
    p.Name AS Program_Name,
    COUNT(a.ID) AS Total_Applications,
    COUNT(CASE WHEN a.Outcome = 'Accepted' THEN 1 END) AS Accepted,
    COUNT(CASE WHEN a.Outcome = 'Rejected' THEN 1 END) AS Rejected,
    COUNT(CASE WHEN a.Outcome = 'Pending' THEN 1 END) AS Pending,
    ROUND(AVG(ap.GPA), 2) AS Avg_Applicant_GPA
FROM Program p
LEFT JOIN Application a ON p.ID = a.Program_ID
LEFT JOIN Applicant ap ON a.Applicant_ID = ap.ID
GROUP BY p.ID, p.Name
/

INSERT INTO Institution (ID, Name, City, State_Province, Country, Accreditation_Status) VALUES (1, 'Central Secondary', 'Toronto', 'ON', 'Canada', 'Accredited')/
INSERT INTO Institution (ID, Name, City, State_Province, Country, Accreditation_Status) VALUES (2, 'Riverside Academy', 'Vancouver', 'BC', 'Canada', 'Accredited')/
INSERT INTO Institution (ID, Name, City, State_Province, Country, Accreditation_Status) VALUES (3, 'Oakwood School', 'London', 'England', 'UK', 'Accredited')/

INSERT INTO Program (ID, Name, Minimum_GPA, Duration_Years, Enrollment_Status) VALUES (1, 'Computer Science', 3.5, 4, 'Open')/
INSERT INTO Program (ID, Name, Minimum_GPA, Duration_Years, Enrollment_Status) VALUES (2, 'Business Admin', 3.0, 4, 'Open')/
INSERT INTO Program (ID, Name, Minimum_GPA, Duration_Years, Enrollment_Status) VALUES (3, 'Engineering', 3.7, 4, 'Closed')/

INSERT INTO Applicant (ID, First_Name, Last_Name, Date_of_Birth, Email, Institution_ID, GPA) VALUES (1001, 'John', 'Doe', TO_DATE('2007-05-15', 'YYYY-MM-DD'), 'john.doe@email.com', 1, 3.8)/
INSERT INTO Applicant (ID, First_Name, Last_Name, Date_of_Birth, Email, Institution_ID, GPA) VALUES (1002, 'Jane', 'Smith', TO_DATE('2006-11-22', 'YYYY-MM-DD'), 'jane.smith@email.com', 2, 3.5)/
INSERT INTO Applicant (ID, First_Name, Last_Name, Date_of_Birth, Email, Institution_ID, GPA) VALUES (1003, 'Alice', 'Johnson', TO_DATE('2007-03-10', 'YYYY-MM-DD'), 'alice.j@email.com', 1, 3.9)/

INSERT INTO Application (ID, Applicant_ID, Program_ID, Submission_Date, Status, Decision_Date, Outcome, Outcome_Notes) VALUES (1, 1001, 1, TO_DATE('2025-01-15', 'YYYY-MM-DD'), 'Completed', TO_DATE('2025-03-01', 'YYYY-MM-DD'), 'Accepted', 'Strong GPA and transcript')/
INSERT INTO Application (ID, Applicant_ID, Program_ID, Submission_Date, Status, Decision_Date, Outcome, Outcome_Notes) VALUES (2, 1002, 2, TO_DATE('2025-02-10', 'YYYY-MM-DD'), 'Completed', TO_DATE('2025-03-15', 'YYYY-MM-DD'), 'Rejected', 'GPA below threshold; weak essay')/
INSERT INTO Application (ID, Applicant_ID, Program_ID, Submission_Date, Status, Decision_Date, Outcome, Outcome_Notes) VALUES (3, 1003, 1, TO_DATE('2025-01-20', 'YYYY-MM-DD'), 'Submitted', NULL, 'Pending', 'Awaiting review')/

INSERT INTO Application_Document (ID, Application_ID, Institution_ID, Document_Type, Document_File) VALUES (1, 1, 1, 'Transcript', 'transcript_1001.pdf')/
INSERT INTO Application_Document (ID, Application_ID, Institution_ID, Document_Type, Document_File) VALUES (2, 1, NULL, 'Essay', 'essay_1001.pdf')/
INSERT INTO Application_Document (ID, Application_ID, Institution_ID, Document_Type, Document_File) VALUES (3, 1, NULL, 'Recommendation', 'rec_1001_1.pdf')/
INSERT INTO Application_Document (ID, Application_ID, Institution_ID, Document_Type, Document_File) VALUES (4, 2, 2, 'Transcript', 'transcript_1002.pdf')/
INSERT INTO Application_Document (ID, Application_ID, Institution_ID, Document_Type, Document_File) VALUES (5, 2, NULL, 'English Test', 'det_1002.pdf')/
"""

def execute_query(sql: str):
    with conn.cursor() as cur:
        cur.execute(sql)
        columns = [desc[0].lower() for desc in cur.description]
        rows = cur.fetchall()
        result = []
        for row in rows:
            row_dict = {}
            for i, val in enumerate(row):
                if isinstance(val, datetime.date):
                    row_dict[columns[i]] = val.isoformat()
                else:
                    row_dict[columns[i]] = val
            result.append(row_dict)
        return result

@app.get("/api/tables/{table}")
def get_table(table: str):
    if table not in ALLOWED_TABLES:
        raise HTTPException(status_code=404, detail="Table not found")
    oracle_table = ALLOWED_TABLES[table]
    sql = f"SELECT * FROM {oracle_table} ORDER BY ID"
    return execute_query(sql)

@app.post("/api/tables/{table}")
def insert_table(table: str, data: dict = Body()):
    if table not in ALLOWED_TABLES:
        raise HTTPException(status_code=404, detail="Table not found")
    oracle_table = ALLOWED_TABLES[table]
    with conn.cursor() as cur:
        cur.execute(f"SELECT NVL(MAX(ID), 0) + 1 FROM {oracle_table}")
        new_id = cur.fetchone()[0]
    fields = ", ".join([k.upper() for k in data.keys()])
    placeholders = ", ".join([f":{k}" for k in data.keys()])
    sql = f"INSERT INTO {oracle_table} (ID, {fields}) VALUES (:id, {placeholders})"
    bind_data = {"id": new_id, **data}
    with conn.cursor() as cur:
        cur.execute(sql, bind_data)
        conn.commit()
    return {"id": new_id}

@app.delete("/api/tables/{table}/{row_id}")
def delete_row(table: str, row_id: int):
    if table not in ALLOWED_TABLES:
        raise HTTPException(status_code=404, detail="Table not found")
    oracle_table = ALLOWED_TABLES[table]
    sql = f"DELETE FROM {oracle_table} WHERE ID = :id"
    with conn.cursor() as cur:
        cur.execute(sql, {"id": row_id})
        conn.commit()
    return {"status": "deleted"}

@app.get("/api/prepared-queries/{query_key}")
def get_prepared_query(query_key: str):
    if query_key not in PREPARED_QUERIES:
        raise HTTPException(status_code=404, detail="Query not found")
    sql = PREPARED_QUERIES[query_key]
    return execute_query(sql)

@app.post("/api/reset")
def reset_db():
    blocks = [block.strip() for block in RESET_SCRIPT.split('/') if block.strip()]
    with conn.cursor() as cur:
        for block in blocks:
            print(f"Executing block:\n{block}\n")
            cur.execute(block)
        conn.commit()
    return {"status": "reset"}

@app.get("/")
def root():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Database App</title>
    <link href="https://cdn.jsdelivr.net/npm/@mdi/font@latest/css/materialdesignicons.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/vuetify@3/dist/vuetify.min.css" rel="stylesheet">
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/vuetify@3/dist/vuetify.min.js"></script>
</head>
<body>
    <div id="app">
        <v-app>
            <v-navigation-drawer app>
                <v-list>
                    <v-list-item
                        v-for="section in sections"
                        :key="section"
                        :title="section"
                        @click="selected = section"
                    ></v-list-item>
                    <v-list-item @click="resetDatabase">Reset Database</v-list-item>
                </v-list>
            </v-navigation-drawer>
            <v-main>
                <div v-if="selected !== 'Prepared Queries'">
                    <v-btn @click="addRow">Add Row</v-btn>
                    <v-data-table :headers="headers" :items="tableData" :items-per-page="-1">
                        <template v-slot:item.actions="{ item }">
                            <v-btn icon @click="deleteRow(item.id)">
                                <v-icon>mdi-delete</v-icon>
                            </v-btn>
                        </template>
                    </v-data-table>
                    <v-dialog v-model="showAdd" max-width="500">
                        <v-card>
                            <v-card-title>Add New Row</v-card-title>
                            <v-card-text>
                                <v-text-field
                                    v-for="field in fields"
                                    :key="field"
                                    v-model="newRow[field]"
                                    :label="field.toUpperCase()"
                                ></v-text-field>
                            </v-card-text>
                            <v-card-actions>
                                <v-btn color="primary" @click="submitAdd">Save</v-btn>
                                <v-btn @click="showAdd = false">Cancel</v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                </div>
                <div v-else>
                    <v-select
                        v-model="selectedQuery"
                        :items="queries"
                        item-title="title"
                        item-value="value"
                        label="Select Query"
                    ></v-select>
                    <v-data-table
                        v-if="queryData.length > 0"
                        :headers="queryHeaders"
                        :items="queryData"
                        :items-per-page="-1"
                    ></v-data-table>
                </div>
            </v-main>
        </v-app>
    </div>
    <script>
        const { createApp } = Vue;
        const { createVuetify } = Vuetify;

        const vuetify = createVuetify();

        createApp({
            data() {
                return {
                    sections: ['Institutions', 'Programs', 'Applicants', 'Applications', 'Application Documents', 'Prepared Queries'],
                    selected: 'Institutions',
                    tableData: [],
                    headers: [],
                    showAdd: false,
                    fields: [],
                    newRow: {},
                    selectedQuery: null,
                    queryData: [],
                    queryHeaders: [],
                    tableMap: {
                        'Institutions': 'institutions',
                        'Programs': 'programs',
                        'Applicants': 'applicants',
                        'Applications': 'applications',
                        'Application Documents': 'application_documents'
                    },
                    fieldMap: {
                        'Institutions': ['name', 'city', 'state_province', 'country', 'accreditation_status'],
                        'Programs': ['name', 'minimum_gpa', 'duration_years', 'enrollment_status'],
                        'Applicants': ['first_name', 'last_name', 'date_of_birth', 'email', 'institution_id', 'gpa'],
                        'Applications': ['applicant_id', 'program_id', 'submission_date', 'status', 'decision_date', 'outcome', 'outcome_notes'],
                        'Application Documents': ['application_id', 'institution_id', 'document_type', 'document_file']
                    },
                    queries: [
                        { title: 'List all institution names and their accreditation status, ordered by name', value: '1' },
                        { title: 'List all open programs sorted alphabetically', value: '2' },
                        { title: 'List applicants names and GPAs, ordered by GPA descending', value: '3' },
                        { title: 'List all applications ordered by submission date', value: '4' },
                        { title: 'List all documents submitted, ordered by application ID', value: '5' },
                        { title: 'List all programs with a minimum GPA of at least 3.5, from highest to lowest', value: '6' },
                        { title: 'List applicants with GPA above the average GPA, ordered by GPA descending', value: '7' },
                        { title: 'Count of applications by status, ordered by count descending', value: '8' },
                        { title: 'Calculate average, min, max GPAs per institution, including standard deviation', value: '9' },
                        { title: 'Display programs where applicant GPA > program average GPA', value: '10' },
                        { title: 'Show applicants without a submitted transcript', value: '11' },
                        { title: 'Show all programs with at least one accepted applicant', value: '12' },
                        { title: 'Display all pending/waitlisted applicants for open programs', value: '13' },
                        { title: 'Show all applicants accepted to Computer Science but not Business Admin', value: '14' },
                        { title: 'Compare applicants average GPA to the programs average GPA', value: '15' },
                        { title: 'Display all submitted documents and programs of accepted applicants', value: '16' },
                        { title: 'Program Acceptance Rate and Average GPA', value: '17' },
                        { title: 'Show average amount of documents per applicant, per institution', value: '18' },
                        { title: 'Display applicants with high GPAs and pending applications', value: '19' }
                    ]
                };
            },
            watch: {
                selected: 'fetchData',
                selectedQuery: 'fetchQueryData'
            },
            methods: {
                async fetchData() {
                    if (this.selected === 'Prepared Queries') return;
                    const table = this.tableMap[this.selected];
                    const res = await fetch(`/api/tables/${table}`);
                    this.tableData = await res.json();
                    if (this.tableData.length > 0) {
                        this.headers = Object.keys(this.tableData[0]).map(key => ({ title: key.toUpperCase(), key }));
                    }
                    this.headers.push({ title: 'ACTIONS', key: 'actions', sortable: false });
                },
                addRow() {
                    this.fields = this.fieldMap[this.selected];
                    this.newRow = {};
                    this.showAdd = true;
                },
                async submitAdd() {
                    const table = this.tableMap[this.selected];
                    await fetch(`/api/tables/${table}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(this.newRow)
                    });
                    this.showAdd = false;
                    this.fetchData();
                },
                async deleteRow(id) {
                    const table = this.tableMap[this.selected];
                    await fetch(`/api/tables/${table}/${id}`, { method: 'DELETE' });
                    this.fetchData();
                },
                async fetchQueryData() {
                    if (!this.selectedQuery) return;
                    const res = await fetch(`/api/prepared-queries/${this.selectedQuery}`);
                    this.queryData = await res.json();
                    if (this.queryData.length > 0) {
                        this.queryHeaders = Object.keys(this.queryData[0]).map(key => ({ title: key.toUpperCase(), key }));
                    }
                },
                async resetDatabase() {
                    await fetch('/api/reset', { method: 'POST' });
                    this.fetchData();
                    this.queryData = [];
                    this.selectedQuery = null;
                }
            },
            mounted() {
                this.fetchData();
            }
        }).use(vuetify).mount('#app');
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)
