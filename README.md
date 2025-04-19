# Restaurant Intelligence

A sophisticated restaurant management and analytics platform built with Flask, featuring machine learning capabilities for business intelligence and decision making.

## Features

- Restaurant data management and analytics
- Machine learning-powered insights
- User authentication and authorization
- Interactive dashboard
- Data visualization
- Business intelligence reporting

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLAlchemy ORM
- **Machine Learning**: Implemented in `ml_model.py`
- **Frontend**: HTML, CSS, JavaScript (Templates)
- **Forms**: Flask-WTF
- **Authentication**: Flask-Login

## Project Structure

```
Restaurant-Intelligence/
├── app.py              # Main application configuration
├── routes.py           # URL route handlers
├── models.py           # Database models
├── forms.py            # Form definitions
├── ml_model.py         # Machine learning components
├── utils.py            # Utility functions
├── extensions.py       # Flask extensions
├── main.py            # Application entry point
├── static/            # Static files (CSS, JS, images)
├── templates/         # HTML templates
├── instance/          # Instance-specific files
└── requirements.txt   # Project dependencies
```

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/sumit007-ui/Restaurant-Intelligence.git
cd Restaurant-Intelligence
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory and add necessary configurations.

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the application:
```bash
python main.py
```

The application will be available at `http://localhost:5000`

## Usage

1. Register a new account or login with existing credentials
2. Navigate through the dashboard to access various features
3. Upload and manage restaurant data
4. View analytics and ML-powered insights
5. Generate and export reports

## API Documentation

The application provides various API endpoints for data management and analytics. Detailed documentation can be found in the routes.py file.

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make changes and commit (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## Author

Sumit Kumar

## Support

For support and queries, please open an issue in the repository. 