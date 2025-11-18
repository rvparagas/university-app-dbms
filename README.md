# Database Application

This project involves creating a database schema for managing applicants, institutions, programs, applications, and application documents. It includes the creation of tables with appropriate constraints, views for summarizing applicant information, and ensuring data integrity through various checks.

## Environment Setup

- Requires Python 3.12
- Requires Port-Forwarded at localhost:1521 to TMU Oracle 12c Database:
    ```
    ssh -L 1521:oracle12c.cs.torontomu.ca:1521 <tmu_cs_user>@moon.cs.torontomu.ca
    ```
- Install dependencies using:
    ```
    pip install -r requirements.txt
    ```

## Starting the Application

- Run the development server with:
    ```
    fastapi dev main.py
    ```
- Enter your Oracle DB username and password when prompted.
- Access the application at `http://localhost:8000`.
- Reset the database (if needed) by clicking "Reset Database" on the sidebar.
- Try out the tables and prepared queries via the web app interface.

## Components Included:

- Frontend Vue.js + Vuetify application for user interaction at root path `/`.
- FastAPI backend for handling database operations and API requests. See `/docs` for API documentation.
- Oracle database schema with tables: Institution, Applicant, Program, Application, Application_Document.
- Views for summarizing applicant information.
