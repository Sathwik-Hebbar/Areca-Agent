import React from "react";
import { FlaskConical, RefreshCw, CheckCircle2, WifiOff, Cpu, AlertTriangle } from "lucide-react";
import { useSoilSensor } from "../context/SoilSensorContext";

const STATUS = {
  ok: { label: "Live", className: "badge-low", Icon: CheckCircle2 },
  sensor_unavailable: { label: "Sensor not available", className: "badge-high", Icon: WifiOff },
  busy: { label: "Busy", className: "badge-moderate", Icon: Cpu },
  invalid_reading: { label: "Invalid reading", className: "badge-urgent", Icon: AlertTriangle },
  no_soil_detected: { label: "No soil detected", className: "badge-moderate", Icon: AlertTriangle },
};

export const SoilMonitor = () => {
  const { result, loading, inFlight, checkNow } = useSoilSensor();
  const isEmpty = result === null;
  const status = result?.status ?? "sensor_unavailable";
  const statusView = STATUS[status] ?? STATUS.sensor_unavailable;
  const StatusIcon = statusView.Icon;
  const reading = status === "ok" ? result?.live_reading : result?.last_stored_reading;
  const timestamp = status === "ok" ? result?.recorded_at : result?.last_stored_reading?.recorded_at;
  const formatTime = (value) => value ? new Date(value).toLocaleString() : "No saved reading yet";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", margin: 0 }}>Soil Monitor</h1>
          <p style={{ fontSize: "0.9rem", color: "#64748b", margin: "0.25rem 0 0" }}>Current soil sensor reading for the selected crop block</p>
        </div>
        <button className="btn btn-outline" onClick={checkNow} disabled={inFlight}>
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          {loading ? "Checking..." : "Check Sensor"}
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title"><FlaskConical size={18} color="#10b981" /><span>Soil Nutrients</span></div>
          {isEmpty ? (
            <span className="badge badge-low"><RefreshCw size={12} className="animate-spin" />Checking sensor...</span>
          ) : (
            <span className={`badge ${statusView.className}`}><StatusIcon size={12} />{statusView.label}</span>
          )}
        </div>

        <span className="badge badge-moderate">Uncalibrated prototype readings</span>
        {status === "no_soil_detected" && <p style={{ color: "#92400e", marginTop: "1rem" }}>Insert the probe into soil.</p>}

        <div className="grid-3" style={{ margin: "1rem 0" }}>
          {[["Nitrogen", reading?.nitrogen], ["Phosphorus", reading?.phosphorus], ["Potassium", reading?.potassium]].map(([label, value]) => (
            <div className="card" key={label} style={{ background: "#f8fafc" }}>
              <p style={{ color: "#64748b", margin: 0 }}>{label}</p>
              <strong style={{ fontSize: "2rem" }}>{value == null ? "—" : Number(value).toFixed(0)}</strong>
            </div>
          ))}
        </div>

        <p style={{ color: "#64748b", marginBottom: 0 }}>{status === "ok" ? "Live reading" : "Last stored reading"}: {formatTime(timestamp)}</p>
      </div>
    </div>
  );
};
