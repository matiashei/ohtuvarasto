# ohtuvarasto
[![CI](https://github.com/matiashei/ohtuvarasto/actions/workflows/main.yml/badge.svg)](https://github.com/matiashei/ohtuvarasto/actions/workflows/main.yml)    [![codecov](https://codecov.io/github/matiashei/ohtuvarasto/graph/badge.svg?token=CR7EJS3IP6)](https://codecov.io/github/matiashei/ohtuvarasto)



Helsingin yliopiston ohjelmistotuotannon kurssin harjoitusrepositorio

## Web User Interface

This application includes a web-based user interface for warehouse management, built with [Flask](https://flask.palletsprojects.com/).

### Features

- **Create Warehouses**: Create multiple warehouses with custom names and capacities measured in cubic meters (m³)
- **Multiple Items**: Each warehouse can store different items (e.g., beer, wine, water)
- **Flexible Units**: Track items in different units:
  - Cubic Meters (m³) - for bulk storage
  - Liters (L) - for liquids
  - Units/Bottles - for individual items
- **View Warehouses**: See all warehouses with their used/available space
- **Edit Warehouses**: Update warehouse names
- **Delete Warehouses**: Remove warehouses that are no longer needed
- **Add/Update/Remove Items**: Manage individual items within each warehouse
- **Dark Mode UI**: Modern, sleek dark-themed interface

### Running the Web Application

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Run the application:
   ```bash
   poetry run python src/app.py
   ```

3. Open your browser and navigate to `http://localhost:5000`

### Environment Variables

- `FLASK_SECRET_KEY`: Secret key for session management (optional, auto-generated if not set)
- `FLASK_DEBUG`: Set to `true` to enable debug mode (default: `false`)

### Technologies Used

- **Flask** (>=3.1.2): Web framework for Python
- **Jinja2**: Template engine for rendering HTML
- **Python 3.12+**: Programming language
