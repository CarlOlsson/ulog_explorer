import sys
import numpy as np
from scipy import signal
import pandas as pd

# from PyQt4 import QtGui, QtCore
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
from pyulog import *
import argparse
from pathlib import Path
from os.path import expanduser
import collections

# The variables currently displayed consists of a list of CurveClass items


class GUIBackend():
    def __init__(self):
        # List of curve class elements currently displayed
        self.plotting_data = []

        # Ordered dictionary of colors and if they are occupied or not
        color_tuples = [("C0", [False, [31, 119, 180]]),
                        ("C1", [False, [255, 127, 14]]),
                        ("C2", [False, [44, 160, 44]]),
                        ("C3", [False, [214, 39, 40]]),
                        ("C4", [False, [148, 103, 189]]),
                        ("C5", [False, [140, 86, 75]]),
                        ("C6", [False, [227, 119, 194]]),
                        ("C7", [False, [127, 127, 127]]),
                        ("C8", [False, [188, 189, 34]]),
                        ("C9", [False, [23, 190, 207]])]

        self.color_dict = collections.OrderedDict(color_tuples)

    # Returns true if the selected topic and field is already in the list
    def contains(self, selected_topic, selected_field):
        selected_topic_and_field = get_name_combined(selected_topic, selected_field)
        for elem in self.plotting_data:
            if elem.selected_topic_and_field == selected_topic_and_field:
                return True

        return False

    # Adds the selected topic and field to the list of variables to plot. Returns false if we don't have space for more variables
    def add_selected_topic_and_field(self, selected_topic, selected_field):
        for key, value in self.color_dict.items():
            if not value[0]:
                self.color_dict[key][0] = True
                color_key = key
                color = value[1]
                break

        self.plotting_data.append(CurveClass(selected_topic, selected_field, color_key, color))

    # Removes the selected topic and field from the list of variables to plot
    def remove_selected_topic_and_field(self, selected_topic, selected_field):
        index = 0
        for elem in self.plotting_data:
            if elem.selected_topic == selected_topic and elem.selected_field == selected_field:
                self.plotting_data.pop(index)
                self.color_dict[elem.color_key][0] = False

            index = index + 1

    def clear_plotting_data(self):
        self.plotting_data = []
        for key, value in self.color_dict.items():
            self.color_dict[key][0] = False


class CurveClass():
    def __init__(self, selected_topic, selected_field, color_key, color):
        self.selected_topic = selected_topic
        self.selected_field = selected_field
        self.selected_topic_and_field = get_name_combined(selected_topic, selected_field)
        self.color_key = color_key
        self.color = color


def get_name_combined(selected_topic, selected_field):
    return selected_topic + "->" + selected_field


def get_name_seperate(selected_topic_and_field):
    selected_topic = selected_topic_and_field.split('->')[0]
    selected_field = selected_topic_and_field.split('->')[1]
    return selected_topic, selected_field


