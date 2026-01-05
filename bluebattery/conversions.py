def cnv_mV_to_V(mV):
    return mV / 1000


cnv_mW_to_W = cnv_mV_to_V


def cnv_10mV_to_V(_10mV):
    return _10mV / 100


cnv_10mA_to_A = cnv_10mV_to_V


def cnv_10mAh_to_Ah(_10mAh):
    return _10mAh / 100


def cnv_mA_to_A(mA):
    return mA / 1000


def cnv_8mA_to_A(_8mA):
    return _8mA / 125


def cnv_100mA_to_A(_100mA):
    return _100mA / 10


cnv_100mV_to_V = cnv_100mA_to_A


def cnv_neg_100mA_to_A(_100mA):
    return -_100mA / 10


def cnv_bb_temp_to_deg_c(bb_temp):
    return (bb_temp - 0x8000) / 100


def cnv_solar_status(status):
    return {0: "active", 1: "standby", 2: "reduced"}.get(status, "unknown")


def cnv_charger_phase(phase):
    return {0: "bulk", 1: "absorption", 2: "float", 3: "care"}.get(
        phase & 0x0F, "unknown"
    )
