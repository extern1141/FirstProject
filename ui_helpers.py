# ui_helpers.py
# Enthält kleine, wiederverwendbare Funktionen, die bei UI-Operationen helfen.

from PyQt6.QtWidgets import QApplication, QTableWidget

def kopiere_markierte_zellen(table_widget: QTableWidget):
    """
    Kopiert den Inhalt der markierten Zellen als tabulatorgetrennten Text
    in die Zwischenablage, was das Einfügen in andere Tabellenkalkulationen erleichtert.
    """
    selected_ranges = table_widget.selectedRanges()
    if not selected_ranges:
        return

    # Findet die Grenzen der Auswahl, um eine rechteckige Datenstruktur zu erstellen.
    top = min(r.topRow() for r in selected_ranges)
    bottom = max(r.bottomRow() for r in selected_ranges)
    left = min(r.leftColumn() for r in selected_ranges)
    right = max(r.rightColumn() for r in selected_ranges)

    output_rows = []
    for r in range(top, bottom + 1):
        row_data = []
        for c in range(left, right + 1):
            item = table_widget.item(r, c)
            # Nur ausgewählte Zellen hinzufügen, ansonsten leer lassen
            if item and item.isSelected():
                row_data.append(item.text())
            else:
                row_data.append('')
        output_rows.append('\t'.join(row_data))
    
    if output_rows:
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(output_rows))

