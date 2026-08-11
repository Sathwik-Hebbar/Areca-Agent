import React, { useState } from "react";
import { Camera, Upload, ShieldCheck, AlertTriangle } from "lucide-react";
import { diseaseApi } from "../api/disease";
import { useFarm } from "../context/FarmContext";

export const DiseaseDetection = () => {
  const { selectedCropBlock } = useFarm();
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError("");
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile || !selectedCropBlock) return;
    setLoading(true);
    setError("");
    try {
      const data = await diseaseApi.detectDisease(selectedCropBlock.id, selectedFile);
      setResult(data);
    } catch (err) {
      setError(err.message || "Detection failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto" }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", margin: 0 }}>Visual Disease Detection</h1>
        <p style={{ fontSize: "0.9rem", color: "#64748b", margin: "0.25rem 0 0 0" }}>
          Upload arecanut leaf or nut bunch photograph for YOLOv8/CNN inference & Bayesian validation
        </p>
      </div>

      <div className="card">
        {error && (
          <div style={{ padding: "0.75rem 1rem", background: "#fee2e2", color: "#b91c1c", borderRadius: "8px", fontSize: "0.85rem", marginBottom: "1rem" }}>
            {error}
          </div>
        )}

        <form onSubmit={handleUpload}>
          <div
            style={{
              border: "2px dashed #cbd5e1",
              borderRadius: "12px",
              padding: "2rem",
              textAlign: "center",
              cursor: "pointer",
              backgroundColor: "#f8fafc",
              marginBottom: "1.25rem",
            }}
            onClick={() => document.getElementById("leaf-file-input").click()}
          >
            <input
              id="leaf-file-input"
              type="file"
              accept="image/*"
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Preview"
                style={{ maxHeight: "260px", maxWidth: "100%", borderRadius: "8px", objectFit: "contain" }}
              />
            ) : (
              <div>
                <Camera size={40} color="#64748b" style={{ margin: "0 auto 0.5rem auto" }} />
                <p style={{ fontWeight: 600, color: "#334155", margin: 0 }}>Click to browse or drop palm leaf photo</p>
                <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Supports JPG, PNG, WEBP</span>
              </div>
            )}
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%" }}
            disabled={!selectedFile || loading || !selectedCropBlock}
          >
            <Upload size={18} />
            {loading ? "Running Vision & Bayesian Inference..." : "Run AI Diagnosis"}
          </button>
        </form>

        {result && (
          <div style={{ marginTop: "1.5rem", padding: "1.25rem", backgroundColor: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "10px" }}>
            <h3 style={{ fontSize: "1.1rem", color: "#166534", margin: "0 0 0.5rem 0" }}>
              Predicted: {result.predicted_disease}
            </h3>
            <p style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem" }}>
              Visual Confidence: <strong>{((result.cnn_confidence || 0) * 100).toFixed(1)}%</strong> | Posterior: <strong>{result.posterior_probability ? `${(result.posterior_probability * 100).toFixed(1)}%` : "Validated"}</strong>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
