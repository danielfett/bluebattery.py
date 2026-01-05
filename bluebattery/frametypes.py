from flags import Flags

from . import conversions as cnv
from .commands import (
    BBFrame,
    BBValue,
    BBValueIgnore,
)

import logging

log = logging.getLogger("Frametypes")

SecFrame = BBFrame(output_id="sec", fields=[BBValue("i", "time_of_day_s")])


def add_reverse_day_counter(characteristic, output_values):
    """
    Frame postprocessing function to create a negative day counter (today=0, yesterday=1, etc.).
    """

    if "max_day_count" in output_values:
        characteristic.max_days_observed = output_values["max_day_count"]

    output_values["days_ago"] = (
        output_values["max_day_count"] - output_values["day_counter"]
    )


LogEntryDaysFrame = BBFrame(
    output_id="log/day/-{days_ago}",
    fields=[
        # bytes 0-1: big endian 16 bit mWh per day**
        BBValue("H", "Wh_day", cnv.cnv_mW_to_W),
        # bytes 2-3: big endian 16-bit max mW per Day**
        BBValue("H", "max_W_day", cnv.cnv_mW_to_W),
        # bytes 4-5: big endian 16-bit min mV per Day
        BBValue("H", "min_V_day", cnv.cnv_mV_to_V),
        # bytes 6-7: big endian 16-bit max mV per Day
        BBValue("H", "max_V_day", cnv.cnv_mV_to_V),
        # bytes 8-9: big endian 16-bit charge time in minutes per Day**
        BBValue("H", "charge_minutes_day"),
        # bytes 10-11: big endian 16-bit day counter for this log entry, counting up from 0
        BBValue("H", "day_counter"),
        # bytes 12-13: big endian 16-bit current day (max day count)
        BBValue("H", "max_day_count"),
        # bytes 14-15: big endian 16-bit Solar charge in 100 mAh**
        BBValue("H", "solar_charge_Ah", cnv.cnv_100mA_to_A),
        # bytes 16-17: big endian 16-bit SOC in 100 mAh
        BBValue("H", "state_of_charge_Ah", cnv.cnv_100mA_to_A),
        # bytes 18-19: big endian 16-bit max current 100 mA
        BBValue("H", "max_current_A", cnv.cnv_100mA_to_A),
        # bytes 20-21: big endian 16-bit min current -100 mA
        BBValue("H", "min_current_A", cnv.cnv_neg_100mA_to_A),
        # bytes 22-23: big endian 16-bit max SOC 100 mAh
        BBValue("H", "max_state_of_charge_Ah", cnv.cnv_100mA_to_A),
        # bytes 24-25: big endian 16-bit min SOC 100 mAh
        BBValue("H", "min_state_of_charge_Ah", cnv.cnv_100mA_to_A),
        # bytes 26-27: big endian 16-bit binary offset max Temperature (x - 0x8000) / 100 °C
        BBValue("H", "max_temperature_deg_C", cnv.cnv_bb_temp_to_deg_c),
        # bytes 28-29: big endian 16-bit binary offset min Temperature (x - 0x8000) / 100 °C
        BBValue("H", "min_temperature_deg_C", cnv.cnv_bb_temp_to_deg_c),
        # bytes 30-31: big endian 16-bit total external charge per day 100 mAh**
        BBValue("H", "total_external_charge_day_Ah", cnv.cnv_100mA_to_A),
        # bytes 32-33: big endian 16-bit total discharge per day 100 mAh
        BBValue("H", "total_discharge_Ah", cnv.cnv_100mA_to_A),
        # bytes 34-35: big endian 16-bit total charge per day 100 mAh
        BBValue("H", "total_charge_day_Ah", cnv.cnv_100mA_to_A),
        # byte 36: 8-bit frame type 0x00
        BBValueIgnore(),
        # bytes 37-38: big endian 16-bit total booster charge per day 100 mAh (V304)**
        BBValue("H", "total_booster_charge_day_Ah", cnv.cnv_100mA_to_A),
    ],
    postprocess=add_reverse_day_counter,
)

