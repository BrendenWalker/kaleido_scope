# Planned duration and roast level

**Status:** Plan only. Not implemented.  
**Depends on:** post-FCs outgas RoR hold + early FirstCrack soft-brake cap (shipped on Energy first).  
**Audience:** next Hybrid refinement after those sensing / soft-brake fixes prove out on a weekly 600 g roast.

## Problem

Hybrid’s RoR target is **BT × phase**. That cannot know when the roast will end. The operator’s real goal is:

1. Let RoR rise to a peak.
2. Decline **smoothly** for the rest of the roast.
3. Land near an intended DROP (time and/or bean temp).

Decline rate therefore needs an **intended end**. You cannot predict the end from the live curve alone. You *can* state it: from this machine/charge’s history, or from an explicit roast-level choice.

Gaenke corpus (12 logs in `RoastHistory/`): CHARGE→DROP **median ~585 s (~9:45)**, FCs ~7:50, DROP BT ~196 °C. Nov 2026 Energy weeks already sit in that band. The Nov 16 failure was shape into/through crack (hot FCs entry + false probe dips), not total time — but planned duration is still the right next control axis once sensing is honest.

## Design (two layers)

Keep **phase baselines** (HP/FC / ET−BT) as they are. Add a **planned end** that only reshapes the **RoR target slope** after the peak (or after drying exit).

```text
roast level preset ──► planned_duration_s + planned_drop_bt
                              │
history default (optional) ───┘
                              │
                    RoastPlanner target RoR
                    (time-to-plan scales decline;
                     BT×phase still picks baselines)
```

Do **not** replace the phase machine with a single time polynomial. Do **not** silently re-average `RoastHistory/` every sample with no visible setting.

### Layer A — Planned duration (implement first)

| Item | Proposal |
| ---- | -------- |
| Setting | `hybridPlannedDurationS` (float, seconds CHARGE→DROP) |
| Default (M6 ~600 g) | **585** (Gaenke median). Editable. |
| Where | Hybrid / Device settings next to backend. Show as `mm:ss`. |
| When applied | At CHARGE (or Hybrid activate). Freeze for that roast. |
| Effect | After peak RoR (or DRY), slope `ror_target` toward a terminal RoR at `t_plan` (e.g. 3.5–5 °C/min at plan). Clamp remaining time so a late FCs cannot steepen into another crash. |
| Saved in `.alog` | Yes — record the planned duration used, like `hybridControlBackend`. |
| Not in scope for A | Reading the whole RoastHistory folder at runtime; auto-updating the default mid-streak. |

Optional later: a “Use lot median” button that scans recent same-title / same-weight logs **once** and writes the setting. Still a visible number the operator can override.

### Layer B — Roast level presets (implement after A)

Presets are named intents that fill Layer A (and DROP BT), not a second controller.

| Level | Planned duration (start point) | Planned DROP BT (start point) | Notes |
| ----- | ------------------------------ | ----------------------------- | ----- |
| Light / City− | ~8:30–9:00 | ~192–195 °C | Shorter plan; earlier decline |
| City (default band) | **~9:45 (585 s)** | **~196 °C** | Matches Gaenke median |
| Full City / City+ | ~10:00–11:00 | ~200–205 °C | Longer plan; slower late decline |

Exact numbers are calibrated from the operator’s sold cups, not locked here. Changing the preset only writes `planned_duration_s` and `planned_drop_bt`. Advanced users can still edit the two numbers directly.

Primary knob for this operator: **total time / development intent**, with DROP BT as the paired landing. If one must lead in the UI, lead with **roast level → duration**, and show DROP BT as the secondary field.

## What stays out until A/B exist

- Using background profile ΔBT as the RoR target (still eyes only).
- MPC as the weekly method (`hybrid_field_ab_plan.md` **Now testing** stays Energy).
- Per-lot ML or automatic length learning without a displayed setting.

## Acceptance

**Layer A:** one Energy roast with planned duration visible at CHARGE; RoR decline after peak is smoother toward DROP without fan pin at FCs; `.alog` records the plan used.

**Layer B:** switching City → Full City changes the two fields before CHARGE; no mid-roast preset change.

**Field gate:** still one knob per week in [hybrid_field_ab_plan.md](hybrid_field_ab_plan.md). Ship outgas hold + early soft-brake, roast one week, *then* open Layer A as the next one-knob change.

## Implementation sketch (when coding starts)

1. `HybridControllerConfig.planned_duration_s` + QSetting + Device UI field.  
2. `RoastPlanner`: after peak/DRY, interpolate RoR by `elapsed / planned_duration_s` (with clamps), while `detect_roast_phase` still drives baselines.  
3. Profile key `hybridPlannedDurationS` on save (CHARGE snapshot).  
4. Preset combo writing the two fields (Layer B).  
5. Tests: late FCs does not produce a steeper soft-brake than early FCs for the same overshoot; plan shorter than elapsed clamps cleanly.
