"""
Physics Utility Functions for Mining Equipment Simulation

This module provides physics-based calculations for realistic mining equipment behavior.
Compatible with Jython 2.7 (Ignition Gateway environment).

Usage:
    from physics_utils import calculate_fuel_consumption, calculate_engine_temp

    fuel_rate = calculate_fuel_consumption(speed=50, load=250, engine_rpm=1800)
    temp = calculate_engine_temp(load=250, ambient=30, speed=50)
"""

import random
from java.lang import Math

# ============================================
# PHYSICAL CONSTANTS
# ============================================

# Haul Truck Specifications (based on CAT 797F)
HAUL_TRUCK_MAX_LOAD_TONNES = 250.0
HAUL_TRUCK_EMPTY_WEIGHT_TONNES = 145.0
HAUL_TRUCK_MAX_SPEED_LOADED_KPH = 35.0
HAUL_TRUCK_MAX_SPEED_EMPTY_KPH = 65.0
HAUL_TRUCK_FUEL_TANK_LITERS = 6000.0
HAUL_TRUCK_ENGINE_POWER_KW = 2610.0

# Crusher Specifications (based on Metso C160)
CRUSHER_NOMINAL_THROUGHPUT_TPH = 2400.0
CRUSHER_MAX_THROUGHPUT_TPH = 3000.0
CRUSHER_NOMINAL_VIBRATION_MM_S = 20.0
CRUSHER_NOMINAL_MOTOR_CURRENT_A = 200.0
CRUSHER_MOTOR_POWER_KW = 160.0

# Conveyor Specifications
CONVEYOR_NOMINAL_SPEED_M_S = 2.5
CONVEYOR_MAX_LOAD_PCT = 100.0
CONVEYOR_MOTOR_POWER_KW = 45.0

# Environmental Constants
AMBIENT_TEMP_MIN_C = 25.0
AMBIENT_TEMP_MAX_C = 40.0
DUST_BASE_LEVEL_UG_M3 = 15.0
NOISE_BASE_LEVEL_DB = 85.0

# Cycle Timing (seconds)
HAUL_TRUCK_CYCLE_TOTAL_SEC = 1380  # 23 minutes
HAUL_TRUCK_LOADING_SEC = 300       # 5 minutes
HAUL_TRUCK_HAULING_SEC = 480       # 8 minutes
HAUL_TRUCK_DUMPING_SEC = 180       # 3 minutes
HAUL_TRUCK_RETURNING_SEC = 420     # 7 minutes

# GPS Coordinates (West Australia mining site)
GPS_BASE_LAT = -31.9505
GPS_BASE_LON = 115.8605
GPS_SITE_RADIUS_KM = 5.0

# ============================================
# NOISE GENERATION
# ============================================

def generate_noise(amplitude, distribution='uniform'):
    """
    Generate realistic sensor noise

    Args:
        amplitude (float): Maximum deviation from nominal
        distribution (str): 'uniform' or 'gaussian'

    Returns:
        float: Noise value
    """
    if distribution == 'gaussian':
        # Gaussian noise (mean=0, std=amplitude/3 for ~99.7% within range)
        return random.gauss(0, amplitude / 3.0)
    else:
        # Uniform noise
        return random.uniform(-amplitude, amplitude)


def smooth_transition(current, target, step_size=0.1):
    """
    Smooth transition from current to target value

    Args:
        current (float): Current value
        target (float): Target value
        step_size (float): Step size (0-1, smaller = smoother)

    Returns:
        float: New value closer to target
    """
    return current * (1.0 - step_size) + target * step_size


# ============================================
# HAUL TRUCK PHYSICS
# ============================================