# available starting with Version V2xx, not anymore supported starting V306
LogEntryFrameOld = BBFrame(
    output_id="log/day/-{days_ago}/extended",
    fields=[
        # bytes 0-1: 16-bit day counter (relative to current day in frame type 0x00)
        BBValue("H", "day_counter"),
        # bytes 2-3: 16-bit wall time in seconds/2
        BBValue("H", "wall_time", lambda value: value * 2),
        # bytes 4-5: 16-bit average battery voltage mV
        BBValue("H", "avg_battery_voltage_V", cnv.cnv_mV_to_V),
        # bytes 6-7: 16-bit average solar current mA
        BBValue("H", "avg_solar_current_A", cnv.cnv_mA_to_A),
        # bytes 8: solar charger status: aktiv, standby, reduced
        BBValue("B", "solar_charger_status", cnv.cnv_solar_status),
        # bytes 9-10: 16-bit average battery current 100 mA
        BBValue("H", "avg_battery_current_A", cnv.cnv_100mA_to_A),
        # bytes 11-12: 16-bit battery SOC 100 mAh
        BBValue("H", "battery_state_of_charge_A", cnv.cnv_mA_to_A),
        # bytes 13+ 0-1: 16-bit day counter (relative to current day in frame type 0x00)
        BBValue("H", "day_counter"),
        # bytes 13+ 2-3: 16-bit wall time in seconds/2
        BBValue("H", "wall_time", lambda value: value * 2),
        # bytes 13+ 4-5: 16-bit average battery voltage mV
        BBValue("H", "avg_battery_voltage_V", cnv.cnv_mV_to_V),
        # bytes 13+ 6-7: 16-bit average solar current mA
        BBValue("H", "avg_solar_current_A", cnv.cnv_mA_to_A),
        # bytes 13+ 8: solar charger status: aktiv, standby, reduced
        BBValue("B", "solar_charger_status", cnv.cnv_solar_status),
        # bytes 13+ 9-10: 16-bit average battery current 100 mA
        BBValue("H", "avg_battery_current_A", cnv.cnv_100mA_to_A),
        # bytes 13+ 11-12: 16-bit battery SOC 100 mAh
        BBValue("H", "battery_state_of_charge_A", cnv.cnv_mA_to_A),
        # bytes 26-35: reserved
        BBValueIgnore(10),
        # byte 36: 8-bit frame type 0x01
        BBValueIgnore(),
    ],
    postprocess=add_reverse_day_counter,
)

