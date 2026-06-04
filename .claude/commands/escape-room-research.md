You are a specialist business intelligence researcher focused on the escape room and immersive entertainment industry in the United States.

The target state for this research report is: **$ARGUMENTS**

Your task is to conduct thorough research on escape room business opportunities in **$ARGUMENTS** and produce a complete, authoritative HTML report file.

## Research Areas to Cover

Use web search to gather current, accurate data across all of the following areas:

### 1. State Demographics & Market Profile
- Total population and population density
- Age distribution (focus on 18–45 core escape room demographic)
- Household income levels and disposable income
- Urban vs rural split; top metro areas by population
- Education levels (correlate with puzzle/experience appetite)
- **Inbound Tourism & Visitor Economy (high priority indicator):**
  - Total annual visitor numbers to the state — domestic and international figures separately
  - Year-on-year trend: is tourism growing, flat, or declining?
  - Top 10 tourist attractions in the state by annual visitor numbers (national monuments, parks, historical sites, theme parks, landmarks, scenic areas, etc.)
  - Which cities or regions capture the highest concentration of tourist traffic
  - Average visitor length of stay and typical spend per day on activities and entertainment
  - Peak tourist seasons and shoulder seasons — map these against escape room demand potential
  - Visitor demographics: family groups, couples, solo travellers, corporate/conference visitors — identify which segments overlap with escape room audiences
  - Convention and conference activity: major venues, annual events, trade shows that bring in large groups (strong corporate booking indicator)
  - Any state tourism board data or "things to do" positioning that escape rooms could tap into
  - Rainy day / indoor activity demand: states with unpredictable or wet weather see higher demand for indoor entertainment from tourists
  - Flag any cities where tourism is the primary economic driver — these represent captive audiences actively seeking activities

- **University & College Population (high priority indicator):**
  - List all universities and colleges in the state with their city and total enrolled student population
  - Identify the top 5 cities by student population concentration
  - Flag any city where students represent more than 10% of the local population as a HIGH OPPORTUNITY market
  - Note proximity of campuses to city centres (walkable vs car-dependent)
  - Student spending patterns on entertainment and experiences
  - Academic calendar — identify peak demand periods (semester time) and low periods (summer, holidays) and how this affects revenue planning
  - Presence of Greek life (fraternities/sororities) — strong indicator of group booking demand
  - Postgraduate and international student population (higher disposable income segment)

### 2. Escape Room Market Landscape
- Estimated number of existing escape room venues in the state
- Key operators (independent vs franchise)
- Major franchise presence (The Escape Game, Breakout, Escapology, Room Escape Adventures, etc.)
- Saturation analysis: venues per capita vs national average
- Geographic distribution — which cities are underserved?
- Pricing benchmarks (average ticket price per person)
- Popular themes and formats in the region

### 3. Business Opportunity Assessment
- Top 3–5 recommended cities or metro areas with rationale
- Greenfield opportunities (markets with no or minimal operators)
- **High-tourism cities and regions — assess each identified tourist hotspot for:**
  - Existing escape room provision relative to visitor volume (is the market underserved for the footfall?)
  - Whether the dominant visitor type (families, couples, groups) aligns with escape room demographics
  - Proximity to major attractions — a venue within walking distance of a top-10 attraction benefits from overflow activity seekers
  - "Rainy day" positioning viability — tourist destinations with variable weather are strong candidates
  - Hotel and accommodation density nearby (guests actively look for evening and daytime activities)
  - Online activity platform presence (TripAdvisor Experiences, Viator, GetYourGuide) — assess whether escape rooms in similar tourist cities perform well on these platforms
- **University towns and college cities — assess each identified high-student city for:**
  - Whether an escape room venue already exists within 1 mile of campus
  - Walk-in trade potential from student foot traffic
  - Group booking potential (sports teams, clubs, societies, corporate-style team events from university departments)
  - Student discount pricing strategy viability
  - Freshers week and orientation period as major annual revenue spikes
  - Venue proximity to student union buildings, bars, and late-night entertainment strips
- Franchise vs independent operator considerations for this state
- Estimated addressable market size
- Seasonal demand factors (tourism peaks, weather, local events, university academic calendar)
- Competition from adjacent entertainment (VR arcades, axe throwing, mini golf, etc.)

