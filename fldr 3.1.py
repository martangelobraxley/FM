import sys
import uuid
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QDialog, QLabel, 
    QLineEdit, QListWidget, QPushButton, QMenu, QWidget, QListWidgetItem, 
    QAction, QTextEdit, QCheckBox, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt

class FolderBrowserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folder Browser")
        self.setGeometry(100, 100, 800, 600)
        
        self.folder_structure = {'name': 'Main Directory', 'folders': [], 'id': str(uuid.uuid4())}
        self.current_directory = self.folder_structure
        self.breadcrumb_path = []

        self.selected_folders = []

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Editable main directory name
        self.directory_name_input = QLineEdit(self.folder_structure['name'])
        self.directory_name_input.textChanged.connect(self.update_main_directory_name)
        main_layout.addWidget(self.directory_name_input)

        # Input box for creating folders
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Enter folder names here, one per line")
        self.input_box.setFixedHeight(self.directory_name_input.sizeHint().height() * 2)  # Make input box half the original size
        self.input_box.installEventFilter(self)
        main_layout.addWidget(self.input_box)

        # Breadcrumb for navigation
        self.breadcrumb_label = QLabel()
        main_layout.addWidget(self.breadcrumb_label)
        
        # Folder list display
        self.folder_list = QListWidget()
        main_layout.addWidget(self.folder_list)
        
        # Context menu for folder actions
        self.folder_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.folder_list.customContextMenuRequested.connect(self.show_context_menu)

        # Paster button
        self.paster_button = QPushButton("Paster")
        self.paster_button.clicked.connect(self.open_paster_window)
        main_layout.addWidget(self.paster_button)

        # Container widget setup
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.refresh_folder_list()
        self.update_breadcrumb()

    def eventFilter(self, source, event):
        if source == self.input_box and event.type() == event.KeyPress and event.key() == Qt.Key_Return:
            self.create_folders_from_input()
            return True
        return super().eventFilter(source, event)

    def create_folders_from_input(self):
        folder_names = [line.strip() for line in self.input_box.toPlainText().splitlines() if line.strip()]
        for name in folder_names:
            new_folder = {'name': name, 'folders': [], 'id': str(uuid.uuid4())}
            self.current_directory['folders'].append(new_folder)
        self.input_box.clear()
        self.refresh_folder_list()

    def show_context_menu(self, pos):
        context_menu = QMenu()
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.open_folder(self.folder_list.currentItem()))
        context_menu.addAction(open_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_folder(self.folder_list.currentItem()))
        context_menu.addAction(delete_action)

        context_menu.exec_(self.folder_list.mapToGlobal(pos))

    def refresh_folder_list(self):
        self.folder_list.clear()
        for folder in self.current_directory['folders']:
            item_widget = FolderItemWidget(folder, self)  # Use FolderItemWidget for each folder item
            item = QListWidgetItem(self.folder_list)
            item.setSizeHint(item_widget.sizeHint())
            self.folder_list.setItemWidget(item, item_widget)
            item.setData(Qt.UserRole, folder)

    def update_breadcrumb(self):
        path_elements = [self.folder_structure] + self.breadcrumb_path + [self.current_directory]
        breadcrumb_text = " > ".join(f"<a href='{i}'>{folder['name']}</a>" for i, folder in enumerate(path_elements))
        self.breadcrumb_label.setText(breadcrumb_text)
        self.breadcrumb_label.setTextFormat(Qt.RichText)
        self.breadcrumb_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.breadcrumb_label.linkActivated.connect(self.navigate_breadcrumb)

    def navigate_breadcrumb(self, link_index):
        index = int(link_index)
        if index == 0:
            self.current_directory = self.folder_structure
            self.breadcrumb_path = []
        elif index <= len(self.breadcrumb_path):
            self.current_directory = self.breadcrumb_path[index - 1]
            self.breadcrumb_path = self.breadcrumb_path[:index - 1]
        self.refresh_folder_list()
        self.update_breadcrumb()

    def open_folder(self, item):
        if not item:
            return
        folder_data = item.data(Qt.UserRole)
        self.breadcrumb_path.append(self.current_directory)
        self.current_directory = folder_data
        self.refresh_folder_list()
        self.update_breadcrumb()

    def delete_folder(self, item):
        if not item:
            return
        folder_data = item.data(Qt.UserRole)
        if folder_data in self.selected_folders:
            self.selected_folders.remove(folder_data)
        self.current_directory['folders'].remove(folder_data)
        self.refresh_folder_list()

    def create_new_folder(self):
        new_folder = {'name': 'New Folder', 'folders': [], 'id': str(uuid.uuid4())}
        self.current_directory['folders'].append(new_folder)
        self.refresh_folder_list()

    def update_main_directory_name(self, new_name):
        self.folder_structure['name'] = new_name
        if self.current_directory == self.folder_structure:
            self.update_breadcrumb()

    def open_paster_window(self):
        self.paster_window = PasterWindow(self)
        self.paster_window.show()

    def paste_secondary_structure(self, secondary_structure):
        def paste_folders(target_folder, source_folder):
            for folder in source_folder['folders']:
                existing_folder = next((f for f in target_folder['folders'] if f['name'] == folder['name']), None)
                if existing_folder:
                    paste_folders(existing_folder, folder)
                else:
                    new_folder = {'name': folder['name'], 'folders': [], 'id': str(uuid.uuid4())}
                    target_folder['folders'].append(new_folder)
                    paste_folders(new_folder, folder)

        for folder in self.selected_folders:
            paste_folders(folder, secondary_structure)
        self.refresh_folder_list()