LogEntryFrameNew = BBFrame(
    output_id="log/day/-{days_ago}/extended",
    fields=[
        # bytes 0-1: 16-bit day counter (relative to current day in frame type 0x00)
        BBValue("H", "day_counter"),
        # bytes 2-3: 16-bit wall time in seconds/2
        BBValue("H", "wall_time", lambda value: value * 2),
        # bytes 4-5: 16-bit average battery voltage mV
        BBValue("H", "avg_battery_voltage_V", cnv.cnv_mV_to_V),
        # bytes 6-7: 16-bit average solar current mA
        BBValue("H", "avg_solar_current_A", cnv.cnv_mA_to_A),
        # bytes 8: solar charger status: aktiv, standby, reduced
        BBValue("B", "solar_charger_status", cnv.cnv_solar_status),
        # bytes 9-10: 16-bit average battery current 100 mA
        BBValue("H", "avg_battery_current_A", cnv.cnv_100mA_to_A),
        # bytes 11-12: 16-bit battery SOC 100 mAh
        BBValue("H", "battery_state_of_charge_A", cnv.cnv_mA_to_A),
        # bytes 13-14: 16-bit booster average input voltage 10mV (starter)**
        BBValue("H", "avg_booster_input_voltage_V", cnv.cnv_10mV_to_V),
        # bytes 15-16: signed 16-bit booster average current 100 mA**
        BBValue("h", "avg_booster_current_A", cnv.cnv_100mA_to_A),
        # bytes 17+ 0-1: 16-bit day counter (relative to current day in frame type 0x00)
        BBValue("H", "day_counter"),
        # bytes 17+ 2-3: 16-bit wall time in seconds/2
        BBValue("H", "wall_time", lambda value: value * 2),
        # bytes 17+ 4-5: 16-bit average battery voltage mV
        BBValue("H", "avg_battery_voltage_V", cnv.cnv_mV_to_V),
        # bytes 17+ 6-7: 16-bit average solar current mA
        BBValue("H", "avg_solar_current_A", cnv.cnv_mA_to_A),
        # bytes 17+ 8: solar charger status: aktiv, standby, reduced
        BBValue("B", "solar_charger_status", cnv.cnv_solar_status),
        # bytes 17+ 9-10: 16-bit average battery current 100 mA
        BBValue("H", "avg_battery_current_A", cnv.cnv_100mA_to_A),
        # bytes 17+ 11-12: 16-bit battery SOC 100 mAh
        BBValue("H", "battery_state_of_charge_A", cnv.cnv_mA_to_A),
        # bytes 17+ 13-14: 16-bit booster average input voltage 10mV (starter)**
        BBValue("H", "avg_booster_input_voltage_V", cnv.cnv_10mV_to_V),
        # bytes 17+ 15-16: signed 16-bit booster average current 100 mA**
        BBValue("h", "avg_booster_current_A", cnv.cnv_100mA_to_A),
        # bytes 34-35: reserved
        BBValueIgnore(2),
        # byte 36: 8-bit frame type 0x01
        BBValueIgnore(),
    ],
    postprocess=add_reverse_day_counter,
)

LogEntryFrameLargeSolarCurrent = BBFrame(
    output_id="log/day/-{days_ago}/extended",
    fields=[
        # bytes 0-1: 16-bit day counter (relative to current day in frame type 0x00)
        BBValue("H", "day_counter"),
        # bytes 2-3: 16-bit wall time in seconds/2
        BBValue("H", "wall_time", lambda value: value * 2),
        # bytes 4-5: 16-bit average battery voltage mV
        BBValue("H", "avg_battery_voltage_V", cnv.cnv_mV_to_V),
        # bytes 6-7: 16-bit average solar current mA
        BBValue("H", "avg_solar_current_A", cnv.cnv_8mA_to_A),  # type 3
        # bytes 8: solar charger status: aktiv, standby, reduced
        BBValue("B", "solar_charger_status", cnv.cnv_solar_status),
        # bytes 9-10: 16-bit average battery current 100 mA
        BBValue("H", "avg_battery_current_A", cnv.cnv_100mA_to_A),
        # bytes 11-12: 16-bit battery SOC 100 mAh
        BBValue("H", "battery_state_of_charge_A", cnv.cnv_mA_to_A),
        # bytes 13-14: 16-bit booster average input voltage 10mV (starter)**
        BBValue("H", "avg_booster_input_voltage_V", cnv.cnv_10mV_to_V),
        # bytes 15-16: signed 16-bit booster average current 100 mA**
        BBValue("h", "avg_booster_current_A", cnv.cnv_100mA_to_A),
        # bytes 17+ 0-1: 16-bit day counter (relative to current day in frame type 0x00)
        BBValue("H", "day_counter"),
        # bytes 17+ 2-3: 16-bit wall time in seconds/2
        BBValue("H", "wall_time", lambda value: value * 2),
        # bytes 17+ 4-5: 16-bit average battery voltage mV
        BBValue("H", "avg_battery_voltage_V", cnv.cnv_mV_to_V),
        # bytes 17+ 6-7: 16-bit average solar current mA
        BBValue("H", "avg_solar_current_A", cnv.cnv_8mA_to_A),  # type 3
        # bytes 17+ 8: solar charger status: aktiv, standby, reduced
        BBValue("B", "solar_charger_status", cnv.cnv_solar_status),
        # bytes 17+ 9-10: 16-bit average battery current 100 mA
        BBValue("H", "avg_battery_current_A", cnv.cnv_100mA_to_A),
        # bytes 17+ 11-12: 16-bit battery SOC 100 mAh
        BBValue("H", "battery_state_of_charge_A", cnv.cnv_mA_to_A),
        # bytes 17+ 13-14: 16-bit booster average input voltage 10mV (starter)**
        BBValue("H", "avg_booster_input_voltage_V", cnv.cnv_10mV_to_V),
        # bytes 17+ 15-16: signed 16-bit booster average current 100 mA**
        BBValue("h", "avg_booster_current_A", cnv.cnv_100mA_to_A),
        # bytes 34-35: reserved
        BBValueIgnore(2),
        # byte 36: 8-bit frame type 0x01
        BBValueIgnore(),
    ],
    postprocess=add_reverse_day_counter,
)


