import React, { useState, useEffect } from "react";
import { CloudSun, Droplets, Thermometer, Wind, AlertTriangle, ShieldCheck, RefreshCw, Calendar } from "lucide-react";
import { weatherApi } from "../api/weather";
import { useFarm } from "../context/FarmContext";

export const Weather = () => {
  const { selectedFarm } = useFarm();
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchWeather = async (force = false) => {
    if (!selectedFarm?.id) return;
    setLoading(true);
    setError("");
    try {
      const data = await weatherApi.getCurrentWeather(selectedFarm.id, force);
      setWeatherData(data);
    } catch (err) {
      console.warn("Weather fetch failed:", err.message);
      setError(err.message || "Failed to load weather telemetry");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather(false);
  }, [selectedFarm?.id]);

  const riskScore = weatherData?.disease_risk?.score ?? weatherData?.disease_risk?.disease_risk_score ?? weatherData?.disease_risk_score ?? 20.0;
  const riskLevel = weatherData?.disease_risk?.level ?? weatherData?.disease_risk_level ?? "low";

  const getUrgencyBadgeClass = (lvl) => {
    switch (lvl?.toLowerCase()) {
      case "urgent":
        return "badge-urgent";
      case "high":
        return "badge-high";
      case "moderate":
      case "medium":
        return "badge-moderate";
      default:
        return "badge-low";
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", margin: 0 }}>Weather & Disease Risk Forecast</h1>
          <p style={{ fontSize: "0.9rem", color: "#64748b", margin: "0.25rem 0 0 0" }}>
            Live Open-Meteo meteorological telemetry for <strong>{selectedFarm?.farm_name || "Plantation"}</strong>
          </p>
        </div>
        <button className="btn btn-outline" onClick={() => fetchWeather(true)} disabled={loading}>
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          {loading ? "Refreshing..." : "Force Live Update"}
        </button>
      </div>

      {error && (
        <div style={{ padding: "0.75rem 1rem", background: "#fee2e2", color: "#b91c1c", borderRadius: "8px", fontSize: "0.85rem", marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      {/* Main 4 Metric Cards */}
      <div className="grid-4" style={{ marginBottom: "1.5rem" }}>
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b" }}>Temperature</span>
            <Thermometer size={18} color="#f97316" />
          </div>
          <h2 style={{ fontSize: "1.75rem", margin: 0, color: "#0f172a" }}>
            {weatherData?.temperature !== undefined ? `${Number(weatherData.temperature).toFixed(1)}°C` : "--"}
          </h2>
          <span style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem", display: "block" }}>
            Source: {weatherData?.source || "Open-Meteo"}
          </span>
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b" }}>Relative Humidity</span>
            <Droplets size={18} color="#0284c7" />
          </div>
          <h2 style={{ fontSize: "1.75rem", margin: 0, color: "#0f172a" }}>
            {weatherData?.humidity !== undefined ? `${Number(weatherData.humidity).toFixed(0)}%` : "--"}
          </h2>
          <span style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem", display: "block" }}>
            Optimal: 60-80%
          </span>
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b" }}>Rainfall (24h)</span>
            <CloudSun size={18} color="#3b82f6" />
          </div>
          <h2 style={{ fontSize: "1.75rem", margin: 0, color: "#0f172a" }}>
            {weatherData?.rainfall_mm !== undefined ? `${Number(weatherData.rainfall_mm).toFixed(1)} mm` : "--"}
          </h2>
          <span style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem", display: "block" }}>
            Cumulative precipitation
          </span>
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b" }}>Fungal Risk Index</span>
            <AlertTriangle size={18} color="#eab308" />
          </div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <h2 style={{ fontSize: "1.75rem", margin: 0, color: "#0f172a" }}>
              {Number(riskScore).toFixed(1)}/100
            </h2>
            <span className={`badge ${getUrgencyBadgeClass(riskLevel)}`}>
              {String(riskLevel).toUpperCase()}
            </span>
          </div>
          <span style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem", display: "block" }}>
            Fungal sporulation index
          </span>
        </div>
      </div>

      {/* 3-Day Forecast Cards */}
      {weatherData?.forecast && weatherData.forecast.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Calendar size={18} color="#0284c7" />
              <span>3-Day Meteorological Forecast</span>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
            {weatherData.forecast.map((f, i) => (
              <div
                key={i}
                style={{
                  padding: "1rem",
                  borderRadius: "10px",
                  backgroundColor: "#f8fafc",
                  border: "1px solid #e2e8f0",
                }}
              >
                <span style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 600, display: "block", marginBottom: "0.4rem" }}>
                  Day +{i + 1} ({new Date(f.timestamp).toLocaleDateString([], { month: "short", day: "numeric" })})
                </span>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#0f172a", marginBottom: "0.25rem" }}>
                  {(f.predicted_temperature ?? f.predicted_temp ?? 0).toFixed(1)}°C
                </div>
                <div style={{ fontSize: "0.8rem", color: "#475569" }}>
                  Humidity: <strong>{(f.predicted_humidity ?? 0).toFixed(0)}%</strong>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#475569" }}>
                  Rainfall: <strong>{(f.predicted_rainfall_mm ?? f.predicted_rainfall ?? 0).toFixed(1)} mm</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
