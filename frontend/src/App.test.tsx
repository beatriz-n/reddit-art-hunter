import { describe, expect, it, vi } from "vitest";
import { getApiHealth } from "./api";

describe("API client", () => {
  it("requests the local health endpoint and parses its response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok", service: "reddit-art-hunter-api" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getApiHealth()).resolves.toEqual({ status: "ok", service: "reddit-art-hunter-api" });
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/health");
    vi.unstubAllGlobals();
  });

  it("fails clearly when the API returns an error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: "API indisponível" }),
    }));
    await expect(getApiHealth()).rejects.toThrow("API indisponível");
    vi.unstubAllGlobals();
  });
});