BCLiveMeasurementsFrame = BBFrame(
    output_id="live/measurement",
    fields=[
        # byte 0: type
        # byte 1: length
        BBValueIgnore(2),
        # 2 bytes (17) value battery voltage in mV
        BBValue(
            "H",
            "battery_voltage_V",
            cnv.cnv_mV_to_V,
            ha_details={
                "platform": "sensor",
                "name": "Battery Voltage",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "suggested_display_precision": 2,
                "state_class": "measurement",
            },
        ),
        # 2 bytes (18) value solar charge current in mA**
        BBValue(
            "H",
            "solar_charge_current_A",
            cnv.cnv_mA_to_A,
            ha_details={
                "platform": "sensor",
                "name": "Solar Charge Current",
                "device_class": "current",
                "unit_of_measurement": "A",
                "suggested_display_precision": 2,
                "state_class": "measurement",
            },
        ),
        # 3 bytes (00) value Battery Current in mA
        BBValue(
            "¾",
            "battery_current_A",
            cnv.cnv_mA_to_A,
            ha_details={
                "platform": "sensor",
                "name": "Battery Current",
                "device_class": "current",
                "unit_of_measurement": "A",
                "suggested_display_precision": 2,
                "state_class": "measurement",
            },
        ),
    ],
)

BCLiveMeasurementsFrameExtended = BBFrame(
    output_id="live/measurement",
    fields=BCLiveMeasurementsFrame.fields
    + [
        # 2 bytes optional heap size in bytes
        BBValue("H", "heap_size_bytes"),
    ],
)


def accumulateSameFieldNames(raw_values):
    """
    post processing function to add fields with the same output_id
    used for adding an extra MSB field for an existing field
    """
    output = []
    for field, raw_value in raw_values:
        found = False
        for i, (existing_field, existing_raw_value) in enumerate(output):
            if existing_field.output_id == field.output_id:
                value = field.value(raw_value)
                output[i] = (existing_field, existing_raw_value + value)
                found = True
                break
        if not found:
            output.append((field, raw_value))
    return output


BCLiveMeasurementsFrameLargeSolarCurrent = BBFrame(
    output_id="live/measurement",
    fields=BCLiveMeasurementsFrameExtended.fields
    + [
        # 1 byte MSB solar charge current
        BBValue("B", "solar_charge_current_A", lambda x: x << 16),
    ],
    preprocess=accumulateSameFieldNames,
)

