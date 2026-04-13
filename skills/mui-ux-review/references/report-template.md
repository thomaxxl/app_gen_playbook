# UX/UI Review Report Template

Use this template for serious page audits and adapt it to the review mode.

## 1. Context

- **Review target:** [page, screenshot, flow, or code area]
- **Page type:** [dashboard, list, detail, form, wizard, etc.]
- **Primary user goal:** [...]
- **Assumptions:** [...]
- **Device emphasis:** [desktop / mobile / both]

## 2. Overall verdict

Write a short paragraph that answers:

- Is the page understandable on first look?
- Can the user complete the main task without avoidable friction?
- What is the single biggest problem?
- What is the highest-leverage improvement?

## 3. Priority summary

- **Critical:** [count]
- **High:** [count]
- **Medium:** [count]
- **Low:** [count]

## 4. Findings

Use one block per finding.

### [Severity] [Short issue title]

- **Category:** [Layout / Navigation / Content / Feedback / Forms / Data / Accessibility / Performance / Mobile]
- **Evidence:** [Name the exact region, control, or behavior]
- **Why it matters:** [Explain the user cost]
- **Recommended change:** [State the fix]
- **Relevant MUI components/patterns:** [List concrete component names]
- **Effort:** [S / M / L]
- **Confidence:** [High / Medium / Low]

## 5. Quick wins

List the smallest changes with outsized benefit.

- [...]
- [...]
- [...]

## 6. Structural changes

List bigger changes that improve architecture, flow, or component fit.

- [...]
- [...]
- [...]

## 7. MUI implementation notes

Translate the main fixes into concrete MUI terms.

- Replace [current pattern] with [`ComponentA` + `ComponentB`] because [...]
- Keep [current component] but change its role from [...] to [...]
- Compose a missing pattern from [`Paper`, `Typography`, `List`, `Button`] for [...]

## 8. Follow-up checks

Only include when useful.

- usability test ideas
- analytics or experiment ideas
- accessibility verification steps
- state coverage to test

## Optional appendix: Category pass/fail sweep

For exhaustive audits, append this small matrix:

| Category | Pass / Warning / Fail | Notes |
|---|---|---|
| Layout & structure | | |
| Navigation | | |
| Content & readability | | |
| Interaction & feedback | | |
| Forms | | |
| Data presentation | | |
| Accessibility | | |
| Performance & states | | |
| Mobile responsiveness | | |
