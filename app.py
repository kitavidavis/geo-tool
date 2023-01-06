import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import turtle as t

from zipfile import ZipFile
from io import BytesIO
import requests

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import geopandas

import qdarkstyle

from PyQt5.QtWidgets import QMainWindow,QAction, QFileDialog, QPushButton, QLineEdit,QFormLayout, QVBoxLayout, QComboBox, QLabel, QWidget
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QSize

import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

try:
    from qtconsole import inprocess
except (ImportError, NameError):
    sys.exit("Error: cannot find qtconsole modules")

try:
    from osgeo import gdal, ogr, osr, gdal_array
except:
    sys.exit('Error: cannot find GDAL/OGR modules')

# Enable GDAL/OGR exceptions
gdal.UseExceptions()

# create a working directory
path = "C:\\Users\\hp\\Desktop\\python-projects\\pyqt-tutorial\\Rasterai"
isExist = os.path.exists(path)
if not isExist:
    os.makedirs(path)
    print("Made new directory at %s" % path)


# Interpret image data as row-major instead of col-major
pg.setConfigOptions(imageAxisOrder='row-major')

global d1
global d2
global w3

class JupyterConsoleWidget(inprocess.QtInProcessRichJupyterWidget):
    def __init__(self):
        super().__init__()

        self.kernel_manager = inprocess.QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

    def shutdown_kernel(self):
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()


class JupyterMainWindow(QtWidgets.QMainWindow):
    def __init__(self, dark_mode=True):
        super().__init__()
        central_dock_area = DockArea()

        # create plot widget (and  dock)
        self.plot_widget = pg.PlotWidget()
        plot_dock = Dock(name="Plot Widget Dock", closable=True)
        plot_dock.addWidget(self.plot_widget)
        central_dock_area.addDock(plot_dock)

        # create jupyter console widget (and  dock)
        self.jupyter_console_widget = JupyterConsoleWidget()
        jupyter_console_dock = Dock("Jupyter Console Dock")
        jupyter_console_dock.addWidget(self.jupyter_console_widget)
        central_dock_area.addDock(jupyter_console_dock)
        self.setCentralWidget(central_dock_area)

        app = QtWidgets.QApplication.instance()
        app.aboutToQuit.connect(self.jupyter_console_widget.shutdown_kernel)

        kernel = self.jupyter_console_widget.kernel_manager.kernel
        kernel.shell.push(dict(np=np, pw=self.plot_widget))

        # set dark mode
        if dark_mode:
            # Set Dark bg color via this relatively roundabout method
            self.jupyter_console_widget.set_default_style(
                "linux"
            )

class GetFilePath(QMainWindow):
    def __init__(self, parent=None):
        super(GetFilePath, self).__init__(parent)


        self.setWindowTitle("Filename")

        self.setMaximumSize(500, 300)
        self.setMinimumSize(500, 300)

        self.setUI

    def setUI(self):
        self.layout = QFormLayout()

        ## URL input form
        fileEdit = QLineEdit()
        fileEdit.setStyleSheet("height: 30px;")

        self.layout.addRow(fileEdit)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)


class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        kwds['enableMenu'] = False
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.RectMode)
        
    ## reimplement right-click to zoom out
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.RightButton:
            self.autoRange()
    
    ## reimplement mouseDragEvent to disable continuous axis zoom
    def mouseDragEvent(self, ev, axis=None):
        if axis is not None and ev.button() == QtCore.Qt.MouseButton.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev, axis=axis)

