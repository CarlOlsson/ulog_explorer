from pyulog import *
import collections
import pandas as pd
import numpy as np
import transforms3d.euler as tfe


class GraphData():
    def __init__(self):
        # Dictionary of topic dataframes
        self.df_dict = {}
        # The path to the currently opened logfile
        self.path_to_logfile = ''
        # List with timestamps for forward transitions
        self.forward_transition_lines = []
        # List with timestamps for backward transitions
        self.back_transition_lines = []
        # True if the marker line is currently displayed
        self.show_marker_line = False
        self.ft_lines_obj = []
        self.bt_lines_obj = []

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

        # Add mag_declination_from_states, mag_inclination_from_states and mag_strength_from_states to estimator_status
        try:
            topic_str = 'estimator_status_0'
            self.df_dict[topic_str]['mag_declination_from_states*'] = np.arctan2(self.df_dict[topic_str]['states[17]'], self.df_dict[topic_str]['states[16]'])
            self.df_dict[topic_str]['mag_declination_from_states* [deg]'] = np.rad2deg(self.df_dict[topic_str]['mag_declination_from_states*'])
            self.df_dict[topic_str]['mag_strength_from_states*'] = (self.df_dict[topic_str]['states[16]'] ** 2 + self.df_dict[topic_str]['states[17]'] ** 2 + self.df_dict[topic_str]['states[18]'] ** 2) ** 0.5
            self.df_dict[topic_str]['mag_inclination_from_states*'] = np.arcsin(self.df_dict[topic_str]['states[18]'] / np.maximum(self.df_dict[topic_str]['mag_strength_from_states*'], np.finfo(np.float32).eps))
            self.df_dict[topic_str]['mag_inclination_from_states* [deg]'] = np.rad2deg(self.df_dict[topic_str]['mag_inclination_from_states*'])
        except Exception as ex:
            print(ex)

        # Add yaw, pitch, roll
        self.add_yaw_pitch_roll('vehicle_attitude_0')
        self.add_yaw_pitch_roll('vehicle_attitude_groundtruth_0')
        self.add_yaw_pitch_roll('vehicle_attitude_setpoint_0', '_d')

        # Add lat_m, lon_m to vehicle_gps_position
        try:
            self.add_lat_lon_m('vehicle_gps_position_0', 'lat', 'lon', 1e7)
        except Exception as ex:
            print(ex)

        try:
            self.add_lat_lon_m('vehicle_gps_position_1', 'lat', 'lon', 1e7)
        except Exception as ex:
            print(ex)

        # Add lat_m, lon_m to vehicle_global_position
        try:
            self.add_lat_lon_m('vehicle_global_position_0', 'lat', 'lon')
        except Exception as ex:
            print(ex)

        # Add lat_m, lon_m to position_setpoint_triplet_0
        try:
            self.add_lat_lon_m('position_setpoint_triplet_0', 'current.lat', 'current.lon')
        except Exception as ex:
            print(ex)

        # Add bits of control_mode_flags and gps_check_fail_flags to estimator_flags*
        try:
            control_mode_flags_values = self.df_dict['estimator_status_0']['control_mode_flags'].values
            topic_str = 'estimator_flags*'
            self.df_dict[topic_str] = pd.DataFrame(((2 ** 0 & control_mode_flags_values) > 0) * 1, index=self.df_dict['estimator_status_0'].index, columns=['CS_TILT_ALIGN*'])  # 0 - true if the filter tilt alignment is complete
            self.df_dict[topic_str]['CS_YAW_ALIGN*'] = ((2 ** 1 & control_mode_flags_values) > 0) * 1  # 1 - true if the filter yaw alignment is complete
            self.df_dict[topic_str]['CS_GPS*'] = ((2 ** 2 & control_mode_flags_values) > 0) * 1  # 2 - true if GPS measurements are being fused
            self.df_dict[topic_str]['CS_OPT_FLOW*'] = ((2 ** 3 & control_mode_flags_values) > 0) * 1  # 3 - true if optical flow measurements are being fused
            self.df_dict[topic_str]['CS_MAG_HDG*'] = ((2 ** 4 & control_mode_flags_values) > 0) * 1  # 4 - true if a simple magnetic yaw heading is being fused
            self.df_dict[topic_str]['CS_MAG_3D*'] = ((2 ** 5 & control_mode_flags_values) > 0) * 1  # 5 - true if 3-axis magnetometer measurement are being fused
            self.df_dict[topic_str]['CS_MAG_DEC*'] = ((2 ** 6 & control_mode_flags_values) > 0) * 1  # 6 - true if synthetic magnetic declination measurements are being fused
            self.df_dict[topic_str]['CS_IN_AIR*'] = ((2 ** 7 & control_mode_flags_values) > 0) * 1  # 7 - true when thought to be airborne
            self.df_dict[topic_str]['CS_WIND*'] = ((2 ** 8 & control_mode_flags_values) > 0) * 1  # 8 - true when wind velocity is being estimated
            self.df_dict[topic_str]['CS_BARO_HGT*'] = ((2 ** 9 & control_mode_flags_values) > 0) * 1  # 9 - true when baro height is being fused as a primary height reference
            self.df_dict[topic_str]['CS_RNG_HGT*'] = ((2 ** 10 & control_mode_flags_values) > 0) * 1  # 10 - true when range finder height is being fused as a primary height reference
            self.df_dict[topic_str]['CS_GPS_HGT*'] = ((2 ** 11 & control_mode_flags_values) > 0) * 1  # 11 - true when GPS height is being fused as a primary height reference
            self.df_dict[topic_str]['CS_EV_POS*'] = ((2 ** 12 & control_mode_flags_values) > 0) * 1  # 12 - true when local position data from external vision is being fused
            self.df_dict[topic_str]['CS_EV_YAW*'] = ((2 ** 13 & control_mode_flags_values) > 0) * 1  # 13 - true when yaw data from external vision measurements is being fused
            self.df_dict[topic_str]['CS_EV_HGT*'] = ((2 ** 14 & control_mode_flags_values) > 0) * 1  # 14 - true when height data from external vision measurements is being fused
            self.df_dict[topic_str]['CS_BETA*'] = ((2 ** 15 & control_mode_flags_values) > 0) * 1  # 15 - true when synthetic sideslip measurements are being fused
            self.df_dict[topic_str]['CS_MAG_FIELD*'] = ((2 ** 16 & control_mode_flags_values) > 0) * 1  # 16 - true when only the magnetic field states are updated by the magnetometer
            self.df_dict[topic_str]['CS_FIXED_WING*'] = ((2 ** 17 & control_mode_flags_values) > 0) * 1  # 17 - true when thought to be operating as a fixed wing vehicle with constrained sideslip
            self.df_dict[topic_str]['CS_MAG_FAULT*'] = ((2 ** 18 & control_mode_flags_values) > 0) * 1  # 18 - true when the magnetomer has been declared faulty and is no longer being used
            self.df_dict[topic_str]['CS_ASPD*'] = ((2 ** 19 & control_mode_flags_values) > 0) * 1  # 19 - true when airspeed measurements are being fused
            self.df_dict[topic_str]['CS_GND_EFFECT*'] = ((2 ** 20 & control_mode_flags_values) > 0) * 1  # 20 - true when when protection from ground effect induced static pressure rise is active
            self.df_dict[topic_str]['CS_RNG_STUCK*'] = ((2 ** 21 & control_mode_flags_values) > 0) * 1  # 21 - true when a stuck range finder sensor has been detected
            self.df_dict[topic_str]['CS_GPS_YAW*'] = ((2 ** 22 & control_mode_flags_values) > 0) * 1  # 22 - true when yaw (not ground course) data from a GPS receiver is being fused
            self.df_dict[topic_str]['CS_MAG_ALIGNED*'] = ((2 ** 23 & control_mode_flags_values) > 0) * 1  # 23 - true when the in-flight mag field alignment has been completed

            gps_check_fail_flags_values = self.df_dict['estimator_status_0']['gps_check_fail_flags'].values
            self.df_dict[topic_str]['GPS_CHECK_FAIL_GPS_FIX*'] = ((2 ** 0 & gps_check_fail_flags_values) > 0) * 1  # 0 : insufficient fix type (no 3D solution)
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MIN_SAT_COUNT*'] = ((2 ** 1 & gps_check_fail_flags_values) > 0) * 1  # 1 : minimum required sat count fail
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MIN_GDOP*'] = ((2 ** 2 & gps_check_fail_flags_values) > 0) * 1  # 2 : minimum required GDoP fail
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_HORZ_ERR*'] = ((2 ** 3 & gps_check_fail_flags_values) > 0) * 1  # 3 : maximum allowed horizontal position error fail
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_VERT_ERR*'] = ((2 ** 4 & gps_check_fail_flags_values) > 0) * 1  # 4 : maximum allowed vertical position error fail
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_SPD_ERR*'] = ((2 ** 5 & gps_check_fail_flags_values) > 0) * 1  # 5 : maximum allowed speed error fail
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_HORZ_DRIFT*'] = ((2 ** 6 & gps_check_fail_flags_values) > 0) * 1  # 6 : maximum allowed horizontal position drift fail - requires stationary vehicle
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_VERT_DRIFT*'] = ((2 ** 7 & gps_check_fail_flags_values) > 0) * 1  # 7 : maximum allowed vertical position drift fail - requires stationary vehicle
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_HORZ_SPD_ERR*'] = ((2 ** 8 & gps_check_fail_flags_values) > 0) * 1  # 8 : maximum allowed horizontal speed fail - requires stationary vehicle
            self.df_dict[topic_str]['GPS_CHECK_FAIL_MAX_VERT_SPD_ERR*'] = ((2 ** 9 & gps_check_fail_flags_values) > 0) * 1  # 9 : maximum allowed vertical velocity discrepancy fail

        except Exception as ex:
            print(ex)

    def add_lat_lon_m(self, topic_str, lat_str, lon_str, div=1):
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

        lat_m, lon_m = self.map_projection(lat, lon, anchor_lat, anchor_lon)
        self.df_dict[topic_str][lat_str + '_m*'] = lat_m
        self.df_dict[topic_str][lon_str + '_m*'] = lon_m

    # Function from flight_review (https://github.com/PX4/flight_review/)
    def map_projection(self, lat, lon, anchor_lat, anchor_lon):
        """ convert lat, lon in [rad] to x, y in [m] with an anchor position """
        sin_lat = np.sin(lat)
        cos_lat = np.cos(lat)
        cos_d_lon = np.cos(lon - anchor_lon)
        sin_anchor_lat = np.sin(anchor_lat)
        cos_anchor_lat = np.cos(anchor_lat)

        arg = sin_anchor_lat * sin_lat + cos_anchor_lat * cos_lat * cos_d_lon
        arg[arg > 1] = 1
        arg[arg < -1] = -1

        np.set_printoptions(threshold=np.nan)
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
