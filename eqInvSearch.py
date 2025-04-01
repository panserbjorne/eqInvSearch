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
    QFileDialog,
    QMessageBox,
    QTreeWidgetItem,
    QHeaderView,
    QMainWindow
)
import qdarktheme
import yaml
from mainWindow import Ui_MainWindow

SETTINGS_FILE = 'settings.yml'
VERSION = "0.1.0"


class IndentDumper(yaml.Dumper):
    '''Custom YAML Dumper that provides indentation'''
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


class MainWindow(QMainWindow):
    '''Main QT Window'''

    def load_config(self):
        '''Load config from file'''

        if os.path.isfile(self.config_file_path):
            with open(self.config_file_path, 'r', encoding='utf-8') as yml_file:
                self.config = yaml.safe_load(yml_file)
        if not self.config:
            self.config = {}
        if 'accounts' not in self.config:
            self.config['accounts'] = {}
        if 'ignoredCharacters' not in self.config:
            self.config['ignoredCharacters'] = []
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
        new_inventory_files = []  # For comparison

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

        previous_selected_char = self.current_selected_char  # For comparsion
        shared_char_last_modified = {}  # To find the most recent file for shared characters
        self.ui.char_select_combo.clear()

        self.inventories_last_loaded = time.time()

        # Set empty variables to be filled
        self.character_list = []
        self.inventory = {}

        # Prompt for inventory file if none are found
        if len(self.inventory_files) == 0:
            add_invdirs_prompt = QMessageBox(self)
            add_invdirs_prompt.setWindowTitle('EQ Inventory Searcher')
            add_invdirs_prompt.setText('Select an Inventory file from your EverQuest directory.')
            add_invdirs_prompt.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            add_invdirs_prompt_resp = add_invdirs_prompt.exec()
            if add_invdirs_prompt_resp == 1024:
                self.invdirs_add()
                self.settings_save()
                self.ui.tabs.setCurrentWidget(self.ui.search_tab)
            else:
                self.ui.tabs.setCurrentWidget(self.ui.settings_tab)
                self.ui.tabs.setTabEnabled(0, False)
        else:  # Disable search tab
            self.ui.tabs.setTabEnabled(0, True)

        for inventory_file in self.inventory_files:
            character_name = inventory_file['file'].replace('-Inventory.txt', '')

            if character_name in self.config['ignoredCharacters']:
                continue

            if character_name not in self.character_list:
                self.character_list.append(character_name)

            inventory_file_path = os.path.join(inventory_file['dir'], inventory_file['file'])

            # Match characters against configured accounts
            account_name = None
            for account in self.config['accounts']:
                if character_name in self.config['accounts'][account]:
                    account_name = account
                    # Compare modified times so that the most recent shared bank data will be used
                    current_file_last_modified = os.path.getmtime(inventory_file_path)
                    if account_name in shared_char_last_modified:
                        if shared_char_last_modified[account_name] > current_file_last_modified:
                            skip_shared_bank = True
                            break
                    skip_shared_bank = False
                    shared_char_last_modified[account_name] = current_file_last_modified
                    break

            with open(inventory_file_path, 'r', encoding='utf-8') as file:
                inventory_text = file.read()

            character_known_item_ids = []
            find_items_re = r'(?P<itemLocation>[\w-]+)\t(?P<itemName>.+)\t(?P<itemID>[\d]+)\t(?P<itemCount>[\d]+)\t(?P<itemSlots>[\d]+)'
            for item in re.finditer(find_items_re, inventory_text):
                item_location = item.group('itemLocation')
                item_name = item.group('itemName')
                item_id = item.group('itemID')
                item_count = int(item.group('itemCount'))

                if item_id == '0':  # Item is either coin or an empty slot
                    if item_count == 0:
                        continue
                    elif item_location == 'General-Coin' or item_location == 'Bank-Coin':
                        item_location = item_location.replace('-Coin', '')
                        item_id = 'in Plat'
                        item_name = 'Coins'
                        item_count = int(item_count / 1000)
                    else:
                        continue

                # Avoid displaying / counting shared bank items multiple times for characters on the same account
                if 'SharedBank' in item_location and account_name:
                    # Skip if the inventory file modification date is older than what is already loaded
                    if skip_shared_bank is True:
                        continue
                    item_character = f'{account_name} (Account)'
                    # If the item has not been seen on this character yet, remove existing records of it for this account
                    if item_id not in character_known_item_ids:
                        if item_id in self.inventory:
                            if item_character in self.inventory[item_id]['characters']:
                                # Subtract the existing account's count from the total
                                self.inventory[item_id]['totalCount'] -= self.inventory[item_id]['characters'][item_character]['count']
                                self.inventory[item_id]['characters'].pop(item_character)
                else:
                    item_character = character_name

                if item_id not in character_known_item_ids:
                    character_known_item_ids.append(item_id)

                if item_id not in self.inventory:
                    self.inventory[item_id] = {'name': item_name, 'totalCount': 0, 'characters': {}}

                self.inventory[item_id]['totalCount'] += item_count

                if item_character not in self.inventory[item_id]['characters']:
                    self.inventory[item_id]['characters'][item_character] = {'locations': {}, 'count': 0}

                self.inventory[item_id]['characters'][item_character]['count'] += item_count

                if item_location not in self.inventory[item_id]['characters'][item_character]['locations']:
                    self.inventory[item_id]['characters'][item_character]['locations'][item_location] = 0
                self.inventory[item_id]['characters'][item_character]['locations'][item_location] += item_count

        # Sort the inventory by Item ID
        self.inventory = dict(natsorted(self.inventory.items()))

        # Sort the character list alphabetically
        if self.config["sortCharacters"]:
            self.character_list.sort()
        # Add the All Characters option at the beginning
        self.character_list.insert(0, 'All')

        # Update the character combo box
        self.ui.char_select_combo.addItems(self.character_list)

        # Attempt to re-select the previous character, defaults to first option (All)
        previous_char_index = self.ui.char_select_combo.findText(previous_selected_char)
        if previous_char_index == -1:
            previous_char_index = 0
        self.ui.char_select_combo.setCurrentIndex(previous_char_index)

    def find_inv_items(self):
        '''Searches the stored inventory for search box contents'''

        self.ui.found_items_tree.clear()  # Remove the current search results

        search_string = self.ui.search_box_edit.displayText()

        # No need to process if search box is empty
        if not search_string:
            return None

        self.current_selected_char = self.ui.char_select_combo.currentText()

        found_items = []  # To hold matching items
        search_string = search_string.replace("'", "['`]")  # EQ sometimes uses `, othertimes '

        characters_with_matches = ['All']

        # Loop thorugh all items that were retrieved from inventory files
        for item_id, item in self.inventory.items():
            item_name = item['name']
            try:
                item_matched = re.search(fr"{search_string}", item_name, re.IGNORECASE)
            except re.PatternError:  # Discard invalid regex patterns
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
                    found_item.setForeground(0, QColor(255, 175, 255))
                    found_item.setForeground(1, QColor(255, 175, 255))
                    found_items_updated = True
                for character, character_info in item['characters'].items():
                    if character not in characters_with_matches:
                        characters_with_matches.append(character)
                    character_count = str(character_info['count'])
                    # When searching all characters, create a character row
                    if self.current_selected_char == 'All':
                        found_char = QTreeWidgetItem([character, character_count])
                        found_char.setTextAlignment(1, Qt.AlignmentFlag.AlignRight)
                        found_char.setForeground(0, QColor(100, 200, 255))
                        found_char.setForeground(1, QColor(100, 200, 255))
                        found_item.addChild(found_char)
                    # When searching a single character, create a parent row for the item with the character's total
                    elif character == self.current_selected_char:
                        found_item = QTreeWidgetItem([item_name + item_id_str, character_count])
                        found_item.setForeground(0, QColor(255, 175, 255))
                        found_item.setForeground(1, QColor(255, 175, 255))
                        found_items_updated = True
                    else:
                        continue
                    location_row_odd = True
                    for location, location_count in character_info['locations'].items():
                        find_location_re = r'^(?P<base_location>[a-zA-Z]+)(?P<base_slot>\d*)-*(?P<sub_location>[a-zA-Z]*)(?P<sub_slot>\d*)'
                        friendly_location_groups = re.finditer(find_location_re, location)
                        if not friendly_location_groups:
                            break
                        for friendly_location in friendly_location_groups:
                            # Recreate the location line with padded values
                            location_friendly_name = friendly_location.group('base_location').ljust(12)
                            if friendly_location.group('base_slot'):
                                location_friendly_name += friendly_location.group('base_slot').rjust(2)
                            if friendly_location.group('sub_location'):
                                location_friendly_name += ', '
                            if friendly_location.group('sub_slot'):
                                location_friendly_name += friendly_location.group('sub_slot').rjust(2)
                        found_location = QTreeWidgetItem([location_friendly_name, str(location_count)])
                        found_location.setFont(0, self.locationRowFont)
                        found_location.setTextAlignment(1, Qt.AlignmentFlag.AlignRight)
                        if location_row_odd is True:
                            found_location.setBackground(0, QColor(50, 50, 50))
                            found_location.setBackground(1, QColor(50, 50, 50))
                            location_row_odd = False
                        else:
                            found_location.setBackground(0, QColor(70, 70, 70))
                            found_location.setBackground(1, QColor(70, 70, 70))
                            location_row_odd = True
                        if self.current_selected_char == "All":
                            # Searching all characters, use the character row as the parent
                            found_char.addChild(found_location)
                        else:
                            # Searching a single character, use the item row as the parent
                            found_item.addChild(found_location)

                if found_items_updated is True:
                    found_item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight)
                    found_items.append(found_item)

        if len(found_items) == 0:
            no_items_row = QTreeWidgetItem(['No matching items found.'])
            found_items.append(no_items_row)
        self.ui.found_items_tree.addTopLevelItems(found_items)
        self.ui.found_items_tree.expandAll()

        for index in range(self.ui.char_select_combo.count()):
            character = self.ui.char_select_combo.itemText(index)
            if character not in characters_with_matches:
                background_color = QColor(240, 120, 120)
            else:
                background_color = QColor(120, 240, 120)
            self.ui.char_select_combo.setItemData(index, background_color, Qt.ItemDataRole.ForegroundRole)
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
                existing_invdirs_count = self.ui.settings_invdirs_tree.topLevelItemCount()
                # Abort if path already exists
                for index in range(existing_invdirs_count):
                    existing_invdir = self.ui.settings_invdirs_tree.topLevelItem(index).data(0, 0)
                    if existing_invdir == new_invdir:
                        return
                invdir_item = QTreeWidgetItem([new_invdir])
                self.ui.settings_invdirs_tree.addTopLevelItem(invdir_item)
                self.mark_settings_changed()
        return

    def invdirs_del(self):
        '''Removes the currently selected EQ directory'''
        selected_dir = self.ui.settings_invdirs_tree.selectedIndexes()
        if selected_dir:
            selected_row = selected_dir[0].row()
            self.ui.settings_invdirs_tree.takeTopLevelItem(selected_row)
            self.mark_settings_changed()

    def sharedaccount_add(self):
        '''Adds a new account as a parent to the Shared Accounts Tree'''
        new_account = QTreeWidgetItem([])
        new_account.setFlags(new_account.flags() | Qt.ItemFlag.ItemIsEditable)
        self.ui.settings_sharedaccounts_tree.addTopLevelItem(new_account)
        self.ui.settings_sharedaccounts_tree.setCurrentItem(new_account)
        self.ui.settings_sharedaccounts_tree.expandItem(new_account)
        self.ui.settings_sharedaccounts_tree.editItem(new_account)

    def sharedaccount_del(self):
        '''Removes a parent level account from the Shared Accounts Tree'''
        account_item = self.ui.settings_sharedaccounts_tree.currentItem()
        if account_item.parent() is None:  # Make sure an account is selected and not a child character
            account_index = self.ui.settings_sharedaccounts_tree.selectedIndexes()
            account_row = account_index[0].row()
            self.ui.settings_sharedaccounts_tree.takeTopLevelItem(account_row)
            self.mark_settings_changed()

    def sharedchar_add(self):
        '''Removes a character from the Individual Characters List and attaches it to an account in the Shared Accounts Tree as a child'''
        character_item = self.ui.settings_individual_chars_list.selectedItems()
        account_item = self.ui.settings_sharedaccounts_tree.currentItem()
        if character_item and account_item:
            character_name = character_item[0].text()
            if account_item.parent() is not None:
                account_item = account_item.parent()
            # Add the character as a child of the account
            new_char_item = QTreeWidgetItem([character_name])
            account_item.addChild(new_char_item)
            # Remove the character from the individual characters list
            character_row = self.ui.settings_individual_chars_list.currentRow()
            self.ui.settings_individual_chars_list.takeItem(character_row)
            self.mark_settings_changed()

    def sharedchar_del(self):
        '''Removes a character from the parent account in the Shared Accounts Tree and adds it to the Individual Characters List'''
        character_item = self.ui.settings_sharedaccounts_tree.currentItem()
        if character_item.parent() is not None:
            parent_item = character_item.parent()
            character_name = character_item.text(0)
            # Add the character to the individual characters list (if not already there)
            if not self.ui.settings_individual_chars_list.findItems(character_name, Qt.MatchFlag.MatchExactly):
                self.ui.settings_individual_chars_list.addItem(character_name)
                self.ui.settings_individual_chars_list.sortItems()
            # Remove the character from the account parent
            parent_item.removeChild(character_item)
            self.mark_settings_changed()

    def ignoredchar_add(self):
        '''Moves a character from the Individual Character list to the Ignore Character list'''
        character_item = self.ui.settings_individual_chars_list.selectedItems()
        if character_item:
            character_name = character_item[0].text()
            self.ui.settings_ignored_chars_list.addItem(character_name)
            self.ui.settings_ignored_chars_list.sortItems()
            character_row = self.ui.settings_individual_chars_list.currentRow()
            self.ui.settings_individual_chars_list.takeItem(character_row)
            self.mark_settings_changed()

    def ignoredchar_del(self):
        '''Moves a character from the Ignore Character list to the Individual Character list'''
        character_item = self.ui.settings_ignored_chars_list.selectedItems()
        if character_item:
            character_name = character_item[0].text()
            self.ui.settings_individual_chars_list.addItem(character_name)
            self.ui.settings_individual_chars_list.sortItems()
            character_row = self.ui.settings_ignored_chars_list.currentRow()
            self.ui.settings_ignored_chars_list.takeItem(character_row)
            self.mark_settings_changed()

    def mark_settings_changed(self):
        '''Records that settings are changed for later prompt'''
        self.settings_changed = True

    def settings_save(self):
        '''Save configured settings'''
        self.settings_changed = False
        # Save Inventory Directory Tree
        new_invdirs_count = self.ui.settings_invdirs_tree.topLevelItemCount()
        self.config['invDirectories'] = []
        for index in range(new_invdirs_count):
            new_invdir = self.ui.settings_invdirs_tree.topLevelItem(index).data(0, 0)
            self.config['invDirectories'].append(new_invdir)
        # Save Show Item IDs checkbox
        self.config['showItemIDs'] = self.ui.settings_showids_check.isChecked()

        self.config['sortCharacters'] = self.ui.settings_sortchars_check.isChecked()

        # Save Shared Accounts Tree
        new_sharedaccounts_count = self.ui.settings_sharedaccounts_tree.topLevelItemCount()
        self.config['accounts'] = {}
        for parent_index in range(new_sharedaccounts_count):
            new_sharedaccount_item = self.ui.settings_sharedaccounts_tree.topLevelItem(parent_index)
            new_sharedaccount_name = new_sharedaccount_item.data(0, 0)
            new_sharedcharacters = []
            for child_index in range(new_sharedaccount_item.childCount()):
                new_sharedcharacter_item = new_sharedaccount_item.child(child_index)
                new_sharedcharacter_name = new_sharedcharacter_item.data(0, 0)
                new_sharedcharacters.append(new_sharedcharacter_name)
            new_sharedcharacters.sort()
            self.config['accounts'][new_sharedaccount_name] = new_sharedcharacters

        # Save Ignored Characters List
        self.config['ignoredCharacters'] = []
        chararacter_item_count = self.ui.settings_ignored_chars_list.count()
        for character_index in range(chararacter_item_count):
            character_item = self.ui.settings_ignored_chars_list.item(character_index)
            character_name = character_item.data(0)
            self.config['ignoredCharacters'].append(character_name)
        self.config['ignoredCharacters'].sort()

        # Save window size and position
        self.config['windowSize'] = {'width': self.width(), 'height': self.height()}
        self.config['windowPosition'] = {'x': self.x(), 'y': self.y()}

        # Save settings to file
        if not os.path.isdir(self.config_dir):
            os.makedirs(self.config_dir)
        with open(self.config_file_path, 'w', encoding='utf-8') as yml_file:
            yaml.dump(self.config, stream=yml_file, Dumper=IndentDumper)

        # Re-load inventory and re-run search
        self.get_inventory_files()
        self.load_inventories()
        self.find_inv_items()

    def update_settings_tab(self):
        '''Refreshes the settings tab'''

        self.ui.settings_invdirs_tree.clear()
        self.ui.settings_sharedaccounts_tree.clear()
        self.ui.settings_individual_chars_list.clear()
        self.ui.settings_ignored_chars_list.clear()

        # Update the Tree of Inventory Dirs
        if self.config['invDirectories']:
            for invdir in self.config['invDirectories']:
                invdir_item = QTreeWidgetItem([invdir])
                self.ui.settings_invdirs_tree.addTopLevelItem(invdir_item)

        # Update the Show Item IDs checkbox
        self.ui.settings_showids_check.setChecked(self.config['showItemIDs'])

        # Update the Sort Characters checkbox
        self.ui.settings_sortchars_check.setChecked(self.config['sortCharacters'])
        self.settings_changed = False

        # Create a list of individual characters
        # Start with every character, they will be removed if associated with an account
        individual_characters = self.character_list
        if 'All' in individual_characters:
            individual_characters.remove('All')

        # Update the Shared Accounts Tree
        if self.config['accounts']:
            for account in self.config['accounts']:
                account_item = QTreeWidgetItem([account])
                account_item.setFlags(account_item.flags() | Qt.ItemFlag.ItemIsEditable)
                for character in self.config['accounts'][account]:
                    character_item = QTreeWidgetItem([character])
                    account_item.addChild(character_item)
                    if character in individual_characters:
                        individual_characters.remove(character)  # Remove this account from the individual characters list
                self.ui.settings_sharedaccounts_tree.addTopLevelItem(account_item)
            self.ui.settings_sharedaccounts_tree.expandAll()

        # Update the Individual Characters list
        if len(individual_characters) > 0:
            for character in individual_characters:
                self.ui.settings_individual_chars_list.addItem(character)
        self.ui.settings_individual_chars_list.sortItems()

        # Update the Ignored Characters list
        if len(self.config['ignoredCharacters']) > 0:
            for character in self.config['ignoredCharacters']:
                self.ui.settings_ignored_chars_list.addItem(character)

    def tab_clicked(self, tab_clicked_index):
        '''Runs tab-specific functions when tab bar is clicked'''
        # Ignore when current tab is clicked
        if self.ui.tabs.currentIndex() == tab_clicked_index:
            return
        tab_clicked = self.ui.tabs.tabText(tab_clicked_index)
        if tab_clicked != 'Settings' and self.settings_changed:
            save_prompt = QMessageBox(self)
            save_prompt.setWindowTitle('EQ Inventory Searcher')
            save_prompt.setText('Save updated settings?')
            save_prompt.setStandardButtons(QMessageBox.Save | QMessageBox.Discard)
            save_prompt_resp = save_prompt.exec()
            if save_prompt_resp == 2048:
                self.settings_save()
            else:
                self.settings_changed = False

    def tab_changed(self, new_active_tab_index):
        '''Runs tab-specific functions when active tab is changed'''
        new_active_tab = self.ui.tabs.tabText(new_active_tab_index)
        if new_active_tab == 'Search':
            self.ui.search_box_edit.setFocus()
        if new_active_tab == 'Settings':
            self.update_settings_tab()

    def char_select_combo_move(self, direction):
        total_items = self.ui.char_select_combo.count()
        selected_index = self.ui.char_select_combo.currentIndex()
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
        self.ui.char_select_combo.setCurrentIndex(new_index)
        return

    def watch_inventory_modifications(self):
        '''Checks to see if inventory files have been modified'''
        self.get_inventory_files()
        found_modified_inventory_files = False
        for inventory_file in self.inventory_files:
            file_path = os.path.join(inventory_file['dir'], inventory_file['file'])
            last_modified = os.stat(file_path).st_mtime
            if last_modified > self.inventories_last_loaded:
                found_modified_inventory_files = True
                break
        if found_modified_inventory_files is True:
            self.load_inventories()

    def __init__(self):

        self.config = {}
        self.inventory_files = []
        self.inventory = {}
        self.inventories_last_loaded = 0
        self.current_selected_char = None
        self.settings_changed = False

        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        window_icon = QIcon()
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(__file__)
        icon_path = os.path.join(application_path, 'eqInvSearch.ico')
        window_icon = QIcon()
        window_icon.addFile(icon_path)
        self.setWindowIcon(window_icon)

        self.ui.found_items_tree.setColumnWidth(1, 85)
        # Only allow the first column to be stretched
        self.ui.found_items_tree.header().setStretchLastSection(False)
        self.ui.found_items_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.ui.about_version_label.setText(f'v{VERSION}')

        self.check_inventory_updates_timer = QTimer(self)
        self.check_inventory_updates_timer.setInterval(1000)

        # Set up QT Widget Connections
        self.ui.tabs.tabBarClicked.connect(self.tab_clicked)
        self.ui.tabs.currentChanged.connect(self.tab_changed)

        self.ui.search_box_edit.textChanged.connect(self.find_inv_items)
        QShortcut('F2', self.ui.search_box_edit).activated.connect(lambda: self.char_select_combo_move('home'))
        QShortcut('Up', self.ui.search_box_edit).activated.connect(lambda: self.char_select_combo_move('up'))
        QShortcut('Down', self.ui.search_box_edit).activated.connect(lambda: self.char_select_combo_move('down'))
        self.ui.char_select_combo.currentTextChanged.connect(self.find_inv_items)

        self.ui.settings_invdirs_add_btn.pressed.connect(self.invdirs_add)
        self.ui.settings_invdirs_del_btn.pressed.connect(self.invdirs_del)
        self.ui.settings_showids_check.checkStateChanged.connect(self.mark_settings_changed)
        self.ui.settings_sortchars_check.checkStateChanged.connect(self.mark_settings_changed)
        self.ui.settings_sharedaccounts_tree.itemChanged.connect(self.mark_settings_changed)
        self.ui.settings_sharedaccounts_add_btn.pressed.connect(self.sharedaccount_add)
        self.ui.settings_sharedaccounts_del_btn.pressed.connect(self.sharedaccount_del)
        self.ui.settings_sharedchar_add_btn.pressed.connect(self.sharedchar_add)
        self.ui.settings_sharedchar_del_btn.pressed.connect(self.sharedchar_del)
        self.ui.settings_ignoredchars_add_btn.pressed.connect(self.ignoredchar_add)
        self.ui.settings_ignoredchars_remove_btn.pressed.connect(self.ignoredchar_del)
        self.ui.settings_save_btn.pressed.connect(self.settings_save)

        self.check_inventory_updates_timer.timeout.connect(self.watch_inventory_modifications)
        self.check_inventory_updates_timer.start()

        # The location row uses whitespace to align values, so prepare a monospace font
        self.locationRowFont = QFont('Consolas,Lucida Sans Typewriter', 14)
        self.locationRowFont.setStyleHint(QFont.StyleHint.TypeWriter)

        # Load inital config
        self.config_dir = platformdirs.user_config_dir('eqInvSearch', appauthor=False)
        self.config_file_path = os.path.join(self.config_dir, SETTINGS_FILE)
        self.load_config()

        # Prepare for first search
        self.get_inventory_files()
        self.load_inventories()

        self.show()
        self.ui.search_box_edit.setFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    qdarktheme.setup_theme()
    defaultFont = QFont('Calibri', 14)
    app.setFont(defaultFont)

    window = MainWindow()

    sys.exit(app.exec())
