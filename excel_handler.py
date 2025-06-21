# excel_handler.py
# Dieses Modul ist ausschließlich für Interaktionen mit Excel-Dateien zuständig.
# Es kapselt die Logik zum Laden, Speichern und Überprüfen von Excel-Dateien.

import os
import pandas as pd
from openpyxl import load_workbook, Workbook
import numpy as np

def is_excel_file_locked(file_path: str) -> bool:
    """
    Überprüft, ob eine Excel-Datei gesperrt ist, indem nach einer temporären
    Lock-Datei von Excel gesucht wird (beginnt mit '~').

    Args:
        file_path (str): Der Pfad zur Excel-Datei.

    Returns:
        bool: True, wenn eine Lock-Datei existiert, sonst False.
    """
    if not os.path.exists(file_path):
        return False
    
    lock_file = os.path.join(os.path.dirname(file_path), "~$" + os.path.basename(file_path))
    return os.path.exists(lock_file)

def get_sheet_names(file_path: str) -> list:
    """
    Ruft die Namen aller Tabellenblätter aus einer Excel-Datei ab.

    Args:
        file_path (str): Der Pfad zur Excel-Datei.

    Returns:
        list: Eine Liste der Tabellenblattnamen.
    
    Raises:
        FileNotFoundError: Wenn die Datei nicht existiert.
        IOError: Wenn die Datei gesperrt ist.
        Exception: Bei anderen Ladefehlern.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Die Datei '{os.path.basename(file_path)}' wurde nicht gefunden.")
    
    if is_excel_file_locked(file_path):
        raise IOError(f"Die Excel-Datei '{os.path.basename(file_path)}' ist gesperrt. Bitte schließen Sie sie in Excel.")

    try:
        xls = pd.ExcelFile(file_path, engine='openpyxl')
        return xls.sheet_names
    except Exception as e:
        raise Exception(f"Fehler beim Lesen der Tabellenblattnamen aus '{os.path.basename(file_path)}': {e}")


def load_sheet(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Lädt ein einzelnes Tabellenblatt aus einer Excel-Datei.

    Args:
        file_path (str): Der Pfad zur Excel-Datei.
        sheet_name (str): Der Name des zu ladenden Tabellenblatts.

    Returns:
        pd.DataFrame: Das geladene DataFrame.

    Raises:
        FileNotFoundError: Wenn die Datei nicht existiert.
        IOError: Wenn die Datei gesperrt ist.
        Exception: Bei anderen Ladefehlern.
    """
    # Die Überprüfungen sind bereits in get_sheet_names, aber zur Sicherheit auch hier.
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Die Datei '{os.path.basename(file_path)}' wurde nicht gefunden.")
    
    if is_excel_file_locked(file_path):
        raise IOError(f"Die Excel-Datei '{os.path.basename(file_path)}' ist gesperrt. Bitte schließen Sie sie in Excel.")

    try:
        # `header=0` verwendet die erste Zeile als Spaltenüberschriften.
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', header=0)
        # Stellt sicher, dass alle Spaltennamen Strings sind, um Fehler zu vermeiden.
        df.columns = df.columns.astype(str)
        return df
    except ValueError as ve:
        # Dieser Fehler tritt oft auf, wenn das Blatt nicht existiert.
        raise ValueError(f"Tabellenblatt '{sheet_name}' nicht in der Datei gefunden oder die Datei ist beschädigt.")
    except Exception as e:
        raise Exception(f"Ein unerwarteter Fehler ist beim Laden von '{sheet_name}' aufgetreten: {e}")


def save_sheet(file_path: str, sheet_name: str, df_to_save: pd.DataFrame):
    """
    Speichert ein DataFrame in einem bestimmten Tabellenblatt einer Excel-Datei.
    Wenn das Blatt existiert, wird es überschrieben.

    Args:
        file_path (str): Der Pfad zur Excel-Datei.
        sheet_name (str): Der Name des Ziel-Tabellenblatts.
        df_to_save (pd.DataFrame): Das zu speichernde DataFrame.
        
    Raises:
        IOError: Wenn die Datei gesperrt ist.
        Exception: Bei anderen Speicherfehlern.
    """
    if is_excel_file_locked(file_path):
        raise IOError(f"Die Excel-Datei '{os.path.basename(file_path)}' ist gesperrt. Speichern nicht möglich.")

    try:
        # pandas' ExcelWriter ermöglicht das Schreiben in bestehende Dateien.
        # `mode='a'` (append) und `if_sheet_exists='replace'` sind hier der Schlüssel.
        with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_to_save.to_excel(writer, sheet_name=sheet_name, index=False)
            
    except FileNotFoundError:
        # Wenn die Datei nicht existiert, erstellen wir sie neu.
        with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
            df_to_save.to_excel(writer, sheet_name=sheet_name, index=False)
            
    except Exception as e:
        raise Exception(f"Fehler beim Speichern der Daten in '{sheet_name}': {e}")
