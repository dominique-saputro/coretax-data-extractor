#!/bin/bash

echo "Activating virtual enviroment..."
source .venv/bin/activate

echo "Updating repository..."
git pull

echo "Starting application..."
streamlit run home.py