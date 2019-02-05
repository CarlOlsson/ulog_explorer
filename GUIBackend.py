# Module: GUIBackend.py

from GraphData import *


class GUIBackend():
    def __init__(self):
        # List of curve class elements currently displayed
        self.curve_list = []
        # The symbol used for each datapoint when plotting
        self.symbol = None
        # The linewidth of the curves in the plot
        self.linewidth = 1
        # True if the legend is currently displayed
        self.show_legend = False
        # True if auto range should be done next frontend update
        self.auto_range = True
        # True if the title is currently displayed
        self.show_title = False
        # True if the transition lines are currently displayed
        self.show_transition_lines = False
        # True if the ROI is currently displayed
        self.show_ROI = False
        # True if the displayed curves are rescaled to [0,1]
        self.rescale_curves = False
        # Currently display mode of the secondary graph
        self.secondary_graph_mode = '2D'

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

        self.graph_data = [GraphData() for _ in [0, 1]]

    def load_ulog_to_graph_data(self, logfile_str, graph_id=0):
        self.graph_data[graph_id].ulog_to_df(logfile_str)
        self.graph_data[graph_id].add_all_fields_to_df()
        self.graph_data[graph_id].get_transition_timestamps()

        # Returns true if the selected topic and field is already in the list
    def contains(self, selected_topic, selected_field):
        selected_topic_and_field = get_name_combined(selected_topic, selected_field)
        for elem in self.curve_list:
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

        self.curve_list.append(CurveClass(selected_topic, selected_field, color_key, color))

    # Removes the selected topic and field from the list of variables to plot
    def remove_selected_topic_and_field(self, selected_topic, selected_field):
        index = 0
        for elem in self.curve_list:
            if elem.selected_topic == selected_topic and elem.selected_field == selected_field:
                self.curve_list.pop(index)
                self.color_dict[elem.color_key][0] = False

            index = index + 1

    def clear_curve_list(self):
        self.curve_list = []
        for key, value in self.color_dict.items():
            self.color_dict[key][0] = False


# The variables currently displayed consists of a list of CurveClass items
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
