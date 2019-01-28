import sys
from scipy import signal

# from PyQt4 import QtGui, QtCore
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import argparse
from pathlib import Path
from os.path import expanduser
from GUIBackend import *


class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()

        # Parse arguments
        parser = argparse.ArgumentParser(description='Used to analyse uLog files')
        parser.add_argument("-f")
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

        self.graph_frame = QtGui.QFrame(self)
        self.graph_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.graph_layout = QtGui.QVBoxLayout(self.graph_frame)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.graph_widget = pg.GraphicsLayoutWidget()

        self.secondary_graph = self.graph_widget.addPlot(row=0, col=0)
        self.secondary_graph.setAspectLocked(lock=True, ratio=1)
        self.secondary_graph.showGrid(True, True, 0.5)

        self.main_graph = self.graph_widget.addPlot(row=0, col=1)
        self.main_graph.showGrid(True, True, 0.5)
        self.main_graph.keyPressEvent = self.keyPressed

        # Populate the graph context menu
        toggle_marker_action = QtGui.QAction('show/hide markers (M)', self.main_graph)
        toggle_marker_action.triggered.connect(self.callback_toggle_marker)
        self.main_graph.scene().contextMenu.append(toggle_marker_action)
        toggle_bold_action = QtGui.QAction('toggle bold curves (B)', self.main_graph)
        toggle_bold_action.triggered.connect(self.callback_toggle_bold)
        self.main_graph.scene().contextMenu.append(toggle_bold_action)
        toggle_title_action = QtGui.QAction('show/hide title (T)', self.main_graph)
        toggle_title_action.triggered.connect(self.callback_toggle_title)
        self.main_graph.scene().contextMenu.append(toggle_title_action)
        toggle_legend_action = QtGui.QAction('show/hide legend (L)', self.main_graph)
        toggle_legend_action.triggered.connect(self.callback_toggle_legend)
        self.main_graph.scene().contextMenu.append(toggle_legend_action)
        toggle_transition_lines_action = QtGui.QAction('show/hide transition lines (I)', self.main_graph)
        toggle_transition_lines_action.triggered.connect(self.callback_toggle_transition_lines)
        self.main_graph.scene().contextMenu.append(toggle_transition_lines_action)
        toggle_marker_line_action = QtGui.QAction('show/hide marker line (D)', self.main_graph)
        toggle_marker_line_action.triggered.connect(self.callback_toggle_marker_line)
        self.main_graph.scene().contextMenu.append(toggle_marker_line_action)
        ROI_action = QtGui.QAction('show/hide ROI (A)', self.main_graph)
        ROI_action.triggered.connect(self.callback_toggle_ROI)
        self.main_graph.scene().contextMenu.append(ROI_action)
        secondary_graph_action = QtGui.QAction('show/hide trajectory graph (Q)', self.main_graph)
        secondary_graph_action.triggered.connect(self.callback_toggle_secondary_graph)
        self.main_graph.scene().contextMenu.append(secondary_graph_action)
        rescale_curves_action = QtGui.QAction('toggle rescaled curves (R)', self.main_graph)
        rescale_curves_action.triggered.connect(self.callback_toggle_rescale_curves)
        self.main_graph.scene().contextMenu.append(rescale_curves_action)

        self.graph_layout.addWidget(self.graph_widget)

        # Load logfile from argument or file dialog
        if args.f and Path(args.f).is_file() and Path(args.f).suffix == ".ulg":
            self.backend.path_to_logfile = args.f
            self.load_logfile_to_tree(self.backend.path_to_logfile)
        elif args.f and Path(args.f).is_dir():
            self.open_logfile(args.f)
        else:
            self.open_logfile()

        self.tree_layout.addWidget(self.topic_tree_widget)

        self.split_vertical_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.split_vertical_0.addWidget(self.selected_fields_frame)
        self.split_vertical_0.addWidget(self.tree_frame)

        self.split_vertical_1 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.split_vertical_1.addWidget(self.graph_frame)

        self.split_horizontal_0 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.split_horizontal_0.addWidget(self.split_vertical_1)
        self.split_horizontal_0.addWidget(self.split_vertical_0)

        self.main_layout.addWidget(self.split_horizontal_0)

        self.setCentralWidget(self.main_widget)

        # List of vertical lines indicating start and stop of VTOL transitions
        self.ft_lines_obj = []
        self.bt_lines_obj = []

        # Create marker line
        self.marker_line = pg.InfiniteLine(angle=90, movable=True, pos=300, pen=pg.mkPen(color='b'), label='',
                                           labelOpts={'position': 0.1, 'color': (0, 0, 0), 'fill': (200, 200, 200, 100), 'movable': True})
        self.marker_line.hide()
        self.main_graph.addItem(self.marker_line, ignoreBounds=True)
        self.marker_line.sigDragged.connect(self.update_marker_line_status)

        # Create ROI
        self.ROI_region = pg.LinearRegionItem()
        self.ROI_region.hide()
        self.main_graph.addItem(self.ROI_region, ignoreBounds=True)

        # Create arrow for the vehicle position in the trajectory analysis
        self.arrow = pg.ArrowItem(Angle=0, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush='g')
        self.arrow.setPos(0, 0)
        self.arrow.hide()
        self.secondary_graph.addItem(self.arrow)

        # Initiate the legend
        self.legend = self.main_graph.addLegend()

        pg.setConfigOptions(antialias=True)

        self.update_frontend()

    def update_marker_line_status(self):
        # TODO: check -1 index here
        marker_line_label = ''
        marker_line_label = marker_line_label + 't = {:0.2f}'.format(self.marker_line.value())
        for elem in self.backend.curve_list:
            idx = np.argmax(self.backend.df_dict[elem.selected_topic].index > self.marker_line.value()) - 1
            value = self.backend.df_dict[elem.selected_topic][elem.selected_field].values[idx]
            value_str = str(value)
            if elem.selected_field[-5:] == 'flags':
                value_str = value_str + " ({0:b})".format(int(value))

            marker_line_label = marker_line_label + '\n' + elem.selected_topic_and_field + ': ' + value_str

        self.marker_line.label.textItem.setPlainText(marker_line_label)

        if self.backend.show_marker_line:
            idx_vehicle_local_position = np.argmax(self.backend.df_dict['vehicle_local_position_0'].index > self.marker_line.value()) - 1
            pos_x = self.backend.df_dict['vehicle_local_position_0']['x'].values[idx_vehicle_local_position]
            pos_y = self.backend.df_dict['vehicle_local_position_0']['y'].values[idx_vehicle_local_position]
            idx_vehicle_attitude = np.argmax(self.backend.df_dict['vehicle_attitude_0'].index > self.marker_line.value()) - 1
            yaw = self.backend.df_dict['vehicle_attitude_0']['yaw321* [deg]'].values[idx_vehicle_attitude]
            self.arrow.setPos(pos_y, pos_x)

    def callback_open_logfile(self):
        self.fronted_cleanup()
        self.open_logfile(self.backend.path_to_logfile)
        self.set_marker_line_in_middle()
        self.update_frontend()
        self.main_graph.autoRange()

    def callback_toggle_secondary_graph(self):
        self.backend.show_secondary_graph = not self.backend.show_secondary_graph
        # Initialize the marker line if it was not already displayed
        if self.backend.show_secondary_graph and not self.backend.show_marker_line:
            self.callback_toggle_marker_line()

        self.update_frontend()

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
        self.backend.show_marker_line = not self.backend.show_marker_line
        self.set_marker_line_in_middle()
        self.update_frontend()

    def set_marker_line_in_middle(self):
        # Calculate midpoint along x axis on current graph
        rect = self.main_graph.viewRange()
        midpoint = (rect[0][1] - rect[0][0]) / 2 + rect[0][0]
        # Set the marker lines location
        self.marker_line.setValue(midpoint)

    def callback_toggle_ROI(self):
        self.backend.show_ROI = not self.backend.show_ROI
        # Calculate left and right quartile along x axis on current graph
        rect = self.main_graph.viewRange()
        left_quartile = (rect[0][1] - rect[0][0]) * 0.25 + rect[0][0]
        right_quartile = (rect[0][1] - rect[0][0]) * 0.75 + rect[0][0]
        # Set the ROI location
        self.ROI_region.setRegion([left_quartile, right_quartile])
        self.update_frontend()

    def fronted_cleanup(self):
        # Remove the transition lines
        for elem in self.ft_lines_obj:
            self.main_graph.removeItem(elem)
        for elem in self.bt_lines_obj:
            self.main_graph.removeItem(elem)

    def keyPressed(self, event):
        # Ctrl + O: Open logfile
        if event.key() == QtCore.Qt.Key_O:
            self.callback_open_logfile()
        # Ctrl + V: Autorange
        if event.key() == QtCore.Qt.Key_V:
            self.main_graph.autoRange()

        # Ctrl + L: Show legend
        elif event.key() == QtCore.Qt.Key_L:
            self.callback_toggle_legend()

        # Ctrl + Q: Toggle trajectory analysis
        elif event.key() == QtCore.Qt.Key_Q:
            self.callback_toggle_secondary_graph()

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

        # Ctrl + Left_arrow: Move marker line to the left
        elif event.key() == QtCore.Qt.Key_Left:
            if self.backend.show_marker_line:
                self.marker_line.setValue(self.marker_line.value() - 1)
                self.update_marker_line_status()

        # Ctrl + Right_arrow: Move marker line to the right
        elif event.key() == QtCore.Qt.Key_Right:
            if self.backend.show_marker_line:
                self.marker_line.setValue(self.marker_line.value() + 1)
                self.update_marker_line_status()

        # Ctrl + P: Print value of selected fields at line
        elif event.key() == QtCore.Qt.Key_P:
            if self.backend.show_marker_line:
                print('t = ' + str(self.marker_line.value()))
                for elem in self.backend.curve_list:
                    idx = np.argmax(self.backend.df_dict[elem.selected_topic].index > self.marker_line.value()) - 1
                    print(elem.selected_topic_and_field + ': ' + str(self.backend.df_dict[elem.selected_topic][elem.selected_field].values[idx]))

            if self.backend.show_ROI:
                minX, maxX = self.ROI_region.getRegion()
                for elem in self.backend.curve_list:
                    idx_min = np.argmax(self.backend.df_dict[elem.selected_topic].index > minX)
                    idx_max = np.argmax(self.backend.df_dict[elem.selected_topic].index > maxX) - 1
                    mean = np.mean(self.backend.df_dict[elem.selected_topic][elem.selected_field].values[idx_min:idx_max])
                    delta_y = self.backend.df_dict[elem.selected_topic][elem.selected_field].values[idx_max] - self.backend.df_dict[elem.selected_topic][elem.selected_field].values[idx_min]
                    delta_t = self.backend.df_dict[elem.selected_topic][elem.selected_field].index[idx_max] - self.backend.df_dict[elem.selected_topic][elem.selected_field].index[idx_min]
                    diff = delta_y / delta_t
                    print(elem.selected_topic_and_field + ' mean: ' + str(mean) + ' diff: ' + str(diff))

    def open_logfile(self, path_to_dir=expanduser('~')):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open Log File', path_to_dir, 'Log Files (*.ulg)')
        if isinstance(filename, tuple):
            filename = filename[0]
        if filename:
            try:
                self.backend.path_to_logfile = filename
                self.load_logfile_to_tree(self.backend.path_to_logfile)
            except Exception as ex:
                print(ex)

    def load_logfile_to_tree(self, logfile_str):
        self.backend.ulog_to_df(logfile_str)
        self.backend.add_all_fields_to_df()
        self.backend.get_transition_timestamps()

        self.topic_tree_widget.clear()
        # for topic_str, fields_df in self.df_dict.iteritems(): python2
        for topic_str, fields_df in sorted(self.backend.df_dict.items()):
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

    def update_frontend(self):
        self.main_graph.clearPlots()
        self.selected_fields_list_widget.clear()
        self.selected_fields_list_widget.clearSelection()
        self.topic_tree_widget.clearSelection()
        self.legend.close()

        # Set all topic colors to white in the tree
        for topic_index in range(self.topic_tree_widget.topLevelItemCount()):
            self.topic_tree_widget.topLevelItem(topic_index).setBackground(0, QtGui.QBrush(QtCore.Qt.white))

        if self.backend.show_legend:
            self.legend = self.main_graph.addLegend()
        for elem in self.backend.curve_list:
            color_brush = QtGui.QColor(elem.color[0], elem.color[1], elem.color[2])
            pen = pg.mkPen(width=self.backend.linewidth, color=color_brush)
            time = self.backend.df_dict[elem.selected_topic].index
            y_value = self.backend.df_dict[elem.selected_topic][elem.selected_field].values
            if self.backend.rescale_curves:
                y_value = (y_value - np.min(y_value)) / (np.max(y_value) - np.min(y_value))

            curve = self.main_graph.plot(time, y_value, pen=pen, name=elem.selected_topic_and_field, symbol=self.backend.symbol, symbolBrush=color_brush, symbolPen=color_brush)

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

        # Display lines at start and stop of forward transition
        if self.backend.show_transition_lines:
            for elem in self.backend.forward_transition_lines:
                vLine = pg.InfiniteLine(angle=90, movable=False, pos=elem, pen=pg.mkPen(color='g'))
                vLine.show()
                self.ft_lines_obj.append(vLine)
                self.main_graph.addItem(vLine, ignoreBounds=True)

            for elem in self.backend.back_transition_lines:
                vLine = pg.InfiniteLine(angle=90, movable=False, pos=elem, pen=pg.mkPen(color='r'))
                vLine.show()
                self.bt_lines_obj.append(vLine)
                self.main_graph.addItem(vLine, ignoreBounds=True)
        else:
            self.fronted_cleanup()

        # Display marker line and arrow
        if self.backend.show_marker_line:
            self.marker_line.show()
            self.arrow.show()
        else:
            self.marker_line.hide()
            self.arrow.hide()

        # Display ROI
        if self.backend.show_ROI:
            self.ROI_region.show()
        else:
            self.ROI_region.hide()

        # Autorange
        if len(self.backend.curve_list) > 0 and self.backend.auto_range:
            self.main_graph.autoRange()
            self.backend.auto_range = False

        elif len(self.backend.curve_list) == 0:
            self.backend.auto_range = True

        # Update the window title
        self.setWindowTitle('ulog_explorer: ' + self.backend.path_to_logfile)

        # Update label of marker line
        self.update_marker_line_status()

        # Display title
        if self.backend.show_title:
            self.main_graph.setTitle(self.backend.path_to_logfile)
        else:
            self.main_graph.setTitle(None)

        # Update secondary graph
        if self.backend.show_secondary_graph:
            self.secondary_graph.clearPlots()
            self.secondary_graph.show()

            # Plot estimated position
            try:
                north_estimated = self.backend.df_dict['vehicle_local_position_0']['x'].values
                east_estimated = self.backend.df_dict['vehicle_local_position_0']['y'].values
                pen = pg.mkPen(width=self.backend.linewidth, color='b')
                curve = self.secondary_graph.plot(east_estimated, north_estimated, name='trajectory', pen=pen)
            except:
                pass

            # Plot measured GPS position
            try:
                north_measured = self.backend.df_dict['vehicle_gps_position_0']['lat_m*'].values
                east_gps_measured = self.backend.df_dict['vehicle_gps_position_0']['lon_m*'].values
                pen = pg.mkPen(width=self.backend.linewidth, color='r')
                curve = self.secondary_graph.plot(east_gps_measured, north_measured, name='trajectory', pen=pen)
            except:
                pass

            # Plot mission setpoints
            try:
                north_setpoint = self.backend.df_dict['position_setpoint_triplet_0']['current.lat_m*'].values
                east_setpoint = self.backend.df_dict['position_setpoint_triplet_0']['current.lon_m*'].values
                pen = pg.mkPen(width=self.backend.linewidth, color='g')
                curve = self.secondary_graph.plot(east_setpoint, north_setpoint, name='trajectory', pen=pen, symbol='o')
            except:
                pass

        else:
            self.secondary_graph.hide()


app = QtGui.QApplication(sys.argv)
GUI = Window()
GUI.show()
sys.exit(app.exec_())
