import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CitationChip } from "./CitationChip";

describe("CitationChip Component", () => {
  it("renders inline citation tag", () => {
    render(<CitationChip tag="[1]" />);
    expect(screen.getByRole("button", { name: /\[1\]/i })).toBeInTheDocument();
  });

  it("displays popover metadata on hover", () => {
    const mockCitation = {
      paper_id: "paper_123",
      paper_title: "Attention Is All You Need",
      page_number: 3,
      section_name: "Multi-Head Attention",
      citation_tag: "[1]",
      snippet: "Multi-head attention allows the model to jointly attend to information...",
    };

    render(<CitationChip tag="[1]" citation={mockCitation} />);
    const chipButton = screen.getByRole("button", { name: /\[1\]/i });

    fireEvent.mouseEnter(chipButton);
    expect(screen.getByText(/Attention Is All You Need/i)).toBeInTheDocument();
    expect(screen.getByText(/Section: Multi-Head Attention/i)).toBeInTheDocument();
    expect(screen.getByText(/Page 3/i)).toBeInTheDocument();
  });
});

