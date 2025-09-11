import os
import json
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface

from .ConfigDialog import ConfigDialog
from .CreateDialog import CreateDialog
from .UploadDialog import UploadDialog
from .PublishDialog import PublishDialog

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".qwc2_uploader_config.json")

class AcugisQWC2Plugin:
    def __init__(self, iface):
        self.iface = iface
        self.create_action = None
        self.upload_action = None
        self.config_action = None

    def initGui(self):
        plugin_dir = os.path.dirname(__file__)
        icon_dir = os.path.join(plugin_dir, 'icons')
        create_icon_path = os.path.join(icon_dir, 'create.png')
        update_icon_path = os.path.join(icon_dir, 'update.png')
        config_icon_path = os.path.join(icon_dir, 'configure.png')
        publish_icon_path = os.path.join(icon_dir, 'publish.png')

        self.config_action = QAction(QIcon(config_icon_path), "Configure &Access", self.iface.mainWindow())
        self.config_action.triggered.connect(self.configure_servers)
        self.iface.addToolBarIcon(self.config_action)
        self.iface.addPluginToMenu("&QWC2", self.config_action)
        
        self.create_action = QAction(QIcon(create_icon_path), "&Create Tenant", self.iface.mainWindow())
        self.create_action.triggered.connect(self.create_tenant)
        self.iface.addToolBarIcon(self.create_action)
        self.iface.addPluginToMenu("&QWC2", self.create_action)
        
        self.upload_action = QAction(QIcon(update_icon_path), "&Update Files", self.iface.mainWindow())
        self.upload_action.triggered.connect(self.upload_files)
        self.iface.addToolBarIcon(self.upload_action)
        self.iface.addPluginToMenu("&QWC2", self.upload_action)
        
        self.publish_action = QAction(QIcon(publish_icon_path), "&Publish Map", self.iface.mainWindow())
        self.publish_action.triggered.connect(self.publish_map)
        self.iface.addToolBarIcon(self.publish_action)
        self.iface.addPluginToMenu("&QWC2", self.publish_action)

    def unload(self):
        self.iface.removePluginMenu("&QWC2", self.create_action)
        self.iface.removeToolBarIcon(self.create_action)
        self.iface.removePluginMenu("&QWC2", self.upload_action)
        self.iface.removeToolBarIcon(self.upload_action)
        self.iface.removePluginMenu("&QWC2", self.config_action)
        self.iface.removeToolBarIcon(self.config_action)
        self.iface.removePluginMenu("&QWC2", self.publish_action)
        self.iface.removeToolBarIcon(self.publish_action)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_config(self, config):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)

    def configure_servers(self):
        config = self.load_config()
        dlg = ConfigDialog(config)
        dlg.exec_()
        self.save_config(config)

    def upload_files(self):
        config = self.load_config()
        
        if not config:
            QMessageBox.warning(None, "No Servers Configured", "Please configure at least one AcuGIS Cloud QWC2 server first.")
            return

        dlg = UploadDialog(config)
        dlg.exec_()
    
    def create_tenant(self):
        config = self.load_config()
        
        if not config:
            QMessageBox.warning(None, "No Servers Configured", "Please configure at least one AcuGIS Cloud QWC2 server first.")
            return

        dlg = CreateDialog(config)
        dlg.exec_()
    
    def publish_map(self):
        config = self.load_config()
        
        if not config:
            QMessageBox.warning(None, "No Servers Configured", "Please configure at least one AcuGIS Cloud QWC2 server first.")
            return

        dlg = PublishDialog(config)
        dlg.exec_()
    

def classFactory(iface):
    return AcugisQWC2Plugin(iface)
