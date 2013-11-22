#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from qimage2ndarray import array2qimage

from data_manager import DataManager
from data_tree_model import DataTreeModel

from gui_flow_layout import FlowLayout


class ImagesGallery(QtGui.QWidget):
    """Images Gallery (ImagesGallery)

    The ImagesGallery class is a widget that display images in a QHBoxLayout.
    """

    def __init__(self, parent=None):
        super(ImagesGallery, self).__init__(parent)

        self._create_ui()

    def show_images(self, images):
        """Show images in a QHBoxLayout

        Args:
            images: An array of images. Each image is a numpy matrix.
        """

        nimages = images.shape[1]
        cur_nwidgets = len(self.subwidgets)

        layout = self.layout()

        # Expand of shrink the sub widgets list

        if nimages > cur_nwidgets:
            for i in xrange(nimages - cur_nwidgets):
                x = QtGui.QLabel()
                self.subwidgets.append(x)
                layout.addWidget(x)
        else:
            for i in xrange(nimages, cur_nwidgets):
                layout.removeWidget(self.subwidgets[i])
                self.subwidgets[i].deleteLater()
            self.subwidgets = self.subwidgets[0:nimages]

        for i, x in enumerate(self.subwidgets):
            qimg = array2qimage(images[0, i])
            x.setPixmap(QtGui.QPixmap.fromImage(qimg))

    def _create_ui(self):
        self.setLayout(FlowLayout())
        self.subwidgets = []


class PedesGallery(QtGui.QWidget):
    """Pedestrian Images Gallery (PedesGallery)

    The PedesGallery class is a widget that display images of a pedestrian from 
    different views.
    """

    def __init__(self, parent=None):
        super(PedesGallery, self).__init__(parent)

        self._create_ui()

    def show_pedes(self, pedes):
        """Show images of a same pedestrian from different views 

        Args:
            pedes: An array of different views of the pedestrian. Each element 
            is itself an array of images in that view.
        """

        nviews = pedes.shape[0]
        cur_nwidgets = len(self.subwidgets)
        
        layout = self.layout()

        # Expand or shrink the sub widgets list

        if nviews > cur_nwidgets:
            for i in xrange(nviews - cur_nwidgets):
                x = ImagesGallery()
                self.subwidgets.append(x)
                layout.addWidget(x)
        else:
            for i in xrange(nviews, cur_nwidgets):
                layout.removeWidget(self.subwidgets[i])
                self.subwidgets[i].deleteLater()
            self.subwidgets = self.subwidgets[0:nviews]

        for i, x in enumerate(self.subwidgets):
            x.show_images(pedes[i])

    def clear(self):
        layout = self.layout()

        for x in self.subwidgets:
            layout.removeWidget(x)
            x.deleteLater()

        self.subwidgets = []

    def _create_ui(self):
        self.setLayout(QtGui.QVBoxLayout())
        self.subwidgets = []


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self._set_codec("UTF-8")

        self._dm = DataManager(verbose=True)

        self._cur_pid = None
        self._cur_pedes = None
        self._cur_index = None

        self._create_panels()
        self._create_docks()
        self._create_menus()

        self.setWindowTitle("Person Re-id Dataset Viewer")
        self.showMaximized()

    def open(self):
        fpath = QtGui.QFileDialog.getOpenFileName(self, "Open File",
            QtCore.QDir.homePath(), "Matlab File (*.mat)")

        if fpath.isEmpty(): return

        # TODO: Handle errors
        self._dm.read(str(fpath))  # Convert QString into Python String

        # TODO: Check if we should manually delete it
        self._tree_dock = QtGui.QTreeView(self._dock)
        self._tree_dock.setModel(DataTreeModel(self._dm, self._tree_dock))
        self._tree_dock.setColumnWidth(0, 200)
        self._tree_dock.setColumnWidth(1, 100)
        self._tree_dock.doubleClicked[QtCore.QModelIndex].connect(self.display)

        self._dock.setWidget(self._tree_dock)

        self._gallery_panel.clear()

    def display(self, index):
        gid = index.parent().row()
        pid = index.row()

        if gid >= 0 and pid >= 0:  # gid is -1 when double click a group
            pedes = self._dm.get_pedes(gid)

            self._cur_pid = pid
            self._cur_pedes = pedes
            self._cur_index = index

            self._gallery_panel.show_pedes(pedes[pid, :])
        else:
            self._cur_pid = None
            self._cur_pedes = None
            self._cur_index = None


    def next_pedes(self):
        if self._cur_pedes is None or self._cur_pid is None: return

        if self._cur_pid + 1 >= self._cur_pedes.shape[0]:
            msg = QtGui.QMessageBox()
            msg.setText("Reach the end of the group")
            msg.exec_()
        else:
            self._cur_pid += 1
            self._gallery_panel.show_pedes(self._cur_pedes[self._cur_pid, :])

            next_index = self._cur_index.sibling(self._cur_pid, 0)
            self._tree_dock.setCurrentIndex(next_index)
            self._cur_index = next_index

    def prev_pedes(self):
        if self._cur_pedes is None or self._cur_pid is None: return

        if self._cur_pid -1 < 0:
            msg = QtGui.QMessageBox()
            msg.setText("Reach the begining of the group")
            msg.exec_()
        else:
            self._cur_pid -= 1
            self._gallery_panel.show_pedes(self._cur_pedes[self._cur_pid, :])
            
            prev_index = self._cur_index.sibling(self._cur_pid, 0)
            self._tree_dock.setCurrentIndex(prev_index)
            self._cur_index = prev_index

    def _set_codec(self, codec_name):
        codec = QtCore.QTextCodec.codecForName(codec_name)
        QtCore.QTextCodec.setCodecForLocale(codec)
        QtCore.QTextCodec.setCodecForCStrings(codec)
        QtCore.QTextCodec.setCodecForTr(codec)

    def _create_panels(self):
        self._gallery_panel = PedesGallery(self)

        self.setCentralWidget(self._gallery_panel)

    def _create_docks(self):

        self._dock = QtGui.QDockWidget(self)
        self._dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self._dock.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
        self._dock.setMinimumWidth(350)

        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock)

    def _create_menus(self):
        # Actions
        open_act = QtGui.QAction("Open", self)
        open_act.setShortcut(QtGui.QKeySequence(QtGui.QKeySequence.Open))
        open_act.triggered.connect(self.open)

        next_pedes_act = QtGui.QAction("Next Pedestrian", self)
        next_pedes_act.setShortcut(QtGui.QKeySequence(QtGui.QKeySequence.Forward))
        next_pedes_act.triggered.connect(self.next_pedes)

        prev_pedes_act = QtGui.QAction("Prev Pedestrian", self)
        prev_pedes_act.setShortcut(QtGui.QKeySequence(QtGui.QKeySequence.Back))
        prev_pedes_act.triggered.connect(self.prev_pedes)

        # Menu Bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(open_act)

        # Tool Bar
        toolbar = self.addToolBar("Toolbar")
        toolbar.addAction(next_pedes_act)
        toolbar.addAction(prev_pedes_act)


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())