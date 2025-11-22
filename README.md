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

## Components Included

- Frontend Vue.js + Vuetify application for user interaction at root path `/`.
- FastAPI backend for handling database operations and API requests. See `/docs` for API documentation.
- Oracle database schema with tables: Institution, Applicant, Program, Application, Application_Document.
- Views for summarizing applicant information.

## Using the Application

After starting the application, you can interact with the database through the web interface. You can add, view, and manage applicants, institutions, programs, applications, and documents. The application also provides prepared queries to retrieve specific information from the database.

```
   FastAPI   Starting development server 🚀

             Searching for package file structure from directories with __init__.py files
Enter Oracle DB username: ********
Enter Oracle DB password: 
             Importing from C:\<redacted_path>
 
    module   🐍 main.py

      code   Importing the FastAPI app object from the module with the following code:

             from main import app

       app   Using import string: main:app

    server   Server started at http://127.0.0.1:8000
    server   Documentation at http://127.0.0.1:8000/docs

       tip   Running in development mode, for production use: fastapi run

             Logs:

      INFO   Will watch for changes in these directories: ['C:\\<redacted_path>']
      INFO   Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
      INFO   Started reloader process [32316] using WatchFiles
      INFO   Started server process [42868]
      INFO   Waiting for application startup.
      INFO   Application startup complete.
```

Open your web browser and navigate to `http://localhost:8000` to start using the application.

If you are launching the app for the first time or want to reset the database, click on "Reset Database" in the sidebar. This will create the necessary tables and views in your Oracle database.
