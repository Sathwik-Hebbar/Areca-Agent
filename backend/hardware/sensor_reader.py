import logging
import threading
from backend.config import settings

logger = logging.getLogger(__name__)

# Module-level lock around serial communication to prevent concurrent port collisions
SERIAL_LOCK = threading.Lock()

# Modbus register addresses for RS485 soil sensor
# Based on QModMaster reference: FC03 holding registers
REG_NITROGEN = 0x3002     # Register 12290
REG_PHOSPHORUS = 0x3003   # Register 12291
REG_POTASSIUM = 0x3004    # Register 12292
NUM_REGISTERS = 3


def read_npk() -> dict:
    """
    Reads Nitrogen, Phosphorus, Potassium holding registers from the soil sensor
    over USB-to-RS485 Modbus RTU in ONE read_registers call.

    IMPORTANT NOTE ON CALIBRATION:
    - All values are reported in UNCALIBRATED prototype units (not calibrated mg/kg or ppm).
    - Phosphorus formula (4093 - raw) is an unverified empirical fit.
    - Raw values 0 and 65535 indicate probe disconnection or wiring faults.
    - If raw_phosphorus > 4093, it is rejected as invalid_reading to prevent database CHECK violation.

    Returns:
        dict with status: 'ok' | 'sensor_unavailable' | 'busy' | 'invalid_reading'
    """
    # Non-blocking lock acquisition: return 'busy' immediately rather than queuing indefinitely
    if not SERIAL_LOCK.acquire(blocking=False):
        logger.info("Soil sensor serial port is currently busy; returning status 'busy'.")
        return {
            "status": "busy",
            "message": "Soil sensor is currently in use by another read operation.",
            "unit": "uncalibrated prototype units",
            "calibration_status": "uncalibrated",
        }

    try:
        import minimalmodbus
        import serial

        port = settings.SENSOR_COM_PORT
        baud = settings.SENSOR_BAUD_RATE
        slave_id = settings.SENSOR_SLAVE_ID
        timeout = settings.SENSOR_TIMEOUT_SECONDS

        instrument = minimalmodbus.Instrument(port, slave_id)
        instrument.serial.baudrate = baud
        instrument.serial.bytesize = 8
        instrument.serial.parity = serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout = timeout
        instrument.mode = minimalmodbus.MODE_RTU
        instrument.clear_buffers_before_each_transaction = True
        instrument.close_port_after_each_call = True

        # Read registers 0x3002 - 0x3004 in a single Modbus FC03 transaction
        registers = instrument.read_registers(REG_NITROGEN, NUM_REGISTERS, functioncode=3)

        raw_n = int(registers[0])
        raw_p = int(registers[1])
        raw_k = int(registers[2])

        # Baseline check when probe is not inserted in soil (air reading):
        # When all three conditions satisfy simultaneously (raw_n=3, raw_p=4093, raw_k=0),
        # the probe is idle in air and must never be persisted as a soil reading.
        if raw_n == 3 and raw_p == 4093 and raw_k == 0:
            logger.info("Soil probe idle in air (raw N=3, P=4093, K=0); reporting baseline N=0, P=0, K=0.")
            return {
                "status": "no_soil_detected",
                "nitrogen": 0.0,
                "phosphorus": 0.0,
                "potassium": 0.0,
                "raw_nitrogen": raw_n,
                "raw_phosphorus": raw_p,
                "raw_potassium": raw_k,
                "unit": "uncalibrated prototype units",
                "calibration_status": "uncalibrated",
                "message": "No soil detected. Insert the probe into soil.",
            }

        # Validate against open-circuit / disconnection / probe fault codes
        if raw_n in (0, 65535) or raw_p in (0, 65535) or raw_k in (0, 65535):
            logger.warning(
                f"Invalid soil sensor telemetry (wiring/probe fault): N={raw_n}, P={raw_p}, K={raw_k}"
            )
            return {
                "status": "invalid_reading",
                "message": f"Wiring or probe fault detected (open circuit / null reading: N={raw_n}, P={raw_p}, K={raw_k}).",
                "raw_nitrogen": raw_n,
                "raw_phosphorus": raw_p,
                "raw_potassium": raw_k,
                "unit": "uncalibrated prototype units",
                "calibration_status": "uncalibrated",
            }

        # Validate empirical Phosphorus bound: (4093 - raw_p) must be >= 0
        if raw_p > 4093:
            logger.warning(
                f"Invalid soil sensor telemetry: raw_phosphorus {raw_p} > 4093 exceeds empirical maximum."
            )
            return {
                "status": "invalid_reading",
                "message": f"Phosphorus raw register value {raw_p} exceeds empirical maximum 4093.",
                "raw_nitrogen": raw_n,
                "raw_phosphorus": raw_p,
                "raw_potassium": raw_k,
                "unit": "uncalibrated prototype units",
                "calibration_status": "uncalibrated",
            }

        # Apply empirical formulas (UNCALIBRATED prototype units)
        derived_n = round(float(raw_n), 2)
        derived_p = round(float(4093 - raw_p), 2)
        derived_k = round(float(raw_k), 2)

        return {
            "status": "ok",
            "nitrogen": derived_n,
            "phosphorus": derived_p,
            "potassium": derived_k,
            "raw_nitrogen": raw_n,
            "raw_phosphorus": raw_p,
            "raw_potassium": raw_k,
            "unit": "uncalibrated prototype units",
            "calibration_status": "uncalibrated",
            "message": "Soil NPK reading acquired successfully (uncalibrated prototype units).",
        }

    except Exception as e:
        logger.warning(f"Soil sensor unavailable on port {settings.SENSOR_COM_PORT}: {e}")
        return {
            "status": "sensor_unavailable",
            "message": f"Soil sensor unavailable on {settings.SENSOR_COM_PORT}: {str(e)}",
            "unit": "uncalibrated prototype units",
            "calibration_status": "uncalibrated",
        }
    finally:
        SERIAL_LOCK.release()