BCSolarChargerEBLFrame = BBFrame(
    output_id="live/solar_charger_ebl",
    fields=[
        # byte 0: type
        # byte 1: length
        BBValueIgnore(2),
        # 2 bytes (09) value Solar max Current per day in mA
        BBValue(
            "H",
            "max_solar_current_day_A",
            cnv.cnv_mA_to_A,
            ha_details={
                "platform": "sensor",
                "name": "Max Solar Current Today (EBL)",
                "device_class": "current",
                "unit_of_measurement": "A",
                "suggested_display_precision": 2,
                "enabled_by_default": False,
            },
        ),
        # 2 bytes (10) value Solar max Watt per day in 1W  use 95% efficiency
        BBValue(
            "H",
            "max_solar_watt_day_W",
            lambda value: value / 0.95,
            ha_details={
                "platform": "sensor",
                "name": "Max Solar Power Today (EBL)",
                "device_class": "power",
                "unit_of_measurement": "W",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
            },
        ),
        # 2 bytes (19) value solar charge in 10mAh (*)
        BBValue(
            "H",
            "solar_charge_day_Ah",
            cnv.cnv_10mAh_to_Ah,
            ha_details={
                "platform": "sensor",
                "name": "Solar Charge Today (EBL)",
                "unit_of_measurement": "Ah",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
                "state_class": "total_increasing",
            },
        ),
        # 2 bytes (20) value solar energy in Wh
        BBValue(
            "H",
            "solar_energy_day_Wh",
            ha_details={
                "platform": "sensor",
                "name": "Solar Energy Today (EBL)",
                "device_class": "energy",
                "unit_of_measurement": "Wh",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
                "state_class": "total_increasing",
            },
        ),
        # 1 byte (21) status solar charger (*) bit 7 indicates sleep
        BBValue(
            "B",
            "solar_charger_status",
            ha_details={
                "platform": "sensor",
                "name": "Solar Charger Status (EBL)",
                "enabled_by_default": False,
            },
        ),
    ],
)

BCSolarChargerStandardFrame = BBFrame(
    output_id="live/solar_charger",
    fields=BCSolarChargerEBLFrame.fields
    + [
        # 2 bytes (22) value solar PV module voltage in 10 mV (*)
        BBValue(
            "H",
            "solar_module_voltage_V",
            cnv.cnv_10mV_to_V,
            ha_details={
                "platform": "sensor",
                "name": "Solar Module Voltage",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "suggested_display_precision": 2,
                "enabled_by_default": False,
                "state_class": "measurement",
            },
        ),
    ],
)


class RelayStatus(Flags):
    enabled = ()
    trigger_soc = ()
    trigger_board_voltage = ()
    trigger_starter_voltage = ()
    trigger_temperature = ()
    trigger_solar_current = ()
    trigger_time = ()
    reserved = ()

    # def __str__(self):
    #    active_flags = [name for name, active in self.__dir__.items() if active and name != "reserved"]
    #    return ",".join(active_flags) if active_flags else "off"


BCSolarChargerExtendedFrame = BBFrame(
    output_id="live/solar_charger_ext",
    fields=BCSolarChargerStandardFrame.fields
    + [
        # 1 byte  Relais Status (BB-X >= V407)
        #  bit 0: 0:off / 1:on
        #  bit 1: 1:SOC
        #  bit 2: 1:Board Voltage
        #  bit 3: 1:Starter Voltage
        #  bit 4: 1:Temperature
        #  bit 5: 1:Solar Current
        #  bit 6: 1:Time
        #  bit 7: reserved
        BBValue("B", "relay_status", RelayStatus),
    ],
)

