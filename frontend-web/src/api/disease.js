import apiClient from "./client";

export const diseaseApi = {
  // Vision Agent: Image upload for CNN detection
  detectDisease: (cropBlockId, imageFile) => {
    const formData = new FormData();
    formData.append("crop_block_id", cropBlockId);
    formData.append("file", imageFile);

    return apiClient.post("/api/v1/agents/vision/detect", formData, {
      headers: {
        "Content-Type": undefined,
      },
      timeout: 60000,
    });
  },

  // Diagnosis Agent: Bayesian posterior validation
  validateDetection: (detectionId) =>
    apiClient.post("/api/v1/agents/diagnosis/validate", {
      detection_id: detectionId,
    }),
};
