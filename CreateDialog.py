import os
import requests
from qgis.PyQt.QtWidgets import QVBoxLayout, QMessageBox, QLineEdit, QDialog, QVBoxLayout, QLabel, QFormLayout, QComboBox, QComboBox, QHBoxLayout, QProgressBar, QTextEdit, QDialog, QVBoxLayout, QPushButton, QSizePolicy
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject
from .util import app_http_login

class CreateDialog(QDialog):
    def __init__(self, config):
        super().__init__()
    
        self.config = config
        self.setWindowTitle("Create AcuGIS Cloud QWC2 tenant")
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

        self.server_dropdown = QComboBox()
        server_names = list(config.keys())
        self.server_dropdown.addItems(server_names)

        self.tenant_name = QLineEdit()
    
        # optional: give inputs some minimum width so the dialog must grow
        self.server_dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tenant_name.setMinimumWidth(100)
    
        form_layout.addRow("Server:", self.server_dropdown)
        form_layout.addRow("Tenant:", self.tenant_name)
    
        self.layout.addLayout(form_layout)
    
        button_box = QHBoxLayout()
        create_btn = QPushButton("Create")
        cancel_btn = QPushButton("Cancel")
        button_box.addWidget(create_btn)
        button_box.addWidget(cancel_btn)
        self.layout.addLayout(button_box)
    
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(120)
        self.log_output.setVisible(False)
        self.layout.addWidget(self.log_output)
                    
        self.setLayout(self.layout)
    
        # make the dialog open bigger and allow growing
        self.setMinimumSize(260, 210)
        self.resize(360, 260)  # initial size
        self.setSizeGripEnabled(True)
    
        # let form fields expand
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    
        create_btn.clicked.connect(self.create_tenant)
        cancel_btn.clicked.connect(self.reject)

    def create_tenant(self):
        server_name = self.server_dropdown.currentText()
        tenant_name = self.tenant_name.text()

        if not server_name or not tenant_name:
            QMessageBox.warning(self, "Missing Info", "Please select a server and tenant name.")
            return

        server_info = self.config[server_name]
        proto = 'https' if server_info['port'] == 443 else 'http'

        s = requests.Session()
        
        try:
            if not app_http_login(s, proto, server_info['host'], server_info['username'], server_info['password']):
                QMessageBox.warning(None, "Login error", "Failed to login.")
                return

            response = s.post(proto + '://' + server_info['host'] + '/admin/action/qwc2.php', data={'create_tenant':True, 'name': tenant_name, 'tenant':'default'}, timeout=(10, 30))
            if response.status_code != 200:
                QMessageBox.warning(None, "HTTP error", "HTTP code " + response.status_code)
                return

            response = response.json();
            if response['success']:
                QMessageBox.information(None, "AcuGIS Cloud QWC2", response['message'])
            else:
                QMessageBox.warning(None, "QWC2 error", response['message'])

        except Exception as e:
            QMessageBox.warning(None, "HTTP error", "HTTP code " + response.status_code)
            return

        self.accept()
