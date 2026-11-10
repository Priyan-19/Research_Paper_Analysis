import { describe, it, expect, beforeEach } from "vitest";
import { getApiBaseUrl, setApiBaseUrl, DEFAULT_API_BASE_URL, apiClient } from "./client";

describe("apiClient & base URL resolution", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns default API base URL when localStorage is empty", () => {
    expect(getApiBaseUrl()).toBe(DEFAULT_API_BASE_URL);
  });

  it("persists and retrieves custom API base URL from localStorage", () => {
    setApiBaseUrl("http://custom-host:9000");
    expect(getApiBaseUrl()).toBe("http://custom-host:9000");
  });

  it("configures axios instance with 60000ms timeout", () => {
    expect(apiClient.defaults.timeout).toBe(60000);
    expect(apiClient.defaults.headers["Content-Type"]).toBe("application/json");
  });
});

