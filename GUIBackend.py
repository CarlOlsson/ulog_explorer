# Module: GUIBackend.py

from pyulog import *
import collections
import pandas as pd
import numpy as np
import transforms3d.euler as tfe


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
        # The path to the currently opened logfile
        self.path_to_logfile = ''
        # True if auto range should be done next frontend update
        self.auto_range = True
        # True if the title is currently displayed
        self.show_title = False
        # True if the transition lines are currently displayed
        self.show_transition_lines = False
        # List with timestamps for forward transitions
        self.forward_transition_lines = []
        # List with timestamps for backward transitions
        self.back_transition_lines = []
        # True if the marker line is currently displayed
        self.show_marker_line = False
        # True if the ROI is currently displayed
        self.show_ROI = False
        # True if the secondary graph currently is displayed
        self.show_secondary_graph = False
        # True if the displayed curves are rescaled to [0,1]
        self.rescale_curves = False

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

    # Convert a pyulog.core.ULog object to a dictionary of dataframes
    def ulog_to_df(self, logfile_str):
        ulog_dict = {}
        for elem in sorted(ULog(logfile_str).data_list, key=lambda d: d.name + str(d.multi_id)):
            topic_name = elem.name + "_" + str(elem.multi_id)
            column_names = set(elem.data.keys())
            df = pd.DataFrame(index=elem.data['timestamp'] / 1e6)
            for name in column_names - {'timestamp'}:
                df[name] = elem.data[name]

            ulog_dict[topic_name] = df

        self.df_dict = ulog_dict

    # Add fields to df_dict. * is added to the names to represent that it was calculated in postprocessing and not logged
    def add_all_fields_to_df(self):
        # Add norm of magnetometer measurement to sensor_combined
        try:
            topic_str = 'sensor_combined_0'
            self.df_dict[topic_str]['magnetometer_ga_norm*'] = np.sqrt(self.df_dict[topic_str]['magnetometer_ga[0]']**2 + self.df_dict[topic_str]['magnetometer_ga[1]']**2 + self.df_dict[topic_str]['magnetometer_ga[2]']**2)
        except Exception as ex:
            print(ex)

        # Add norm of accelerometer measurement to sensor_combined
        try:
            topic_str = 'sensor_combined_0'
            self.df_dict[topic_str]['accelerometer_m_s2_norm*'] = np.sqrt(self.df_dict[topic_str]['accelerometer_m_s2[0]']**2 + self.df_dict[topic_str]['accelerometer_m_s2[1]']**2 + self.df_dict[topic_str]['accelerometer_m_s2[2]']**2)
        except Exception as ex:
            print(ex)

        # Add windspeed magnitude and direction to wind_estimate
        try:
            topic_str = 'wind_estimate_0'
            self.df_dict[topic_str]['windspeed_magnitude*'] = np.sqrt(self.df_dict[topic_str]['windspeed_north']**2 + self.df_dict[topic_str]['windspeed_east']**2)
            self.df_dict[topic_str]['windspeed_direction*'] = np.arctan2(self.df_dict[topic_str]['variance_north'], self.df_dict[topic_str]['variance_east'])
            self.df_dict[topic_str]['windspeed_direction* [deg]'] = np.rad2deg(self.df_dict[topic_str]['windspeed_direction*'])
        except Exception as ex:
            print(ex)

        # Add vxy and vxyz to vehicle_local_position
        try:
            topic_str = 'vehicle_local_position_0'
            self.df_dict[topic_str]['vxy*'] = np.sqrt(self.df_dict[topic_str]['vx']**2 + self.df_dict[topic_str]['vy']**2)
            self.df_dict[topic_str]['vxyz*'] = np.sqrt(self.df_dict[topic_str]['vx']**2 + self.df_dict[topic_str]['vy']**2 + self.df_dict[topic_str]['vz']**2)
        except Exception as ex:
            print(ex)

        # Add vel_ne and vel_ned to vehicle_global_position
        try:
            topic_str = 'vehicle_global_position_0'
            self.df_dict[topic_str]['vel_ne*'] = np.sqrt(self.df_dict[topic_str]['vel_n']**2 + self.df_dict[topic_str]['vel_e']**2)
            self.df_dict[topic_str]['vel_ned*'] = np.sqrt(self.df_dict[topic_str]['vel_n']**2 + self.df_dict[topic_str]['vel_e']**2 + self.df_dict[topic_str]['vel_d']**2)
        except Exception as ex:
            print(ex)

        # Add vel_ne_m_s to vehicle_gps_position_0
        try:
            topic_str = 'vehicle_gps_position_0'
            self.df_dict[topic_str]['vel_ne_m_s*'] = np.sqrt(self.df_dict[topic_str]['vel_n_m_s']**2 + self.df_dict[topic_str]['vel_e_m_s']**2)
        except Exception as ex:
            print(ex)

        # Add vel_ne_m_s to vehicle_gps_position_1
        try:
            topic_str = 'vehicle_gps_position_1'
            self.df_dict[topic_str]['vel_ne_m_s*'] = np.sqrt(self.df_dict[topic_str]['vel_n_m_s']**2 + self.df_dict[topic_str]['vel_e_m_s']**2)
        except Exception as ex:
            print(ex)

        # Add mag_declination_from_states to estimator_status
        try:
            topic_str = 'estimator_status_0'
            self.df_dict[topic_str]['mag_declination_from_states*'] = np.arctan2(self.df_dict[topic_str]['states[17]'], self.df_dict[topic_str]['states[16]'])
            self.df_dict[topic_str]['mag_declination_from_states* [deg]'] = np.rad2deg(self.df_dict[topic_str]['mag_declination_from_states*'])
        except Exception as ex:
            print(ex)

        # Add yaw, pitch, roll
        self.add_yaw_pitch_roll('vehicle_attitude_0')
        self.add_yaw_pitch_roll('vehicle_attitude_groundtruth_0')
        self.add_yaw_pitch_roll('vehicle_attitude_setpoint_0', '_d')

    def add_yaw_pitch_roll(self, topic_str, field_name_suffix=''):
        try:
            q0 = self.df_dict[topic_str]['q' + field_name_suffix + '[0]']
            q1 = self.df_dict[topic_str]['q' + field_name_suffix + '[1]']
            q2 = self.df_dict[topic_str]['q' + field_name_suffix + '[2]']
            q3 = self.df_dict[topic_str]['q' + field_name_suffix + '[3]']

            yaw, pitch, roll = np.array(
                [
                    tfe.quat2euler([q0i, q1i, q2i, q3i], 'szyx')
                    for q0i, q1i, q2i, q3i in zip(q0, q1, q2, q3)
                ]
            ).T

            self.df_dict[topic_str]['yaw321*'] = yaw
            self.df_dict[topic_str]['pitch321*'] = pitch
            self.df_dict[topic_str]['roll321*'] = roll

            self.df_dict[topic_str]['yaw312*'] = np.arctan2(-2.0 * (q1 * q2 - q0 * q3), q0 * q0 - q1 * q1 + q2 * q2 - q3 * q3)

            self.df_dict[topic_str]['yaw321* [deg]'] = np.rad2deg(self.df_dict[topic_str]['yaw321*'])
            self.df_dict[topic_str]['pitch321* [deg]'] = np.rad2deg(self.df_dict[topic_str]['pitch321*'])
            self.df_dict[topic_str]['roll321* [deg]'] = np.rad2deg(self.df_dict[topic_str]['roll321*'])

            self.df_dict[topic_str]['yaw312* [deg]'] = np.rad2deg(self.df_dict[topic_str]['yaw312*'])
        except Exception as ex:
            print(ex)

    def get_transition_timestamps(self):
        forward_transition_lines = self.df_dict['vehicle_status_0'].index[self.df_dict['vehicle_status_0'].ne(self.df_dict['vehicle_status_0'].shift())['in_transition_to_fw']].tolist()
        forward_transition_lines.pop(0)
        self.forward_transition_lines = forward_transition_lines

        logical_series = self.df_dict['vehicle_status_0'].ne(self.df_dict['vehicle_status_0'].shift())[['in_transition_mode']]
        logical_series2 = self.df_dict['vehicle_status_0']['is_rotary_wing'] == True

        df_comb = pd.concat([logical_series, logical_series2], axis=1)

        idx = (df_comb['in_transition_mode']) & (df_comb['is_rotary_wing'])
        back_transition_lines = self.df_dict['vehicle_status_0'].index[idx].tolist()
        back_transition_lines.pop(0)
        self.back_transition_lines = back_transition_lines


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
