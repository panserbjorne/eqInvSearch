'''GUI application to search and display items from EQ inventory files'''

# Options for compiling with Nuitka:
# nuitka-project: --onefile
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --windows-console-mode=disable
# nuitka-project: --windows-icon-from-ico=eqInvSearch.ico
# nuitka-project: --include-data-file=eqInvSearch.ico=eqInvSearch.ico

import os
import re
import sys
import time
from natsort import natsorted
import platformdirs
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)
import qdarktheme
import yaml

SETTINGS_FILE = 'settings.yml'

class IndentDumper(yaml.Dumper):
    '''Custom YAML Dumper that provides indentation'''
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

class MainWindow(QWidget):
    '''Main QT Window'''

    def load_config(self):
        '''Load config from file'''

        if os.path.isfile(self.config_file_path):
            with open (self.config_file_path, 'r', encoding='utf-8') as yml_file:
                self.config = yaml.safe_load(yml_file)
        if not self.config:
            self.config = {}
        if 'invDirectories' not in self.config:
            self.config['invDirectories'] = []
        if 'showItemIDs' not in self.config:
            self.config['showItemIDs'] = False
        if 'sortCharacters' not in self.config:
            self.config['sortCharacters'] = False

    def get_inventory_files(self):
        '''Finds inventory files in provided directories'''

        # Abort if no directories have been provided
        if not self.config['invDirectories']:
            self.inventory_files = []
        new_inventory_files = [] # For comparison

        # Find inventory files each EQ directory
        for inv_directory in self.config['invDirectories']:
            for file in os.listdir(inv_directory):
                if file.endswith('-Inventory.txt'):
                    new_inventory_files.append({'dir': inv_directory, 'file': file})

        # If the known inventory files list has changed, mark them as never loaded
        if self.inventory_files != new_inventory_files:
            self.inventory_files = new_inventory_files
            self.inventories_last_loaded = 0
        return

    def load_inventories(self):
        '''Load items from inventory files'''

        previous_selected_char = self.current_selected_char # For comparsion
        self.char_select_combo.clear()

        self.inventories_last_loaded = time.time()

        # Set empty variables to be filled
        character_list = []
        self.inventory = {}

        if len(self.inventory_files) == 0:
            self.tabs.setTabEnabled(0, False)
            self.tabs.setCurrentWidget(self.settings_tab)
        else:
            self.tabs.setTabEnabled(0, True)

        for inventory_file in self.inventory_files:
            character_name = inventory_file['file'].replace('-Inventory.txt', '')

            if character_name not in character_list:
                character_list.append(character_name)

            inventory_file_path = os.path.join(inventory_file['dir'], inventory_file['file'])

            with open(inventory_file_path, 'r', encoding='utf-8') as file:
                inventory_text = file.read()

            find_re = r'(?P<itemLocation>[\w-]+)\t(?P<itemName>.+)\t(?P<itemID>[\d]+)\t(?P<itemCount>[\d]+)\t(?P<itemSlots>[\d]+)'
            for item in re.finditer(find_re, inventory_text):
                item_location = item.group('itemLocation')
                item_name = item.group('itemName')
                item_id = item.group('itemID')
                item_count = int(item.group('itemCount'))

                if item_id == '0': # Item is either coin or an empty slot
                    if item_count == 0:
                        continue
                    elif item_location == 'General-Coin' or item_location == 'Bank-Coin':
                        item_location = item_location.replace('-Coin', '')
                        item_id = 'in Plat'
                        item_name = 'Coins'
                        item_count = int(item_count / 1000)
                    else:
                        continue

                if item_id not in self.inventory:
                    self.inventory[item_id] = {'name': item_name, 'totalCount': 0, 'characters': {}}

                self.inventory[item_id]['totalCount'] += item_count

                if character_name not in self.inventory[item_id]['characters']:
                    self.inventory[item_id]['characters'][character_name] = {'locations': {}, 'count': 0}

                self.inventory[item_id]['characters'][character_name]['count'] += item_count

                if item_location not in self.inventory[item_id]['characters'][character_name]['locations']:
                    self.inventory[item_id]['characters'][character_name]['locations'][item_location] = 0
                self.inventory[item_id]['characters'][character_name]['locations'][item_location] += item_count

        # Sort the inventory by Item ID
        self.inventory = dict(natsorted(self.inventory.items()))

        # Sort the character list alphabetically
        if self.config["sortCharacters"]:
            character_list.sort()
        # Add the All Characters option at the beginning
        character_list.insert(0, 'All')

        # Update the character combo box
        self.char_select_combo.addItems(character_list)

        # Attempt to re-select the previous character, defaults to first option (All)
        previous_char_index = self.char_select_combo.findText(previous_selected_char)
        if previous_char_index == -1:
            previous_char_index = 0
        self.char_select_combo.setCurrentIndex(previous_char_index)

    def find_inv_items(self):
        '''Searches the stored inventory for search box contents'''

        self.found_items_tree.clear() # Remove the current search results

        search_string = self.search_box_edit.displayText()

        # No need to process if search box is empty
        if not search_string:
            return None

        self.current_selected_char = self.char_select_combo.currentText()

        found_items = [] # To hold matching items
        search_string = search_string.replace("'","['`]") # EQ sometimes uses `, othertimes '

        characters_with_matches = ['All']

        # Loop thorugh all items that were retrieved from inventory files
        for item_id, item in self.inventory.items():
            item_name = item['name']
            try:
                item_matched = re.search(fr"{search_string}", item_name, re.IGNORECASE)
            except re.PatternError: # Discard invalid regex patterns
                item_matched = False

            #  Can either match on item or item ID
            if item_matched or search_string in str(item_id):
                found_items_updated = False

                if self.config['showItemIDs']:
                    item_id_str = f' ({item_id})'
                else:
                    item_id_str = ''

                # When searching all characters, create a parent row for the item with the grand total
                if self.current_selected_char == 'All':
                    total_count = str(item['totalCount'])
                    found_item = QTreeWidgetItem([item_name + item_id_str, total_count])
                    found_item.setForeground(0,QColor(255,175,255))
                    found_item.setForeground(1,QColor(255,175,255))
                    found_items_updated = True
                for character, character_info in item['characters'].items():
                    if character not in characters_with_matches:
                        characters_with_matches.append(character)
                    character_count = str(character_info['count'])
                    # When searching all characters, create a character row
                    if self.current_selected_char == 'All':
                        found_char = QTreeWidgetItem([character, character_count])
                        found_char.setTextAlignment(1,Qt.AlignmentFlag.AlignRight)
                        found_char.setForeground(0,QColor(100,200,255))
                        found_char.setForeground(1,QColor(100,200,255))
                        found_item.addChild(found_char)
                    # When searching a single character, create a parent row for the item with the character's total
                    elif character == self.current_selected_char:
                        found_item = QTreeWidgetItem([item_name + item_id_str, character_count])
                        found_item.setForeground(0,QColor(255,175,255))
                        found_item.setForeground(1,QColor(255,175,255))
                        found_items_updated = True
                    else:
                        continue
                    location_row_odd = True
                    for location, location_count in character_info['locations'].items():
                        location_friendly_name = location.replace('-Slot',' - ')
                        location_friendly_name = re.sub(r'^([a-zA-Z]+)(\d+)', r'\1\t\2', location_friendly_name)
                        #foundItemsTree.insert(locationParent, 'end', text=locationFriendlyName, values=(str(locationCount)), tags=locationRowTag) # Add item locations
                        found_location = QTreeWidgetItem([location_friendly_name, str(location_count)])
                        found_location.setTextAlignment(1,Qt.AlignmentFlag.AlignRight)
                        if location_row_odd is True:
                            found_location.setBackground(0,QColor(50,50,50))
                            found_location.setBackground(1,QColor(50,50,50))
                            location_row_odd = False
                        else:
                            found_location.setBackground(0,QColor(70,70,70))
                            found_location.setBackground(1,QColor(70,70,70))
                            location_row_odd = True
                        if self.current_selected_char == "All":
                            # Searching all characters, use the character row as the parent
                            found_char.addChild(found_location)
                        else:
                            # Searching a single character, use the item row as the parent
                            found_item.addChild(found_location)

                if found_items_updated is True:
                    found_item.setTextAlignment(1,Qt.AlignmentFlag.AlignRight)
                    found_items.append(found_item)

        if len(found_items) == 0:
            no_items_row = QTreeWidgetItem(['No matching items found.'])
            found_items.append(no_items_row)
        self.found_items_tree.addTopLevelItems(found_items)
        self.found_items_tree.expandAll()

        for index in range(self.char_select_combo.count()):
            character = self.char_select_combo.itemText(index)
            if character not in characters_with_matches:
                background_color = QColor(240,120,120)
            else:
                #background_color = None
                background_color = QColor(120,240,120)
            self.char_select_combo.setItemData(index, background_color, Qt.ItemDataRole.ForegroundRole)
        return

    def invdirs_add(self):
        '''Add an EQ directory via prompt'''
        new_invdir_dialog = QFileDialog(self)
        new_invdir_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        new_invdir_dialog.setNameFilter("Inventories (*-Inventory.txt)")
        new_invdir_dialog.setViewMode(QFileDialog.ViewMode.List)
        if new_invdir_dialog.exec():
            selected_inv_file = new_invdir_dialog.selectedFiles()
            if selected_inv_file:
                new_invdir = os.path.dirname(selected_inv_file[0])
                if not os.path.isdir(new_invdir):
                    return
                new_invdir = os.path.normpath(new_invdir)
                existing_invdirs_count = self.settings_invdirs_tree.topLevelItemCount()
                # Abort if path already exists
                for index in range(existing_invdirs_count):
                    existing_invdir = self.settings_invdirs_tree.topLevelItem(index).data(0,0)
                    if existing_invdir == new_invdir:
                        return
                invdir_item = QTreeWidgetItem([new_invdir])
                self.settings_invdirs_tree.addTopLevelItem(invdir_item)
                self.mark_settings_changed()
        return

    def invdirs_del(self):
        '''Removes the currently selected EQ directory'''
        selected_dir = self.settings_invdirs_tree.selectedIndexes()
        if selected_dir:
            selected_row = selected_dir[0].row()
            self.settings_invdirs_tree.takeTopLevelItem(selected_row)
            self.mark_settings_changed()

    def mark_settings_changed(self):
        '''Records that settings are changed for later prompt'''
        self.settings_changed = True

    def settings_save(self):
        '''Save configured settings'''
        self.settings_changed = False
        # Save Inventory Directory Tree
        new_invdirs_count = self.settings_invdirs_tree.topLevelItemCount()
        self.config['invDirectories'] = []
        for index in range(new_invdirs_count):
            new_invdir = self.settings_invdirs_tree.topLevelItem(index).data(0,0)
            self.config['invDirectories'].append(new_invdir)
        # Save Show Item IDs checkbox
        self.config['showItemIDs'] = self.settings_showids_check.isChecked()

        self.config['sortCharacters'] = self.settings_sortchars_check.isChecked()

        # Save settings to file
        if not os.path.isdir(self.config_dir):
            os.makedirs(self.config_dir)
        with open (self.config_file_path, 'w', encoding='utf-8') as yml_file:
            yaml.dump(self.config, stream=yml_file, Dumper=IndentDumper)

        # Re-load inventory and re-run search
        self.get_inventory_files()
        self.load_inventories()
        self.find_inv_items()

    def update_settings_tab(self):
        '''Refreshes the settings tab'''
        # Update the Tree of Inventory Dirs
        self.settings_invdirs_tree.clear()
        if self.config['invDirectories']:
            for invdir in self.config['invDirectories']:
                invdir_item = QTreeWidgetItem([invdir])
                self.settings_invdirs_tree.addTopLevelItem(invdir_item)
        # Update the Show Item IDs checkbox
        self.settings_showids_check.setChecked(self.config['showItemIDs'])
        # Update the Sort Characters checkbox
        self.settings_sortchars_check.setChecked(self.config['sortCharacters'])
        self.settings_changed = False

    def tab_clicked(self, tab_clicked_index):
        '''Runs tab-specific functions when tab bar is clicked'''
        # Ignore when current tab is clicked
        if self.tabs.currentIndex() == tab_clicked_index:
            return
        tab_clicked = self.tabs.tabText(tab_clicked_index)
        if tab_clicked == 'Settings':
            self.update_settings_tab()
        else:
            if self.settings_changed is True:
                save_prompt = QMessageBox(self)
                save_prompt.setWindowTitle('EQ Inventory Searcher')
                save_prompt.setText('Save updated settings?')
                save_prompt.setStandardButtons(QMessageBox.Save | QMessageBox.Discard)
                save_prompt_resp = save_prompt.exec()
                if save_prompt_resp == 2048:
                    self.settings_save()
                else:
                    self.settings_changed = False

    def char_select_combo_move(self, direction):
        total_items = self.char_select_combo.count()
        selected_index = self.char_select_combo.currentIndex()
        if direction == 'home':
            new_index = 0
        elif direction == 'up':
            if selected_index == 0:
                new_index = total_items - 1
            else:
                new_index = selected_index - 1
        else:
            if selected_index == total_items - 1:
                new_index = 0
            else:
                new_index = selected_index + 1
        self.char_select_combo.setCurrentIndex(new_index)
        return


    def tab_changed(self, new_active_tab_index):
        '''Runs tab-specific functions when active tab is changed'''
        new_active_tab = self.tabs.tabText(new_active_tab_index)
        if new_active_tab == 'Search':
            self.search_box_edit.setFocus()

    def __init__(self, *args, **kwargs):

        self.config = {}
        self.inventory_files = []
        self.inventory = {}
        self.inventories_last_loaded = 0
        self.current_selected_char = None
        self.settings_changed = False

        super().__init__(*args, **kwargs)

        self.setWindowTitle('EQ Inventory Searcher')
        self.resize(470,600)
        window_icon = QIcon()
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(__file__)
        icon_path = os.path.join(application_path, 'eqInvSearch.ico')
        window_icon = QIcon()
        window_icon.addFile(icon_path)
        self.setWindowIcon(window_icon)

        self.base_layout = QGridLayout(self)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.base_layout)

        self.tabs = QTabWidget(self)
        self.base_layout.addWidget(self.tabs, 0, 0)

        self.search_tab = QWidget(self)
        self.tabs.addTab(self.search_tab, 'Search')
        self.settings_tab = QWidget(self)
        self.tabs.addTab(self.settings_tab, 'Settings')
        self.about_tab = QWidget(self)
        self.tabs.addTab(self.about_tab, 'About')

        self.search_tab_layout = QGridLayout()
        self.search_box_layout = QLabel('Search Items:', self)
        self.char_select_label = QLabel('Character:', self)
        self.search_box_edit = QLineEdit(self)
        self.char_select_combo = QComboBox(self)
        self.found_items_tree = QTreeWidget(self)
        self.found_items_tree.setColumnCount(2)
        self.found_items_tree.setHeaderLabels(['', 'Quantity'])
        self.found_items_tree.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.found_items_tree.setColumnWidth(0,350)
        self.found_items_tree.setColumnWidth(1,55)

        self.search_tab.setLayout(self.search_tab_layout)
        self.search_tab_layout.addWidget(self.search_box_layout, 0, 0)
        self.search_tab_layout.addWidget(self.char_select_label, 0, 4, 1, 2)
        self.search_tab_layout.addWidget(self.search_box_edit, 1, 0, 1, 4)
        self.search_tab_layout.addWidget(self.char_select_combo, 1, 4, 1, 2)
        self.search_tab_layout.addWidget(self.found_items_tree, 2, 0, 1, 6)
        self.search_tab_layout.setRowStretch(2,1)

        self.settings_tab_layout = QGridLayout()
        self.settings_invdirs_label = QLabel('Directories containing inventory files:', self)
        self.settings_invdirs_tree = QTreeWidget(self)
        self.settings_invdirs_tree.setColumnCount(1)
        self.settings_invdirs_tree.setHeaderHidden(True)
        self.settings_invdirs_add_btn = QPushButton('Add Directory', self)
        self.settings_invdirs_del_btn = QPushButton('Delete Directory', self)
        self.settings_invdirs_end_splitter = QFrame()
        self.settings_invdirs_end_splitter.setFrameShape( QFrame.HLine )
        self.settings_invdirs_end_splitter.setMidLineWidth(10)
        self.settings_showids_check = QCheckBox(text="Show Item IDs")
        self.settings_sortchars_check = QCheckBox(text="Sort Characters")
        self.settings_enableregex_check = QCheckBox(text="Enable Regex")
        self.settings_enableregex_check.setEnabled(False)
        self.settings_enableregex_check.setChecked(True)
        self.settings_misc_end_splitter = QFrame()
        self.settings_misc_end_splitter.setFrameShape( QFrame.HLine )
        self.settings_misc_end_splitter.setMidLineWidth(10)
        self.settings_save_btn = QPushButton('Save Settings', self)

        self.settings_tab.setLayout(self.settings_tab_layout)
        self.settings_tab_layout.addWidget(self.settings_invdirs_label,0,0,1,3)
        self.settings_tab_layout.addWidget(self.settings_invdirs_tree,1,0,1,3)
        self.settings_tab_layout.addWidget(self.settings_invdirs_add_btn,2,0)
        self.settings_tab_layout.addWidget(self.settings_invdirs_del_btn,2,2)
        self.settings_tab_layout.addWidget(self.settings_invdirs_end_splitter,3,0,1,3)
        self.settings_tab_layout.addWidget(self.settings_showids_check,4,0)
        self.settings_tab_layout.addWidget(self.settings_sortchars_check,4,2)
        self.settings_tab_layout.addWidget(self.settings_enableregex_check,5,0)
        self.settings_tab_layout.addWidget(self.settings_misc_end_splitter,6,0,1,3)
        self.settings_tab_layout.addWidget(self.settings_save_btn,7,1)
        self.settings_tab_layout.setRowStretch(5,1)

        self.about_tab_layout = QGridLayout()
        self.about_info_label = QLabel()
        self.about_info_label.setTextFormat(Qt.TextFormat.RichText)
        self.about_info_label.setWordWrap(True)
        self.about_info_label.setOpenExternalLinks(True)
        self.about_info_label.setStyleSheet('padding: 10px;')
        self.about_info_label.setFrameStyle(QFrame.Panel)
        self.about_info_label.setText('''
        Searches for items in Inventory.txt files generated from Everquest.<p>
        These files are usually located in your EverQuest directory, add them on the settings tab.<p>
        To create or update the inventory files, run the following command while in-game:<br>
        <span style='font-family:Consolas; color:lightgreen;'>/outputfile inventory</span><p>
        This application was designed for <a href="https://projectquarm.com/">Project Quarm</a> with the <a href="https://github.com/iamclint/Zeal">Zeal plug-in</a> installed, it may or may not work on other servers.<p>
        ''')
        self.about_version_label = QLabel('v0.1.0', self)
        self.about_version_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        self.about_tab.setLayout(self.about_tab_layout)
        self.about_tab_layout.addWidget(self.about_info_label,0,0)
        self.about_tab_layout.addWidget(self.about_version_label,1,0)
        self.about_tab_layout.setRowStretch(1,1)


        self.check_inventory_updates_timer = QTimer(self)
        self.check_inventory_updates_timer.setInterval(1000)

        # Load inital config
        self.config_dir = platformdirs.user_config_dir('eqInvSearch', appauthor=False)
        self.config_file_path = os.path.join(self.config_dir, SETTINGS_FILE)
        self.load_config()
        self.update_settings_tab()
        self.get_inventory_files()
        self.load_inventories()

        # Set up QT Widget Connections
        self.tabs.tabBarClicked.connect(self.tab_clicked)
        self.tabs.currentChanged.connect(self.tab_changed)

        self.search_box_edit.textChanged.connect(self.find_inv_items)
        #test_action = QAction()
        #test_action.triggered.connect(self.char_select_combo_next)
        #test_action.setShortcut(QKeySequence('Ctrl+Down'))
        QShortcut( 'F2', self.search_box_edit ).activated.connect( lambda : self.char_select_combo_move('home') )
        QShortcut( 'Up', self.search_box_edit ).activated.connect( lambda : self.char_select_combo_move('up') )
        QShortcut( 'Down', self.search_box_edit ).activated.connect( lambda : self.char_select_combo_move('down') )
        #next_char_hotkey = QKeyEvent()
        #next_char_hotkey.keyCombination()
        #self.search_box_edit.keyPressEvent(
        self.char_select_combo.currentTextChanged.connect(self.find_inv_items)

        self.settings_invdirs_add_btn.pressed.connect(self.invdirs_add)
        self.settings_invdirs_del_btn.pressed.connect(self.invdirs_del)
        self.settings_save_btn.pressed.connect(self.settings_save)
        self.settings_showids_check.checkStateChanged.connect(self.mark_settings_changed)
        self.settings_sortchars_check.checkStateChanged.connect(self.mark_settings_changed)

        self.check_inventory_updates_timer.timeout.connect(self.watch_inventory_modifications)

        self.check_inventory_updates_timer.start()
        self.show()
        self.search_box_edit.setFocus()


    def watch_inventory_modifications(self):
        '''Checks to see if inventory files have been modified'''
        self.get_inventory_files()
        found_modified_inventory_files = False
        for inventory_file in self.inventory_files:
            file_path = os.path.join(inventory_file['dir'],inventory_file['file'])
            last_modified = os.stat(file_path).st_mtime
            if last_modified > self.inventories_last_loaded:
                found_modified_inventory_files = True
                break
        if found_modified_inventory_files is True:
            self.load_inventories()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    APP_STYLESHEET = '''
    QTabWidget::tab-bar {
        alignment: center;
    }
    '''
    qdarktheme.setup_theme(additional_qss=APP_STYLESHEET)

    defaultFont = QFont('Calibre', 12)
    app.setFont(defaultFont)

    window = MainWindow()

    sys.exit(app.exec())