class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()

        # Parse arguments
        parser = argparse.ArgumentParser(description='Used to analyse uLog files')
        parser.add_argument("-f")
        args = parser.parse_args()

        self.main_widget = QtGui.QWidget(self)
        self.main_layout = QtGui.QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        self.setGeometry(50, 50, 1000, 800)  # (x_pos, y_pos, width, height)
        # self.showMaximized()
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        # List of selected topics
        self.selected_fields_frame = QtGui.QFrame(self)
        self.selected_fields_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.selected_fields_and_button_layout = QtGui.QVBoxLayout(self.selected_fields_frame)
        self.selected_fields_list_widget = QtGui.QListWidget(self.selected_fields_frame)
        self.selected_fields_list_widget.itemClicked.connect(self.callback_selected_fields_list_clicked)
        self.selected_fields_and_button_layout.addWidget(self.selected_fields_list_widget)

        clear_btn_layout = QtGui.QHBoxLayout()
        self.clear_btn = QtGui.QPushButton('Clear')
        self.clear_btn.clicked.connect(self.callback_clear_plot)
        clear_btn_layout.addWidget(self.clear_btn)
        self.selected_fields_and_button_layout.addLayout(clear_btn_layout)

        # Create the frame for the data tree used to select topics to plot
        self.tree_frame = QtGui.QFrame(self)
        self.tree_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.tree_frame.resize(200, 700)
        self.tree_layout = QtGui.QVBoxLayout(self.tree_frame)

        self.topic_tree_widget = QtGui.QTreeWidget(self.tree_frame)
        self.topic_tree_widget.clear()
        self.topic_tree_widget.setColumnCount(1)
        self.topic_tree_widget.setHeaderHidden(True)
        self.topic_tree_widget.setExpandsOnDoubleClick(False)
        self.topic_tree_widget.itemClicked.connect(self.callback_topic_tree_clicked)
        self.topic_tree_widget.itemDoubleClicked.connect(self.callback_topic_tree_doubleClicked)
        # self.topic_tree_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)  # make it possible to select many items
        # self.topic_tree_widget.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)  # use this one
        self.topic_tree_widget.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        # self.topic_tree_widget.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)  # make it possible to select many items
        # self.topic_tree_widget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)  # http://doc.qt.io/archives/qt-4.8/qabstractitemview.html

        # Load logfile from argument or file dialog
        if args.f and Path(args.f).is_file() and Path(args.f).suffix == ".ulg":
            self.path_to_logfile = args.f
            self.load_logfile_to_tree(self.path_to_logfile)
        elif args.f and Path(args.f).is_dir():
            self.open_logfile(args.f)
        else:
            self.open_logfile()

        self.tree_layout.addWidget(self.topic_tree_widget)
        # -----------------------------------

        self.graph_frame = QtGui.QFrame(self)
        self.graph_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.graph_layout = QtGui.QVBoxLayout(self.graph_frame)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.graph_widget = pg.GraphicsLayoutWidget()

        self.main_graph = self.graph_widget.addPlot(row=0, col=0)
        self.main_graph.showGrid(True, True, 0.5)
        self.main_graph.keyPressEvent = self.keyPressed
        # self.main_graph.addLegend()

        self.graph_layout.addWidget(self.graph_widget)

        self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter1.addWidget(self.selected_fields_frame)
        self.splitter1.addWidget(self.tree_frame)

        self.splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter2.addWidget(self.graph_frame)

        self.splitter3 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.splitter3.addWidget(self.splitter2)
        self.splitter3.addWidget(self.splitter1)

        self.main_layout.addWidget(self.splitter3)

        self.setCentralWidget(self.main_widget)

        self.linewidth = 1
        self.show_legend = False

        self.backend = GUIBackend()
        self.update_frontend()

    def keyPressed(self, event):
        if event.key() == QtCore.Qt.Key_R:
            self.main_graph.autoRange()
        elif event.key() == QtCore.Qt.Key_O:
            self.open_logfile(self.path_to_logfile)
            self.update_frontend()
            self.main_graph.autoRange()
        elif event.key() == QtCore.Qt.Key_L:
            self.show_legend = not self.show_legend
            self.update_frontend()
        elif event.key() == QtCore.Qt.Key_C:
            self.callback_clear_plot()
        elif event.key() == QtCore.Qt.Key_B:
            if self.linewidth == 1:
                self.linewidth = 3
            else:
                self.linewidth = 1

            self.update_frontend()

    def open_logfile(self, path_to_dir=expanduser('~')):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open Log File', path_to_dir, 'Log Files (*.ulg)')
        if isinstance(filename, tuple):
            filename = filename[0]
        if filename:
            try:
                self.path_to_logfile = filename
                self.load_logfile_to_tree(self.path_to_logfile)
            except Exception as ex:
                print(ex)

    def load_logfile_to_tree(self, logfile_str):
        self.df_dict = self.ulog_to_df(logfile_str)

        self.topic_tree_widget.clear()
        # for topic_str, fields_df in self.df_dict.iteritems(): python2
        for topic_str, fields_df in sorted(self.df_dict.items()):
            current_topic = QtGui.QTreeWidgetItem(self.topic_tree_widget, [topic_str])
            for field in sorted(list(fields_df)):
                current_field = QtGui.QTreeWidgetItem(current_topic, [field])

    def callback_topic_tree_doubleClicked(self):
        print("dont double click!")

    def callback_selected_fields_list_clicked(self, item):
        # Remove the selected field from the tree
        selected_topic_and_field = item.text()
        selected_topic, selected_field = get_name_seperate(selected_topic_and_field)
        self.backend.remove_selected_topic_and_field(selected_topic, selected_field)
        self.update_frontend()

    def callback_clear_plot(self):
        self.backend.clear_plotting_data()
        self.update_frontend()

    def callback_topic_tree_clicked(self, item, col):
        # Do nothing if a topic was pressed
        if item.parent() is None:
            item.setSelected(False)
            item.setExpanded(not item.isExpanded())
            return

        # Get the selected topic and field as strings
        selected_topic = item.parent().text(0)
        selected_field = item.text(0)

        if self.backend.contains(selected_topic, selected_field):
            self.backend.remove_selected_topic_and_field(selected_topic, selected_field)
            self.update_frontend()
            return

        self.backend.add_selected_topic_and_field(selected_topic, selected_field)
        self.update_frontend()

        # Color the selected field and correspnding topic grey in the tree view
        # item.setBackground(0, QtGui.QBrush(QtCore.Qt.gray))
        # item.parent().setBackground(0, QtGui.QBrush(QtCore.Qt.gray))

    def update_frontend(self):
        self.main_graph.clearPlots()
        self.selected_fields_list_widget.clear()
        self.selected_fields_list_widget.clearSelection()
        self.topic_tree_widget.clearSelection()

        # Set all topic colors to white in the tree
        for topic_index in range(self.topic_tree_widget.topLevelItemCount()):
            self.topic_tree_widget.topLevelItem(topic_index).setBackground(0, QtGui.QBrush(QtCore.Qt.white))

        if self.show_legend:
            self.main_graph.addLegend()
            self.show_legend = False
        for elem in self.backend.plotting_data:
            color = elem.color
            pen = pg.mkPen(width=self.linewidth, color=color)
            curve = self.main_graph.plot(self.df_dict[elem.selected_topic].index, self.df_dict[elem.selected_topic][elem.selected_field].values, pen=pen, name=elem.selected_topic_and_field)

            # Add the newly selected field to the list of all currently selected fields
            new_list_item = QtGui.QListWidgetItem(elem.selected_topic_and_field)
            new_list_item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
            self.selected_fields_list_widget.addItem(new_list_item)

            # Show the current curve class element as selected in the tree view and the corresponding topic as grey
            top_level_item = self.topic_tree_widget.findItems(elem.selected_topic, QtCore.Qt.MatchExactly)[0]
            top_level_item.setBackground(0, QtGui.QBrush(QtCore.Qt.gray))
            for field_index in range(top_level_item.childCount()):
                field_name = top_level_item.child(field_index).text(0)
                if field_name == elem.selected_field:
                    top_level_item.child(field_index).setSelected(True)
                    break

        # Autorange if only one field is displayed
        if len(self.backend.plotting_data) == 1:
            self.main_graph.autoRange()

        # Update the window title
        self.setWindowTitle('ulog_explorer: ' + self.path_to_logfile)

    # Convert a pyulog.core.ULog object to a dictionary of dataframes
    def ulog_to_df(self, logfile_str):
        ulog_dict = {}
        for ulog_topic_object in ULog(logfile_str).data_list:
            topic_name = ulog_topic_object.name
            column_names = set(ulog_topic_object.data.keys())
            df = pd.DataFrame(index=ulog_topic_object.data['timestamp'] / 1e6)
            for name in column_names - {'timestamp'}:
                df[name] = ulog_topic_object.data[name]

            ulog_dict[topic_name] = df
        return ulog_dict


app = QtGui.QApplication(sys.argv)
GUI = Window()
GUI.show()
sys.exit(app.exec_())