def calculate_fuel_consumption(speed, load, engine_rpm=1800, terrain_grade=0):
    """
    Calculate fuel consumption rate for haul truck

    Physics:
    - Base consumption proportional to engine RPM
    - Speed increases consumption (air resistance ~ v^2)
    - Load increases consumption (gravitational work)
    - Terrain grade affects consumption (uphill = more fuel)

    Args:
        speed (float): Speed in km/h
        load (float): Load in tonnes
        engine_rpm (int): Engine RPM (default 1800)
        terrain_grade (float): Grade in % (positive = uphill)

    Returns:
        float: Fuel consumption rate in % per second
    """
    # Base consumption (engine running, stationary)
    base_rate = 0.015  # 0.015% per second (~90L/hour at idle)

    # Speed component (air resistance increases with v^2)
    speed_factor = (speed / 50.0) ** 2 * 0.03

    # Load component (more weight = more fuel)
    load_factor = (load / HAUL_TRUCK_MAX_LOAD_TONNES) * 0.04

    # RPM component (higher RPM = more fuel)
    rpm_factor = (engine_rpm / 1800.0 - 1.0) * 0.01

    # Terrain component (uphill = significantly more fuel)
    terrain_factor = terrain_grade * 0.002

    total_rate = base_rate + speed_factor + load_factor + rpm_factor + terrain_factor

    # Add realistic noise (±5%)
    noise = generate_noise(total_rate * 0.05)

    return max(0.01, total_rate + noise)


def calculate_engine_temp(load, ambient_temp, speed, coolant_flow=1.0):
    """
    Calculate engine coolant temperature

    Physics:
    - Base temperature = ambient + 40°C (engine operating temp)
    - Load increases heat generation
    - Speed increases cooling (airflow)
    - Coolant flow affects heat transfer

    Args:
        load (float): Load in tonnes
        ambient_temp (float): Ambient temperature in °C
        speed (float): Speed in km/h
        coolant_flow (float): Coolant flow rate (0-1, default 1.0)

    Returns:
        float: Engine temperature in °C
    """
    # Base operating temperature (thermal equilibrium at idle)
    base_temp = ambient_temp + 40.0

    # Load heating (more work = more heat)
    load_heating = (load / HAUL_TRUCK_MAX_LOAD_TONNES) * 25.0

    # Speed cooling (airflow through radiator)
    speed_cooling = -(speed / 50.0) * 8.0

    # Coolant effectiveness
    coolant_effectiveness = coolant_flow * 1.0

    # Calculate final temperature
    temp = base_temp + load_heating + speed_cooling / coolant_effectiveness

    # Add thermal noise (±2°C)
    noise = generate_noise(2.0)

    # Clamp to reasonable range
    return max(60.0, min(120.0, temp + noise))


def calculate_vibration(speed, load, road_condition=1.0, suspension_health=1.0):
    """
    Calculate chassis vibration

    Physics:
    - Base vibration from engine/drivetrain
    - Speed increases vibration (road irregularities)
    - Load affects suspension compression
    - Suspension health affects damping

    Args:
        speed (float): Speed in km/h
        load (float): Load in tonnes
        road_condition (float): Road quality (0-1, 1=perfect)
        suspension_health (float): Suspension condition (0-1, 1=perfect)

    Returns:
        float: Vibration in mm/s
    """
    # Base vibration (engine running, stationary)
    base_vibration = 2.0

    # Speed component (road irregularities scale with speed)
    speed_vibration = (speed / 15.0) * (2.0 - road_condition)

    # Load component (heavy load = more vibration)
    load_vibration = (load / HAUL_TRUCK_MAX_LOAD_TONNES) * 1.5

    # Suspension damping (poor suspension = more vibration)
    suspension_factor = 1.0 / max(0.5, suspension_health)

    total_vibration = (base_vibration + speed_vibration + load_vibration) * suspension_factor

    # Add noise (±15%)
    noise = generate_noise(total_vibration * 0.15)

    return max(0.5, total_vibration + noise)


