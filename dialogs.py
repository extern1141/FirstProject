# dialogs.py
# Dieses Modul enthält alle benutzerdefinierten QDialog-Klassen,
# die in der Anwendung verwendet werden. Dies hält die main_window.py übersichtlich.

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
    QLineEdit, QMessageBox, QListWidget, QListWidgetItem, QCheckBox, QGroupBox, QSpacerItem,
    QSizePolicy
)
from PyQt6.QtCore import Qt

class ConfirmExitDialog(QDialog):
    """Ein einfacher Dialog, der den Benutzer fragt, ob er die Anwendung wirklich beenden möchte."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anwendung verlassen?")
        self.setFixedSize(350, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        message_label = QLabel("Möchten Sie die Anwendung wirklich verlassen?")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message_label)

        button_layout = QHBoxLayout()
        yes_button = QPushButton("Ja")
        yes_button.clicked.connect(self.accept)
        no_button = QPushButton("Nein")
        no_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

class FilterDialog(QDialog):
    """Dialog zum Anwenden von Filtern und Sortierungen auf die Tabelle."""
    def __init__(self, column_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter und Sortierung")
        
        # Initialisiere die Rückgabewerte
        self.filter_column_name = None
        self.filter_text = ""
        self.sort_column_name = None
        self.sort_type = None

        layout = QVBoxLayout(self)

        # Filter-Sektion
        filter_group = QGroupBox("Filtern")
        filter_layout = QVBoxLayout()
        filter_layout.addWidget(QLabel("Spalte zum Filtern:"))
        self.filter_column_combo = QComboBox()
        self.filter_column_combo.addItem("Alle Spalten", "")
        self.filter_column_combo.addItems(column_names)
        filter_layout.addWidget(self.filter_column_combo)
        
        filter_layout.addWidget(QLabel("Filtertext:"))
        self.filter_text_input = QLineEdit()
        self.filter_text_input.setPlaceholderText("Text eingeben...")
        filter_layout.addWidget(self.filter_text_input)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Sortier-Sektion
        sort_group = QGroupBox("Sortieren")
        sort_layout = QVBoxLayout()
        sort_layout.addWidget(QLabel("Spalte zum Sortieren:"))
        self.sort_column_combo = QComboBox()
        self.sort_column_combo.addItem("Keine", "")
        self.sort_column_combo.addItems(column_names)
        sort_layout.addWidget(self.sort_column_combo)
        
        sort_layout.addWidget(QLabel("Sortierreihenfolge:"))
        self.sort_type_combo = QComboBox()
        self.sort_type_combo.addItems([
            "Aufsteigend (A-Z)", 
            "Absteigend (Z-A)",
            "Numerisch aufsteigend (0-9)", 
            "Numerisch absteigend (9-0)"
        ])
        sort_layout.addWidget(self.sort_type_combo)
        sort_group.setLayout(sort_layout)
        layout.addWidget(sort_group)

        # Buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Anwenden")
        apply_button.clicked.connect(self.apply_and_accept)
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def apply_and_accept(self):
        """Liest die Werte aus den Widgets aus und schließt den Dialog."""
        self.filter_column_name = self.filter_column_combo.currentData() or self.filter_column_combo.currentText()
        if self.filter_column_name == "Alle Spalten":
            self.filter_column_name = ""
            
        self.filter_text = self.filter_text_input.text().strip()
        
        self.sort_column_name = self.sort_column_combo.currentData() or self.sort_column_combo.currentText()
        if self.sort_column_name == "Keine":
            self.sort_column_name = ""

        sort_map = {
            "Aufsteigend (A-Z)": 'az',
            "Absteigend (Z-A)": 'za',
            "Numerisch aufsteigend (0-9)": 'num_asc',
            "Numerisch absteigend (9-0)": 'num_desc'
        }
        self.sort_type = sort_map.get(self.sort_type_combo.currentText())
        
        self.accept()

class RecentFilesDialog(QDialog):
    """Dialog zur Anzeige und Auswahl von zuletzt verwendeten Dateien."""
    def __init__(self, recent_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zuletzt geöffnete Dateien")
        self.setMinimumSize(500, 300)

        self.selected_file = None
        self.open_new_file_requested = False
        self.recent_files = recent_files[:] # Kopie erstellen

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Wählen Sie eine Datei aus der Liste oder öffnen Sie eine neue Datei."))

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.list_widget)
        self.populate_list()

        button_layout = QHBoxLayout()
        open_button = QPushButton("Ausgewählte öffnen")
        open_button.clicked.connect(self.accept_selection)
        
        open_new_button = QPushButton("Neue Datei öffnen...")
        open_new_button.clicked.connect(self.request_new_file)

        remove_button = QPushButton("Aus Liste entfernen")
        remove_button.clicked.connect(self.remove_selected)

        button_layout.addWidget(open_button)
        button_layout.addWidget(open_new_button)
        button_layout.addWidget(remove_button)
        layout.addLayout(button_layout)

    def populate_list(self):
        """Füllt die Liste mit den Dateipfaden."""
        self.list_widget.clear()
        for file_path in self.recent_files:
            # Zeigt nur den Dateinamen an, speichert aber den vollen Pfad.
            item = QListWidgetItem(os.path.basename(file_path))
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.list_widget.addItem(item)
    
    def accept_selection(self):
        """Wird bei Doppelklick oder Klick auf 'Öffnen' aufgerufen."""
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_file = current_item.data(Qt.ItemDataRole.UserRole)
            self.accept()

    def request_new_file(self):
        """Signalisiert, dass der Benutzer eine neue Datei auswählen möchte."""
        self.open_new_file_requested = True
        self.accept()
        
    def remove_selected(self):
        """Entfernt den ausgewählten Eintrag aus der Liste."""
        current_item = self.list_widget.currentItem()
        if current_item:
            file_to_remove = current_item.data(Qt.ItemDataRole.UserRole)
            if file_to_remove in self.recent_files:
                self.recent_files.remove(file_to_remove)
                self.populate_list()


class SettingsDialog(QDialog):
    """Dialog zur Verwaltung der Anwendungseinstellungen."""
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.settings = current_settings.copy()

        layout = QVBoxLayout(self)
        
        # Einstellungs-Gruppe
        settings_group = QGroupBox("Allgemeine Einstellungen")
        settings_layout = QVBoxLayout()
        
        self.auto_save_checkbox = QCheckBox("Änderungen beim Beenden automatisch speichern")
        self.auto_save_checkbox.setChecked(self.settings.get('auto_save', False))
        self.auto_save_checkbox.stateChanged.connect(
            lambda state: self.update_setting('auto_save', state == Qt.CheckState.Checked.value)
        )
        settings_layout.addWidget(self.auto_save_checkbox)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Speichern")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
    def update_setting(self, key, value):
        """Aktualisiert einen Wert im Einstellungs-Dictionary."""
        self.settings[key] = value

