-- Insert sample data into Agentic HMI tables
USE agentic_hmi;

-- Insert sample sensor data with anomalies
INSERT INTO sensor_data VALUES
('sensor1', 'REACTOR_01', 'temperature', 92.5, '°C', 'good', CURRENT_TIMESTAMP()),
('sensor2', 'REACTOR_01', 'pressure', 3.2, 'bar', 'good', CURRENT_TIMESTAMP()),
('sensor3', 'PUMP_07', 'vibration', 4.2, 'mm/s', 'good', CURRENT_TIMESTAMP()),
('sensor4', 'PUMP_07', 'flow_rate', 145.3, 'L/min', 'good', CURRENT_TIMESTAMP()),
('sensor5', 'CONVEYOR_02', 'belt_speed', 2.1, 'm/s', 'good', CURRENT_TIMESTAMP()),
('sensor6', 'CONVEYOR_02', 'belt_tension', 95, 'N', 'good', CURRENT_TIMESTAMP());

-- Insert sample recommendations
INSERT INTO agent_recommendations VALUES
('rec001', 'REACTOR_01', 'high_temperature', 'high',
 'Temperature exceeding normal operating range (92°C, normal: 70-80°C)',
 'Reduce feed rate by 15% and increase cooling water flow to maximum',
 0.87,
 'Analysis: Likely caused by cooling system efficiency degradation',
 'Temperature should return to normal within 15 minutes',
 'pending', NULL, NULL, NULL, NULL, NULL, NULL,
 CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),

('rec002', 'PUMP_07', 'vibration_anomaly', 'medium',
 'Vibration levels increasing trend detected (4.2 mm/s)',
 'Schedule bearing inspection within next maintenance window',
 0.73,
 'Analysis: Possible bearing wear or misalignment',
 'Vibration should stabilize after maintenance',
 'pending', NULL, NULL, NULL, NULL, NULL, NULL,
 CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),

('rec003', 'CONVEYOR_02', 'belt_tension', 'low',
 'Belt tension below optimal range',
 'Adjust tension to 120N using tensioning mechanism',
 0.91,
 'Analysis: Normal wear requiring routine adjustment',
 'Belt tension will be within spec after adjustment',
 'pending', NULL, NULL, NULL, NULL, NULL, NULL,
 CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());