def calculate_gps_position(cycle_time, base_lat=GPS_BASE_LAT, base_lon=GPS_BASE_LON):
    """
    Calculate GPS position based on haul cycle

    Simulates a realistic haul path:
    - Loading area: North side of site
    - Dump area: South side of site
    - Path: Elliptical route

    Args:
        cycle_time (int): Current cycle time in seconds
        base_lat (float): Base latitude
        base_lon (float): Base longitude

    Returns:
        tuple: (latitude, longitude)
    """
    # Normalize cycle time to 0-1
    cycle_progress = float(cycle_time) / HAUL_TRUCK_CYCLE_TOTAL_SEC

    # Elliptical path (north-south movement)
    angle = cycle_progress * 2.0 * Math.PI

    # Latitude oscillates (north-south)
    # 0.02 degrees ≈ 2.2 km movement
    lat_offset = 0.01 * Math.sin(angle)

    # Longitude oscillates (east-west, smaller movement)
    lon_offset = 0.005 * Math.cos(angle)

    # Add small random wander (GPS accuracy ±10m)
    lat_noise = generate_noise(0.0001, 'gaussian')
    lon_noise = generate_noise(0.0001, 'gaussian')

    latitude = base_lat + lat_offset + lat_noise
    longitude = base_lon + lon_offset + lon_noise

    return (latitude, longitude)


def calculate_tire_pressure(nominal_psi=100.0, temperature=30.0, age_factor=1.0):
    """
    Calculate tire pressure with temperature and aging effects

    Physics:
    - Pressure increases ~1 PSI per 10°F temperature rise
    - Older tires lose pressure faster
    - Random slow leaks possible

    Args:
        nominal_psi (float): Nominal tire pressure
        temperature (float): Ambient temperature in °C
        age_factor (float): Tire age (0-1, 1=new, 0=worn)

    Returns:
        float: Tire pressure in PSI
    """
    # Temperature effect (ideal gas law)
    temp_fahrenheit = temperature * 9.0 / 5.0 + 32.0
    temp_delta_f = temp_fahrenheit - 70.0  # Reference temp 70°F
    temp_effect = temp_delta_f / 10.0  # 1 PSI per 10°F

    # Aging effect (older tires lose pressure)
    age_loss = (1.0 - age_factor) * 5.0

    # Calculate pressure
    pressure = nominal_psi + temp_effect - age_loss

    # Add noise (±1 PSI)
    noise = generate_noise(1.0)

    return max(80.0, min(120.0, pressure + noise))


# ============================================
# CRUSHER PHYSICS
# ============================================

def calculate_crusher_vibration(throughput, bearing_condition=1.0, runtime_hours=0):
    """
    Calculate crusher vibration based on operating conditions

    Physics:
    - Base vibration from rotating components
    - Throughput affects load vibration
    - Bearing wear increases vibration
    - Runtime hours affect component wear

    Args:
        throughput (float): Current throughput in tonnes/hour
        bearing_condition (float): Bearing health (0-1, 1=perfect)
        runtime_hours (float): Hours since last maintenance

    Returns:
        float: Vibration in mm/s
    """
    # Nominal vibration at nominal throughput
    base_vibration = CRUSHER_NOMINAL_VIBRATION_MM_S

    # Throughput effect (higher load = slightly higher vibration)
    throughput_ratio = throughput / CRUSHER_NOMINAL_THROUGHPUT_TPH
    throughput_effect = (throughput_ratio - 1.0) * 3.0

    # Bearing wear (exponential increase as bearings degrade)
    bearing_factor = 1.0 / max(0.3, bearing_condition)

    # Maintenance effect (vibration creeps up over time)
    maintenance_effect = (runtime_hours / 1000.0) * 2.0

    total_vibration = (base_vibration + throughput_effect + maintenance_effect) * bearing_factor

    # Add noise (±5%)
    noise = generate_noise(total_vibration * 0.05)

    return max(5.0, total_vibration + noise)


