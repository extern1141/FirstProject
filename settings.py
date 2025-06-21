# settings.py
# Definiert anwendungsspezifische Konstanten und Konfigurationen.

import os

# --- Kernkonfiguration ---

# Standardpfad zur Excel-Datei, falls keine andere ausgewählt wurde.
EXCEL_PFAD = "Inventargegenstände.xlsx"

# Pfad zur Logo-Datei.
LOGO_PFAD = os.path.join("bilder", "logo.jpg")


# --- Hilfsfunktionen für die Ersteinrichtung (Optional) ---
# Dieser Abschnitt kann für die finale Version entfernt werden. Er hilft bei der
# Entwicklung, indem er sicherstellt, dass die benötigten Dateien existieren.

def _create_dummy_excel_if_not_exists():
    """Erstellt eine Dummy-Excel-Datei, falls sie nicht vorhanden ist."""
    if not os.path.exists(EXCEL_PFAD):
        try:
            import pandas as pd
            print(f"Warnung: '{EXCEL_PFAD}' nicht gefunden. Erstelle eine Dummy-Datei...")
            dummy_data = {
                'Gegenstand': ['Laptop', 'Maus', 'Tastatur'],
                'Kategorie': ['IT', 'IT', 'IT'],
                'Mitarbeiter': ['Max Mustermann', 'Max Mustermann', 'Erika Mustermann'],
                'Preis': [1200.50, 25.00, 75.99]
            }
            dummy_df = pd.DataFrame(dummy_data)
            
            with pd.ExcelWriter(EXCEL_PFAD, engine='openpyxl') as writer:
                dummy_df.to_excel(writer, sheet_name='Inventar', index=False)
            print(f"Dummy-Excel-Datei erstellt: {EXCEL_PFAD}")
        except ImportError:
            print("Fehler: 'pandas' oder 'openpyxl' ist nicht installiert. Dummy-Datei konnte nicht erstellt werden.")
        except Exception as e:
            print(f"Unbekannter Fehler beim Erstellen der Dummy-Excel-Datei: {e}")

def _create_dummy_logo_if_not_exists():
    """Erstellt ein Dummy-Logo, falls es nicht vorhanden ist."""
    if not os.path.exists(LOGO_PFAD):
        logo_dir = os.path.dirname(LOGO_PFAD)
        if not os.path.exists(logo_dir):
            os.makedirs(logo_dir)
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            print(f"Warnung: '{LOGO_PFAD}' nicht gefunden. Erstelle ein Dummy-Logo...")
            img = Image.new('RGB', (200, 50), color = (240, 124, 3))
            d = ImageDraw.Draw(img)
            try:
                # Versuche eine Standardschriftart zu laden
                font = ImageFont.truetype("arial.ttf", 15)
            except IOError:
                # Wenn nicht gefunden, verwende eine einfache Standardschrift
                font = ImageFont.load_default()
            d.text((10,10), "Inventar-App", fill=(255,255,255), font=font)
            img.save(LOGO_PFAD)
            print(f"Dummy-Logo erstellt: {LOGO_PFAD}")
        except ImportError:
            print("Fehler: 'Pillow' ist nicht installiert. Dummy-Logo konnte nicht erstellt werden.")
        except Exception as e:
            print(f"Unbekannter Fehler beim Erstellen des Dummy-Logos: {e}")


# Führe die Hilfsfunktionen aus, wenn das Modul geladen wird.
_create_dummy_excel_if_not_exists()
_create_dummy_logo_if_not_exists()

