# main.py
# Dies ist der Haupteinstiegspunkt der Anwendung.
# Seine einzige Aufgabe ist es, die Anwendung zu initialisieren und das Hauptfenster anzuzeigen.

import sys
from PyQt6.QtWidgets import QApplication

# --- KORREKTUR ---
# Die Zeile "from ui.main_window import MainWindow" wurde geändert,
# da alle Python-Dateien im selben Verzeichnis liegen.
from main_window import MainWindow

def run_app():
    """
    Initialisiert die QApplication und startet den Event-Loop.
    """
    app = QApplication(sys.argv)
    
    # Instanziiert das Hauptfenster aus der main_window.py Datei
    fenster = MainWindow()
    fenster.show()  # Zeigt das Fenster an
    
    # Startet die Anwendung und wartet auf das Beenden
    sys.exit(app.exec())

if __name__ == "__main__":
    # Dieser Block wird nur ausgeführt, wenn das Skript direkt gestartet wird.
    run_app()
