import React, { useState, useEffect } from "react";
import { TrendingUp, Building, Calendar, ArrowUpRight, ArrowDownRight, RefreshCw } from "lucide-react";
import { marketApi } from "../api/market";
import { useAuth } from "../context/AuthContext";

export const Market = () => {
  const { profile } = useAuth();
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const preferredMandi = profile?.preferred_mandi || "Shivamogga APMC";

  const fetchMarket = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await marketApi.getPrices(preferredMandi);
      setMarketData(data);
    } catch (err) {
      console.warn("Market fetch failed:", err.message);
      setError(err.message || "Failed to load market data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarket();
  }, [preferredMandi]);

  // Determine trend from forecast array vs current price
  const currentPrice = marketData?.current_price_per_kg ?? 475.0;
  const forecastList = marketData?.forecast || [];
  const modelUsed = forecastList[0]?.forecast_model || "linear_trend_regression";

  const finalForecastPrice = forecastList.length > 0
    ? forecastList[forecastList.length - 1].predicted_price_per_kg
    : currentPrice;
  const isRising = finalForecastPrice >= currentPrice;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", margin: 0 }}>APMC Market Trends & Forecasts</h1>
          <p style={{ fontSize: "0.9rem", color: "#64748b", margin: "0.25rem 0 0 0" }}>
            Live mandi prices from data.gov.in with 7-day predictive forecasting
          </p>
        </div>
        <button className="btn btn-outline" onClick={fetchMarket} disabled={loading}>
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          {loading ? "Refreshing..." : "Refresh Mandi"}
        </button>
      </div>

      {error && (
        <div style={{ padding: "0.75rem 1rem", background: "#fee2e2", color: "#b91c1c", borderRadius: "8px", fontSize: "0.85rem", marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      <div className="grid-2" style={{ marginBottom: "1.5rem" }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Building size={18} color="#10b981" />
              <span>Current Spot Price ({marketData?.mandi_name || preferredMandi})</span>
            </div>
            <span className={`badge ${isRising ? "badge-low" : "badge-urgent"}`}>
              {isRising ? "Rising Trend" : "Falling Trend"}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
            <h2 style={{ fontSize: "2.25rem", margin: 0, color: "#0f172a" }}>₹{currentPrice.toFixed(2)}</h2>
            <span style={{ fontSize: "1rem", color: "#64748b" }}>/ kg ({marketData?.commodity || "Arecanut"})</span>
          </div>
          <p style={{ fontSize: "0.85rem", color: "#64748b", marginTop: "0.5rem", marginBottom: 0 }}>
            Model: <strong>{modelUsed}</strong> | Source: <strong>{marketData?.source || "data.gov.in"}</strong>
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <TrendingUp size={18} color="#0284c7" />
              <span>7-Day Harvest Timing Recommendation</span>
            </div>
          </div>
          <p style={{ fontSize: "0.95rem", color: "#334155", margin: 0 }}>
            {isRising
              ? "Market prices remain stable to rising across Karnataka APMC mandis. Favorable window for orderly harvesting and staggered mandi sales over the next 7 days."
              : "Prices are projected to soften slightly over the upcoming week. Recommended to expedite threshing and sell available harvested lots immediately."}
          </p>
        </div>
      </div>

      {/* 7-Day Forecast Table */}
      {forecastList.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Calendar size={18} color="#10b981" />
              <span>7-Day APMC Price Projection ({marketData?.mandi_name || preferredMandi})</span>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.75rem" }}>
            {forecastList.map((item, idx) => {
              const diff = item.predicted_price_per_kg - currentPrice;
              return (
                <div
                  key={idx}
                  style={{
                    padding: "0.85rem",
                    borderRadius: "10px",
                    backgroundColor: "#f8fafc",
                    border: "1px solid #e2e8f0",
                    textAlign: "center",
                  }}
                >
                  <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600, display: "block" }}>
                    Day {idx + 1} ({new Date(item.forecast_date).toLocaleDateString([], { month: "short", day: "numeric" })})
                  </span>
                  <div style={{ fontSize: "1.15rem", fontWeight: 700, color: "#0f172a", margin: "0.25rem 0" }}>
                    ₹{item.predicted_price_per_kg.toFixed(2)}
                  </div>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      fontWeight: 600,
                      color: diff >= 0 ? "#16a34a" : "#dc2626",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "2px",
                    }}
                  >
                    {diff >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                    {diff >= 0 ? `+₹${diff.toFixed(2)}` : `-₹${Math.abs(diff).toFixed(2)}`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
