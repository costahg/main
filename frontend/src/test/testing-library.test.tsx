import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

function SmokeComponent() {
  return <button type="button">Tigrify</button>
}

describe("frontend test environment", () => {
  it("renders React components with jest-dom assertions", () => {
    render(<SmokeComponent />)

    expect(screen.getByRole("button", { name: "Tigrify" })).toBeEnabled()
  })
})
