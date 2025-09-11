import os
import requests
import re
from qgis.PyQt.QtWidgets import QVBoxLayout, QMessageBox, QDialog, QVBoxLayout, QLabel, QFormLayout, QComboBox, QComboBox, QHBoxLayout, QProgressBar, QTextEdit, QDialog, QVBoxLayout, QPushButton, QCheckBox, QSizePolicy
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject
from .util import app_http_login

class UploadDialog(QDialog):
    def __init__(self, config):
        super().__init__()
    
        self.config = config
        self.setWindowTitle("Update AcuGIS Cloud QWC2 theme from Project Directory")
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
        self.tenant_dropdown = QComboBox()
        self.config_checkbox = QCheckBox();

        # optional: give inputs some minimum width so the dialog must grow
        self.server_dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tenant_dropdown.setMinimumWidth(100)

        self.s = None

        server_names = list(config.keys())
        self.server_dropdown.addItems(server_names)
        self.server_dropdown.currentIndexChanged.connect(self.onServerChanged)
        
        self.onServerChanged()
    
        form_layout.addRow("Server:", self.server_dropdown)
        form_layout.addRow("Tenant:", self.tenant_dropdown)
        form_layout.addRow("Configure:", self.config_checkbox)
    
        self.layout.addLayout(form_layout)
    
        button_box = QHBoxLayout()
        upload_btn = QPushButton("Upload")
        cancel_btn = QPushButton("Cancel")
        button_box.addWidget(upload_btn)
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

        upload_btn.clicked.connect(self.start_upload)
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
        self.tenant_dropdown.clear()
        self.tenant_dropdown.addItems(tenants)

    def read_in_chunks(self, file_object, chunk_size=65536):
        while True:
            data = file_object.read(chunk_size)
            if not data:
                break
            yield data

    def start_upload(self):
        server_name = self.server_dropdown.currentText()
        tenant_name = self.tenant_dropdown.currentText()

        if not server_name or not tenant_name:
            QMessageBox.warning(self, "Missing Info", "Please select a server and remote path.")
            return

        server_info = self.config[server_name]
        project_path = QgsProject.instance().fileName()
        if not project_path:
            QMessageBox.warning(None, "No Project", "Please save the QGIS project first.")
            return
        project_dir = os.path.dirname(project_path)
        
        proto = 'https' if server_info['port'] == 443 else 'http'

        try:            
            response = self.s.post(proto + '://' + server_info['host'] + '/admin/action/qwc2.php', data={'list_tenant':True, 'tenant': tenant_name}, timeout=(10, 30))
            if response.status_code != 200:
                response = response.json();
                QMessageBox.warning(None, "Login error", "Failed to get tenant info: " + response['message'])
                return

        except Exception as e:
            QMessageBox.warning(None, "HTTP error", "HTTP exception in tenant info: " + str(e))
            return

        tenant_info = response.json()['tenant'];
        
        file_list = []
        for root, _, files in os.walk(project_dir):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, project_dir)
                
                try:
                    file_info = next(item for item in tenant_info['files'] if item["path"] == relative_path)
                except StopIteration:   # if file is missing on remote
                    file_info = {'path':relative_path, 'mtime':0}
                local_mtime = os.path.getmtime(local_path)

                if int(local_mtime) > file_info['mtime']:
                    file_list.append((local_path,relative_path));
        
        if len(file_list) == 0:
            QMessageBox.warning(None, "Upload info", "No new files to upload")
            return

        project_dir = os.path.dirname(project_path)
        try:
            self.progress_bar.setMaximum(len(file_list))
            self.progress_bar.setVisible(True)
            self.log_output.setVisible(True)
            
            store_updated = True
            chunk_size = tenant_info['post_max_size'] - 1000

            for i, (local_path,relative_path) in enumerate(file_list):
                self.progress_bar.setValue(i + 1)
                try:
                    with open(local_path, 'rb') as f:
                        offset = 0
                        
                        post_values={'action':'upload_bytes', 'source': os.path.basename(local_path)}
                        
                        for chunk in self.read_in_chunks(f):                                
                            post_values['start'] = offset
                            post_values['bytes'] = chunk
                            response = self.s.post(proto + '://' + server_info['host'] + '/admin/action/upload.php', data=post_values, timeout=(10, 30));
                            if response.status_code != 200:
                                raise Exception("Chunk upload failed")
                            offset = offset + len(chunk)
                    
                    post_values={'tenant':tenant_name, 'update_file':True, 'relative_path': relative_path, 'mtime': os.path.getmtime(local_path)}
                    response = self.s.post(proto + '://' + server_info['host'] + '/admin/action/qgs.php', data=post_values, timeout=(10, 30));
                    if response.status_code != 200:
                        raise Exception("Store update failed")

                    self.log_output.append(f"✔ Uploaded: {relative_path}")

                except Exception as e:
                    store_updated = False
                    self.log_output.append(f"✖ Failed to upload {relative_path}: {e}")

            if self.config_checkbox.isChecked():
                self.log_output.setAcceptRichText(True)
                self.log_output.append(f"✖ Running configure for tenant {tenant_name} ...")

                response = self.s.post(proto + '://' + server_info['host'] + '/admin/action/configs.php', data={'tenant':tenant_name, 'configure':True}, timeout=(10, 30));
                if response.status_code != 200:
                    raise Exception("Tenant configure failed")

                response = response.json();
                if response['success']:
                    msg = ''

                    no_tags = re.compile('<.*?>')

                    for l in response['message'].splitlines():
                        if l.startswith('['):
                            msg = msg + re.sub(no_tags, '', l[29:]) + "\n"
                        else:
                            msg = msg + re.sub(no_tags, '', l) + "\n"
                        self.log_output.append(msg)
                else:
                    QMessageBox.warning(None, "QWC2 error", response['message'])

            if store_updated:
                QMessageBox.information(self, "Upload Complete", "Project directory uploaded successfully.")
            else:
                QMessageBox.critical(self, "Upload Incomplete", "Project directory wasn't uploaded successfully.")

            self.accept()
        except Exception as e:
            QMessageBox.critical(None, "Upload Failed", f"An error occurred: {e}")
        
    def get_tenants(self, server_info):
        rv = {}
        
        proto = 'https' if server_info['port'] == 443 else 'http'
        try:
            response = self.s.post(proto + '://' + server_info['host'] + '/admin/action/qwc2.php', data={'list_tenants':True, 'tenant':'default'}, timeout=(10, 30))
            if response.status_code == 200:
                response = response.json()
                rv = response['tenants']
        except Exception as e:
            QMessageBox.critical(None, "HTTP Error", f"An error occurred: {e}")

        return rv