class LoadURL(QMainWindow):
    def __init__(self, parent=None):
        super(LoadURL, self).__init__(parent)

        self.setWindowTitle("Load URL")

        self.setMaximumSize(500, 300)
        self.setMinimumSize(500, 300)

        self.setUI()

    def setUI(self):
        self.layout = QFormLayout()

        ## URL input form
        fileTypeLabel = QLabel("File Type")
        self.fileTypeField = QComboBox()
        self.fileTypeField.setStyleSheet("height: 30px; margin-bottom: 10px;")

        self.layout.addRow(fileTypeLabel, self.fileTypeField)

        types = ["CSV", "Raster", "ESRI Shapefile"]

        self.fileTypeField.addItems(types)

        urlLabel = QLabel("URL")
        self.urlEdit = QLineEdit()
        self.urlEdit.placeholderText="e.g https://example.com"
        self.urlEdit.setStyleSheet("height: 30px;")

        self.layout.addRow(urlLabel, self.urlEdit)

        connect_button = QPushButton('Load')
        connect_button.setStyleSheet("height: 30px; margin: 30px;")
        connect_button.clicked.connect(self.parseURL)
        self.layout.addRow(connect_button)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

    def parseURL(self):
        file_type = self.fileTypeField.currentText()
        url = self.urlEdit.text()

        if file_type == "CSV":
            w3.write(strn="Parsing csv -> "+url + "\n")
            dataset = urllib.request.urlopen(url)
            for record in dataset:
                w3.write(strn=str(record)+ "\n")

        elif file_type == "Raster":
            w3.write(strn="Parsing raster ->"+url+ "\n")
            dataset = urllib.request.urlopen(url)
            print(dataset)

        elif file_type == "ESRI Shapefile":
            w3.write(strn="Parsing shapefile ->" + url+"\n")

            file_location = os.path.join(path, os.path.basename(url))

            #print(file_location)

            self.downloadURL(url=url, save_path=file_location)

            
            zip = open(file_location, "rb")

            zipShape = ZipFile(zip)

            layers = []

            for fileName in zipShape.namelist():
                ext = os.path.splitext(fileName)[1][1:]
                if ext != "shp":
                    continue
                else:
                    layers.append(os.path.join(path, fileName).replace("\\","/"))

            # unzip the file contents to get the zip contents
            with ZipFile(file_location, 'r') as zip_ref:
                zip_ref.extractall(path)

            for layer in layers:
                driver = ogr.GetDriverByName('ESRI Shapefile')
                data_source = driver.Open(layer) # 0 means read-only. 1 means writeable
                # check to see if the shapefile is found
                if data_source is None:
                    w3.write(strn="Could not open %s \n" % layer)
                else:
                    mpl.rcParams['toolbar'] = 'None'
                    w3.write(strn="Opened %s \n" % layer)
                    l = data_source.GetLayer()
                    featureCount = l.GetFeatureCount()
                    w3.write(strn="Number of features in %s: %d \n" % (l, featureCount))
                    gdf = geopandas.GeoDataFrame
                    shp = gdf.from_file(layer)
                    shp.plot()
                    plt.axis('off')
                    plt.show()
       
        self.close()

    def downloadURL(self, url, save_path, chunk_size=128):
        r = requests.get(url, stream=True)
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)

        w3.write(strn="Download complete..... \n")


