# OpenWInD UI Upgrade Guide

This guide summarises the current state of the React UI in `ui/`, compares it with the
capabilities exposed in the Inria OpenWInD demo, and outlines a practical backlog to
close the gaps. Treat it as a living blueprint while evolving the application toward a
production-ready experience for first-time instrument designers.

## 1. Current application structure

* **Single-level navigation** – `App.jsx` exposes six high-level routes (Home,
  Geometry, Simulation, Optimization, Results, Settings) rendered inside a shared
  layout and toast provider.【F:ui/src/App.jsx†L1-L53】
* **Workspace-centric state** – `WorkspaceProvider` persists geometry, simulation
  options, optimisation history and user preferences to local storage, offering a
  single source of truth for every page.【F:ui/src/lib/workspace.jsx†L1-L191】
* **Home orientation** – the Home page already onboards users with quick-start
  guidance, preset loading, workspace status and API diagnostics.【F:ui/src/pages/Home.jsx†L9-L210】
* **Geometry tooling** – Geometry combines tone-hole tables, live spacing
  validation, a clarinet SVG preview and recommendation options backed by the
  server APIs.【F:ui/src/pages/Geometry.jsx†L1-L200】【F:ui/src/components/ClarinetPreview.jsx†L1-L95】
* **Acoustic analysis** – Simulation offers control over environmental
  parameters, note selection, impedance/intonation charts and export actions.
  【F:ui/src/pages/Simulation.jsx†L1-L307】【F:ui/src/components/ChartImpedance.jsx†L1-L22】
* **Optimisation workflow** – Optimisation streams progress events, visualises
  convergence and allows automatic application of the final geometry.
  【F:ui/src/pages/Optimization.jsx†L1-L240】
* **Result consolidation** – Results centralises exports, before/after comparison,
  sensitivity charts and optimisation metrics, linking back to the workspace state.
  【F:ui/src/pages/Results.jsx†L1-L240】

The architecture is modular and well suited for incremental enhancements; however,
several user-facing flows remain flatter or less discoverable than the Inria demo.

## 2. Required parity with the Inria demo

The Inria demo surface highlights a multi-section workflow with anchor navigation
("Define Geometry", "Acoustic Computations" plus nested panels such as "Bore",
"Holes/Valves", "Fingering Chart", "Pitch options", "Advanced options",
"Temporal Simulation", "Export Impedance", and reference comparison tools).【62f01f†L1-L16】
To deliver the same breadth inside the React UI:

1. **Geometry parity**
   * Introduce sub-navigation or tabs so users can switch between Bore settings,
     Tone-hole editing, Fingering charts and constraint panels without scrolling.
   * Expose fingering chart visualisations (not just note chips) to mirror the demo’s
     instrument diagram.
2. **Acoustic computations parity**
   * Group simulation inputs into "Main parameters", "Pitch options" and
     "Advanced options" sections matching the demo anchors.
   * Add a dedicated "Temporal Simulation" card for impulse/step response once the
     backend exposes time-domain data (currently absent from `simulationResult`).
3. **Export and reference parity**
   * Provide explicit "Export impedance" actions alongside JSON/CSV exports,
     allowing users to download impedance curves for external analysis.
   * Implement "Keep as reference" / "Remove reference" so players can pin a
     baseline simulation and compare future runs side by side.
4. **Internationalisation**
   * The demo offers English/French toggles; surface the same toggle globally using
     React-i18next (or Vite’s built-in i18n support) and store the language choice in
     `WorkspaceProvider`.
5. **Reference geometry management**
   * Extend the Results page to save and visualise multiple geometries, including a
     reference overlay in `ClarinetPreview` to emulate the demo’s comparison mode.

## 3. Recommended backlog

### 3.1 Information architecture

1. **Global layout upgrade**
   * Replace the flat nav with a two-tier layout (primary sections + secondary
     anchors) so users can jump straight to Bore, Holes/Valves, etc. Add `HashLink`
     support or sticky in-page tabs on Geometry and Simulation pages.
2. **Responsive panels**
   * Convert each `Card` block into a collapsible section with summary chips so
     tablet users can see key metrics at a glance.
3. **Contextual help system**
   * Extract the onboarding paragraphs into reusable `InfoTip` components and tie
     them to fields (e.g., `NumberField` accepts a `help` prop).

### 3.2 Geometry enhancements