def calculate_motor_current(throughput, motor_efficiency=0.95, voltage=440):
    """
    Calculate motor current draw based on load

    Physics:
    - Power = Torque × Angular velocity
    - Current = Power / (Voltage × Efficiency × Power Factor)
    - Throughput directly correlates with torque

    Args:
        throughput (float): Current throughput in tonnes/hour
        motor_efficiency (float): Motor efficiency (0-1)
        voltage (float): Supply voltage (V)

    Returns:
        float: Motor current in Amps
    """
    # Nominal current at nominal throughput
    nominal_current = CRUSHER_NOMINAL_MOTOR_CURRENT_A

    # Current scales linearly with throughput (approximation)
    throughput_ratio = throughput / CRUSHER_NOMINAL_THROUGHPUT_TPH
    current = nominal_current * throughput_ratio

    # Efficiency factor (lower efficiency = higher current for same power)
    efficiency_factor = 0.95 / motor_efficiency
    current = current * efficiency_factor

    # Add noise (±3%)
    noise = generate_noise(current * 0.03)

    return max(50.0, min(300.0, current + noise))


def calculate_motor_temperature(current, ambient_temp, cooling_effectiveness=1.0):
    """
    Calculate motor winding temperature

    Physics:
    - Heat generation = I²R (Joule heating)
    - Cooling rate proportional to temperature difference
    - Thermal equilibrium when heating = cooling

    Args:
        current (float): Motor current in Amps
        ambient_temp (float): Ambient temperature in °C
        cooling_effectiveness (float): Cooling system effectiveness (0-1)

    Returns:
        float: Motor temperature in °C
    """
    # Base temperature rise due to current
    nominal_rise = 50.0  # Temperature rise at nominal current
    current_ratio = current / CRUSHER_NOMINAL_MOTOR_CURRENT_A
    heat_rise = nominal_rise * (current_ratio ** 2)  # I²R relationship

    # Cooling effectiveness (better cooling = lower temp)
    cooling_factor = 1.0 / max(0.5, cooling_effectiveness)

    # Calculate final temperature
    temp = ambient_temp + (heat_rise * cooling_factor)

    # Add noise (±2°C)
    noise = generate_noise(2.0)

    return max(ambient_temp + 10, min(150.0, temp + noise))


def calculate_chute_level(runtime_hours, feed_rate, throughput):
    """
    Calculate chute fill level

    Physics:
    - Level oscillates as material flows in batches
    - High feed rate = higher level
    - High throughput = lower level (faster processing)

    Args:
        runtime_hours (float): Runtime in hours
        feed_rate (float): Input feed rate in tonnes/hour
        throughput (float): Output throughput in tonnes/hour

    Returns:
        float: Chute level in %
    """
    # Base oscillation (material arrives in cycles)
    base_level = 60.0
    oscillation = 20.0 * Math.sin(runtime_hours * 10.0)

    # Feed/throughput balance
    balance_factor = (feed_rate - throughput) / throughput * 15.0

    level = base_level + oscillation + balance_factor

    # Add noise (±5%)
    noise = generate_noise(5.0)

    # Clamp to 0-100%
    return max(0.0, min(100.0, level + noise))


# ============================================
# CONVEYOR PHYSICS
# ============================================

def calculate_conveyor_load(upstream_throughput, belt_speed, belt_width=1.2):
    """
    Calculate conveyor belt loading percentage

    Physics:
    - Load = Material volume / Belt capacity
    - Belt capacity = Speed × Width × Height × Material density

    Args:
        upstream_throughput (float): Upstream feed rate in tonnes/hour
        belt_speed (float): Belt speed in m/s
        belt_width (float): Belt width in meters

    Returns:
        float: Belt load in %
    """
    # Belt capacity (tonnes/hour at 100% load)
    # Typical: 2.5 m/s × 1.2m width × 0.3m height × 1.6 t/m³ ≈ 5200 t/hr
    belt_capacity_tph = belt_speed * belt_width * 0.3 * 1.6 * 3600.0

    # Calculate load percentage
    load_pct = (upstream_throughput / belt_capacity_tph) * 100.0

    # Add noise (±3%)
    noise = generate_noise(3.0)

    return max(0.0, min(100.0, load_pct + noise))


