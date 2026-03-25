import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.core import QgsProject

from .forest_review_dialog import ForestReviewDialog


class ForestReviewPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.dialog = None

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self.action = QAction(icon, "Forest Lot Checker", self.iface.mainWindow())
        self.action.setToolTip("Open Forest Lot Checker")
        self.action.triggered.connect(self.run)

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("&Forest Lot Checker", self.action)

    def unload(self):
        self.iface.removePluginVectorMenu("&Forest Lot Review", self.action)
        self.iface.removeToolBarIcon(self.action)
        if self.dialog:
            self.dialog.close()

    def run(self):
        if self.dialog is None or not self.dialog.isVisible():
            self.dialog = ForestReviewDialog(self.iface, self.iface.mainWindow())
            self.dialog.show()
        else:
            self.dialog.raise_()
            self.dialog.activateWindow()