### 4. Commercial Real Estate & Location Data (PRIORITY SECTION — provide maximum detail)

**Hard requirements — discard any property or area that does not meet these:**
- Minimum 2,000 sq ft (anything below is not suitable and must be excluded from the report)
- Target range: 3,500–6,000 sq ft to comfortably accommodate 4–6 escape rooms plus supporting spaces
- Room sizing context: each escape room typically requires 250–400 sq ft; 4–6 rooms therefore needs 1,000–2,400 sq ft of playable space, plus reception/waiting area (400–600 sq ft), GM monitoring station, corridors, bathrooms, storage, and staff areas

**For each of the top recommended cities, provide:**
- Current average commercial lease rate per sq ft (monthly and annual) — distinguish between Class A, B, and C space
- What "reasonable" price per sq ft looks like for that specific market vs what would be considered premium/overpriced
- Specific neighbourhoods, districts, or streets that represent prime locations (high footfall, visibility, passing trade)
- Proximity factors to prioritise: entertainment districts, restaurants and bars, cinemas, bowling alleys, shopping centres, transport hubs, hotels, tourist attractions
- Current vacancy rates for suitable commercial space in those areas
- Any specific properties or developments currently available that match the size criteria (sourced from LoopNet, CoStar, Crexi, or local commercial real estate listings where possible)
- Parking availability — surface, structured, or street (important for group bookings)
- Ground floor vs upper floor considerations (ground floor preferred for accessibility and walk-in trade; upper floor may offer lower rates)
- Loading access for large props, set dressing, and equipment delivery
- Fit-out considerations: ceiling height (minimum 9ft recommended), column-free floor plans preferred, power supply capacity

**Lease structure intelligence:**
- Typical lease lengths being offered in this market (3, 5, 10 year terms)
- Whether landlords in this market are offering rent-free periods or fit-out contributions for quality tenants
- Triple net (NNN) vs gross lease norms for the state
- Any tenant improvement allowances typical in this market

**Red flags to flag in the report:**
- Areas with declining footfall or retail blight
- Locations where parking is severely limited
- Markets where commercial rents have spiked unsustainably in the past 2 years
- Any enterprise zone incentives or small business grants available in the state that could offset real estate costs

### 5. Regulatory & Operational Environment
- State business registration requirements
- Relevant safety codes (fire safety, occupancy limits for immersive venues)
- Liquor licence availability (relevant for venues offering drinks)
- State small business support programs or incentives

### 6. Financial Benchmarks
- Industry average revenue per room per year
- Typical fit-out/build cost range for this market
- Estimated break-even timeline
- Any notable recent escape room openings, closures, or acquisitions in the state

## Output Instructions

1. Save the completed report as an HTML file at: `reports/escape-room-$ARGUMENTS.html` (use the state name, lowercase, spaces replaced with hyphens — e.g. `escape-room-new-york.html`)

2. The HTML file must be fully self-contained and print-ready (suitable for PDF conversion via browser print). Use inline CSS only — no external stylesheets or CDN links.

3. Use this structure and styling approach:
   - Clean, professional layout with a dark header bar (#1a1a2e) and white body
   - Accent colour: #e94560 (red) for headings and highlights
   - Section cards with light grey backgrounds (#f8f9fa) and subtle box shadows
   - A clear cover section at the top with: report title, state name, date generated, and "Prepared for: Wendy"
   - Table of contents with anchor links
   - Each research section as a clearly labelled card/section
   - An Executive Summary section at the top (after the cover) that distils the top 5 findings
   - A "Top Recommended Locations" summary table
   - A "Key Risks & Considerations" section at the end
   - Footer with: "Research conducted by Claude AI | $ARGUMENTS Escape Room Market Report | [current date]"

4. After saving the file, confirm the file path and tell the user they can open it in any browser and use File → Print → Save as PDF to generate the PDF version.

## Quality Standards
- All claims should be grounded in real, current data found via web search
- Where exact figures are unavailable, provide clearly labelled estimates with methodology
- Avoid generic filler — every paragraph should contain actionable, specific intelligence
- Flag any data that could not be verified with a clear note
- Aim for a report that reads as if produced by a specialist business consultancy
