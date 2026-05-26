# RAG-Database

A minimal project scaffold for experimenting with Retrieval-Augmented Generation (RAG) methods using a custom database. The repository provides basic scripts for database setup, data population, and a Dash web application for data exploration or interaction.

## Workflow

1. **Installation and Setup**  
   Start by installing the project dependencies. The recommended method is via pip and `setup.py`:

   ```bash
   pip install .
   ```

2. **Database Population**  
   Use the provided Jupyter notebook to populate your database:

   - Open `populate.ipynb` in your preferred Jupyter environment and follow the steps inside to generate and insert the data needed by the application.

3. **Run the Application**  
   Once the database is populated, you can start the web application:

   ```bash
   python app.py
   ```

   The Dash app will launch and can be accessed locally through your browser.

## File Structure

- `setup.py` — Installation script; sets up the environment and dependencies.
- `populate.ipynb` — Jupyter notebook for generating and populating the database.
- `app.py` — Main application entry point (Dash web app or API).

## Requirements

All dependencies are listed in `requirements.txt`. Use your preferred package manager to install them, or run:

```bash
pip install -r requirements.txt
```

## Notes

- The database backend and schema are defined within the setup and not intended for large-scale usage.
- This project is intended as a simple template or starting point for RAG experimentation and not for production use.

## License

idk