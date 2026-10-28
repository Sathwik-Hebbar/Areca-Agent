import apiClient from "./client";

export const soilApi = {
  readSoil: (cropBlockId, manual = false) => {
    return apiClient.post("/api/v1/hardware/soil/read", {
      crop_block_id: cropBlockId,
      manual: manual,
    });
  },

  getLatest: (cropBlockId) => {
    return apiClient.get("/api/v1/hardware/soil/latest", {
      params: { crop_block_id: cropBlockId },
    });
  },
};
