import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SettingsPage } from "./SettingsPage";

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("SettingsPage", () => {
  it("renders configuration headers and inputs", () => {
    renderWithClient(<SettingsPage />);

    expect(screen.getByText(/System Preferences & LLM Setup/i)).toBeInTheDocument();
    expect(screen.getByText(/FastAPI Backend Connection/i)).toBeInTheDocument();
    expect(screen.getByText(/Large Language Model Reasoning Engine/i)).toBeInTheDocument();
    expect(screen.getByText(/Design Theme Mode/i)).toBeInTheDocument();
  });

  it("allows changing API base URL", () => {
    renderWithClient(<SettingsPage />);

    const input = screen.getByDisplayValue("http://127.0.0.1:8000");
    fireEvent.change(input, { target: { value: "http://localhost:8080" } });
    expect(input).toHaveValue("http://localhost:8080");

    const saveButton = screen.getByRole("button", { name: /Save & Connect/i });
    fireEvent.click(saveButton);
  });
});
