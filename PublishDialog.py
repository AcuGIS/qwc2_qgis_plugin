import os
import requests
from qgis.PyQt.QtWidgets import QVBoxLayout, QMessageBox, QLineEdit, QDialog, QVBoxLayout, QLabel, QFormLayout, QComboBox, QComboBox, QHBoxLayout, QProgressBar, QTextEdit, QDialog, QVBoxLayout, QPushButton, QCheckBox, QListWidget, QListWidgetItem, QSizePolicy
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject
from .util import app_http_login

class PublishDialog(QDialog):
    def __init__(self, config):
        super().__init__()
    
        self.config = config
        self.setWindowTitle("Create AcuGIS Cloud QWC2 Map")
        self.layout = QVBoxLayout()
    
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        if os.path.exists(logo_path):
            logo_label.setPixmap(QIcon(logo_path).pixmap(120, 40))
        branding_label = QLabel("<b style='font-size:14pt;'>AcuGIS Cloud QWC2 Plugin</b><br><span style='font-size:10pt;'>Secure AcuGIS Cloud QWC2 Deployment Tool</span>")
        branding_label.setAlignment(Qt.AlignCenter)
    
        self.layout.addWidget(logo_label)
        self.layout.addWidget(branding_label)
    
        form_layout = QFormLayout()

        self.s = None

        self.server_dropdown = QComboBox()
        server_names = list(config.keys())
        self.server_dropdown.addItems(server_names)
        self.server_dropdown.currentIndexChanged.connect(self.onServerChanged)
        
        self.tenant_dropdown = QComboBox()
        self.tenant_dropdown.currentIndexChanged.connect(self.updateThemes)
    
        self.theme_dropdown = QComboBox()

        # optional: give inputs some minimum width so the dialog must grow
        self.server_dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tenant_dropdown.setMinimumWidth(100)
    
        self.onServerChanged()

        self.map_name = QLineEdit()
        self.map_desc = QLineEdit()
        self.media_dir = QLineEdit()
        
        self.public_access = QCheckBox()
        
        self.access_groups = {}
        self.access_groups_dropdown = QListWidget()
        self.access_groups_dropdown.setSelectionMode(QListWidget.MultiSelection)
        
        self.updateAccessGroups()

        form_layout.addRow("Server:", self.server_dropdown)
        form_layout.addRow("Tenant:", self.tenant_dropdown)
        form_layout.addRow("Theme:", self.theme_dropdown)

        form_layout.addRow("Name:", self.map_name)
        form_layout.addRow("Description:", self.map_desc)
        
        form_layout.addRow("Media dir:", self.media_dir)
        form_layout.addRow("Public Access:", self.public_access)
        form_layout.addRow("Access Groups:", self.access_groups_dropdown)
    
        self.layout.addLayout(form_layout)
    
        button_box = QHBoxLayout()
        create_btn = QPushButton("Create")
        cancel_btn = QPushButton("Cancel")
        button_box.addWidget(create_btn)
        button_box.addWidget(cancel_btn)
        self.layout.addLayout(button_box)
            
        self.setLayout(self.layout)
    
        # make the dialog open bigger and allow growing
        self.setMinimumSize(260, 350)
        self.resize(360, 400)  # initial size
        self.setSizeGripEnabled(True)
    
        # let form fields expand
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    
        create_btn.clicked.connect(self.create_map)
        cancel_btn.clicked.connect(self.reject)
    
    def onServerChanged(self):
        server_info = self.config.get(self.server_dropdown.currentText(), {})
        proto = 'https' if server_info['port'] == 443 else 'http'
        
        if self.s:
            self.s.close()
        self.s = requests.Session()
                
        if not app_http_login(self.s, proto, server_info['host'], server_info['username'], server_info['password']):
            QMessageBox.warning(None, "Login error", "Failed to login.")
            self.s.close()
            self.accept()

        self.updateTenants()
            
    def updateTenants(self):
        server_info = self.config.get(self.server_dropdown.currentText(), {})
        tenants = self.get_tenants(server_info)
        tenants.sort()
        self.tenant_dropdown.clear()
        self.tenant_dropdown.addItems(tenants)
    
    def updateThemes(self):
        server_info = self.config.get(self.server_dropdown.currentText(), {})
        tenant_name = self.tenant_dropdown.currentText()
        
        themes = self.get_themes(server_info,tenant_name)
        themes.sort()
        self.theme_dropdown.clear()
        self.theme_dropdown.addItems(themes)
    
    def updateAccessGroups(self):
        server_info = self.config.get(self.server_dropdown.currentText(), {})

        self.access_groups_dropdown.clear()
        
        for g in self.get_access_groups(server_info):
            self.access_groups[g['name']] = g['id']
            self.access_groups_dropdown.addItem(QListWidgetItem(g['name']))
    
    def get_access_groups(self, server_info):
        rv = {}
        
        proto = 'https' if server_info['port'] == 443 else 'http'
        try:
            response = self.s.post(proto + '://' + server_info['host'] + '/admin/action/access_groups.php', data={'list':True}, timeout=(10, 30))
            if response.status_code == 200:
                response = response.json()
                if response['success']:
                    rv = response['access_groups']
                else:
                    QMessageBox.warning(None, "QWC2 Error", response['message'])
        except Exception as e:
            QMessageBox.critical(None, "HTTP Error", f"An error occurred: {e}")

        return rv

    def get_tenants(self, server_info):
        rv = {}
        
        proto = 'https' if server_info['port'] == 443 else 'http'
        try:
            response = self.s.post(proto + '://' + server_info['host'] + '/admin/action/qwc2.php', data={'list_tenants':True, 'tenant':'default'}, timeout=(10, 30))
            if response.status_code == 200:
                response = response.json()
                if response['success']:
                    rv = response['tenants']
                else:
                    QMessageBox.warning(None, "QWC2 Error", response['message'])
        except Exception as e:
            QMessageBox.critical(None, "HTTP Error", f"An error occurred: {e}")

        return rv
    
    def get_themes(self, server_info,tenant_name):
        rv = {}
        
        proto = 'https' if server_info['port'] == 443 else 'http'
        try:
            response = self.s.post(proto + '://' + server_info['host'] + '/admin/action/qwc2.php', data={'themes':True, 'tenant':tenant_name}, timeout=(10, 30))
            if response.status_code == 200:
                response = response.json()
                if response['success']:
                    rv = response['themes']
                else:
                    QMessageBox.warning(None, "QWC2 Error", response['message'])
        except Exception as e:
            QMessageBox.critical(None, "HTTP Error", f"An error occurred: {e}")

        return rv
            
    def create_map(self):
        server_name = self.server_dropdown.currentText()
        tenant_name = self.tenant_dropdown.currentText()

        map_name = self.map_name.text()
        map_desc = self.map_desc.text()
        map_theme = self.theme_dropdown.currentText()
        media_dir = self.media_dir.text()
        
        # convert access group names to ids
        map_access_groups = []
        for g in self.access_groups_dropdown.selectedItems():
            map_access_groups.append(self.access_groups[g.text()])

        if not server_name or not map_name:
            QMessageBox.warning(self, "Missing Info", "Please select a server and tenant name.")
            return
        
        if not map_access_groups:
            QMessageBox.warning(self, "Missing Info", "Please select map access groups.")
            return

        server_info = self.config[server_name]
        proto = 'https' if server_info['port'] == 443 else 'http'
        
        try:
            map_data = {'save':1, 'id': 0, 'tenant': tenant_name, 'name':map_name, 'description':map_desc, 'media_dir':media_dir, 'qwc2_theme': map_theme, 'accgrps[]':map_access_groups}
            if self.public_access.isChecked():
                map_data['is_public'] = True
            
            response = self.s.post(proto + '://' + server_info['host'] + '/admin/action/map.php', data=map_data, timeout=(10, 30))
            if response.status_code != 200:
                QMessageBox.warning(None, "HTTP error", "HTTP code " + response.status_code)
                return

            response = response.json();
            if response['success']:
                if map_theme.startswith('scan/'):
                    map_theme = map_theme[5:]
                map_url = proto + '://' + server_info['host'] + '/apps/' + response['id'] + '/?t=' + map_theme
                QMessageBox.information(None, "AcuGIS Cloud QWC2", 'Map published. You can view it at <a href="' + map_url +'">' + map_url + '</a>')
            else:
                QMessageBox.warning(None, "QWC2 error", response['message'])

        except Exception as e:
            QMessageBox.warning(None, "HTTP error", "HTTP code " + response.status_code)
            return

        self.accept()