BCSolarChargerLargeSolarCurrent = BBFrame(
    output_id="live/solar_charger_ext",
    fields=BCSolarChargerExtendedFrame.fields
    + [
        # 1 byte phase bits [0:3]: onyl valid when (status solar charger & 0x18 > 0)
        #     0: Bulk
        #     1: Absorption
        #     2: Float
        #     3: Care
        BBValue(
            "B",
            "solar_charger_phase",
            ha_details={
                "platform": "sensor",
                "name": "Solar Charger Phase",
                "enabled_by_default": False,
            },
        ),
        # 1 byte (09) MSB [23:16] solar max current per day (>= V418)
        BBValue(
            "B",
            "max_solar_current_day_A",
            lambda x: x << 16,
            ha_details={
                "platform": "sensor",
                "name": "Max Solar Current Today",
                "device_class": "current",
                "unit_of_measurement": "A",
                "suggested_display_precision": 2,
                "enabled_by_default": False,
            },
        ),
        # 1 byte (19) MSB [23:16] solar charge (>= V418)
        BBValue(
            "B",
            "solar_charge_day_Ah",
            lambda x: x << 16,
            ha_details={
                "platform": "sensor",
                "name": "Solar Charge Today",
                "unit_of_measurement": "Ah",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
                "state_class": "total_increasing",
            },
        ),
    ],
    preprocess=accumulateSameFieldNames,
)

BCBatteryComputer1Frame = BBFrame(
    output_id="live/battery_comp_1",
    fields=[
        # byte 0: type
        # byte 1: length
        BBValueIgnore(2),
        # 2 bytes (01) value Battery Charge in 10mAh (*)
        BBValue(
            "H",
            "battery_charge_Ah",
            cnv.cnv_10mAh_to_Ah,
            ha_details={
                "platform": "sensor",
                "name": "Battery Charge",
                "unit_of_measurement": "Ah",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
                "state_class": "measurement",
            },
        ),
        # 2 bytes (02) value SOC in 0.1% steps
        BBValue(
            "H",
            "state_of_charge_percent",
            lambda x: x / 10,
            ha_details={
                "platform": "sensor",
                "name": "State of Charge",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "suggested_display_precision": 0,
                "state_class": "measurement",
            },
        ),
        # 2 bytes (03) value Battery max Current per day in 10mA (*)
        BBValue(
            "H",
            "max_battery_current_day_A",
            cnv.cnv_10mA_to_A,
            ha_details={
                "platform": "sensor",
                "name": "Max Battery Current Today",
                "device_class": "current",
                "unit_of_measurement": "A",
                "suggested_display_precision": 2,
                "enabled_by_default": False,
            },
        ),
        # 2 bytes (04) value Battery min Current per day in 10mA (*)
        BBValue(
            "H",
            "min_battery_current_day_A",
            lambda x: x / -10,
            ha_details={
                "platform": "sensor",
                "name": "Min Battery Current Today",
                "device_class": "current",
                "unit_of_measurement": "A",
                "suggested_display_precision": 2,
                "enabled_by_default": False,
            },
        ),
        # 2 bytes (05) value Battery max Charge per day in 10mAh
        BBValue(
            "H",
            "max_battery_charge_day_Ah",
            cnv.cnv_10mAh_to_Ah,
            ha_details={
                "platform": "sensor",
                "name": "Max Battery Charge Today",
                "unit_of_measurement": "Ah",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
            },
        ),
        # 2 bytes (06) value Battery min Charge per day in 10mAh
        BBValue(
            "H",
            "min_battery_charge_day_Ah",
            cnv.cnv_10mAh_to_Ah,
            ha_details={
                "platform": "sensor",
                "name": "Min Battery Charge Today",
                "unit_of_measurement": "Ah",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
            },
        ),
        # 2 bytes (07) value Battery max Voltage per day in mV
        BBValue(
            "H",
            "max_battery_voltage_day_V",
            cnv.cnv_mV_to_V,
            ha_details={
                "platform": "sensor",
                "name": "Max Battery Voltage Today",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "suggested_display_precision": 2,
                "enabled_by_default": False,
            },
        ),
        # 2 bytes (08) value Battery min Voltage per day in mV
        BBValue(
            "H",
            "min_battery_voltage_day_V",
            cnv.cnv_mV_to_V,
            ha_details={
                "platform": "sensor",
                "name": "Min Battery Voltage Today",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "suggested_display_precision": 2,
                "enabled_by_default": False,
            },
        ),
    ],
)

