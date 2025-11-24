# Crime Management System

## Overview

This repository contains a comprehensive Crime Management System built with Flask, designed to help law enforcement agencies track and manage crime records, criminals, cases, evidence, victims, witnesses, and police stations. The system features role-based access control with three primary roles: administrators, police officers, and analysts.

The application provides functionality for managing crime records, case tracking, criminal profiling, evidence management, and statistical analysis of crime data with visualization capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework

The application is built using Flask, a lightweight WSGI web application framework in Python. The main application structure follows the Flask application factory pattern with some modifications:

- `app.py`: Initializes the Flask application, configures the database, and sets up the login manager
- `main.py`: The entry point for running the application that imports necessary modules
- `models.py`: Defines SQLAlchemy ORM models for the database schema
- `routes.py`: Contains all the route handlers for the application
- `forms.py`: Contains WTForms form classes for data validation and handling
- `utils.py`: Contains utility functions like role-based authentication decorators

### Database

The application uses SQLAlchemy ORM with Flask-SQLAlchemy integration. The database model includes:

- User management (authentication and role-based authorization)
- Crime records
- Criminal profiles
- Case management
- Evidence tracking
- Victim and witness information
- Police stations and officers

The database is configured to use a PostgreSQL database (based on the Nix packages in the `.replit` file), but could be set up to use any SQLAlchemy-compatible database.

### Authentication & Authorization

The system uses Flask-Login for authentication with a custom role-based authorization mechanism implemented through the `role_required` decorator in `utils.py`. There are three main roles:

1. **Admin**: Full access to all features, including user management
2. **Officer**: Can manage crimes, cases, evidence, etc., but has limited access to admin functions
3. **Analyst**: Has read-only access to data for analysis and reporting

### Frontend

The frontend uses:
- Bootstrap for responsive design with a dark theme
- Jinja2 templates for server-side rendering
- Font Awesome icons
- Leaflet.js for map visualizations
- Chart.js for data visualization

## Key Components

### User Management

- Registration, login, profile management
- Role-based access control
- Password hashing for security

### Crime Records

- Create, view, edit, and search crime records
- Associate crimes with locations, dates, and types
- Link crimes to cases, criminals, victims, and witnesses

### Case Management

- Create and track cases
- Assign officers to cases
- Record case notes and progress
- Link cases to crimes, evidence, and involved parties

### Criminal Records

- Profile criminals with personal details
- Track criminal history and associated crimes
- Search and filter capabilities

### Evidence Management

- Track physical evidence
- Record chain of custody
- Associate evidence with crimes and cases

### Victim and Witness Records

- Record victim and witness information
- Link to crimes and cases
- Protect sensitive information

### Reporting & Analytics

- Crime statistics with date range filtering
- Visualization with charts and graphs
- Spatial analysis with mapping functions

## Data Flow

1. **Authentication Flow**:
   - Users log in through the login form
   - Flask-Login validates credentials and establishes a session
   - Role-based middleware checks permissions for protected routes

2. **Crime Recording Flow**:
   - Officers record new crimes with associated details
   - Crimes are linked to locations, victims, and other entities
   - Cases may be created to investigate crimes

3. **Case Management Flow**:
   - Cases are created and assigned to officers
   - Evidence, suspects, and witnesses are associated with cases
   - Case progress is tracked through status updates and notes

4. **Reporting Flow**:
   - Crime data is aggregated for statistical analysis
   - Charts and maps visualize crime patterns and trends
   - Filters allow for specific data selection and analysis

## External Dependencies

### Python Packages

- **Flask**: Web framework
- **Flask-SQLAlchemy**: ORM for database operations
- **Flask-Login**: Authentication management
- **Flask-WTF**: Form handling and validation
- **Werkzeug**: Utilities, including password hashing
- **SQLAlchemy**: Database ORM
- **Gunicorn**: WSGI HTTP Server
- **Psycopg2**: PostgreSQL adapter
- **Python-dotenv**: Environment variable management

### Frontend Libraries

- **Bootstrap**: Frontend framework (loaded from CDN)
- **Font Awesome**: Icon library (loaded from CDN)
- **Leaflet.js**: Interactive maps (loaded from CDN)
- **Chart.js**: Data visualization (integrated in JS files)

## Deployment Strategy

The application is configured for deployment on Replit with:

- Gunicorn as the WSGI HTTP server
- Automatic scaling capability
- PostgreSQL as the database (based on Nix configuration)
- Environment variables for configuration

The `.replit` file includes:
- Python 3.11 as the language
- Openssl and PostgreSQL as Nix packages
- Deployment target set to "autoscale"
- Run command configured for Gunicorn
- Port binding configured for port 5000

The deployment setup ensures proper handling of HTTPS proxying through the `ProxyFix` middleware, allowing proper URL generation.