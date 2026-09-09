# Kaleido Scope roadmap

Product sequence for this fork. Control math and MPC phases live in [kaleido_mpc_spec.md](kaleido_mpc_spec.md). Weekly roast notes: [hybrid_field_ab_plan.md](hybrid_field_ab_plan.md). README teaser: [../README.md](../README.md).

Each milestone should leave the app roastable on a Kaleido. Do not default MPC until M2’s field gate.

| Milestone | Status |
|-----------|--------|
| Hybrid Energy, Machine PID warmup → CHARGE, Lite MPC (optional), COOLDOWN | **Shipped** on `main` |
| **M0** Kaleido-only machines; keep Kaleido channels + generic extra loggers | **In flight** — `remove_support_for_other_machines` (test, then merge) |
| **M1** Machine presets + schedule editor | Next |
| **M2** Live diagnostics, quiet MPC fan, then gated MPC default | After M1 |
| Drum RC, `.alog` calibration wizard, learned plant | Later |

---

## Shipped

- Dual-actuator **Hybrid Controller** (Energy): declining RoR shape; HP slow, FC fast; air-first after first crack.
- Machine PID warmup (`AH=1`) until CHARGE, then Hybrid (`AH=0`).
- Optional **Lite MPC** backend; Energy is default and timeout fallback.
- **COOLDOWN** (air 100% / drum 10% until BT < 50°C, then all off). Manual button, not implicit on DROP.
- Artisan logging / graphs / `.alog` / `.aset`.

Background profiles are visual only. Hybrid does not follow background RoR.

---

## M0 — Kaleido machines, extra loggers stay

**Goal:** Config looks like a Kaleido app, not Artisan-with-fifty-roasters.

**Keep**

| Role | What |
|------|------|
| Meter | Kaleido BT/ET (Network / Serial). NONE / Virtual as needed. |
| Kaleido extras (same connection) | `+Kaleido SV/AT`, `+Kaleido Drum/AH`, `+Kaleido Heater/Fan` |
| Generic extra **loggers** | Phidget, Arduino TC4, Yocto, Virtual, NONE — second probe on the graph, not “part of the Kaleido” |

**Drop**

Other roasting **machines** as meter or extra (`+IKAWA`, Aillio, Hottop, Santoker, Fuji-as-machine, …). Machine presets under `src/includes/Machines/` except Kaleido Network / Serial.

**Not this milestone:** schedule editor, M1–M10 shape presets, diagnostic curves, defaulting MPC.

### Exit criteria

- Roast → Machine lists Kaleido Network and Kaleido Serial (plus leftover Kaleido Legacy only if you still need it).
- Device meter is Kaleido BT/ET; Hybrid / Machine PID / Software PID still work.
- Extra Devices can add the three `+Kaleido` channels **and** a Phidget / TC4 / Yocto / Virtual extra; those extras sample.
- Fuji, Aillio, IKAWA, Hottop, etc. are gone from machine and meter pickers.
- Hybrid roast + COOLDOWN still work on Network and Serial.
- Existing Kaleido `.alog` / `.aset` still load.

### In-flight branch

[`remove_support_for_other_machines`](https://github.com/BrendenWalker/kaleido_scope/tree/remove_support_for_other_machines) already strips other machines. Before merge, confirm generic extra **loggers** still work: locked scope keeps them. Dash-hiding (`-Phidget…`) or deleting logger drivers (`phidgets.py`, TC4, Yocto) is an overshoot — restore those extras if they cannot be added and sampled.

---

## M1 — One plan per machine, not one M6 600 g secret

Today Hybrid’s shape plan is baked for ~600 g M6 medium/light. Other models run that plan anyway.

**Scope**

1. Machine presets (M1 / M2 / M6 / M10 + charge weight) that swap the shape plan and plant priors.
2. Schedule editor in the UI (espresso vs filter, not only baked defaults). Persist in `.aset`.

**Exit:** picking a machine/charge preset changes the RoR/HP/FC schedule you can see in Device (or an obvious Hybrid settings pane). A 150 g M1 does not silently use the 600 g M6 table.

Control architecture: spec §18 “Machine profile YAML / UI presets”; spec §21 currently parks the editor as v1 out-of-scope — this milestone is when that moves in.

---

## M2 — Inspectable Hybrid, then quieter MPC

**Scope**

1. Live diagnostic curves: commanded HP/FC, phase, Energy Bias, predicted RoR.
2. MPC fan hunting (sawtooth FC vs Energy) until actuator travel is in the same neighborhood as a good Energy roast.
3. **Then** consider defaulting Hybrid backend to MPC.

**Gate (do not skip):** two consecutive weekly 600 g MPC roasts you would sell, same build, fan not sawtoothing. Abort remains Energy. Details: [hybrid_field_ab_plan.md](hybrid_field_ab_plan.md).

Defaulting MPC now is rejected until that streak exists.

---

## Later

- Drum speed (RC) as a third actuator (needs a model; do not couple HP/FC/RC blindly).
- Per-machine calibration wizard from local `.alog` files.
- Adaptive / learned thermal response; historical-roast ML.

Twin Tier 2 and learned gains are also listed as Planned/Future in the [MPC spec §18](kaleido_mpc_spec.md#18-roadmap).

---

## Out of scope (until explicitly pulled in)

- Forcing Machine PID or Software PID onto the Hybrid shape plan.
- Implicit COOLDOWN on DROP (keep the button; optional auto-cooldown can be a later checkbox).
- Using this fork as a generic Artisan replacement for non-Kaleido machines — stay on [upstream Artisan](https://github.com/artisan-roaster-scope/artisan).
