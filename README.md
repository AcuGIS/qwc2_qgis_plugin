# QWC2 Plugin for AcuGIS Cloud

![AcuGIS Cloud QWC2 Upload QGIS](docs/_static/Menu.png)

AcuGIS [QWC2 Login App](https://git.sh8.eu/LymonHead/qwc2_login_app/) Plugin for QGIS is a plugin for tranfering contents of a QGIS Project to a QWC2 Login App tenant.

## Features

- Store multiple servers access details
- Transfer entrire directory contents, including sub folders.
- Uses chunks for uploads, to support very large files

## Uses:

- Any case in which you wish to transfer project directory to a AcuGIS Cloud QWC2 server

## Installation

Download qwc2_qgis_plugin.zip to your desktop

In QGIS, go to Plugins > Manage and Install Plugins and click on "Install from Zip" in left menu.

Browse to location where you saved qwc2_qgis_plugin.zip and then click "Install Plugin"

Once installed, you should see the Plugins menu.

Plugin location /home/$USER/.local/share/QGIS/QGIS3/profiles/default/python/plugins/qwc2_qgis_plugin

## Configure Servers:

![AcuGIS Cloud QWC2 Upload QGIS](docs/_static/Create-Servers.png)

- Begin by selecting 'Configure Access':

- Click Add to add server(s).

- Enter Server information

- Click Save.

## Create Tenants


![AcuGIS Cloud QWC2 Upload QGIS](docs/_static/Tenant.png)

- Create Tenants via Plugin
- Select Tenant when Publishing



## Upload to QWC2

![AcuGIS Cloud QWC2 Upload QGIS](docs/_static/Upload.png)


Go to 'Upload Project Directory to Tenant'

Select the Server you wish to upload to.
Select the Tenant you wish to upload to.
Click Upload

.. note::
    Plugin uses file modification time to decide, if a file has to be uploaded.
    
A success message will be displayed up completion.


## Publish Your Map

![AcuGIS Cloud QWC2 Upload QGIS](docs/_static/Publish.png)


## Use Cases

The plugin is only for AcuGIS QWC2 hosting services. It will not work with generic QWC2 installation.