class FolderItemWidget(QWidget):
    def __init__(self, folder, parent=None):
        super().__init__(parent)
        self.folder = folder
        self.parent_widget = parent
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        self.label = QLabel(self.folder['name'])
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.label.mouseDoubleClickEvent = self.enable_inline_editing  # Enable inline editing on double click
        layout.addWidget(self.label)
        self.checkbox = QCheckBox()
        layout.addWidget(self.checkbox)
        layout.addStretch()
        layout.setSpacing(10)  # Adjust the horizontal spacing
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for smaller height
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  # Set minimum vertical size policy

        self.checkbox.stateChanged.connect(self.handle_checkbox_state_change)

    def handle_checkbox_state_change(self):
        if self.checkbox.isChecked():
            if self.folder not in self.parent_widget.selected_folders:
                self.parent_widget.selected_folders.append(self.folder)
        else:
            if self.folder in self.parent_widget.selected_folders:
                self.parent_widget.selected_folders.remove(self.folder)

    def enable_inline_editing(self, event):
        self.label.hide()
        self.line_edit = QLineEdit(self.folder['name'])
        self.line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.layout().insertWidget(0, self.line_edit)
        self.line_edit.setFocus()
        self.line_edit.editingFinished.connect(self.finish_inline_editing)

    def finish_inline_editing(self):
        new_name = self.line_edit.text()
        self.folder['name'] = new_name
        self.label.setText(new_name)
        self.line_edit.deleteLater()
        self.label.show()

