# app_logic.py
# Diese Datei enthält die Kernlogik der Anwendung zur Datenverwaltung.
# Sie ist verantwortlich für das Verwalten des DataFrames, die Undo/Redo-Funktionalität
# und die Anwendung von Filtern und Sortierungen.

import pandas as pd

class AppLogic:
    """
    Verwaltet den Zustand und die Logik der Inventardaten.
    """
    def __init__(self):
        # Das Haupt-DataFrame, das die Originaldaten eines Tabellenblatts enthält.
        self.df = pd.DataFrame()
        
        # Ein DataFrame, das die aktuell angezeigte, potenziell gefilterte und sortierte Ansicht darstellt.
        self._current_view_df = pd.DataFrame()

        # Stacks für die Undo/Redo-Funktionalität. Speichert den Zustand des df als JSON.
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_steps = 50  # Begrenzt die Anzahl der speicherbaren Undo-Schritte.

        # Aktiver Zustand für Filter und Sortierung
        self._active_filter_col = None
        self._active_filter_text = ""
        self._active_sort_col = None
        self._active_sort_type = None

    def load_new_sheet(self, dataframe: pd.DataFrame):
        """
        Lädt Daten für ein neues Tabellenblatt und setzt den Zustand zurück.

        Args:
            dataframe (pd.DataFrame): Das neue DataFrame, das geladen werden soll.
        """
        self.df = dataframe.copy(deep=True)
        self.undo_stack = []
        self.redo_stack = []
        self._active_filter_col = None
        self._active_filter_text = ""
        self._active_sort_col = None
        self._active_sort_type = None
        
        self.push_state() # Speichert den initialen Zustand für Undo.
        self.apply_filters_and_sort()

    def get_current_view(self) -> pd.DataFrame:
        """Gibt die aktuell gefilterte und sortierte Ansicht der Daten zurück."""
        return self._current_view_df

    def push_state(self):
        """
        Speichert den aktuellen Zustand des DataFrames im Undo-Stack.
        Löscht den Redo-Stack, da eine neue Änderung vorgenommen wurde.
        """
        try:
            # Serialisiert das DataFrame in einen JSON-String für den Vergleich und die Speicherung.
            # `orient='split'` ist effizient und bewahrt dtypes gut.
            current_df_json = self.df.to_json(orient='split', date_format='iso')

            # Nur pushen, wenn sich der Zustand tatsächlich geändert hat.
            if not self.undo_stack or self.undo_stack[-1] != current_df_json:
                self.undo_stack.append(current_df_json)
                self.redo_stack = []  # Eine neue Aktion löscht den Redo-Stack.
                
                # Begrenzt die Größe des Undo-Stacks, um Speicher zu sparen.
                if len(self.undo_stack) > self.max_undo_steps:
                    self.undo_stack.pop(0)
        except Exception as e:
            print(f"Fehler beim Speichern des Undo-Zustands: {e}")

    def undo(self) -> bool:
        """
        Macht die letzte Aktion rückgängig.
        Gibt True zurück, wenn erfolgreich, sonst False.
        """
        if len(self.undo_stack) > 1:
            # Bewegt den aktuellen Zustand zum Redo-Stack
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)

            # Lädt den vorherigen Zustand
            previous_state_json = self.undo_stack[-1]
            self.df = pd.read_json(previous_state_json, orient='split')
            self.apply_filters_and_sort()
            return True
        return False

    def redo(self) -> bool:
        """
        Stellt die zuletzt rückgängig gemachte Aktion wieder her.
        Gibt True zurück, wenn erfolgreich, sonst False.
        """
        if self.redo_stack:
            # Nimmt den Zustand vom Redo-Stack und macht ihn zum aktuellen Zustand
            state_to_restore = self.redo_stack.pop()
            self.undo_stack.append(state_to_restore)

            self.df = pd.read_json(state_to_restore, orient='split')
            self.apply_filters_and_sort()
            return True
        return False

    def apply_filters_and_sort(self, filter_col=None, filter_text=None, sort_col=None, sort_type=None):
        """
        Wendet die übergebenen oder die gespeicherten Filter- und Sortierkriterien an.
        """
        # Aktualisiert die internen Kriterien, wenn neue übergeben werden.
        if filter_col is not None: self._active_filter_col = filter_col
        if filter_text is not None: self._active_filter_text = filter_text
        if sort_col is not None: self._active_sort_col = sort_col
        if sort_type is not None: self._active_sort_type = sort_type
        
        if self.df.empty:
            self._current_view_df = pd.DataFrame(columns=self.df.columns)
            return

        temp_df = self.df.copy()

        # 1. Filter anwenden
        if self._active_filter_text:
            search_term = self._active_filter_text.strip().lower()
            if search_term:
                # Filtern auf eine bestimmte Spalte oder alle Spalten
                if self._active_filter_col and self._active_filter_col in temp_df.columns:
                    # Stellt sicher, dass die Spalte für den Vergleich als String behandelt wird.
                    temp_df = temp_df[temp_df[self._active_filter_col].astype(str).str.lower().str.contains(search_term, na=False)]
                else:
                    # Sucht in allen Spalten
                    temp_df = temp_df[
                        temp_df.apply(lambda row: row.astype(str).str.lower().str.contains(search_term, na=False).any(), axis=1)
                    ]

        # 2. Sortierung anwenden
        if self._active_sort_col and self._active_sort_col in temp_df.columns:
            column_to_sort = self._active_sort_col
            
            ascending = True
            is_numeric_sort = False

            if self._active_sort_type in ['za', 'num_desc']:
                ascending = False
            
            if self._active_sort_type in ['num_asc', 'num_desc']:
                is_numeric_sort = True

            if is_numeric_sort:
                # Konvertiert die Spalte für die Sortierung zu einem numerischen Typ.
                # `errors='coerce'` verwandelt ungültige Werte in `NaN`.
                temp_df[column_to_sort] = pd.to_numeric(temp_df[column_to_sort], errors='coerce')
                # `na_position='last'` stellt sicher, dass leere Werte immer am Ende landen.
                temp_df = temp_df.sort_values(by=column_to_sort, ascending=ascending, na_position='last')
            else:
                # Sortiert als Text, ignoriert Groß-/Kleinschreibung.
                temp_df = temp_df.sort_values(by=column_to_sort, ascending=ascending, na_position='last', key=lambda col: col.astype(str).str.lower())
        
        self._current_view_df = temp_df

    def reset_filters_and_sort(self):
        """Setzt alle Filter- und Sortierkriterien zurück."""
        self.apply_filters_and_sort(filter_col="", filter_text="", sort_col="", sort_type="")

