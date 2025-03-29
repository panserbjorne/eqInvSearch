# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGridLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(469, 650)
        MainWindow.setMinimumSize(QSize(20, 0))
        self.base_widget = QWidget(MainWindow)
        self.base_widget.setObjectName(u"base_widget")
        self.base_layout = QGridLayout(self.base_widget)
        self.base_layout.setObjectName(u"base_layout")
        self.base_layout.setHorizontalSpacing(6)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget(self.base_widget)
        self.tabs.setObjectName(u"tabs")
        self.tabs.setStyleSheet(u"QTabWidget::tab-bar { alignment: center }")
        self.search_tab = QWidget()
        self.search_tab.setObjectName(u"search_tab")
        self.search_layout = QGridLayout(self.search_tab)
        self.search_layout.setObjectName(u"search_layout")
        self.char_select_label = QLabel(self.search_tab)
        self.char_select_label.setObjectName(u"char_select_label")

        self.search_layout.addWidget(self.char_select_label, 0, 1, 1, 1)

        self.search_box_layout = QLabel(self.search_tab)
        self.search_box_layout.setObjectName(u"search_box_layout")

        self.search_layout.addWidget(self.search_box_layout, 0, 0, 1, 1)

        self.char_select_combo = QComboBox(self.search_tab)
        self.char_select_combo.setObjectName(u"char_select_combo")

        self.search_layout.addWidget(self.char_select_combo, 1, 1, 1, 1)

        self.search_box_edit = QLineEdit(self.search_tab)
        self.search_box_edit.setObjectName(u"search_box_edit")

        self.search_layout.addWidget(self.search_box_edit, 1, 0, 1, 1)

        self.found_items_tree = QTreeWidget(self.search_tab)
        self.found_items_tree.headerItem().setText(0, "")
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setTextAlignment(1, Qt.AlignCenter);
        self.found_items_tree.setHeaderItem(__qtreewidgetitem)
        self.found_items_tree.setObjectName(u"found_items_tree")
        self.found_items_tree.setColumnCount(2)

        self.search_layout.addWidget(self.found_items_tree, 2, 0, 1, 2)

        self.search_layout.setRowStretch(2, 1)
        self.search_layout.setColumnStretch(0, 1)
        self.tabs.addTab(self.search_tab, "")
        self.settings_tab = QWidget()
        self.settings_tab.setObjectName(u"settings_tab")
        self.settings_layout = QGridLayout(self.settings_tab)
        self.settings_layout.setObjectName(u"settings_layout")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.settings_layout.addItem(self.verticalSpacer_2, 4, 0, 1, 1)

        self.settings_sortchars_check = QCheckBox(self.settings_tab)
        self.settings_sortchars_check.setObjectName(u"settings_sortchars_check")

        self.settings_layout.addWidget(self.settings_sortchars_check, 2, 1, 1, 1)

        self.settings_save_btn = QPushButton(self.settings_tab)
        self.settings_save_btn.setObjectName(u"settings_save_btn")
        self.settings_save_btn.setMaximumSize(QSize(100, 16777215))

        self.settings_layout.addWidget(self.settings_save_btn, 5, 0, 1, 2, Qt.AlignmentFlag.AlignHCenter)

        self.settings_enableregex_check = QCheckBox(self.settings_tab)
        self.settings_enableregex_check.setObjectName(u"settings_enableregex_check")
        self.settings_enableregex_check.setEnabled(False)
        self.settings_enableregex_check.setChecked(True)

        self.settings_layout.addWidget(self.settings_enableregex_check, 3, 0, 1, 1)

        self.settings_invdirs_layout = QGridLayout()
        self.settings_invdirs_layout.setObjectName(u"settings_invdirs_layout")
        self.settings_invdirs_lower_spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.settings_invdirs_layout.addItem(self.settings_invdirs_lower_spacer, 5, 1, 1, 1)

        self.settings_invdirs_upper_spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.settings_invdirs_layout.addItem(self.settings_invdirs_upper_spacer, 1, 1, 1, 1)

        self.settings_invdirs_add_btn = QPushButton(self.settings_tab)
        self.settings_invdirs_add_btn.setObjectName(u"settings_invdirs_add_btn")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ListAdd))
        self.settings_invdirs_add_btn.setIcon(icon)

        self.settings_invdirs_layout.addWidget(self.settings_invdirs_add_btn, 2, 1, 1, 1)

        self.settings_invdirs_del_btn = QPushButton(self.settings_tab)
        self.settings_invdirs_del_btn.setObjectName(u"settings_invdirs_del_btn")
        icon1 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ListRemove))
        self.settings_invdirs_del_btn.setIcon(icon1)

        self.settings_invdirs_layout.addWidget(self.settings_invdirs_del_btn, 4, 1, 1, 1)

        self.settings_invdirs_label = QLabel(self.settings_tab)
        self.settings_invdirs_label.setObjectName(u"settings_invdirs_label")

        self.settings_invdirs_layout.addWidget(self.settings_invdirs_label, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.settings_invdirs_layout.addItem(self.verticalSpacer, 3, 1, 1, 1)

        self.settings_invdirs_tree = QTreeWidget(self.settings_tab)
        self.settings_invdirs_tree.headerItem().setText(0, "")
        self.settings_invdirs_tree.setObjectName(u"settings_invdirs_tree")
        self.settings_invdirs_tree.setColumnCount(1)
        self.settings_invdirs_tree.header().setVisible(False)

        self.settings_invdirs_layout.addWidget(self.settings_invdirs_tree, 1, 0, 5, 1)


        self.settings_layout.addLayout(self.settings_invdirs_layout, 0, 0, 1, 2)

        self.settings_invdirs_end_line = QFrame(self.settings_tab)
        self.settings_invdirs_end_line.setObjectName(u"settings_invdirs_end_line")
        self.settings_invdirs_end_line.setMinimumSize(QSize(0, 6))
        self.settings_invdirs_end_line.setLineWidth(6)
        self.settings_invdirs_end_line.setFrameShape(QFrame.Shape.HLine)
        self.settings_invdirs_end_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.settings_layout.addWidget(self.settings_invdirs_end_line, 1, 0, 1, 2)

        self.settings_showids_check = QCheckBox(self.settings_tab)
        self.settings_showids_check.setObjectName(u"settings_showids_check")

        self.settings_layout.addWidget(self.settings_showids_check, 2, 0, 1, 1)

        self.settings_layout.setRowStretch(4, 1)
        self.tabs.addTab(self.settings_tab, "")
        self.about_tab = QWidget()
        self.about_tab.setObjectName(u"about_tab")
        self.about_tab_layout = QGridLayout(self.about_tab)
        self.about_tab_layout.setObjectName(u"about_tab_layout")
        self.about_info_label = QLabel(self.about_tab)
        self.about_info_label.setObjectName(u"about_info_label")
        self.about_info_label.setTextFormat(Qt.TextFormat.RichText)
        self.about_info_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.about_info_label.setWordWrap(True)

        self.about_tab_layout.addWidget(self.about_info_label, 0, 0, 1, 1)

        self.about_version_label = QLabel(self.about_tab)
        self.about_version_label.setObjectName(u"about_version_label")
        self.about_version_label.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing)

        self.about_tab_layout.addWidget(self.about_version_label, 1, 0, 1, 1)

        self.about_tab_layout.setRowStretch(1, 1)
        self.tabs.addTab(self.about_tab, "")

        self.base_layout.addWidget(self.tabs, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.base_widget)

        self.retranslateUi(MainWindow)

        self.tabs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"EQ Inventory Searcher", None))
        self.char_select_label.setText(QCoreApplication.translate("MainWindow", u"Character:", None))
        self.search_box_layout.setText(QCoreApplication.translate("MainWindow", u"Search Items:", None))
        ___qtreewidgetitem = self.found_items_tree.headerItem()
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("MainWindow", u"Quantity", None));
        self.tabs.setTabText(self.tabs.indexOf(self.search_tab), QCoreApplication.translate("MainWindow", u"Search", None))
        self.settings_sortchars_check.setText(QCoreApplication.translate("MainWindow", u"Sort Characters", None))
        self.settings_save_btn.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.settings_enableregex_check.setText(QCoreApplication.translate("MainWindow", u"Enable Regex", None))
        self.settings_invdirs_add_btn.setText("")
        self.settings_invdirs_del_btn.setText("")
        self.settings_invdirs_label.setText(QCoreApplication.translate("MainWindow", u"Directories containing inventory files:", None))
        self.settings_showids_check.setText(QCoreApplication.translate("MainWindow", u"Show Item IDs", None))
        self.tabs.setTabText(self.tabs.indexOf(self.settings_tab), QCoreApplication.translate("MainWindow", u"Settings", None))
        self.about_info_label.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Searches for items in Inventory.txt files generated from Everquest.</p><p>These files are usually located in your EverQuest directory, add them on the settings tab.</p><p>To create or update the inventory files, run the following command while in-game:<br/><span style=\" font-family:'Consolas'; color:#90ee90;\">/outputfile inventory</span></p><p>This application was designed for <a href=\"https://projectquarm.com/\"><span style=\" text-decoration: underline; color:#99ebff;\">Project Quarm</span></a> with the <a href=\"https://github.com/iamclint/Zeal\"><span style=\" text-decoration: underline; color:#99ebff;\">Zeal plug-in</span></a> installed, it may or may not work on other servers.<br/></p></body></html>", None))
        self.tabs.setTabText(self.tabs.indexOf(self.about_tab), QCoreApplication.translate("MainWindow", u"About", None))
    # retranslateUi

