import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Card } from "./Card";

describe("Card Component", () => {
  it("renders children content inside the card", () => {
    render(
      <Card>
        <h3>Research Paper Overview</h3>
        <p>Grounded academic insights</p>
      </Card>
    );

    expect(screen.getByText("Research Paper Overview")).toBeInTheDocument();
    expect(screen.getByText("Grounded academic insights")).toBeInTheDocument();
  });

  it("formats and displays plateNumber correctly", () => {
    render(<Card plateNumber={3}>Content</Card>);
    expect(screen.getByText("03")).toBeInTheDocument();
  });
});

