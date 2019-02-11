import sys
from scipy import signal

# from PyQt4 import QtGui, QtCore
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import argparse
from pathlib import Path
import os
from os.path import expanduser
from GUIBackend import *
import subprocess


class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()

        # Parse arguments
        parser = argparse.ArgumentParser(description='Used to analyse uLog files')
        parser.add_argument("input_path", nargs='?', help='Path to directory or .ulg file to open', type=str, default=expanduser('~'))
        args = parser.parse_args()

        # Initialize the GUI backend
        self.backend = GUIBackend()

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

        # Add filter box
        self.filter_box = QtGui.QLineEdit()
        self.filter_box.setPlaceholderText('filter by topic name')
        self.filter_box.textChanged.connect(self.callback_filter_box)
        self.selected_fields_and_button_layout.addWidget(self.filter_box)

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
        self.topic_tree_widget.setSelectionMode(QtGui.QAbstractItemView.NoSelection)

        self.main_graph_frame = QtGui.QFrame(self)
        self.main_graph_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.main_graph_layout = QtGui.QHBoxLayout(self.main_graph_frame)

        self.secondary_graph_frame = QtGui.QFrame(self)
        self.secondary_graph_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.secondary_graph_layout = QtGui.QHBoxLayout(self.secondary_graph_frame)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.graph = [pg.PlotWidget() for _ in [0, 1]]
        self.graph[0].showGrid(True, True, 0.5)
        self.graph[1].showGrid(True, True, 0.5)
        self.graph[0].keyPressEvent = self.keyPressed_main_graph
        self.graph[1].keyPressEvent = self.keyPressed_secondary_graph

        # Populate the graph context menu
        toggle_marker_action = QtGui.QAction('show/hide markers (M)', self.graph[0])
        toggle_marker_action.triggered.connect(self.callback_toggle_marker)
        self.graph[0].scene().contextMenu.append(toggle_marker_action)
        toggle_bold_action = QtGui.QAction('toggle bold curves (B)', self.graph[0])
        toggle_bold_action.triggered.connect(self.callback_toggle_bold)
        self.graph[0].scene().contextMenu.append(toggle_bold_action)
        self.graph[1].scene().contextMenu.append(toggle_bold_action)
        toggle_title_action = QtGui.QAction('show/hide title (T)', self.graph[0])
        toggle_title_action.triggered.connect(self.callback_toggle_title)
        self.graph[0].scene().contextMenu.append(toggle_title_action)
        self.graph[1].scene().contextMenu.append(toggle_title_action)
        toggle_legend_action = QtGui.QAction('show/hide legend (L)', self.graph[0])
        toggle_legend_action.triggered.connect(self.callback_toggle_legend)
        self.graph[0].scene().contextMenu.append(toggle_legend_action)
        toggle_transition_lines_action = QtGui.QAction('show/hide transition lines (I)', self.graph[0])
        toggle_transition_lines_action.triggered.connect(self.callback_toggle_transition_lines)
        self.graph[0].scene().contextMenu.append(toggle_transition_lines_action)
        self.graph[1].scene().contextMenu.append(toggle_transition_lines_action)
        toggle_marker_line_action = QtGui.QAction('show/hide marker line (D)', self.graph[0])
        toggle_marker_line_action.triggered.connect(self.callback_toggle_marker_line)
        self.graph[0].scene().contextMenu.append(toggle_marker_line_action)
        toggle_changed_parameters_action = QtGui.QAction('show/hide changed parameters', self.graph[0])
        toggle_changed_parameters_action.triggered.connect(self.callback_toggle_changed_parameters)
        self.graph[0].scene().contextMenu.append(toggle_changed_parameters_action)
        ROI_action = QtGui.QAction('show/hide ROI (A)', self.graph[0])
        ROI_action.triggered.connect(self.callback_toggle_ROI)
        self.graph[0].scene().contextMenu.append(ROI_action)
        secondary_graph_action = QtGui.QAction('show/hide trajectory graph (Q)', self.graph[0])
        secondary_graph_action.triggered.connect(self.callback_toggle_2D_trajectory_graph)
        self.graph[0].scene().contextMenu.append(secondary_graph_action)
        self.graph[1].scene().contextMenu.append(secondary_graph_action)
        rescale_curves_action = QtGui.QAction('toggle rescaled curves (R)', self.graph[0])
        rescale_curves_action.triggered.connect(self.callback_toggle_rescale_curves)
        self.graph[0].scene().contextMenu.append(rescale_curves_action)
        self.graph[1].scene().contextMenu.append(rescale_curves_action)
        open_logfile_action = QtGui.QAction('open main logfile (O)', self.graph[0])
        open_logfile_action.setShortcut("Ctrl+O")
        open_logfile_action.triggered.connect(self.callback_open_main_logfile)
        self.graph[0].scene().contextMenu.append(open_logfile_action)
        open_secondary_logfile_action = QtGui.QAction('open secondary logfile (U)', self.graph[0])
        open_secondary_logfile_action.setShortcut("Ctrl+U")
        open_secondary_logfile_action.triggered.connect(self.callback_open_secondary_logfile)
        self.graph[0].scene().contextMenu.append(open_secondary_logfile_action)
        self.graph[1].scene().contextMenu.append(open_secondary_logfile_action)
        link_graph_range_action = QtGui.QAction('link visible range (K)', self.graph[0])
        link_graph_range_action.triggered.connect(self.callback_toggle_link_graph_range)
        self.graph[0].scene().contextMenu.append(link_graph_range_action)
        ulog_info_action = QtGui.QAction('print ulog info', self.graph[0])
        ulog_info_action.triggered.connect(self.callback_ulog_info)
        self.graph[0].scene().contextMenu.append(ulog_info_action)
        ulog_messages_action = QtGui.QAction('print ulog messages', self.graph[0])
        ulog_messages_action.triggered.connect(self.callback_ulog_messages)
        self.graph[0].scene().contextMenu.append(ulog_messages_action)

        self.main_graph_layout.addWidget(self.graph[0])
        self.secondary_graph_layout.addWidget(self.graph[1])

        self.tree_layout.addWidget(self.topic_tree_widget)

        self.split_vertical_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.split_vertical_0.addWidget(self.selected_fields_frame)
        self.split_vertical_0.addWidget(self.tree_frame)

        self.split_horizontal_0 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.split_horizontal_0.addWidget(self.secondary_graph_frame)
        self.split_horizontal_0.addWidget(self.main_graph_frame)
        self.split_horizontal_0.setSizes([0, 1])

        self.split_vertical_1 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.split_vertical_1.addWidget(self.split_horizontal_0)

        self.split_horizontal_1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.split_horizontal_1.addWidget(self.split_vertical_1)
        self.split_horizontal_1.addWidget(self.split_vertical_0)

        menu_bar = QtGui.QMenuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(open_logfile_action)
        file_menu.addAction(open_secondary_logfile_action)

        plot_menu = menu_bar.addMenu("&Plot")
        plot_menu.addAction(toggle_marker_action)
        plot_menu.addAction(toggle_bold_action)
        plot_menu.addAction(toggle_title_action)
        plot_menu.addAction(toggle_legend_action)
        plot_menu.addAction(toggle_transition_lines_action)
        plot_menu.addAction(toggle_marker_line_action)
        plot_menu.addAction(ROI_action)
        plot_menu.addAction(rescale_curves_action)
        plot_menu.addAction(secondary_graph_action)
        plot_menu.addAction(link_graph_range_action)

        self.main_layout.addWidget(self.split_horizontal_1)
        self.main_layout.addWidget(menu_bar)

        self.setCentralWidget(self.main_widget)

        # Create marker line
        self.marker_line = pg.InfiniteLine(angle=90, movable=True, pos=300, pen=pg.mkPen(color='b'), label='',
                                           labelOpts={'position': 0.1, 'color': (0, 0, 0), 'fill': (200, 200, 200, 100), 'movable': True})
        self.marker_line.hide()
        self.graph[0].addItem(self.marker_line, ignoreBounds=True)
        self.marker_line.sigDragged.connect(self.update_marker_line_status)

        # Create ROI
        self.ROI_region = pg.LinearRegionItem()
        self.ROI_region.hide()
        self.graph[0].addItem(self.ROI_region, ignoreBounds=True)

        # Create arrow for the vehicle position in the trajectory analysis
        self.arrow = pg.ArrowItem(Angle=0, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush='g')
        self.arrow.setPos(0, 0)
        self.arrow.hide()
        self.graph[1].addItem(self.arrow)

        # Initiate the legend
        self.legend = self.graph[0].addLegend()

        pg.setConfigOptions(antialias=True)

        # Load logfile from argument or file dialog
        self.callback_open_logfile(args.input_path)

    def close_application(self):
        print("whooaaaa so custom!!!")
        sys.exit()

    def callback_filter_box(self, filter_str):
        # Hide all topics
        for i in range(self.topic_tree_widget.topLevelItemCount()):
            self.topic_tree_widget.topLevelItem(i).setHidden(True)
        # Show all topics that match the filter
        top_level_items_to_show = self.topic_tree_widget.findItems(filter_str, QtCore.Qt.MatchStartsWith)
        for elem in top_level_items_to_show:
            elem.setHidden(False)

    def update_marker_line_status(self):
        # TODO: check -1 index here
        marker_line_label = ''
        marker_line_label = marker_line_label + 't = {:0.2f}'.format(self.marker_line.value())
        for elem in self.backend.curve_list:
            idx = np.argmax(self.backend.graph_data[0].df_dict[elem.selected_topic].index > self.marker_line.value()) - 1
            value = self.backend.graph_data[0].df_dict[elem.selected_topic][elem.selected_field].values[idx]
            value_str = str(value)
            if elem.selected_field[-5:] == 'flags':
                value_str = value_str + " ({0:b})".format(int(value))

            marker_line_label = marker_line_label + '\n' + elem.selected_topic_and_field + ': ' + value_str

        self.marker_line.label.textItem.setPlainText(marker_line_label)

        if self.backend.graph_data[0].show_marker_line and self.backend.secondary_graph_mode == '2D':
            # Put arrow at estimated position if it exists, otherwise at the GPS position
            if 'vehicle_local_position_0' in self.backend.graph_data[0].df_dict:
                topic_str = 'vehicle_local_position_0'
                x = 'x'
                y = 'y'
            elif 'vehicle_gps_position_0' in self.backend.graph_data[0].df_dict:
                topic_str = 'vehicle_gps_position_0'
                x = 'lat_m*'
                y = 'lon_m*'
            else:
                return

            idx_vehicle_local_position = np.argmax(self.backend.graph_data[0].df_dict[topic_str].index > self.marker_line.value()) - 1
            pos_x = self.backend.graph_data[0].df_dict[topic_str][x].values[idx_vehicle_local_position]
            pos_y = self.backend.graph_data[0].df_dict[topic_str][y].values[idx_vehicle_local_position]
            # idx_vehicle_attitude = np.argmax(self.backend.graph_data[0].df_dict['vehicle_attitude_0'].index > self.marker_line.value()) - 1
            # yaw = self.backend.graph_data[0].df_dict['vehicle_attitude_0']['yaw321* [deg]'].values[idx_vehicle_attitude]
            self.arrow.setPos(pos_y, pos_x)

    def callback_open_logfile(self, input_path=expanduser('~'), graph_id=0):
        if Path(input_path).is_file() and Path(input_path).suffix == ".ulg":
            self.backend.graph_data[graph_id].path_to_logfile = input_path
            self.fronted_cleanup()
            self.backend.load_ulog_to_graph_data(self.backend.graph_data[graph_id].path_to_logfile, graph_id)
            if graph_id == 0:
                self.load_logfile_to_tree()
            self.set_marker_line_in_middle(graph_id)
            self.update_frontend()
            self.graph[0].autoRange()
            self.graph[1].autoRange()

        else:
            filename = QtGui.QFileDialog.getOpenFileName(self, 'Open Log File', input_path, 'Log Files (*.ulg)')
            if isinstance(filename, tuple):
                filename = filename[0]
            if filename:
                try:
                    self.callback_open_logfile(filename, graph_id)
                except Exception as ex:
                    print(ex)

    def load_logfile_to_tree(self):
        self.topic_tree_widget.clear()
        # for topic_str, fields_df in self.graph_data[0].df_dict.iteritems(): python2
        for topic_str, fields_df in sorted(self.backend.graph_data[0].df_dict.items()):
            current_topic = QtGui.QTreeWidgetItem(self.topic_tree_widget, [topic_str])
            for field in sorted(list(fields_df)):
                current_field = QtGui.QTreeWidgetItem(current_topic, [field])

    def callback_open_main_logfile(self):
        self.callback_open_logfile(os.path.dirname(self.backend.graph_data[0].path_to_logfile))

    def callback_open_secondary_logfile(self):
        self.callback_open_logfile(os.path.dirname(self.backend.graph_data[0].path_to_logfile), 1)
        self.backend.secondary_graph_mode = 'secondary_logfile'
        self.backend.show_title = True
        if not self.split_screen_active():
            self.split_horizontal_0.setSizes([1, 1])

        self.update_frontend()
        self.graph[1].autoRange()

    def callback_toggle_2D_trajectory_graph(self):
        self.unlink_graph_range()
        if self.split_screen_active():
            if self.backend.secondary_graph_mode == '2D':
                self.split_horizontal_0.setSizes([0, 1])
            else:
                self.backend.secondary_graph_mode = '2D'
        else:
            self.split_horizontal_0.setSizes([1, 1])
            self.backend.secondary_graph_mode = '2D'

        self.update_frontend()
        self.graph[1].autoRange()

    def split_screen_active(self):
        rect = self.split_horizontal_0.sizes()
        return rect[0] > 0

    def toggle_split_screen(self):
        if not self.split_screen_active():
            self.split_horizontal_0.setSizes([1, 1])
            if not self.backend.graph_data[0].show_marker_line:
                self.callback_toggle_marker_line()
        else:
            self.split_horizontal_0.setSizes([0, 1])

    def callback_toggle_rescale_curves(self):
        self.backend.rescale_curves = not self.backend.rescale_curves
        self.backend.auto_range = True
        self.update_frontend()

    def callback_toggle_marker(self):
        if self.backend.symbol == None:
            self.backend.symbol = 'o'
        else:
            self.backend.symbol = None

        self.update_frontend()

    def callback_toggle_bold(self):
        if self.backend.linewidth == 1:
            self.backend.linewidth = 3
        else:
            self.backend.linewidth = 1

        self.update_frontend()

    def callback_toggle_title(self):
        self.backend.show_title = not self.backend.show_title
        self.update_frontend()

    def callback_toggle_legend(self):
        self.backend.show_legend = not self.backend.show_legend
        self.update_frontend()

    def callback_toggle_transition_lines(self):
        self.backend.show_transition_lines = not self.backend.show_transition_lines
        self.update_frontend()

    def callback_toggle_marker_line(self):
        self.backend.graph_data[0].show_marker_line = not self.backend.graph_data[0].show_marker_line
        self.set_marker_line_in_middle()
        self.update_frontend()

    def plot_parameter_changes(self, graph_id=0):
        last_timestamp = 0
        last_label = ''
        for elem in self.backend.graph_data[graph_id].changed_parameters:
            timestamp = elem[0] / 1e6
            label = elem[1] + ": " + str(elem[2])
            if timestamp == last_timestamp:
                label = label + "\n" + last_label
                self.backend.graph_data[graph_id].parameter_lines_obj[-1].label.textItem.setPlainText(label)
            else:
                parameter_changed_line = pg.InfiniteLine(angle=90, movable=False, pos=timestamp, pen=pg.mkPen(color='k'), label=label,
                                                         labelOpts={'position': 0.8, 'color': (0, 0, 0), 'fill': (200, 200, 200, 100), 'movable': True})
                parameter_changed_line.show()
                self.graph[graph_id].addItem(parameter_changed_line, ignoreBounds=True)
                self.backend.graph_data[graph_id].parameter_lines_obj.append(parameter_changed_line)

            last_timestamp = timestamp
            last_label = label

    def callback_toggle_changed_parameters(self):
        self.backend.show_changed_parameters = not self.backend.show_changed_parameters
        if self.backend.show_changed_parameters:
            self.plot_parameter_changes()
            if self.split_screen_active() and self.backend.secondary_graph_mode == 'secondary_logfile':
                self.plot_parameter_changes(1)
        else:
            for elem in self.backend.graph_data[0].parameter_lines_obj:
                self.graph[0].removeItem(elem)
            for elem in self.backend.graph_data[1].parameter_lines_obj:
                self.graph[1].removeItem(elem)

    def set_marker_line_in_middle(self, graph_id=0):
        # Calculate midpoint along x axis on current graph
        rect = self.graph[0].viewRange()
        midpoint = (rect[0][1] - rect[0][0]) / 2 + rect[0][0]
        # Set the marker lines location
        self.marker_line.setValue(midpoint)

    def callback_toggle_ROI(self):
        self.backend.show_ROI = not self.backend.show_ROI
        # Calculate left and right quartile along x axis on current graph
        rect = self.graph[0].viewRange()
        left_quartile = (rect[0][1] - rect[0][0]) * 0.25 + rect[0][0]
        right_quartile = (rect[0][1] - rect[0][0]) * 0.75 + rect[0][0]
        # Set the ROI location
        self.ROI_region.setRegion([left_quartile, right_quartile])
        self.update_frontend()

    def callback_toggle_link_graph_range(self):
        if self.backend.secondary_graph_mode == 'secondary_logfile':
            self.backend.link_xy_range = not self.backend.link_xy_range

            if self.backend.link_xy_range:
                self.graph[1].getViewBox().setXLink(self.graph[0])
                self.graph[1].getViewBox().setYLink(self.graph[0])
            else:
                self.unlink_graph_range()

    def unlink_graph_range(self):
        self.graph[1].getViewBox().setXLink(None)
        self.graph[1].getViewBox().setYLink(None)

    def callback_ulog_info(self):
        print("########### ulog_info: " + self.backend.graph_data[0].path_to_logfile + " ###########")
        subprocess.run(["ulog_info", self.backend.graph_data[0].path_to_logfile])

    def callback_ulog_messages(self):
        print("########### ulog_messages: " + self.backend.graph_data[0].path_to_logfile + " ###########")
        subprocess.run(["ulog_messages", self.backend.graph_data[0].path_to_logfile])

    def fronted_cleanup(self):
        # Remove the transition lines
        for idx in range(2):
            for elem in self.backend.graph_data[idx].ft_lines_obj:
                self.graph[idx].removeItem(elem)
            for elem in self.backend.graph_data[idx].bt_lines_obj:
                self.graph[idx].removeItem(elem)

    def keyPressed_main_graph(self, event):
        # Ctrl + O: Open logfile
        if event.key() == QtCore.Qt.Key_O:
            self.callback_open_logfile(os.path.dirname(self.backend.graph_data[0].path_to_logfile))
        # Ctrl + U: Open secondary logfile
        if event.key() == QtCore.Qt.Key_U:
            self.callback_open_secondary_logfile()

        # Ctrl + V: Autorange
        if event.key() == QtCore.Qt.Key_V:
            self.graph[0].autoRange()

        # Ctrl + L: Show legend
        elif event.key() == QtCore.Qt.Key_L:
            self.callback_toggle_legend()

        # Ctrl + Q: Toggle trajectory analysis
        elif event.key() == QtCore.Qt.Key_Q:
            self.callback_toggle_2D_trajectory_graph()

        # Ctrl + C: Clear plot
        elif event.key() == QtCore.Qt.Key_C:
            self.callback_clear_plot()

        # Ctrl + M: Toggle plot marker
        elif event.key() == QtCore.Qt.Key_M:
            self.callback_toggle_marker()

        # Ctrl + B: Make curves bold
        elif event.key() == QtCore.Qt.Key_B:
            self.callback_toggle_bold()

        # Ctrl + T: Toggle title
        elif event.key() == QtCore.Qt.Key_T:
            self.callback_toggle_title()

        # Ctrl + I: Toggle transition lines
        elif event.key() == QtCore.Qt.Key_I:
            self.callback_toggle_transition_lines()

        # Ctrl + U: Force update frontend
        elif event.key() == QtCore.Qt.Key_U:
            self.update_frontend()

        # Ctrl + D: Toggle marker line
        elif event.key() == QtCore.Qt.Key_D:
            self.callback_toggle_marker_line()

        # Ctrl + A: Toggle ROI
        elif event.key() == QtCore.Qt.Key_A:
            self.callback_toggle_ROI()

        # Ctrl + R: Rescale curves
        elif event.key() == QtCore.Qt.Key_R:
            self.callback_toggle_rescale_curves()

        # Ctrl + K: Link axes
        elif event.key() == QtCore.Qt.Key_K:
            self.callback_toggle_link_graph_range()

            # Ctrl + 0: Show quaternion covariances
        elif event.key() == QtCore.Qt.Key_0:
            self.backend.clear_curve_list()
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[0]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[1]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[2]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[3]')
            self.update_frontend()
            self.graph[0].autoRange()

        # Ctrl + 1: Show velocity covariances
        elif event.key() == QtCore.Qt.Key_1:
            self.backend.clear_curve_list()
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[4]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[5]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[6]')
            self.update_frontend()
            self.graph[0].autoRange()

        # Ctrl + 2: Show position covariances
        elif event.key() == QtCore.Qt.Key_2:
            self.backend.clear_curve_list()
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[7]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[8]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[9]')
            self.update_frontend()
            self.graph[0].autoRange()

        # Ctrl + 3: Show delta angle bias covariances
        elif event.key() == QtCore.Qt.Key_3:
            self.backend.clear_curve_list()
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[10]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[11]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[12]')
            self.update_frontend()
            self.graph[0].autoRange()

        # Ctrl + 4: Show delta velocity bias covariances
        elif event.key() == QtCore.Qt.Key_4:
            self.backend.clear_curve_list()
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[13]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[14]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[15]')
            self.update_frontend()
            self.graph[0].autoRange()

        # Ctrl + 5: Show earth magnetic field state covariances
        elif event.key() == QtCore.Qt.Key_5:
            self.backend.clear_curve_list()
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[16]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[17]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[18]')
            self.update_frontend()
            self.graph[0].autoRange()

        # Ctrl + 6: Show body magnetic field state covariances
        elif event.key() == QtCore.Qt.Key_6:
            self.backend.clear_curve_list()
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[19]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[20]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[21]')
            self.update_frontend()
            self.graph[0].autoRange()

        # Ctrl + 7: Show wind state covariances
        elif event.key() == QtCore.Qt.Key_7:
            self.backend.clear_curve_list()
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[22]')
            self.backend.add_selected_topic_and_field('estimator_status_0', 'covariances[23]')
            self.update_frontend()
            self.graph[0].autoRange()

        # Ctrl + Left_arrow: Move marker line to the left
        elif event.key() == QtCore.Qt.Key_Left:
            if self.backend.graph_data[0].show_marker_line:
                self.marker_line.setValue(self.marker_line.value() - 1)
                self.update_marker_line_status()

        # Ctrl + Right_arrow: Move marker line to the right
        elif event.key() == QtCore.Qt.Key_Right:
            if self.backend.graph_data[0].show_marker_line:
                self.marker_line.setValue(self.marker_line.value() + 1)
                self.update_marker_line_status()

        # Ctrl + P: Print value of selected fields at line
        elif event.key() == QtCore.Qt.Key_P:
            if self.backend.graph_data[0].show_marker_line:
                print('t = ' + str(self.marker_line.value()))
                for elem in self.backend.curve_list:
                    idx = np.argmax(self.backend.graph_data[0].df_dict[elem.selected_topic].index > self.marker_line.value()) - 1
                    print(elem.selected_topic_and_field + ': ' + str(self.backend.graph_data[0].df_dict[elem.selected_topic][elem.selected_field].values[idx]))

            if self.backend.show_ROI:
                minX, maxX = self.ROI_region.getRegion()
                for elem in self.backend.curve_list:
                    idx_min = np.argmax(self.backend.graph_data[0].df_dict[elem.selected_topic].index > minX)
                    idx_max = np.argmax(self.backend.graph_data[0].df_dict[elem.selected_topic].index > maxX) - 1
                    mean = np.mean(self.backend.graph_data[0].df_dict[elem.selected_topic][elem.selected_field].values[idx_min:idx_max])
                    delta_y = self.backend.graph_data[0].df_dict[elem.selected_topic][elem.selected_field].values[idx_max] - self.backend.graph_data[0].df_dict[elem.selected_topic][elem.selected_field].values[idx_min]
                    delta_t = self.backend.graph_data[0].df_dict[elem.selected_topic][elem.selected_field].index[idx_max] - self.backend.graph_data[0].df_dict[elem.selected_topic][elem.selected_field].index[idx_min]
                    diff = delta_y / delta_t
                    print(elem.selected_topic_and_field + ' mean: ' + str(mean) + ' diff: ' + str(diff))

    def keyPressed_secondary_graph(self, event):
        # Ctrl + V: Autorange
        if event.key() == QtCore.Qt.Key_V:
            self.graph[1].autoRange()

    def callback_topic_tree_doubleClicked(self):
        print("dont double click!")

    def callback_selected_fields_list_clicked(self, item):
        # Remove the selected field from the tree
        selected_topic_and_field = item.text()
        selected_topic, selected_field = CurveClass.get_name_seperate(selected_topic_and_field)
        self.backend.remove_selected_topic_and_field(selected_topic, selected_field)
        self.update_frontend()

    def callback_clear_plot(self):
        self.backend.clear_curve_list()
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

    def add_curve(self, graph_id, elem, color_brush):
        time = self.backend.graph_data[graph_id].df_dict[elem.selected_topic].index
        y_value = self.backend.graph_data[graph_id].df_dict[elem.selected_topic][elem.selected_field].values
        if self.backend.rescale_curves:
            y_value = (y_value - np.min(y_value)) / (np.max(y_value) - np.min(y_value))

        pen = pg.mkPen(width=self.backend.linewidth, color=color_brush)
        curve = self.graph[graph_id].plot(time, y_value, pen=pen, name=elem.selected_topic_and_field, symbol=self.backend.symbol, symbolBrush=color_brush, symbolPen=color_brush)

        # Add a marker if any of the samples are nan
        if np.isnan(y_value).any():
            time_of_nans = time[np.isnan(y_value)]
            zero_vector = 0 * time_of_nans
            curve = self.graph[graph_id].plot(time_of_nans, zero_vector, pen=pen, name=elem.selected_topic_and_field, symbol='t', symbolBrush=color_brush, symbolPen=color_brush, symbolSize=20)

    def update_frontend(self):
        self.graph[0].clearPlots()
        self.graph[1].clearPlots()
        self.graph[1].setAspectLocked(lock=False, ratio=1)
        self.selected_fields_list_widget.clear()
        self.selected_fields_list_widget.clearSelection()
        self.topic_tree_widget.clearSelection()
        self.legend.close()
        self.marker_line.hide()
        self.arrow.hide()
        self.ROI_region.hide()
        self.graph[0].setTitle(None)
        self.graph[1].setTitle(None)
        self.fronted_cleanup()

        # Set all topic colors to white in the tree
        for topic_index in range(self.topic_tree_widget.topLevelItemCount()):
            self.topic_tree_widget.topLevelItem(topic_index).setBackground(0, QtGui.QBrush(QtCore.Qt.white))

        if self.backend.show_legend:
            self.legend = self.graph[0].addLegend()
        for elem in self.backend.curve_list:
            color_brush = QtGui.QColor(elem.color[0], elem.color[1], elem.color[2])
            # Add the newly selected field to the list of all currently selected fields
            new_list_item = QtGui.QListWidgetItem(elem.selected_topic_and_field)
            new_list_item.setBackground(color_brush)
            self.selected_fields_list_widget.addItem(new_list_item)

            # Show the current curve class element as selected in the tree view and the corresponding topic as grey
            top_level_item = self.topic_tree_widget.findItems(elem.selected_topic, QtCore.Qt.MatchExactly)[0]
            top_level_item.setBackground(0, QtGui.QBrush(QtCore.Qt.gray))
            for field_index in range(top_level_item.childCount()):
                field_name = top_level_item.child(field_index).text(0)
                if field_name == elem.selected_field:
                    top_level_item.child(field_index).setSelected(True)
                    break

            self.add_curve(0, elem, color_brush)

            if self.backend.secondary_graph_mode == 'secondary_logfile':
                self.add_curve(1, elem, color_brush)

        # Display lines at start and stop of forward transition
        if self.backend.show_transition_lines:
            max_range = range(1)
            if self.backend.secondary_graph_mode == 'secondary_logfile':
                max_range = range(2)
            for idx in max_range:
                for elem in self.backend.graph_data[idx].forward_transition_lines:
                    vLine = pg.InfiniteLine(angle=90, movable=False, pos=elem, pen=pg.mkPen(color='g'))
                    vLine.show()
                    self.backend.graph_data[idx].ft_lines_obj.append(vLine)
                    self.graph[idx].addItem(vLine, ignoreBounds=True)

                for elem in self.backend.graph_data[idx].back_transition_lines:
                    vLine = pg.InfiniteLine(angle=90, movable=False, pos=elem, pen=pg.mkPen(color='r'))
                    vLine.show()
                    self.backend.graph_data[idx].bt_lines_obj.append(vLine)
                    self.graph[idx].addItem(vLine, ignoreBounds=True)

        # Display marker line
        if self.backend.graph_data[0].show_marker_line:
            self.marker_line.show()

            # Display ROI
        if self.backend.show_ROI:
            self.ROI_region.show()

        # Autorange
        if len(self.backend.curve_list) > 0 and self.backend.auto_range:
            self.graph[0].autoRange()
            self.graph[1].autoRange()
            self.backend.auto_range = False

        elif len(self.backend.curve_list) == 0:
            self.backend.auto_range = True

        # Update the window title
        # self.setWindowTitle('ulog_explorer')

        # Update label of marker line
        self.update_marker_line_status()

        # Display title
        if self.backend.show_title:
            self.graph[0].setTitle(self.backend.graph_data[0].path_to_logfile)
            if self.backend.secondary_graph_mode == 'secondary_logfile':
                self.graph[1].setTitle(self.backend.graph_data[1].path_to_logfile)
            else:
                self.graph[1].setTitle(self.backend.graph_data[0].path_to_logfile)

        # Update 2D trajectory graph if enabled
        if self.backend.secondary_graph_mode == '2D':
            self.graph[1].setAspectLocked(lock=True, ratio=1)
            if self.backend.graph_data[0].show_marker_line:
                self.arrow.show()
            # Plot estimated position
            try:
                north_estimated = self.backend.graph_data[0].df_dict['vehicle_local_position_0']['x'].values
                east_estimated = self.backend.graph_data[0].df_dict['vehicle_local_position_0']['y'].values
                pen = pg.mkPen(width=self.backend.linewidth, color='b')
                curve = self.graph[1].plot(east_estimated, north_estimated, name='trajectory', pen=pen)
            except:
                pass

            # Plot measured GPS position
            try:
                north_measured = self.backend.graph_data[0].df_dict['vehicle_gps_position_0']['lat_m*'].values
                east_gps_measured = self.backend.graph_data[0].df_dict['vehicle_gps_position_0']['lon_m*'].values
                pen = pg.mkPen(width=self.backend.linewidth, color='r')
                curve = self.graph[1].plot(east_gps_measured, north_measured, name='trajectory', pen=pen)
            except:
                pass

            # Plot mission setpoints
            try:
                north_setpoint = self.backend.graph_data[0].df_dict['position_setpoint_triplet_0']['current.lat_m*'].values
                east_setpoint = self.backend.graph_data[0].df_dict['position_setpoint_triplet_0']['current.lon_m*'].values
                pen = pg.mkPen(width=self.backend.linewidth, color='g')
                curve = self.graph[1].plot(east_setpoint, north_setpoint, name='trajectory', pen=pen, symbol='o')
            except:
                pass


def main():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    GUI.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