def calculate_belt_alignment(age_factor=1.0, load_asymmetry=0.0):
    """
    Calculate belt tracking offset from center

    Physics:
    - Belt naturally wanders due to imperfections
    - Older belts wander more
    - Asymmetric loading causes drift

    Args:
        age_factor (float): Belt age (0-1, 1=new)
        load_asymmetry (float): Load imbalance (-1 to 1)

    Returns:
        float: Belt offset in mm (negative = left, positive = right)
    """
    # Base wander (random walk)
    base_wander = generate_noise(0.5, 'gaussian')

    # Age effect (older belts wander more)
    age_wander = (1.0 - age_factor) * generate_noise(1.0)

    # Load asymmetry effect
    asymmetry_drift = load_asymmetry * 2.0

    offset = base_wander + age_wander + asymmetry_drift

    # Clamp to ±10mm (physical limits)
    return max(-10.0, min(10.0, offset))


# ============================================
# ENVIRONMENTAL CALCULATIONS
# ============================================

def calculate_ambient_temperature(time_of_day_hours):
    """
    Calculate ambient temperature based on time of day

    Physics:
    - Minimum temperature at sunrise (~6am)
    - Maximum temperature at ~2pm
    - Sinusoidal variation

    Args:
        time_of_day_hours (float): Hour of day (0-24)

    Returns:
        float: Ambient temperature in °C
    """
    # Temperature peaks at 14:00 (2pm)
    peak_hour = 14.0
    min_hour = 6.0

    # Sinusoidal variation
    hour_offset = time_of_day_hours - peak_hour
    angle = (hour_offset / 12.0) * Math.PI

    # Temperature range
    temp_min = AMBIENT_TEMP_MIN_C
    temp_max = AMBIENT_TEMP_MAX_C
    temp_range = temp_max - temp_min

    temp = temp_min + temp_range * (0.5 - 0.5 * Math.cos(angle))

    # Add daily variation (±2°C)
    noise = generate_noise(2.0)

    return temp + noise


def calculate_dust_level(crusher_total_throughput, wind_speed=10.0, humidity=30.0):
    """
    Calculate airborne dust concentration

    Physics:
    - Dust generation proportional to crushing activity
    - Wind disperses dust (lower concentration)
    - Humidity settles dust

    Args:
        crusher_total_throughput (float): Total crusher throughput in tonnes/hour
        wind_speed (float): Wind speed in km/h
        humidity (float): Relative humidity in %

    Returns:
        float: Dust concentration in µg/m³
    """
    # Base dust level
    base_dust = DUST_BASE_LEVEL_UG_M3

    # Crushing generates dust (more activity = more dust)
    crushing_dust = (crusher_total_throughput / 7200.0) * 30.0  # Max 30 at full capacity

    # Wind dispersion (higher wind = lower local concentration)
    wind_factor = 1.0 / (1.0 + wind_speed / 20.0)

    # Humidity effect (higher humidity = dust settles)
    humidity_factor = 1.0 - (humidity / 200.0)

    dust_level = (base_dust + crushing_dust) * wind_factor * humidity_factor

    # Add noise (±20%)
    noise = generate_noise(dust_level * 0.2)

    return max(5.0, dust_level + noise)


# ============================================
# OPERATOR SIMULATION
# ============================================

def get_operator_skill_factor(operator_id):
    """
    Get operator skill level (affects performance)

    Args:
        operator_id (str): Operator badge ID (e.g., "OP_101")

    Returns:
        float: Skill factor (0.8-1.2, 1.0=average)
    """
    # Extract operator number
    try:
        op_num = int(operator_id.split('_')[1])
    except:
        op_num = 101

    # Deterministic skill based on operator ID
    # Use modulo to create variation
    skill_variation = ((op_num % 10) - 5) * 0.04  # Range: -0.2 to +0.2

    skill_factor = 1.0 + skill_variation

    return max(0.8, min(1.2, skill_factor))


