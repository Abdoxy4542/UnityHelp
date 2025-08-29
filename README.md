# UnityAid Platform

UnityAid is an AI-powered humanitarian platform designed to assist aid organizations in managing operations, collecting data, and generating insights to deliver help more effectively.

## Key Features

*   **Account Management**: Secure user registration and profile management.
*   **Assessments**: Create and deploy custom surveys and assessments for data collection in the field.
*   **Reporting**: Generate insightful reports and visualizations from collected data.
*   **Dashboard**: A central hub for viewing key metrics and real-time information.
*   **Integrations**: Connect with other humanitarian data sources and services (HDX, KoboToolbox, etc.).
*   **Alerts**: A system for sending and managing alerts.

## Project Structure

The project follows a standard Django structure, with functionality organized into modular "apps".

```
unityaid_platform/
├── apps/                 # Core application modules (the "rooms" of the project)
│   ├── accounts/         # User authentication and management
│   ├── assessments/      # Creating and managing assessments
│   ├── reports/          # Data analysis and report generation
│   ├── dashboard/        # Main user dashboard
│   └── ...               # Other functional modules
├── config/               # Project-level configuration (settings, URLs)
├── static/               # CSS, JavaScript, and image files
├── templates/            # HTML templates for the user interface
├── media/                # User-uploaded files and media
├── requirements.txt      # List of Python package dependencies
└── manage.py             # Django's command-line utility for administrative tasks
```

## Setup and Installation

Follow these steps to get the project running on a Windows machine.

### 1. Prerequisites

*   [Python 3.10+](https://www.python.org/downloads/)
*   [Git](https://git-scm.com/downloads/)

### 2. Clone the Repository

Open your terminal or command prompt and clone the project to your local machine:

```bash
git clone <your-repository-url>
cd unityaid_platform
```

### 3. Create and Activate a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create the virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate
```

### 4. Install Dependencies

Install all the required Python packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 5. Set Up the PostgreSQL Database

This project is configured to use a PostgreSQL database with the PostGIS extension for geographic data support.

1.  **Install PostgreSQL & PostGIS**:
    *   Download and install PostgreSQL from the [official website](https://www.postgresql.org/download/). During installation, you will be prompted to set a password for the default `postgres` user. **Remember this password.**
    *   After installing PostgreSQL, use the "Application Stack Builder" (included with the installation) to add the **PostGIS** extension. This is required for handling geographic data.

2.  **Create the Database (`unityaid_db`)**:
    You can do this using a graphical tool like pgAdmin (recommended) or the command line.

    *   **Option A: Using pgAdmin (Easy)**
        1.  Open pgAdmin and connect to your server using the password you set.
        2.  In the left panel, right-click **Databases** -> **Create** -> **Database...**.
        3.  Enter `unityaid_db` as the "Database name" and click **Save**.

    *   **Option B: Using SQL Shell (psql)**
        1.  Open the "SQL Shell (psql)" application.
        2.  Press Enter to accept the default connection settings until it prompts for a password.
        3.  Enter your PostgreSQL password.
        4.  At the `postgres=#` prompt, type the following command and press Enter:
            ```sql
            CREATE DATABASE unityaid_db;
            ```

3.  **Create and Configure the `.env` File**:
    This file securely stores your database credentials in the project's root folder (the same folder as `manage.py`).

    1.  **Create the file**: Open a text editor (like Notepad), paste the content below, and go to `File > Save As...`. Set the "Save as type" to **All Files (\*.\*)** and name the file `.env`.
    2.  **Add the content**:
        ```env
        # .env file for UnityAid Platform

        # --- SECURITY WARNING ---
        # Generate a new secret key for production.
        SECRET_KEY='your-secret-key-here'

        # Set to False in production
        DEBUG=True

        # --- DATABASE CONFIGURATION ---
        DB_NAME=unityaid_db
        DB_USER=postgres
        DB_PASSWORD=your_postgres_password
        DB_HOST=localhost
        DB_PORT=5432
        ```
    3.  **Update the placeholders**:
        *   Replace `your_postgres_password` with the actual password for your `postgres` user.
        *   Replace `your-secret-key-here` with a new secret key. Generate one by running this command in your terminal:
          ```bash
          python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
          ```
          Copy the output and paste it into the `.env` file.

### 6. Run Database Migrations

With the database and `.env` file configured, run the initial migrations to build your database tables.


```bash
python manage.py migrate
```

### 7. Create a Superuser (Admin)

Create an admin account to access the Django admin interface:

```bash
python manage.py createsuperuser
```
Follow the prompts to set a username, email, and password.

### 8. Run the Development Server

Start the local development server:

```bash
python manage.py runserver
```

The application will be available at **http://127.0.0.1:8000/**. You can access the admin panel at **http://127.0.0.1:8000/admin/**.