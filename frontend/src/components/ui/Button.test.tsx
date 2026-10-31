import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Button } from "./Button";

describe("Editorial Button Component", () => {
  it("renders correctly with children", () => {
    render(<Button>Inquire Corpus</Button>);
    expect(screen.getByRole("button", { name: /Inquire Corpus/i })).toBeInTheDocument();
  });

  it("handles click events properly", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);
    fireEvent.click(screen.getByRole("button", { name: /Click Me/i }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("applies primary editorial styles", () => {
    render(<Button variant="primary">Primary Action</Button>);
    const btn = screen.getByRole("button", { name: /Primary Action/i });
    expect(btn.className).toContain("bg-parchment-primary");
  });

  it("respects disabled state", () => {
    const handleClick = vi.fn();
    render(<Button disabled onClick={handleClick}>Disabled</Button>);
    const btn = screen.getByRole("button", { name: /Disabled/i });
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(handleClick).not.toHaveBeenCalled();
  });
});