def get_current_shift_operator(time_of_day_hours, equipment_index):
    """
    Get operator ID based on shift time and equipment

    Args:
        time_of_day_hours (float): Hour of day (0-24)
        equipment_index (int): Equipment index (for crew assignment)

    Returns:
        str: Operator badge ID
    """
    # Day shift: 06:00-18:00 (operators 101-110)
    # Night shift: 18:00-06:00 (operators 111-120)

    if 6 <= time_of_day_hours < 18:
        # Day shift
        base_operator = 101
    else:
        # Night shift
        base_operator = 111

    # Assign operator based on equipment index
    operator_num = base_operator + (equipment_index % 10)

    return "OP_{:03d}".format(operator_num)


# ============================================
# FAULT SIMULATION HELPERS
# ============================================

def calculate_bearing_wear_rate(load_factor, lubrication_quality, temperature):
    """
    Calculate bearing wear rate (for fault simulation)

    Args:
        load_factor (float): Load relative to rated (0-1)
        lubrication_quality (float): Lube quality (0-1, 1=perfect)
        temperature (float): Operating temperature in °C

    Returns:
        float: Wear rate factor (1.0=nominal, >1.0=accelerated)
    """
    # Base wear rate
    base_rate = 1.0

    # Overload accelerates wear exponentially
    load_rate = 1.0 + (load_factor ** 2)

    # Poor lubrication dramatically increases wear
    lube_rate = 1.0 / max(0.1, lubrication_quality)

    # High temperature accelerates wear (Arrhenius relationship)
    temp_rate = 1.0 + ((temperature - 80.0) / 50.0) * 0.5

    wear_rate = base_rate * load_rate * lube_rate * max(1.0, temp_rate)

    return wear_rate


# ============================================
# VALIDATION / TESTING
# ============================================

def validate_physics_ranges():
    """
    Validate that physics calculations return reasonable values

    Returns:
        dict: Test results
    """
    results = {}

    # Test haul truck physics
    fuel_rate = calculate_fuel_consumption(speed=50, load=250)
    results['fuel_rate_in_range'] = 0.01 <= fuel_rate <= 0.15

    engine_temp = calculate_engine_temp(load=250, ambient_temp=30, speed=50)
    results['engine_temp_in_range'] = 60 <= engine_temp <= 120

    vibration = calculate_vibration(speed=50, load=250)
    results['vibration_in_range'] = 0 <= vibration <= 20

    # Test crusher physics
    crusher_vib = calculate_crusher_vibration(throughput=2400)
    results['crusher_vib_in_range'] = 10 <= crusher_vib <= 30

    motor_current = calculate_motor_current(throughput=2400)
    results['motor_current_in_range'] = 150 <= motor_current <= 250

    # Test GPS
    lat, lon = calculate_gps_position(cycle_time=0)
    results['gps_in_range'] = (abs(lat - GPS_BASE_LAT) < 0.1 and
                                abs(lon - GPS_BASE_LON) < 0.1)

    return results


# ============================================
# MAIN (for testing)
# ============================================

if __name__ == '__main__':
    # This won't run in Ignition Gateway, but useful for development/testing
    print("Physics Utilities Module - Test Mode")
    print("=" * 50)

    # Run validation
    results = validate_physics_ranges()
    print("\nValidation Results:")
    for test, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print("  {}: {}".format(test, status))

    # Example calculations
    print("\nExample Calculations:")
    print("-" * 50)

    fuel = calculate_fuel_consumption(speed=50, load=250)
    print("Fuel consumption (50 km/h, 250t load): {:.4f} %/sec".format(fuel))

    temp = calculate_engine_temp(load=250, ambient_temp=30, speed=50)
    print("Engine temperature (250t load, 30C ambient): {:.1f} C".format(temp))

    vib = calculate_crusher_vibration(throughput=2400, bearing_condition=1.0)
    print("Crusher vibration (2400 t/hr, healthy bearings): {:.1f} mm/s".format(vib))

    current = calculate_motor_current(throughput=2400)
    print("Motor current (2400 t/hr): {:.1f} A".format(current))

    lat, lon = calculate_gps_position(cycle_time=0)
    print("GPS position (cycle start): {:.6f}, {:.6f}".format(lat, lon))
