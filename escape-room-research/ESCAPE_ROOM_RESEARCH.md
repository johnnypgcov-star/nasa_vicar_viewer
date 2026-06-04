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

## Operator Context Built Into Every Report
Wendy operates a 3-room escape room in a mall in Vancouver, Washington (est. 2022,
performing well). The agent knows this and tailors every report accordingly:
- Mall and retail entertainment centre locations are prioritised (her proven model)
- All city recommendations are benchmarked against her Vancouver, WA market
- Recommendations are framed for an experienced operator, not a first-time entrant

## What the Report Covers
1. **State Demographics & Market Profile** — population, age, income; economic
   health (unemployment, job growth, major employers); net migration and tax burden
   (HIGH RISK flag for outmigration states); inbound tourism (visitor numbers,
   top 10 attractions, seasonal peaks); university populations (HIGH OPPORTUNITY
   flag for student-heavy cities)
2. **Escape Room Market Landscape** — competitor mapping, franchise presence,
   saturation; Google search demand; Groupon/discount platform health check;
   full competitor sentiment analysis across Google, Yelp, TripAdvisor, Facebook,
   Instagram (MARKET OPPORTUNITY and ESTABLISHED COMPETITOR flags)
3. **Business Opportunity Assessment** — top 3–5 cities with rationale; Vancouver
   WA benchmark comparison; corporate and team-building market; major events
   calendar; tourist and university city assessments; franchise options; multi-site
   scaling considerations; weekend vs weekday demand balance
4. **Commercial Real Estate & Location Data** — mall and retail centre
   opportunities (graded A/B/C); prime site assessment; lease rates per sq ft;
   physical property requirements; lease structure intelligence; red flags
5. **Regulatory & Operational Environment** — business registration; safety
   codes; ADA compliance; liquor licences; permitting and build timelines;
   small business grants
6. **Financial Benchmarks & Operating Costs** — revenue per room; build costs;
   break-even timeline; labour market and staffing costs; insurance; technology
   and booking systems; ancillary revenue potential

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
