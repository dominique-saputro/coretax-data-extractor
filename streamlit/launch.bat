@echo off

echo Activating virtual enviroment...
call .venv\Scripts\activate.bat

echo Updating repository...
git pull

echo Starting application...
streamlit run home.py

pause