# V2 source extreme audit — diagnostic only

Uses the unchanged validated Jan–Mar input and saved global bases. Both raw and ≤100-mile comparisons retain those same original bases; neither is refitted. No canonical artifact is modified and no cleaning decision is applied.

Distance thresholds are strict >; percentages use all input rows. Denominator bucket lower bounds are inclusive except zero, which is excluded; upper bounds are exclusive. Empty-bucket statistics are unavailable. Root-cause A and B counts are inclusive and overlap at C (both); A_only, B_only, C and D form a disjoint partition. These are descriptive flags, not proof of source errors or legitimate fares.

Weather-hour relative mean change is 100 × abs(diagnostic mean − raw mean) / abs(raw mean). Zero raw means would be undefined and counted separately. Top 10 affected cells are ranked by absolute mean change; the full table also includes both population SDs. Missing cells are not fabricated.

Checks reproduced canonical means and population SD, verified count conservation, and confirmed every canonical file hash unchanged. No clustering or production work. Source-cleaning decision required: extreme distance records materially affect means/SD; denominator sensitivity remains after the diagnostic cap.
