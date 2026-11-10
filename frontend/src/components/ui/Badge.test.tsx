import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "./Badge";

describe("Badge Component", () => {
  it("renders text content correctly", () => {
    render(<Badge>Hybrid RAG</Badge>);
    expect(screen.getByText("Hybrid RAG")).toBeInTheDocument();
  });

  it("applies variant classes accurately", () => {
    const { container, rerender } = render(<Badge variant="vector">Vector</Badge>);
    expect(container.firstChild).toHaveClass("bg-[#e2e8f0]");

    rerender(<Badge variant="graph">Graph</Badge>);
    expect(container.firstChild).toHaveClass("bg-[#fef3c7]");

    rerender(<Badge variant="hybrid">Hybrid</Badge>);
    expect(container.firstChild).toHaveClass("bg-[#dcfce7]");
  });
});

