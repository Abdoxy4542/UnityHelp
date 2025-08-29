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

### 5. Set Up the Database

Run the initial database migrations to set up the necessary tables.

```bash
python manage.py migrate
```

### 6. Create a Superuser (Admin)

Create an admin account to access the Django admin interface:

```bash
python manage.py createsuperuser
```
Follow the prompts to set a username, email, and password.

### 7. Run the Development Server

Start the local development server:

```bash
python manage.py runserver
```

The application will be available at **http://127.0.0.1:8000/**. You can access the admin panel at **http://127.0.0.1:8000/admin/**.