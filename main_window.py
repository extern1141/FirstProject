# main_window.py
# Enthält die `MainWindow`-Klasse, die das Hauptfenster der Anwendung definiert.
# Diese Klasse ist für die Erstellung und Anordnung aller UI-Widgets verantwortlich
# und für die Verknüpfung von Benutzeraktionen (Klicks, Eingaben) mit der Anwendungslogik.

import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QTableWidget, QTableWidgetItem, QMessageBox, QTabBar, QMenu, QFileDialog, 
    QStatusBar, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction, QColor, QBrush

# Importiere Logik und Helfer aus den neuen Modulen
from app_logic import AppLogic
import excel_handler
from ui_helpers import kopiere_markierte_zellen
from dialogs import ConfirmExitDialog, FilterDialog, RecentFilesDialog, SettingsDialog
from settings import EXCEL_PFAD, LOGO_PFAD

class MainWindow(QMainWindow):
    """
    Das Hauptfenster der Inventar-Anwendung.
    """
    def __init__(self):
        super().__init__()
        
        # Initialisiert die Kernlogik für die Datenverwaltung
        self.logic = AppLogic()
        
        # Speichert Pfade und Einstellungen
        self.settings = self._load_settings()
        self.excel_path = self.settings.get('last_excel_path', EXCEL_PFAD)
        self.sheet_names = []
        self.current_sheet = ""

        # UI-bezogene Zustände
        self.search_hits = []
        self.current_hit_index = -1
        
        self.init_ui()
        self._post_init_load()

    # --- UI Initialisierung ---
    def init_ui(self):
        """Baut die Benutzeroberfläche auf."""
        self.setWindowTitle("Inventarverwaltung")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(LOGO_PFAD))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Obere Leiste mit Aktionen
        top_bar_layout = QHBoxLayout()
        self._create_top_bar(top_bar_layout)
        main_layout.addLayout(top_bar_layout)

        # Tab-Leiste für Tabellenblätter
        self.tab_bar = QTabBar()
        self.tab_bar.setMovable(True)
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.currentChanged.connect(self._handle_sheet_change)
        self.tab_bar.tabCloseRequested.connect(self._handle_sheet_close)
        main_layout.addWidget(self.tab_bar)

        # Die Haupttabelle
        self.table = QTableWidget()
        self._setup_table()
        main_layout.addWidget(self.table)
        
        # Statusleiste
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.show_status("Bereit.")

    def _create_top_bar(self, layout: QHBoxLayout):
        """Erstellt die obere Leiste mit Buttons und Suchfeld."""
        # Dateimenü
        btn_file = QPushButton("Datei")
        file_menu = QMenu()
        file_menu.addAction("Neue Datei öffnen...", self._handle_open_new_file)
        file_menu.addAction("Zuletzt geöffnet...", self._show_recent_files_dialog)
        file_menu.addSeparator()
        file_menu.addAction("Speichern", self._handle_save)
        file_menu.addSeparator()
        file_menu.addAction("Beenden", self.close)
        btn_file.setMenu(file_menu)
        layout.addWidget(btn_file)

        # Suchfeld
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("In Tabelle suchen...")
        self.search_input.textChanged.connect(self._handle_search)
        layout.addWidget(self.search_input)
        
        # Undo/Redo Buttons
        undo_button = QPushButton("Rückgängig")
        undo_button.clicked.connect(self._handle_undo)
        layout.addWidget(undo_button)

        redo_button = QPushButton("Wiederherstellen")
        redo_button.clicked.connect(self._handle_redo)
        layout.addWidget(redo_button)
        
        layout.addStretch()

        # Einstellungsbutton
        settings_button = QPushButton("Einstellungen")
        settings_button.clicked.connect(self._show_settings_dialog)
        layout.addWidget(settings_button)

    def _setup_table(self):
        """Konfiguriert die QTableWidget."""
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.AnyKeyPressed)
        self.table.cellChanged.connect(self._handle_cell_changed)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_table_context_menu)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)

    def _post_init_load(self):
        """Lädt die initialen Daten, nachdem das UI-Setup abgeschlossen ist."""
        # Verzögert den Ladevorgang, damit das Fenster zuerst gezeichnet werden kann.
        QTimer.singleShot(100, self._load_initial_data)
        
    # --- Daten- und Dateihandling ---
    def _load_initial_data(self):
        """Lädt die erste Excel-Datei beim Start."""
        if os.path.exists(self.excel_path):
            self._load_excel_file(self.excel_path)
        else:
            self.show_status(f"Standard-Excel-Datei nicht gefunden. Bitte öffnen Sie eine Datei.", 5000)
            self._show_recent_files_dialog()

    def _load_excel_file(self, file_path: str, sheet_to_select: str = None):
        """
        Lädt eine komplette Excel-Datei, aktualisiert das UI und die Logik.
        """
        self.show_status(f"Lade '{os.path.basename(file_path)}'...")
        try:
            self.sheet_names = excel_handler.get_sheet_names(file_path)
            if not self.sheet_names:
                self.show_error("Keine Tabellenblätter", f"Die Datei '{os.path.basename(file_path)}' enthält keine Tabellenblätter.")
                return

            self.excel_path = file_path
            self._update_recent_files(file_path)

            # Wähle das erste Blatt aus, wenn keins angegeben ist oder das angegebene nicht existiert.
            self.current_sheet = sheet_to_select if sheet_to_select in self.sheet_names else self.sheet_names[0]
            
            self._load_current_sheet_data()
            self._update_tab_bar()
            self.show_status(f"'{os.path.basename(file_path)}' geladen.", 3000)

        except (FileNotFoundError, IOError, ValueError, Exception) as e:
            self.show_error("Fehler beim Laden der Excel-Datei", str(e))
            self.clear_all_data()

    def _load_current_sheet_data(self):
        """Lädt die Daten des aktuell ausgewählten Tabellenblatts."""
        if not self.current_sheet:
            return
        
        try:
            df = excel_handler.load_sheet(self.excel_path, self.current_sheet)
            self.logic.load_new_sheet(df)
            self._update_table_view()
        except Exception as e:
            self.show_error(f"Fehler beim Laden von Blatt '{self.current_sheet}'", str(e))
            self.clear_all_data()

    def _handle_save(self, show_message=True):
        """Speichert das aktuelle Tabellenblatt in die Excel-Datei."""
        if self.logic.df.empty or not self.current_sheet:
            if show_message:
                self.show_warning("Nichts zu speichern", "Es sind keine Daten zum Speichern geladen.")
            return False

        try:
            excel_handler.save_sheet(self.excel_path, self.current_sheet, self.logic.df)
            self.logic.push_state() # Der gespeicherte Zustand ist der neue "saubere" Zustand
            if show_message:
                self.show_status(f"Blatt '{self.current_sheet}' erfolgreich gespeichert.", 3000)
            return True
        except (IOError, Exception) as e:
            if show_message:
                self.show_error("Fehler beim Speichern", str(e))
            return False
            
    def clear_all_data(self):
        """Setzt die Anwendung in einen sauberen, leeren Zustand zurück."""
        self.logic.load_new_sheet(pd.DataFrame())
        self.sheet_names = []
        self.current_sheet = ""
        self._update_tab_bar()
        self._update_table_view()

    # --- UI Aktualisierungen ---
    def _update_table_view(self):
        """Aktualisiert die QTableWidget mit den Daten aus der AppLogic."""
        self.table.blockSignals(True) # Verhindert, dass cellChanged während der Aktualisierung ausgelöst wird
        
        df_view = self.logic.get_current_view()
        self.table.setRowCount(df_view.shape[0])
        self.table.setColumnCount(df_view.shape[1])
        self.table.setHorizontalHeaderLabels(df_view.columns.astype(str))

        for r_idx, (orig_index, row) in enumerate(df_view.iterrows()):
            for c_idx, value in enumerate(row):
                item_text = "" if pd.isna(value) else str(value)
                item = QTableWidgetItem(item_text)
                self.table.setItem(r_idx, c_idx, item)

        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)
        self._handle_search(self.search_input.text()) # Suche erneut anwenden, um Highlights zu aktualisieren
        
    def _update_tab_bar(self):
        """Aktualisiert die Tab-Leiste mit den aktuellen Tabellenblattnamen."""
        self.tab_bar.blockSignals(True)
        self.tab_bar.clear()
        
        for name in self.sheet_names:
            self.tab_bar.addTab(name)
            
        if self.current_sheet in self.sheet_names:
            index = self.sheet_names.index(self.current_sheet)
            self.tab_bar.setCurrentIndex(index)
            
        self.tab_bar.blockSignals(False)
        
    def _highlight_search_results(self):
        """Hebt Suchergebnisse in der Tabelle hervor."""
        # Zuerst alle alten Hervorhebungen entfernen
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item:
                    item.setBackground(QColor("white"))
        
        if not self.search_hits:
            return
            
        # Neue Hervorhebungen setzen
        for r, c in self.search_hits:
            item = self.table.item(r, c)
            if item:
                item.setBackground(QBrush(QColor("yellow")))

    # --- Event-Handler für Benutzeraktionen ---
    def _handle_sheet_change(self, index: int):
        """Wird aufgerufen, wenn der Benutzer auf einen anderen Tab klickt."""
        new_sheet = self.tab_bar.tabText(index)
        if new_sheet and new_sheet != self.current_sheet:
            self.current_sheet = new_sheet
            self._load_current_sheet_data()
            
    def _handle_sheet_close(self, index: int):
        """Fragt, ob ein Tabellenblatt aus der Excel-Datei gelöscht werden soll."""
        # HINWEIS: Logik zum Löschen von Blättern aus Excel ist komplex und hier
        # zur Vereinfachung weggelassen. Dies schließt nur den Tab in der UI.
        sheet_name = self.tab_bar.tabText(index)
        reply = QMessageBox.question(self, "Tab schließen",
                                     f"Möchten Sie den Tab für '{sheet_name}' wirklich schließen?\n(Dies löscht das Blatt nicht aus der Excel-Datei)",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.tab_bar.removeTab(index)

    def _handle_cell_changed(self, row: int, column: int):
        """Wird aufgerufen, wenn der Benutzer den Inhalt einer Zelle ändert."""
        new_text = self.table.item(row, column).text()
        
        # Den originalen Index aus dem View-DataFrame holen
        try:
            original_index = self.logic.get_current_view().index[row]
            column_name = self.logic.df.columns[column]
            
            # Logik-Schicht vor der Änderung benachrichtigen, um Undo zu ermöglichen
            self.logic.push_state()
            
            # Die Änderung im Haupt-DataFrame durchführen
            self.logic.df.loc[original_index, column_name] = new_text
            
            self.show_status("Zelle geändert. Ungespeicherte Änderungen.", 2000)
        except IndexError:
            # Passiert, wenn in eine neue, leere Zeile getippt wird.
            # Diese Logik müsste erweitert werden, um neue Zeilen korrekt zu behandeln.
            print(f"Warnung: Änderung in Zeile {row} konnte nicht zugeordnet werden.")
            pass

    def _handle_open_new_file(self):
        """Öffnet einen Dateidialog, um eine neue Excel-Datei auszuwählen."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Excel-Datei öffnen",
            os.path.dirname(self.excel_path),
            "Excel-Dateien (*.xlsx *.xls)"
        )
        if file_path:
            self._load_excel_file(file_path)
            
    def _handle_search(self, text: str):
        """Filtert die Tabellenansicht basierend auf dem Suchtext."""
        self.search_hits = []
        text = text.strip().lower()

        if not text:
            self._highlight_search_results()
            self.show_status("Suche zurückgesetzt.", 1500)
            return
            
        df_view = self.logic.get_current_view()
        for r_idx, (orig_index, row) in enumerate(df_view.iterrows()):
            for c_idx, value in enumerate(row):
                if text in str(value).lower():
                    self.search_hits.append((r_idx, c_idx))
        
        self.show_status(f"{len(self.search_hits)} Treffer gefunden.", 2000)
        self._highlight_search_results()
        
    def _handle_undo(self):
        if self.logic.undo():
            self._update_table_view()
            self.show_status("Aktion rückgängig gemacht.", 2000)
        else:
            self.show_status("Keine weiteren Aktionen zum Rückgängigmachen.", 2000)

    def _handle_redo(self):
        if self.logic.redo():
            self._update_table_view()
            self.show_status("Aktion wiederhergestellt.", 2000)
        else:
            self.show_status("Keine weiteren Aktionen zum Wiederherstellen.", 2000)

    # --- Dialog-Handler ---
    def _show_recent_files_dialog(self):
        """Zeigt den Dialog mit den zuletzt verwendeten Dateien."""
        dialog = RecentFilesDialog(self.settings.get('recent_excel_files', []), self)
        if dialog.exec():
            # Aktualisierte Liste der letzten Dateien speichern
            self.settings['recent_excel_files'] = dialog.recent_files
            self._save_settings()

            if dialog.open_new_file_requested:
                self._handle_open_new_file()
            elif dialog.selected_file:
                self._load_excel_file(dialog.selected_file)

    def _show_filter_dialog(self):
        """Zeigt den Filter- und Sortierdialog."""
        if self.logic.df.empty:
            self.show_warning("Keine Daten", "Es sind keine Daten zum Filtern oder Sortieren geladen.")
            return

        dialog = FilterDialog(self.logic.df.columns.tolist(), self)
        if dialog.exec():
            self.logic.apply_filters_and_sort(
                dialog.filter_column_name,
                dialog.filter_text,
                dialog.sort_column_name,
                dialog.sort_type
            )
            self._update_table_view()
            self.show_status("Filter und Sortierung angewendet.", 2000)

    def _show_settings_dialog(self):
        """Zeigt den Einstellungsdialog."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.settings
            self._save_settings()
            self.show_status("Einstellungen gespeichert.", 2000)

    def _show_table_context_menu(self, pos):
        """Zeigt das Kontextmenü für die Tabelle."""
        menu = QMenu()
        menu.addAction("Kopieren", lambda: kopiere_markierte_zellen(self.table))
        # Hier können weitere Aktionen wie "Einfügen", "Zeile löschen" etc. hinzugefügt werden.
        menu.exec(self.table.mapToGlobal(pos))
        
    # --- Einstellungs- und Zustandsverwaltung ---
    def _load_settings(self) -> dict:
        """Lädt Einstellungen aus einer JSON-Datei."""
        try:
            with open("app_settings.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'recent_excel_files': [], 'auto_save': False}

    def _save_settings(self):
        """Speichert die aktuellen Einstellungen in eine JSON-Datei."""
        try:
            self.settings['last_excel_path'] = self.excel_path
            with open("app_settings.json", 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            self.show_warning("Speicherfehler", f"Einstellungen konnten nicht gespeichert werden: {e}")

    def _update_recent_files(self, file_path: str):
        """Aktualisiert die Liste der zuletzt verwendeten Dateien."""
        recent = self.settings.get('recent_excel_files', [])
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        self.settings['recent_excel_files'] = recent[:10] # Auf 10 begrenzen
        self._save_settings()
        
    # --- Hilfsfunktionen für Nachrichten ---
    def show_status(self, message, timeout=0):
        self.statusBar.showMessage(message, timeout)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)
        
    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)
        
    # --- Beenden der Anwendung ---
    def closeEvent(self, event):
        """Wird aufgerufen, wenn der Benutzer versucht, das Fenster zu schließen."""
        # TODO: Hier eine Prüfung auf ungespeicherte Änderungen einfügen.
        # z.B. if self.logic.has_unsaved_changes():
        
        dialog = ConfirmExitDialog(self)
        if dialog.exec():
            self._save_settings()
            event.accept()
        else:
            event.ignore()

