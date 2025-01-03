# Plumbing Dashboard v1.2.0

A comprehensive web-based dashboard for managing plumbing business operations. This application helps track jobs, manage customer information, and handle scheduling for plumbing services.

## Features

- Customer Management
- Job Tracking
- Schedule Management
- Invoice Generation
- Service History
- Dashboard Analytics

## Installation

1. Clone the repository:
```bash
git clone https://github.com/lavorno/Plumbing-Dashboard.git
cd Plumbing-Dashboard
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python app.py
```

5. Run the application:
```bash
flask run
```

## Technology Stack

- Python
- Flask
- SQLite
- HTML/CSS
- JavaScript

## Project Structure

```
Plumbing-Dashboard/
├── app.py              # Main application file
├── config/            # Configuration files
├── templates/         # HTML templates
├── requirements.txt   # Python dependencies
└── plumbing.db       # SQLite database
```

## Version History

- v1.2.0 - Dashboard Improvements
  - Fixed monthly expenses display on dashboard
  - Added individual truck expenses to monthly expenses
  - Improved expense calculations and display
  - Enhanced dashboard UI/UX
- v1.0.0 - Initial release with core functionality
  - Basic customer management
  - Job tracking
  - Schedule management
  - Invoice generation

## Contributing

This is a private project. Please contact the repository owner for contribution guidelines.

## License

All rights reserved. This project is proprietary and confidential.