class PostgreSQL(QMainWindow):
    x = 1

    def __init__(self, parent=None):
        super(PostgreSQL, self).__init__(parent)

        self.setWindowTitle("Connect to PostgreSQL")

        self.setMaximumSize(500, 300)
        self.setMinimumSize(500, 300)

        self.setUI()

    def setUI(self):
        self.layout = QFormLayout()

        ## server name label and input field 
        serverLabel = QLabel("Server Name:")
        serverField = QLineEdit()

        serverField.setStyleSheet("height: 30px;")

        self.layout.addRow(serverLabel, serverField)

        databaseLabel = QLabel("Database Name:")
        databaseField = QLineEdit()

        databaseField.setStyleSheet("height: 30px;")

        self.layout.addRow(databaseLabel, databaseField)

        usernameLabel = QLabel("Username:")
        usernameEdit = QLineEdit()

        usernameEdit.setStyleSheet("height: 30px;")

        self.layout.addRow(usernameLabel, usernameEdit)

        passwordLabel = QLabel("Password:")
        passwordField = QLineEdit(echoMode=QLineEdit.EchoMode.Password)

        passwordField.setStyleSheet("height: 30px;")

        self.layout.addRow(passwordLabel, passwordField)

        self.connect_button = QPushButton('Connect')
        self.connect_button.setStyleSheet("height: 30px; margin: 30px;")
        self.layout.addRow(self.connect_button)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.work_dir = os.path.join("C:\\", "RasterAI")
        
        self.setWindowTitle("Raster AI")

        self.setMinimumHeight(650)

        self.setMinimumWidth(500)

        button_action = QAction(QIcon("icons/icons/document.png"), "New", self)
        button_action.setShortcut(QKeySequence('Ctrl+N'))
        button_action.triggered.connect(self.onMyToolBarButtonClick)

        open_folder = QAction(QIcon("icons/icons/folder-horizontal-open.png"), "Open", self)
        open_folder.setShortcut(QKeySequence('Ctrl+O'))
        open_folder.triggered.connect(self.open)

        open_from = QAction("Open from URL", self)
        open_from.triggered.connect(self.showURLLoader)

        open_recent = QAction("Open Recent", self)

        connect_postgres = QAction("Connect to PostgreSQL", self)
        connect_postgres.triggered.connect(self.showPostgreSQLDialog)

        connect_geopsy_collect = QAction("Connect to GeoPsy Collect", self)

        save = QAction(QIcon("icons/icons/printer.png"),"Save", self)
        save.setShortcut(QKeySequence('Ctrl+S'))

        save_as = QAction(QIcon("icons/icons/printer--arrow.png"), "Save As", self)
        save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))

        undo = QAction("Undo", self)
        undo.setShortcut(QKeySequence('Ctrl+Z'))
        redo = QAction("Redo", self)
        exit_app = QAction("Exit App", self)
        exit_app.setShortcut(QKeySequence('Ctrl+Q'))
        exit_app.triggered.connect(self.exitApp)

        # tools item
        self.polygonize = QAction("Polygonize Raster", self)
        self.polygonize.setEnabled(False)
        self.polygonize.triggered.connect(self.polygonizeRaster)

        vector_to_raster = QAction("Vector to Raster", self)

        # view menu items
        console_menu = QAction("Jupyter Console", self)
        console_menu.triggered.connect(self.connectJupyterConsole)

        menu = self.menuBar()

        menu.setBaseSize(200, 650)

        menu.setStyleSheet(
            """
             QMenuBar::item {
                margin-right: 15px;
                background-color: transparent;
             }
            QMenu {
                margin: 5px; /* some spacing around the menu */
                top: 20px;
            }
            QMenu::item {
                padding: 8px 25px 8px 20px;
            }
            """
            )


        file_menu = menu.addMenu("&File")
        file_menu.addAction(button_action)
        file_menu.addSeparator()
        file_menu.addAction(open_folder)
        file_menu.addAction(open_from)
        file_menu.addAction(open_recent)
        file_menu.addSeparator()
        file_menu.addAction(save)
        file_menu.addAction(save_as)
        file_menu.addSeparator()
        file_menu.addAction(connect_postgres)
        file_menu.addAction(connect_geopsy_collect)
        file_menu.addSeparator()
        file_menu.addAction(undo)
        file_menu.addAction(redo)
        file_menu.addSeparator()
        file_menu.addAction(exit_app)
        project_menu = menu.addMenu("&Tools")
        project_menu.addAction(self.polygonize)
        project_menu.addAction(vector_to_raster)
        layer_menu = menu.addMenu("&Layer")
        edit_menu = menu.addMenu("&Edit")
        view_menu = menu.addMenu("&View")
        view_menu.addAction(console_menu)
        settings_menu = menu.addMenu("&Settings")

        self.PostgreSQLDialog = PostgreSQL(self)
        self.LoadURL = LoadURL(self)
        self.GetFilePath = GetFilePath(self)

    def onMyToolBarButtonClick(self, s):
        print("click", s)

    def open(self):
        filename = QFileDialog.getOpenFileName(self, 'Select File', '.')
        self.filename = filename[0]
        self.getRasterMetadata(filename=self.filename)
        self.getRasterBands(filename=self.filename)
        dataset = gdal.Open(self.filename, gdal.GA_ReadOnly) 
        # Note GetRasterBand() takes band no. starting from 1 not 0
        band = dataset.GetRasterBand(1)
        arr = band.ReadAsArray()

        colors = [
            (0, 0, 0),
            (4, 5, 61),
            (84, 42, 55),
            (15, 87, 60),
            (208, 17, 141),
            (255, 255, 255)
        ]
 
        # color map
        cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color = colors)

        v = pg.image(arr)
        #v.ui.histogram.hide()
        #v.ui.roiBtn.hide()
        #v.ui.menuBtn.hide()
        #v.imageItem.getHistogram().hide()
        v.setColorMap(cmap)
        d1.addWidget(v)
        #srcband = gtif.GetRasterBand(1)
        #srcband.ComputeStatistics(0)
        #print ("[ MIN ] = ", srcband.GetMinimum())
        #print ("[ MAX ] = ", srcband.GetMaximum())

        hist = pg.HistogramLUTItem()
        hist.setImageItem(arr)
        d2.addWidget(hist)

        self.polygonize.setEnabled(True)

    def getRasterMetadata(self, filename):
        gtif = gdal.Open(filename)
        w3.write(strn="------------ Getting raster metadata --------------\n")
        w3.write(strn=json.dumps(gtif.GetMetadata()) + "\n")
        w3.write(strn="------------ End of raster metadata --------------\n")

    def getRasterBands(self, filename):
        src_ds = gdal.Open(filename)
        if src_ds is None:
            print("Unable to open %s" %filename)
            sys.exit(1)

        w3.write(strn="---------------- Total band count --------------\n")
        w3.write(strn= "Total bands="+str(src_ds.RasterCount)+"\n")
        w3.write(strn="---------------- Done counting bands --------------\n")

        for band in range(src_ds.RasterCount):
            band += 1
            w3.write(strn="[Getting Band] %s \n" % band)
            srcband = src_ds.GetRasterBand(band)
            if srcband is None:
                continue
            stats = srcband.GetStatistics(True, True)
            if stats is None:
                continue

            w3.write(strn="[STATS] = Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f \n" % ( \
                stats[0], stats[1], stats[2], stats[3]
            ))

    def histogram(self, a, bins=list(range(0, 256))):
        fa = a.flat
        n = gdal_array.numpy.searchsorted(gdal_array.numpy.sort(fa), bins)
        n = gdal_array.numpy.concatenate([n, [len(fa)]])
        hist = n[1:]-n[:-1]
        return hist

    def drawHistogram(self, hist, scale=True):
        t.color("black")
        axes=((-355, -200), (355, -200), (-355, -200), (-355, 250))
        t.up()
        for p in axes:
            t.goto(p)
            t.down()
            t.up()

    def polygonizeRaster(self):
        src_ds = gdal.Open(self.filename)

        if src_ds is None:
            w3.write("Unable to open %s" % self.filename)

        try:
            srcband = src_ds.GetRasterBand(1)
        except:
            print("Band 3 not found")
            sys.exit()


        name = os.path.basename(self.filename).split('.')[0]
        layerName = name
        drv = ogr.GetDriverByName("ESRI Shapefile")
        dst_ds = drv.CreateDataSource(layerName + ".shp")
        dst_layer = dst_ds.CreateLayer(layerName, srs=None)
        gdal.Polygonize(srcband,None, dst_layer, -1, [], callback=None )

    def connectJupyterConsole(self):
        main_jc = JupyterMainWindow(dark_mode=True)
        main_jc.show()

    def showPostgreSQLDialog(self):
        self.PostgreSQLDialog.show()

    def showURLLoader(self):
        self.LoadURL.show()

    def showGetFilePath(self):
        self.GetFilePath.show()

    def connectPostgreSQL(self, serverName, databaseName, userName, password):
        connectionString = "PG: host=%s dbname=%s user=%s password=%s" %(serverName, databaseName, userName, password)
        connection = ogr.Open(connectionString)

        layerList = []
        for i in connection:
            dataLayer = i.GetName()
            if not dataLayer in layerList:
                layerList.append(dataLayer)

        layerList.sort()

        for j in layerList:
            print(j)
    def processFilename(self):
        dataset = gdal.Open(self.filename, gdal.GA_ReadOnly)
        band = dataset.GetRasterBand(1)
        print("Band Type={}".format(gdal.GetDataTypeName(band.DataType)))
    def setDarkTheme(self):
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

    def setLightTheme(self):
        app.setStyleSheet("")

    def exitApp(self):
        sys.exit()



