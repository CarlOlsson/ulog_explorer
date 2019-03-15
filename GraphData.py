from pyulog import *
import collections
import pandas as pd
import numpy as np


class GraphData():
    def __init__(self):
        # Dictionary of topic dataframes
        self.df_dict = {}
        # List of changed parameters
        self.changed_parameters = []
        # The path to the currently opened logfile
        self.path_to_logfile = ''
        # List with timestamps for forward transitions
        self.forward_transition_lines = []
        # List with timestamps for backward transitions
        self.back_transition_lines = []
        # True if the marker line is currently displayed
        self.show_marker_line = False
        # List of objects used to display green lines at start and stop of forward transition
        self.ft_lines_obj = []
        # List of objects used to display red lines at start and stop of backward transition
        self.bt_lines_obj = []
        # List of objects used to display lines at parameter changes
        self.parameter_lines_obj = []
        # Object used to display the graph legend
        self.legend_obj = None
        # Object used to display the marker line
        self.marker_line_obj = None
        # The position of the marker line
        self.marker_line_pos = 0
        # Dictionary of initial parameters
        self.initial_parameters = {}
        # Graph title
        self.title = ''
        self._logfile_str = ''

    # Convert a pyulog.core.ULog object to a dictionary of dataframes
    def ulog_to_df(self, logfile_str):
        self.df_dict.clear()
        self._logfile_str = logfile_str
        ulog = ULog(logfile_str)
        for elem in sorted(ulog.data_list, key=lambda d: d.name + str(d.multi_id)):
            topic_name = elem.name + "_" + str(elem.multi_id)
            column_names = set(elem.data.keys())
            df = pd.DataFrame(index=elem.data['timestamp'] / 1e6)
            for name in column_names - {'timestamp'}:
                df[name] = elem.data[name]

            self.df_dict[topic_name] = df

        self.changed_parameters = ulog.changed_parameters
        self.initial_parameters = ulog.initial_parameters
        self.logged_messages = ulog.logged_messages
        self.start_timestamp = ulog.start_timestamp
        self.last_timestamp = ulog.last_timestamp
        self.dropouts = ulog.dropouts
        self.msg_info_dict = ulog.msg_info_dict
        self.msg_info_multiple_dict = ulog.msg_info_multiple_dict
        self.data_list = ulog.data_list
        self._set_title()
        self._get_transition_timestamps()
        self._add_all_fields_to_df()

    def _set_title(self):
        self.title = self._logfile_str
        if 'AIRCRAFT_ID' in self.initial_parameters:
            self.title = self.title + " ({0})".format(int(self.initial_parameters['AIRCRAFT_ID']))

    # Add fields to df_dict. * is added to the names to represent that it was calculated in postprocessing and not logged
    def _add_all_fields_to_df(self):
        # Add norm of magnetometer measurement to sensor_combined
        try:
            topic_str = 'sensor_combined_0'
            self.df_dict[topic_str]['magnetometer_ga_norm*'] = np.sqrt(self.df_dict[topic_str]['magnetometer_ga[0]']**2 + self.df_dict[topic_str]['magnetometer_ga[1]']**2 + self.df_dict[topic_str]['magnetometer_ga[2]']**2)
        except Exception as ex:
            pass

        # Add norm of accelerometer measurement to sensor_combined
        try:
            topic_str = 'sensor_combined_0'
            self.df_dict[topic_str]['accelerometer_m_s2_norm*'] = np.sqrt(self.df_dict[topic_str]['accelerometer_m_s2[0]']**2 + self.df_dict[topic_str]['accelerometer_m_s2[1]']**2 + self.df_dict[topic_str]['accelerometer_m_s2[2]']**2)
        except Exception as ex:
            pass

        # Add windspeed magnitude and direction to wind_estimate
        try:
            topic_str = 'wind_estimate_0'
            self.df_dict[topic_str]['windspeed_magnitude*'] = np.sqrt(self.df_dict[topic_str]['windspeed_north']**2 + self.df_dict[topic_str]['windspeed_east']**2)
            self.df_dict[topic_str]['windspeed_direction*'] = np.arctan2(self.df_dict[topic_str]['variance_north'], self.df_dict[topic_str]['variance_east'])
            self.df_dict[topic_str]['windspeed_direction* [deg]'] = np.rad2deg(self.df_dict[topic_str]['windspeed_direction*'])
        except Exception as ex:
            pass

        # Add vxy and vxyz to vehicle_local_position
        try:
            topic_str = 'vehicle_local_position_0'
            self.df_dict[topic_str]['vxy*'] = np.sqrt(self.df_dict[topic_str]['vx']**2 + self.df_dict[topic_str]['vy']**2)
            self.df_dict[topic_str]['vxyz*'] = np.sqrt(self.df_dict[topic_str]['vx']**2 + self.df_dict[topic_str]['vy']**2 + self.df_dict[topic_str]['vz']**2)
        except Exception as ex:
            pass

        # Add vel_ne and vel_ned to vehicle_global_position
        try:
            topic_str = 'vehicle_global_position_0'
            self.df_dict[topic_str]['vel_ne*'] = np.sqrt(self.df_dict[topic_str]['vel_n']**2 + self.df_dict[topic_str]['vel_e']**2)
            self.df_dict[topic_str]['vel_ned*'] = np.sqrt(self.df_dict[topic_str]['vel_n']**2 + self.df_dict[topic_str]['vel_e']**2 + self.df_dict[topic_str]['vel_d']**2)
        except Exception as ex:
            pass

        # Add vel_ne_m_s to vehicle_gps_position_0
        try:
            topic_str = 'vehicle_gps_position_0'
            self.df_dict[topic_str]['vel_ne_m_s*'] = np.sqrt(self.df_dict[topic_str]['vel_n_m_s']**2 + self.df_dict[topic_str]['vel_e_m_s']**2)
            self.df_dict[topic_str]['gpsCOG*'] = np.arctan2(self.df_dict[topic_str]['vel_e_m_s'], self.df_dict[topic_str]['vel_n_m_s'])
            self.df_dict[topic_str]['gpsCOG* [deg]'] = np.rad2deg(self.df_dict[topic_str]['gpsCOG*'])
        except Exception as ex:
            pass

        # Add vel_ne_m_s to vehicle_gps_position_1
        try:
            topic_str = 'vehicle_gps_position_1'
            self.df_dict[topic_str]['vel_ne_m_s*'] = np.sqrt(self.df_dict[topic_str]['vel_n_m_s']**2 + self.df_dict[topic_str]['vel_e_m_s']**2)
            self.df_dict[topic_str]['gpsCOG*'] = np.arctan2(self.df_dict[topic_str]['vel_e_m_s'], self.df_dict[topic_str]['vel_n_m_s'])
            self.df_dict[topic_str]['gpsCOG* [deg]'] = np.rad2deg(self.df_dict[topic_str]['gpsCOG*'])
        except Exception as ex:
            pass

        # Add mag_declination_from_states, mag_inclination_from_states and mag_strength_from_states to estimator_status
        try:
            topic_str = 'estimator_status_0'
            self.df_dict[topic_str]['mag_declination_from_states*'] = np.arctan2(self.df_dict[topic_str]['states[17]'], self.df_dict[topic_str]['states[16]'])
            self.df_dict[topic_str]['mag_declination_from_states* [deg]'] = np.rad2deg(self.df_dict[topic_str]['mag_declination_from_states*'])
            self.df_dict[topic_str]['mag_strength_from_states*'] = (self.df_dict[topic_str]['states[16]'] ** 2 + self.df_dict[topic_str]['states[17]'] ** 2 + self.df_dict[topic_str]['states[18]'] ** 2) ** 0.5
            self.df_dict[topic_str]['mag_inclination_from_states*'] = np.arcsin(self.df_dict[topic_str]['states[18]'] / np.maximum(self.df_dict[topic_str]['mag_strength_from_states*'], np.finfo(np.float32).eps))
            self.df_dict[topic_str]['mag_inclination_from_states* [deg]'] = np.rad2deg(self.df_dict[topic_str]['mag_inclination_from_states*'])
            self.df_dict[topic_str]['ekfGOG*'] = np.arctan2(self.df_dict[topic_str]['states[5]'], self.df_dict[topic_str]['states[4]'])
            self.df_dict[topic_str]['ekfGOG* [deg]'] = np.rad2deg(self.df_dict[topic_str]['ekfGOG*'])
        except Exception as ex:
            pass

        # Add fields to ekf2_innovations
        try:
            topic_str = 'ekf2_innovations_0'
            self.df_dict[topic_str]['heading_innov_var^0.5'] = np.sqrt(self.df_dict[topic_str]['heading_innov_var'])
            self.df_dict[topic_str]['mag_innov_var[0]^0.5'] = np.sqrt(self.df_dict[topic_str]['mag_innov_var[0]'])
            self.df_dict[topic_str]['mag_innov_var[1]^0.5'] = np.sqrt(self.df_dict[topic_str]['mag_innov_var[1]'])
            self.df_dict[topic_str]['mag_innov_var[2]^0.5'] = np.sqrt(self.df_dict[topic_str]['mag_innov_var[2]'])
            self.df_dict[topic_str]['beta_innov_var^0.5'] = np.sqrt(self.df_dict[topic_str]['beta_innov_var'])
            self.df_dict[topic_str]['vel_pos_innov_var[0]^0.5'] = np.sqrt(self.df_dict[topic_str]['vel_pos_innov_var[0]'])
            self.df_dict[topic_str]['vel_pos_innov_var[1]^0.5'] = np.sqrt(self.df_dict[topic_str]['vel_pos_innov_var[1]'])
            self.df_dict[topic_str]['vel_pos_innov_var[2]^0.5'] = np.sqrt(self.df_dict[topic_str]['vel_pos_innov_var[2]'])
            self.df_dict[topic_str]['heading_innov* [deg]'] = np.rad2deg(self.df_dict[topic_str]['heading_innov'])
        except Exception as ex:
            pass

        # Add yaw, pitch, roll
        self._add_yaw_pitch_roll('vehicle_attitude_0', 'q')
        self._add_yaw_pitch_roll('vehicle_attitude_groundtruth_0', 'q')
        self._add_yaw_pitch_roll('vehicle_attitude_setpoint_0', 'q_d')
        self._add_yaw_pitch_roll('estimator_status_0', 'q')
        self._add_yaw_pitch_roll('estimator_status_0', 'states')

        # Add lat_m, lon_m to vehicle_gps_position
        try:
            self._add_lat_lon_m('vehicle_gps_position_0', 'lat', 'lon', 1e7)
        except Exception as ex:
            pass

        try:
            self._add_lat_lon_m('vehicle_gps_position_1', 'lat', 'lon', 1e7)
        except Exception as ex:
            pass

        # Add lat_m, lon_m to vehicle_global_position
        try:
            self._add_lat_lon_m('vehicle_global_position_0', 'lat', 'lon')
        except Exception as ex:
            pass

        # Add lat_m, lon_m to position_setpoint_triplet_0
        try:
            self._add_lat_lon_m('position_setpoint_triplet_0', 'current.lat', 'current.lon')
        except Exception as ex:
            pass

        # Add dt to sensor_combined_0
        try:
            topic_str = 'sensor_combined_0'
            self.df_dict[topic_str]['dt*'] = np.insert(np.diff(self.df_dict[topic_str].index) * 1e6, 0, 0)
        except Exception as ex:
            pass

        # Add bits of control_mode_flags and gps_check_fail_flags to estimator_flags*
        try:
            control_mode_flags_values = self.df_dict['estimator_status_0']['control_mode_flags'].values
            topic_str = 'estimator_flags*'
            self.df_dict[topic_str] = pd.DataFrame(((2 ** 0 & control_mode_flags_values) > 0) * 1, index=self.df_dict['estimator_status_0'].index, columns=['CS_TILT_ALIGN'])  # 0 - true if the filter tilt alignment is complete
            self.df_dict[topic_str]['CS_YAW_ALIGN'] = ((2 ** 1 & control_mode_flags_values) > 0) * 1  # 1 - true if the filter yaw alignment is complete
            self.df_dict[topic_str]['CS_GPS'] = ((2 ** 2 & control_mode_flags_values) > 0) * 1  # 2 - true if GPS measurements are being fused
            self.df_dict[topic_str]['CS_OPT_FLOW'] = ((2 ** 3 & control_mode_flags_values) > 0) * 1  # 3 - true if optical flow measurements are being fused
            self.df_dict[topic_str]['CS_MAG_HDG'] = ((2 ** 4 & control_mode_flags_values) > 0) * 1  # 4 - true if a simple magnetic yaw heading is being fused
            self.df_dict[topic_str]['CS_MAG_3D'] = ((2 ** 5 & control_mode_flags_values) > 0) * 1  # 5 - true if 3-axis magnetometer measurement are being fused
            self.df_dict[topic_str]['CS_MAG_DEC'] = ((2 ** 6 & control_mode_flags_values) > 0) * 1  # 6 - true if synthetic magnetic declination measurements are being fused
            self.df_dict[topic_str]['CS_IN_AIR'] = ((2 ** 7 & control_mode_flags_values) > 0) * 1  # 7 - true when thought to be airborne
            self.df_dict[topic_str]['CS_WIND'] = ((2 ** 8 & control_mode_flags_values) > 0) * 1  # 8 - true when wind velocity is being estimated
            self.df_dict[topic_str]['CS_BARO_HGT'] = ((2 ** 9 & control_mode_flags_values) > 0) * 1  # 9 - true when baro height is being fused as a primary height reference
            self.df_dict[topic_str]['CS_RNG_HGT'] = ((2 ** 10 & control_mode_flags_values) > 0) * 1  # 10 - true when range finder height is being fused as a primary height reference
            self.df_dict[topic_str]['CS_GPS_HGT'] = ((2 ** 11 & control_mode_flags_values) > 0) * 1  # 11 - true when GPS height is being fused as a primary height reference
            self.df_dict[topic_str]['CS_EV_POS'] = ((2 ** 12 & control_mode_flags_values) > 0) * 1  # 12 - true when local position data from external vision is being fused
            self.df_dict[topic_str]['CS_EV_YAW'] = ((2 ** 13 & control_mode_flags_values) > 0) * 1  # 13 - true when yaw data from external vision measurements is being fused
            self.df_dict[topic_str]['CS_EV_HGT'] = ((2 ** 14 & control_mode_flags_values) > 0) * 1  # 14 - true when height data from external vision measurements is being fused
            self.df_dict[topic_str]['CS_BETA'] = ((2 ** 15 & control_mode_flags_values) > 0) * 1  # 15 - true when synthetic sideslip measurements are being fused
            self.df_dict[topic_str]['CS_MAG_FIELD'] = ((2 ** 16 & control_mode_flags_values) > 0) * 1  # 16 - true when only the magnetic field states are updated by the magnetometer
            self.df_dict[topic_str]['CS_FIXED_WING'] = ((2 ** 17 & control_mode_flags_values) > 0) * 1  # 17 - true when thought to be operating as a fixed wing vehicle with constrained sideslip
            self.df_dict[topic_str]['CS_MAG_FAULT'] = ((2 ** 18 & control_mode_flags_values) > 0) * 1  # 18 - true when the magnetomer has been declared faulty and is no longer being used
            self.df_dict[topic_str]['CS_ASPD'] = ((2 ** 19 & control_mode_flags_values) > 0) * 1  # 19 - true when airspeed measurements are being fused
            self.df_dict[topic_str]['CS_GND_EFFECT'] = ((2 ** 20 & control_mode_flags_values) > 0) * 1  # 20 - true when when protection from ground effect induced static pressure rise is active
            self.df_dict[topic_str]['CS_RNG_STUCK'] = ((2 ** 21 & control_mode_flags_values) > 0) * 1  # 21 - true when a stuck range finder sensor has been detected
            self.df_dict[topic_str]['CS_GPS_YAW'] = ((2 ** 22 & control_mode_flags_values) > 0) * 1  # 22 - true when yaw (not ground course) data from a GPS receiver is being fused
            self.df_dict[topic_str]['CS_MAG_ALIGNED'] = ((2 ** 23 & control_mode_flags_values) > 0) * 1  # 23 - true when the in-flight mag field alignment has been completed

            gps_check_fail_flags_values = self.df_dict['estimator_status_0']['gps_check_fail_flags'].values
            self.df_dict[topic_str]['GPS_CHECK_FAIL_GPS_FIX'] = ((2 ** 0 & gps_check_fail_flags_values) > 0) * 1  # 0 : insufficient fix type (no 3D solution)
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MIN_SAT_COUNT'] = ((2 ** 1 & gps_check_fail_flags_values) > 0) * 1  # 1 : minimum required sat count fail
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MIN_GDOP'] = ((2 ** 2 & gps_check_fail_flags_values) > 0) * 1  # 2 : minimum required GDoP fail
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_HORZ_ERR'] = ((2 ** 3 & gps_check_fail_flags_values) > 0) * 1  # 3 : maximum allowed horizontal position error fail
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_VERT_ERR'] = ((2 ** 4 & gps_check_fail_flags_values) > 0) * 1  # 4 : maximum allowed vertical position error fail
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_SPD_ERR'] = ((2 ** 5 & gps_check_fail_flags_values) > 0) * 1  # 5 : maximum allowed speed error fail
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_HORZ_DRIFT'] = ((2 ** 6 & gps_check_fail_flags_values) > 0) * 1  # 6 : maximum allowed horizontal position drift fail - requires stationary vehicle
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_VERT_DRIFT'] = ((2 ** 7 & gps_check_fail_flags_values) > 0) * 1  # 7 : maximum allowed vertical position drift fail - requires stationary vehicle
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_HORZ_SPD_ERR'] = ((2 ** 8 & gps_check_fail_flags_values) > 0) * 1  # 8 : maximum allowed horizontal speed fail - requires stationary vehicle
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_VERT_SPD_ERR'] = ((2 ** 9 & gps_check_fail_flags_values) > 0) * 1  # 9 : maximum allowed vertical velocity discrepancy fail

        except Exception as ex:
            pass

    def _add_lat_lon_m(self, topic_str, lat_str, lon_str, div=1):
        lat = np.deg2rad(self.df_dict[topic_str][lat_str].values / div)
        lon = np.deg2rad(self.df_dict[topic_str][lon_str].values / div)

        anchor_lat = lat[0]
        anchor_lon = lon[0]

        # try to get the anchor position from the dataset
        try:
            local_pos_data = self.df_dict['vehicle_local_position_0']
            indices = np.nonzero(local_pos_data['ref_timestamp'])
            if len(indices[0]) > 0:
                anchor_lat = np.deg2rad(local_pos_data['ref_lat'].values[indices[0][0]])
                anchor_lon = np.deg2rad(local_pos_data['ref_lon'].values[indices[0][0]])
        except:
            pass

        lat_m, lon_m = self._map_projection(lat, lon, anchor_lat, anchor_lon)
        self.df_dict[topic_str][lat_str + '_m*'] = lat_m
        self.df_dict[topic_str][lon_str + '_m*'] = lon_m

    # Function from flight_review (https://github.com/PX4/flight_review/)
    def _map_projection(self, lat, lon, anchor_lat, anchor_lon):
        """ convert lat, lon in [rad] to x, y in [m] with an anchor position """
        sin_lat = np.sin(lat)
        cos_lat = np.cos(lat)
        cos_d_lon = np.cos(lon - anchor_lon)
        sin_anchor_lat = np.sin(anchor_lat)
        cos_anchor_lat = np.cos(anchor_lat)

        arg = sin_anchor_lat * sin_lat + cos_anchor_lat * cos_lat * cos_d_lon
        arg[arg > 1] = 1
        arg[arg < -1] = -1

        # np.set_printoptions(threshold=np.nan)
        c = np.arccos(arg)
        k = np.copy(lat)
        for i in range(len(lat)):
            if np.abs(c[i]) < np.finfo(float).eps:
                k[i] = 1
            else:
                k[i] = c[i] / np.sin(c[i])

        CONSTANTS_RADIUS_OF_EARTH = 6371000
        x = k * (cos_anchor_lat * sin_lat - sin_anchor_lat * cos_lat * cos_d_lon) * \
            CONSTANTS_RADIUS_OF_EARTH
        y = k * cos_lat * np.sin(lon - anchor_lon) * CONSTANTS_RADIUS_OF_EARTH

        return x, y

    def _add_yaw_pitch_roll(self, topic_str, field_name_suffix=''):
        try:
            q0 = self.df_dict[topic_str][field_name_suffix + '[0]']
            q1 = self.df_dict[topic_str][field_name_suffix + '[1]']
            q2 = self.df_dict[topic_str][field_name_suffix + '[2]']
            q3 = self.df_dict[topic_str][field_name_suffix + '[3]']

            self.df_dict[topic_str][field_name_suffix + '_' + 'yaw312*'] = np.arctan2(-2.0 * (q1 * q2 - q0 * q3), q0 * q0 - q1 * q1 + q2 * q2 - q3 * q3)
            self.df_dict[topic_str][field_name_suffix + '_' + 'roll312*'] = np.arcsin(2.0 * (q2 * q3 + q0 * q1))
            self.df_dict[topic_str][field_name_suffix + '_' + 'pitch312*'] = np.arctan2(-2.0 * (q1 * q3 - q0 * q2), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3)

            self.df_dict[topic_str][field_name_suffix + '_' + 'yaw312* [deg]'] = np.rad2deg(self.df_dict[topic_str][field_name_suffix + '_' + 'yaw312*'])
            self.df_dict[topic_str][field_name_suffix + '_' + 'roll312* [deg]'] = np.rad2deg(self.df_dict[topic_str][field_name_suffix + '_' + 'roll312*'])
            self.df_dict[topic_str][field_name_suffix + '_' + 'pitch312* [deg]'] = np.rad2deg(self.df_dict[topic_str][field_name_suffix + '_' + 'pitch312*'])
        except Exception as ex:
            pass

    def _get_transition_timestamps(self):
        if self.df_dict['vehicle_status_0']['in_transition_mode'].any():
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

    def ulog_info(self):
        print("########### ulog_info: " + self.path_to_logfile + " ###########")
        # From pyulog.info
        verbose = False
        m1, s1 = divmod(int(self.start_timestamp / 1e6), 60)
        h1, m1 = divmod(m1, 60)
        m2, s2 = divmod(int((self.last_timestamp - self.start_timestamp) / 1e6), 60)
        h2, m2 = divmod(m2, 60)
        print("Logging start time: {:d}:{:02d}:{:02d}, duration: {:d}:{:02d}:{:02d}".format(
            h1, m1, s1, h2, m2, s2))

        dropout_durations = [dropout.duration for dropout in self.dropouts]
        if len(dropout_durations) == 0:
            print("No Dropouts")
        else:
            print("Dropouts: count: {:}, total duration: {:.1f} s, max: {:} ms, mean: {:} ms"
                  .format(len(dropout_durations), sum(dropout_durations) / 1000.,
                          max(dropout_durations),
                          int(sum(dropout_durations) / len(dropout_durations))))

        # version = self.get_version_info_str()
        # if not version is None:
        #     print('SW Version: {}'.format(version))

        print("Info Messages:")
        for k in sorted(self.msg_info_dict):
            if not k.startswith('perf_') or verbose:
                print(" {0}: {1}".format(k, self.msg_info_dict[k]))

        if len(self.msg_info_multiple_dict) > 0:
            if verbose:
                print("Info Multiple Messages:")
                for k in sorted(self.msg_info_multiple_dict):
                    print(" {0}: {1}".format(k, self.msg_info_multiple_dict[k]))
            else:
                print("Info Multiple Messages: {}".format(
                    ", ".join(["[{}: {}]".format(k, len(self.msg_info_multiple_dict[k])) for k in
                               sorted(self.msg_info_multiple_dict)])))

        print("")
        print("{:<41} {:7}, {:10}".format("Name (multi id, message size in bytes)",
                                          "number of data points", "total bytes"))

        data_list_sorted = sorted(self.data_list, key=lambda d: d.name + str(d.multi_id))
        for d in data_list_sorted:
            message_size = sum([ULog.get_field_size(f.type_str) for f in d.field_data])
            num_data_points = len(d.data['timestamp'])
            name_id = "{:} ({:}, {:})".format(d.name, d.multi_id, message_size)
            print(" {:<40} {:7d} {:10d}".format(name_id, num_data_points,
                                                message_size * num_data_points))

    def ulog_messages(self):
        print("########### ulog_messages: " + self.path_to_logfile + " ###########")
        # From pyulog.messages
        for m in self.logged_messages:
            m1, s1 = divmod(int(m.timestamp / 1e6), 60)
            h1, m1 = divmod(m1, 60)
            print("{:d}:{:02d}:{:02d} {:}: {:}".format(
                h1, m1, s1, m.log_level_str(), m.message))
