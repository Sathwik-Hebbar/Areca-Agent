import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import { useFarm } from "./FarmContext";
import { soilApi } from "../api/soil";

const SoilSensorContext = createContext(null);
const FAST_INTERVAL_MS = 60_000;
const BACKOFF_INTERVAL_MS = 5 * 60_000;

export const SoilSensorProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const { selectedCropBlock } = useFarm();
  const cropBlockId = selectedCropBlock?.id ?? null;
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const timerRef = useRef(null);
  const inFlightRef = useRef(false);
  const mountedRef = useRef(false);
  const configRef = useRef(null);
  const consecutiveUnavailableRef = useRef(0);
  const pendingRestartRef = useRef(false);
  const runReadRef = useRef(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = null;
  }, []);

  const scheduleNext = useCallback(() => {
    clearTimer();
    if (!mountedRef.current || document.visibilityState !== "visible") return;
    const delay = consecutiveUnavailableRef.current >= 3
      ? BACKOFF_INTERVAL_MS
      : FAST_INTERVAL_MS;
    timerRef.current = setTimeout(() => runReadRef.current?.(false), delay);
  }, [clearTimer]);

  const runRead = useCallback(async (manual = false) => {
    const activeConfig = configRef.current;
    if (!activeConfig?.isAuthenticated || !activeConfig.cropBlockId || inFlightRef.current) return;

    const requestBlockId = activeConfig.cropBlockId;
    inFlightRef.current = true;
    setLoading(true);

    try {
      const nextResult = await soilApi.readSoil(requestBlockId, manual);
      if (mountedRef.current && configRef.current?.cropBlockId === requestBlockId) {
        setResult(nextResult);
        consecutiveUnavailableRef.current =
          nextResult.status === "sensor_unavailable"
            ? consecutiveUnavailableRef.current + 1
            : 0;
      }
    } catch {
      if (mountedRef.current && configRef.current?.cropBlockId === requestBlockId) {
        setResult((previous) => ({
          status: "sensor_unavailable",
          live_reading: null,
          stored: false,
          last_stored_reading: previous?.last_stored_reading ?? null,
          message: "Sensor service is not available.",
        }));
        consecutiveUnavailableRef.current += 1;
      }
    } finally {
      inFlightRef.current = false;
      if (!mountedRef.current) return;
      setLoading(false);

      if (configRef.current?.cropBlockId !== requestBlockId) {
        if (pendingRestartRef.current) {
          pendingRestartRef.current = false;
          runReadRef.current?.(false);
        }
        return;
      }
      scheduleNext();
    }
  }, [scheduleNext]);

  runReadRef.current = runRead;

  useEffect(() => {
    const nextConfig = { isAuthenticated, cropBlockId };
    const configChanged =
      configRef.current?.isAuthenticated !== isAuthenticated ||
      configRef.current?.cropBlockId !== cropBlockId;

    mountedRef.current = true;
    configRef.current = nextConfig;
    clearTimer();

    if (!isAuthenticated || !cropBlockId) {
      consecutiveUnavailableRef.current = 0;
      pendingRestartRef.current = false;
      setResult(null);
      setLoading(false);
      return () => {
        mountedRef.current = false;
        clearTimer();
      };
    }

    if (configChanged) {
      consecutiveUnavailableRef.current = 0;
      setResult(null);
    }

    const onVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        clearTimer();
      } else {
        runReadRef.current?.(false);
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    if (inFlightRef.current) {
      pendingRestartRef.current = configChanged;
    } else if (configChanged && document.visibilityState === "visible") {
      runReadRef.current?.(false);
    }

    return () => {
      mountedRef.current = false;
      clearTimer();
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [isAuthenticated, cropBlockId, clearTimer]);

  const checkNow = useCallback(() => runRead(true), [runRead]);

  return (
    <SoilSensorContext.Provider value={{ result, loading, inFlight: inFlightRef.current, checkNow }}>
      {children}
    </SoilSensorContext.Provider>
  );
};

export const useSoilSensor = () => {
  const context = useContext(SoilSensorContext);
  if (!context) throw new Error("useSoilSensor must be used within SoilSensorProvider");
  return context;
};