BCBatteryComputer2Frame = BBFrame(
    output_id="live/battery_comp_2",
    fields=[
        # byte 0: type
        # byte 1: length
        BBValueIgnore(2),
        # 2 bytes (11) value Temperature in °C binary offset
        BBValue(
            "H",
            "temperature_deg_C",
            cnv.cnv_bb_temp_to_deg_c,
            ha_details={
                "platform": "sensor",
                "name": "Battery Temperature",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "suggested_display_precision": 1,
                "state_class": "measurement",
            },
        ),
        # 2 bytes (12) value min Temperature per day in °C binary offset
        BBValue(
            "H",
            "min_temperature_deg_C",
            cnv.cnv_bb_temp_to_deg_c,
            ha_details={
                "platform": "sensor",
                "name": "Min Temperature Today",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "suggested_display_precision": 1,
                "enabled_by_default": False,
            },
        ),
        # 2 bytes (13) value max Temperature per day in °C binary offset
        BBValue(
            "H",
            "max_temperature_deg_C",
            cnv.cnv_bb_temp_to_deg_c,
            ha_details={
                "platform": "sensor",
                "name": "Max Temperature Today",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "suggested_display_precision": 1,
                "enabled_by_default": False,
            },
        ),
        # 3 bytes (14) value summed total charge per day in 32/225 mAh (*)
        # TODO: unsigned
        BBValue(
            "¾",
            "total_charge_day_Ah",
            lambda x: (x * (32 / 225)) / 1000,
            ha_details={
                "platform": "sensor",
                "name": "Total Charge Today",
                "unit_of_measurement": "Ah",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
                "state_class": "total_increasing",
            },
        ),
        # 3 bytes (15) value summed total discharge per day in 32/225 mAh (*)
        # TODO: unsigned
        BBValue(
            "¾",
            "total_discharge_day_Ah",
            lambda x: (x * (32 / 225)) / 1000,
            ha_details={
                "platform": "sensor",
                "name": "Total Discharge Today",
                "unit_of_measurement": "Ah",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
                "state_class": "total_increasing",
            },
        ),
        # 3 bytes (16) value summed total external charge per in 32/225 mAh (*)
        # TODO: unsigned
        BBValue(
            "¾",
            "total_external_charge_day_Ah",
            lambda x: (x * (32 / 225)) / 1000,
            ha_details={
                "platform": "sensor",
                "name": "Total External Charge Today",
                "unit_of_measurement": "Ah",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
                "state_class": "total_increasing",
            },
        ),
    ],
)

BCIntradayLogEntryFrame = BBFrame(
    output_id="live/intraday_log",
    fields=[
        # byte 0: type
        # byte 1: length
        BBValueIgnore(2),
        # byte 2: record #
        BBValue("B", "record_number"),
    ],
)

BCIntradayLogEntryFrameExtended = BBFrame(
    output_id="live/intraday_log",
    fields=BCIntradayLogEntryFrame.fields
    + [
        BBValue("B", "log_type"),
    ],
)

BCNoBoosterDataFrame = BBFrame(
    output_id="live/info",
    fields=[
        # byte 0: type
        # byte 1: length
        BBValueIgnore(2),
        # 2 bytes value output voltage in 10 mV (Board Battery)**
        BBValue(
            "H",
            "battery_voltage_V",
            cnv.cnv_10mV_to_V,
            ha_details={
                "platform": "sensor",
                "name": "Battery Voltage",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "suggested_display_precision": 2,
                "state_class": "measurement",
            },
        ),
        # 2 bytes value input voltage in 10 mV (Starter Battery)**
        BBValue(
            "H",
            "starter_battery_voltage_V",
            cnv.cnv_10mV_to_V,
            ha_details={
                "platform": "sensor",
                "name": "Starter Battery Voltage",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "suggested_display_precision": 2,
                "state_class": "measurement",
            },
        ),
    ],
)