class PasterWindow(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Paster Structure")
        self.setGeometry(150, 150, 600, 500)
        
        self.paster_structure = {'name': 'Paster Root', 'folders': [], 'id': str(uuid.uuid4())}
        self.current_directory = self.paster_structure
        self.breadcrumb_path = []

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Add directory_name_input attribute
        self.directory_name_input = QLineEdit(self.paster_structure['name'])

        # Input box for creating folders at the top of the folder structure
        self.input_box = QTextEdit()  # Changed to QTextEdit for taller height
        self.input_box.setPlaceholderText("Enter folder names here, one per line")
        self.input_box.setFixedHeight(self.directory_name_input.sizeHint().height() * 2)  # Make input box half the original size
        self.input_box.installEventFilter(self)
        layout.addWidget(self.input_box)

        # Breadcrumb for Paster
        self.breadcrumb_label = QLabel()
        layout.addWidget(self.breadcrumb_label)

        # Folder list for Paster
        self.folder_list = QListWidget()
        layout.addWidget(self.folder_list)
        
        # Context menu for Paster
        self.folder_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.folder_list.customContextMenuRequested.connect(self.show_context_menu)

        # Paste button
        self.paste_button = QPushButton("Paste Structure")
        self.paste_button.clicked.connect(self.paste_structure)
        layout.addWidget(self.paste_button)

        self.setLayout(layout)
        self.refresh_folder_list()
        self.update_breadcrumb()

    def eventFilter(self, source, event):
        if source == self.input_box and event.type() == event.KeyPress and event.key() == Qt.Key_Return:
            self.create_folders_from_input()
            return True
        return super().eventFilter(source, event)

    def create_folders_from_input(self):
        folder_names = [line.strip() for line in self.input_box.toPlainText().splitlines() if line.strip()]
        for name in folder_names:
            new_folder = {'name': name, 'folders': [], 'id': str(uuid.uuid4())}
            self.current_directory['folders'].append(new_folder)
        self.input_box.clear()
        self.refresh_folder_list()

    def paste_structure(self):
        self.main_window.paste_secondary_structure(self.paster_structure)

    def show_context_menu(self, pos):
        context_menu = QMenu()
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.open_folder(self.folder_list.currentItem()))
        context_menu.addAction(open_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_folder(self.folder_list.currentItem()))
        context_menu.addAction(delete_action)

        context_menu.exec_(self.folder_list.mapToGlobal(pos))

    def refresh_folder_list(self):
        self.folder_list.clear()
        for folder in self.current_directory['folders']:
            item_widget = FolderItemWidgetNoCheckbox(folder, self)  # Use FolderItemWidgetNoCheckbox for each folder item
            item = QListWidgetItem(self.folder_list)
            item.setSizeHint(item_widget.sizeHint())
            self.folder_list.setItemWidget(item, item_widget)
            item.setData(Qt.UserRole, folder)

    def update_breadcrumb(self):
        path_elements = [self.paster_structure] + self.breadcrumb_path + [self.current_directory]
        breadcrumb_text = " > ".join(f"<a href='{i}'>{folder['name']}</a>" for i, folder in enumerate(path_elements))
        self.breadcrumb_label.setText(breadcrumb_text)
        self.breadcrumb_label.setTextFormat(Qt.RichText)
        self.breadcrumb_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.breadcrumb_label.linkActivated.connect(self.navigate_breadcrumb)

    def navigate_breadcrumb(self, link_index):
        index = int(link_index)
        if index == 0:
            self.current_directory = self.paster_structure
            self.breadcrumb_path = []
        elif index <= len(self.breadcrumb_path):
            self.current_directory = self.breadcrumb_path[index - 1]
            self.breadcrumb_path = self.breadcrumb_path[:index - 1]
        self.refresh_folder_list()
        self.update_breadcrumb()

    def open_folder(self, item):
        if not item:
            return
        folder_data = item.data(Qt.UserRole)
        self.breadcrumb_path.append(self.current_directory)
        self.current_directory = folder_data
        self.refresh_folder_list()
        self.update_breadcrumb()

    def delete_folder(self, item):
        if not item:
            return
        folder_data = item.data(Qt.UserRole)
        self.current_directory['folders'].remove(folder_data)
        self.refresh_folder_list()

    def create_new_folder(self):
        new_folder = {'name': 'New Folder', 'folders': [], 'id': str(uuid.uuid4())}
        self.current_directory['folders'].append(new_folder)
        self.refresh_folder_list()

class FolderItemWidgetNoCheckbox(QWidget):
    def __init__(self, folder, parent=None):
        super().__init__(parent)
        self.folder = folder
        self.parent_widget = parent
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        self.label = QLabel(self.folder['name'])
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.label.mouseDoubleClickEvent = self.enable_inline_editing  # Enable inline editing on double click
        layout.addWidget(self.label)
        layout.addStretch()
        layout.setSpacing(10)  # Adjust the horizontal spacing
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for smaller height
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  # Set minimum vertical size policy

    def enable_inline_editing(self, event):
        self.label.hide()
        self.line_edit = QLineEdit(self.folder['name'])
        self.line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.layout().insertWidget(0, self.line_edit)
        self.line_edit.setFocus()
        self.line_edit.editingFinished.connect(self.finish_inline_editing)

    def finish_inline_editing(self):
        new_name = self.line_edit.text()
        self.folder['name'] = new_name
        self.label.setText(new_name)
        self.line_edit.deleteLater()
        self.label.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FolderBrowserApp()
    window.show()
    sys.exit(app.exec_())