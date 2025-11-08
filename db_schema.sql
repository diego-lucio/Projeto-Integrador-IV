CREATE DATABASE IF NOT EXISTS air_quality CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE air_quality;

CREATE TABLE IF NOT EXISTS cetesb_readings (
  station_code VARCHAR(20) NOT NULL,
  station_name VARCHAR(100) NULL,
  dt DATETIME NOT NULL,
  pollutant VARCHAR(16) NOT NULL,
  value DOUBLE NULL,
  unit VARCHAR(16) NULL,
  valid_flag TINYINT NULL,
  source VARCHAR(32) DEFAULT 'CETESB',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (station_code, dt, pollutant)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS inmet_readings (
  station_code VARCHAR(10) NOT NULL,
  dt DATETIME NOT NULL,
  temp_c DOUBLE NULL,
  umid_pct DOUBLE NULL,
  press_hpa DOUBLE NULL,
  wind_dir_deg DOUBLE NULL,
  wind_vel_mps DOUBLE NULL,
  rain_mm DOUBLE NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (station_code, dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE OR REPLACE VIEW vw_air_quality_join AS
SELECT 
  c.station_code AS aq_station,
  c.dt AS dt_hour,
  c.pollutant,
  c.value AS pollutant_value,
  c.unit AS pollutant_unit,
  i.station_code AS met_station,
  i.temp_c, i.umid_pct, i.press_hpa, i.wind_dir_deg, i.wind_vel_mps, i.rain_mm
FROM cetesb_readings c
LEFT JOIN inmet_readings i
  ON i.dt = c.dt;
