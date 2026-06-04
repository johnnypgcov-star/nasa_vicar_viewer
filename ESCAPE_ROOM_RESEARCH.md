# Escape Room Research Agent — Setup Notes

## What This Is
A custom slash command that generates a professional business intelligence
report on escape room opportunities in any US state. The report is saved
as a self-contained HTML file that can be printed to PDF and sent to Wendy.

## How to Run It
In any Claude Code session with this repo open, type:

```
/escape-room-research Texas
```

Replace `Texas` with any US state name. For two-word states use the full name:

```
/escape-room-research New York
/escape-room-research North Carolina
```

## Where the Report Goes
Saved to: `reports/escape-room-[state].html`

To convert to PDF: open the file in Chrome or Safari → File → Print → Save as PDF.

## What the Report Covers
1. **State Demographics & Market Profile** — population, age distribution,
   household income, tourism visitor numbers, university and college
   populations (cities with high student concentrations flagged as HIGH
   OPPORTUNITY markets)
2. **Escape Room Market Landscape** — existing venues, franchise presence,
   saturation analysis, underserved cities, pricing benchmarks
3. **Business Opportunity Assessment** — top 3–5 recommended cities,
   greenfield markets, addressable market size, seasonal demand; university
   towns assessed for campus proximity, walk-in trade, group bookings,
   freshers week revenue spikes
4. **Commercial Real Estate & Location Data** — see requirements below
5. **Regulatory & Operational Environment** — business registration, safety
   codes, liquor licence rules, small business incentives
6. **Financial Benchmarks** — revenue per room, fit-out costs, break-even timeline

## Wendy's Site Requirements (Section 4)
These are hard-coded into the agent — it will filter accordingly automatically:

- **Minimum size: 2,000 sq ft** (anything below is excluded from the report)
- **Target range: 3,500–6,000 sq ft** to accommodate 4–6 rooms comfortably
- **Room count: 4–6 escape rooms** (each room ~250–400 sq ft)
- Prime location focus — high footfall, entertainment districts, near
  restaurants, bars, hotels, transport hubs
- Per-city lease rate breakdowns (Class A, B, C space)
- Parking, loading access, ceiling height, column-free floor plan notes
- Lease structure intelligence — terms, rent-free periods, fit-out contributions
- Red flags flagged: declining areas, parking black spots, overpriced markets

## Report Format
- Professional HTML with dark header, white body, red accents
- Cover page: report title, state name, date, "Prepared for: Wendy"
- Executive summary (top 5 findings)
- Clickable table of contents
- Top Recommended Locations summary table
- Key Risks & Considerations section
- Footer: "Research conducted by Claude AI | [State] Escape Room Market Report | [date]"

## Files
- Agent definition: `.claude/commands/escape-room-research.md`
- Reports output: `reports/` directory
