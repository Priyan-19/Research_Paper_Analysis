import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { EmptyState } from "./EmptyState";

describe("EmptyState Component", () => {
  it("renders heading and academic description cleanly", () => {
    render(<EmptyState />);

    expect(
      screen.getByRole("heading", { name: /What would you like to research today\?/i })
    ).toBeInTheDocument();

    expect(
      screen.getByText(/Grounded academic inquiry across indexed PDFs/i)
    ).toBeInTheDocument();
  });
});