BCBoosterDataFrame = BBFrame(
    output_id="live/booster",
    fields=BCNoBoosterDataFrame.fields
    + [
        # 2 bytes signed value charge current in 100 mA (Booster current)
        BBValue(
            "H",
            "booster_charge_current_A",
            cnv.cnv_100mA_to_A,
            ha_details={
                "platform": "sensor",
                "name": "Booster Charge Current",
                "device_class": "current",
                "unit_of_measurement": "A",
                "suggested_display_precision": 2,
                "state_class": "measurement",
            },
        ),
        # 1 byte status booster
        BBValue(
            "B",
            "booster_status",
            ha_details={
                "platform": "sensor",
                "name": "Booster Status",
                "enabled_by_default": False,
            },
        ),
        # 3 bytes value summed total booster charge per day in 256/18000 Ah
        # TODO: unsigned
        BBValue(
            "¾",
            "total_booster_charge_day_Ah",
            lambda x: x * (256 / 18000),
            ha_details={
                "platform": "sensor",
                "name": "Total Booster Charge Today",
                "unit_of_measurement": "Ah",
                "suggested_display_precision": 0,
                "enabled_by_default": False,
                "state_class": "total_increasing",
            },
        ),
    ],
)

BCBoosterDataFrameExtended = BBFrame(
    output_id="live/booster",
    fields=BCBoosterDataFrame.fields
    + [
        # 1 byte limit mode: 0x00: unknown, 0x01: off, 0x02: on
        BBValue(
            "B",
            "booster_limit",
            ha_details={
                "platform": "sensor",
                "name": "Booster Limit Mode",
                "enabled_by_default": False,
            },
        ),
        # 1 byte phase bits [0:3]: only valid when (status booster & 0xc0 > 0)
        #    0: Bulk
        #    1: Absorption
        #    2: Float
        #    3: Care
        BBValue(
            "B",
            "booster_phase",
            cnv.cnv_charger_phase,
            ha_details={
                "platform": "sensor",
                "name": "Booster Phase",
                "enabled_by_default": False,
            },
        ),
    ],
)

BCBoosterDataFrameExtendedBBX = BBFrame(
    output_id="live/booster",
    fields=BCBoosterDataFrameExtended.fields
    + [
        # 2 bytes value analog board voltage***
        BBValue(
            "H",
            "analog_board_voltage_V",
            cnv.cnv_mV_to_V,
            ha_details={
                "platform": "sensor",
                "name": "Analog Board Voltage",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "suggested_display_precision": 2,
                "enabled_by_default": False,
                "state_class": "measurement",
            },
        ),
        # 2 bytes value analog starter voltage***
        BBValue(
            "H",
            "analog_starter_voltage_V",
            cnv.cnv_mV_to_V,
            ha_details={
                "platform": "sensor",
                "name": "Analog Starter Voltage",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "suggested_display_precision": 2,
                "enabled_by_default": False,
                "state_class": "measurement",
            },
        ),
    ],
)

ALL_FRAME_TYPES = [
    SecFrame,
    LogEntryDaysFrame,
    LogEntryFrameOld,
    LogEntryFrameNew,
    LogEntryFrameLargeSolarCurrent,
    BCLiveMeasurementsFrame,
    BCLiveMeasurementsFrameExtended,
    BCLiveMeasurementsFrameLargeSolarCurrent,
    BCSolarChargerEBLFrame,
    BCSolarChargerStandardFrame,
    BCSolarChargerExtendedFrame,
    BCSolarChargerLargeSolarCurrent,
    BCBatteryComputer1Frame,
    BCBatteryComputer2Frame,
    BCIntradayLogEntryFrame,
    BCIntradayLogEntryFrameExtended,
    BCNoBoosterDataFrame,
    BCBoosterDataFrame,
    BCBoosterDataFrameExtended,
    BCBoosterDataFrameExtendedBBX,
]