1. **Bore & barrel editor**
   * Move bore length/diameter controls from global state into a dedicated `BoreForm`
     component placed ahead of the tone-hole table to mirror "Bore" section.
2. **Fingering chart**
   * Extend `ClarinetPreview` to render fingerings (closed/open states per note) and
     allow toggling note sets; the existing `selectedNotes` list from the Simulation
     page can be lifted into the workspace for reuse.
3. **Constraint tabs**
   * Separate constraint editing into "Main parameters" vs "Advanced options" tabs
     and wire them to `setConstraints`, ensuring validations remain in
     `validateHoleSpacing`.
4. **Recommendation wizard**
   * Offer a step-by-step modal (player profile → pitch → registers) that culminates
     in `recommend()` calls, improving clarity for first-time users.

### 3.3 Simulation upgrades

1. **Sectional layout**
   * Split `SimulationPage` into `MainParametersPanel`, `PitchOptionsPanel` and
     `AdvancedOptionsPanel` components. Map existing fields (`temp_C`, `concert_pitch_hz`,
     `transposition`, etc.) into those panels for parity with the demo sections.【F:ui/src/pages/Simulation.jsx†L40-L246】
2. **Temporal simulation**
   * Extend `simulate()` API to request time-domain responses and plot them using a
     new `ChartTemporalResponse` (e.g., area chart). Offer export buttons akin to the
     demo’s download link.
3. **Reference management**
   * Introduce `useReferenceSimulation` hook storing the last "Keep as reference"
     snapshot in local storage. Display dual charts comparing current vs reference
     impedance/intonation and add "Remove reference" control.
4. **Impedance export**
   * Reuse `handleExport('csv')` infrastructure to generate a CSV tailored to
     impedance (`freq,zin_abs,zin_re`) and surface the action in the Impedance card.

### 3.4 Optimisation & results

1. **Reference overlays**
   * Allow users to promote any optimisation result to "reference" so
     `ChartConvergence` and `ChartSensitivity` can overlay multiple runs for context.
2. **Simulation context**
   * Link the new reference simulation data to the Results page so the "Last
     simulation snapshot" reflects whether metrics come from the baseline or an
     optimisation run.【F:ui/src/pages/Results.jsx†L180-L240】
3. **DXF/STEP previews**
   * Provide quick previews (e.g., embed a lightweight viewer or show metadata) to
     reassure users the export succeeded without leaving the UI.

### 3.5 Accessibility & polish

1. **Keyboard discoverability**
   * Ensure all new tabs and collapsible sections use WAI-ARIA roles. The existing
     skip link establishes a good foundation.【F:ui/src/App.jsx†L22-L49】
2. **Visual hierarchy**
   * Adopt a consistent colour coding for joints/sections (already present in
     `ClarinetPreview`) across charts and tables to build muscle memory.【F:ui/src/components/ClarinetPreview.jsx†L1-L95】
3. **Empty states**
   * Mirror the demo’s placeholders by providing richer explanations when data is
     missing (e.g., callouts in Simulation when no notes are selected).

## 4. Implementation sequencing

1. **Sprint 1** – Navigation & localisation
   * Build the language toggle, add i18n wrappers, refactor page layouts into
     sectional components, and verify route-level accessibility.
2. **Sprint 2** – Geometry + simulation parity
   * Implement Bore/Fingering tabs, impedance export, reference simulation
     workflow, and restructure Simulation sections.
3. **Sprint 3** – Temporal tools & advanced exports
   * Coordinate with backend to expose time-domain responses, add temporal chart and
     file exports, and extend Results to compare references.
4. **Sprint 4** – Optimisation depth & final polish
   * Layer in multi-run comparisons, visual previews for exports and fine-tune the
     onboarding copy/tooltips based on user feedback.

## 5. Validation checklist

* ✅ Geometry page offers Bore, Holes/Valves, Fingering Chart and constraint tabs
  mirroring the Inria anchors.
* ✅ Simulation page groups controls into Main parameters, Pitch options, Advanced
  options, includes Temporal simulation chart and impedance export.
* ✅ Users can keep/remove reference simulations and compare charts.
* ✅ English/French localisation toggled globally with persisted preference.
* ✅ Results page surfaces before/after comparisons, convergence, sensitivity and
  reference overlays with matching downloads.
* ✅ Accessibility: all new controls keyboard-operable with descriptive labelling.

Completing this backlog aligns the React UI with the Inria demo’s breadth while
retaining the cleaner information architecture already present in the repository.