app = pg.mkQApp()

namespace = {'pg': pg, 'np': np, 'plt': plt, 'gdal': gdal, 'sys': sys, 'ogr': ogr, 'osr': osr }

## initial text to display on the python console
text = """
This is an interactive python console.\n
"""

app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

w = MainWindow()

area = DockArea()

w.setCentralWidget(area)

w.resize(1000, 600)

## Create docks, place theme into the window one at a time
d1 = Dock("Canvas", size=(1000, 650)) # give this dock the minimum posible size
d2 = Dock("Charts", size=(700, 300), closable=True)
d3 = Dock("Console", size=(500, 200), closable=True)
d4 = Dock("Variables", size=(700, 400), closable=True)


d1.hideTitleBar()
d2.hideTitleBar()
d3.hideTitleBar()
d4.hideTitleBar()

area.addDock(d1, 'left')
area.addDock(d2, 'right')
area.addDock(d3, 'bottom', d1)
area.addDock(d4, 'bottom', d2)

w3 = ConsoleWidget(namespace=namespace, text=text, historyFile=None, editor=None)
[w3.findChild(QPushButton, name).deleteLater() for name in ("exceptionBtn", "historyBtn")]
d3.addWidget(w3)

## list of drivers available
count = ogr.GetDriverCount()
formatsList = []
for i in range(count):
    driver = ogr.GetDriver(i)
    driverName = driver.GetName()
    if not driverName in formatsList:
        formatsList.append(driverName)

formatsList.sort()


w.show()
app.exec()