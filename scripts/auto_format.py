"""
This script auto-formats a Jupyter Notebook file.
It loads the notebook, and then re-saves it, which applies automatic formatting.
"""
import nbformat

# Load and re-save to auto-format
with open("notebooks\80k_cleaning.ipynb", "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

with open("notebooks\80k_cleaning_n.ipynb", "w", encoding="utf-8") as f:
    nbformat.write(nb, f)