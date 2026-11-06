# Hybrid field refinement — weekly 600 g

**Audience:** Operator who roasts **one ~600 g batch per week** on a Kaleido M6.  
**Now testing:** **Energy.** Control mode is **Hybrid Controller**, Device backend **Energy** (`hybridControlBackend` = `energy`). Not Machine PID, not Software PID, and **not MPC**. MPC stays parked until this line is edited. The later switch is §10, and it is not this week's roast.  
**Goal:** Judge each week's Energy roast against last week. Change **one** Energy knob between weeks when the curve is not production-good (RoR shape + quiet fan).  
**Canonical control docs:** [kaleido_mpc_spec.md](kaleido_mpc_spec.md) §19.4, [README.md](../README.md).

The method for the next roast is the **Now testing** line. Sentences further down that still mention MPC are history or that later gate. They are not an instruction to select MPC. The 2026-11-01 Gaenke review followed an older "weekly MPC" cadence and treated an Energy roast as if MPC had run it.

Same-day Energy vs MPC pairs are **not** the plan. A second 600 g the same day ages the leftover green and makes next-week comparison worse than the extra pair is worth.

---

## 0. Study 1 (done) — what we learned

Three live pairs (Jul–Sep 2026). Spreadsheet / filenames are truth (P2 ran MPC first). Algorithm changed after P1. Those logs predate `hybridControlBackend` in the `.alog`; the spreadsheet is how you know which backend each one used.

| Finding | Implication |
| -------- | ----------- |
| Post-fix RoR shape was in typical declining-best-practice range | Do not freeze the study waiting for more matched pairs |
| Post-fix MPC fan travel ~3× Energy (sawtooth FC) | Fan hunting is a software problem. It is not a reason to make MPC the weekly roast |
| P1 heat-after-DROP and missed Start Heating | Appear fixed on P2/P3 logs |
| Dual-batch weeks leave stale green | Sequential one-batch refinement from here |

Energy is the method under test. MPC is not refined on the weekly roast until **Now testing** says so.

---

## 1. Success criteria (per roast, then a short streak)

Judge **this week's Energy roast** against last week's Energy roast, and against a frozen Energy reference of the same lot when you have one.

| Outcome | What you do next week |
| -------- | --------------------- |
| RoR declining, no scary FC-window peak, **fan not sawtoothing**, DROP cuts heat | Keep **Energy** on the same build. One good week does not switch the test to MPC |
| RoR still fine, fan still hunting or HP twitching | Stay on Energy only if you just landed the one knob aimed at that. Otherwise note it and do not add a second knob |
| RoR crash, runaway HP, oscillation that feels unsafe | Abort. Machine PID is for warmup recovery if Hybrid itself is the problem. File notes. Do not tune through it mid-roast |
| New lot, late CHARGE, missed FCs, or a build change | Count as a **labeled trial**, not a streak |

**Primary (from the `.alog`, CHARGE→DROP):**

1. **RoR shape** — does it decline through Maillard / FC the way you would accept in production? RMSE vs the built-in M6 schedule is supporting evidence, not a gate by itself.
2. **FC travel / hunting** — visual sawtooth plus ∑\|ΔFC\|. Target: in the same neighborhood as a good Energy roast of similar length (Study 1 Energy was ~900–1400), not 2–4× that.
3. **HP after DROP** — should snap toward 0, not linger.

**Secondary:** DROP BT & time, FCs time/BT, development time, cup notes if you cup that week.

**Which backend the log used:** read `hybridControlBackend` in the `.alog` (`energy` or `mpc`). The key is written when that roast hits CHARGE, and a resave keeps it. It is the record. The filename tag and anyone's memory are labels. Logs saved before the key existed do not have it; those still need the scorecard note. Opening a log does not change the backend the machine will use next.

---

## 2. Weekly cadence (one batch)

| Week | What you roast | Backend |
| ---- | -------------- | ------- |
| N | One 600 g Hybrid roast | **Energy** (the **Now testing** line) |
| N+1 | One 600 g Hybrid roast | Energy on the **same** build if week N was good; otherwise the one-knob change you noted |

An MPC roast is out of cadence until **Now testing** is edited. Do not add one the same day as the Energy batch.

Put last week's `.alog` on the Artisan **background** for eyes. Background must not drive control.

### One knob per week

Between weeks you **may** change the Energy controller (that is the point). Record the commit / note. Examples of "one knob": a fan-hunting patch, then later a schedule tweak — not both in the same roast.

Do **not** retune Hybrid PID / slews mid-roast because the curve looked weird.

---

## 3. What to freeze vs what to record

Freeze only what would make this week's roast uninterpretable.

| Variable | Rule |
| -------- | ---- |
| Charge weight | **600 g** |
| Machine | Same roaster, drum, probe paths |
| Control mode | **Hybrid Controller**, backend **Energy**. Not Machine PID, Software PID, or MPC |
| Schedule | Built-in M6 shape unless the one-knob change *is* the schedule |
| Background | Eyes only; same file for a streak if you can |
| DROP habit | Same intent (e.g. drop at FCs+… or BT …) during a streak |

**Record every week (expected to move):** lot / bag age, ambient, RH if you have it, pre-heat hold after SV, Artisan commit, CHARGE BT (late START is a confounder — note it), qualitative fan/RoR notes. Backend comes from the file (§1), not from this list.

---

## 4. Roast-day checklist

1. Backend **Energy**, matching **Now testing**. Control checkbox on; ET/BT = Kaleido.
2. Portion **one** 600 g charge. Write lot / bag-open on the scorecard.
3. Full cold-start pre-heat: warmup SV **195**, Start Heating, hold **25+ min** after SV is first reached (fixed clock, not eyeball).
4. **START** recording, then **CHARGE** at the usual hot-drum condition. If Artisan asks for beans that are already in, still mark CHARGE as you dump — late CHARGE (~90–110 °C BT) poisons drying comparison.
5. Mark **DRY / FCs / FCe / DROP** as usual. If you hit FCe by accident, note it; FCs is the one the controller wants.
6. Do **not** fight Hybrid with sliders unless aborting (§6).
7. After DROP: confirm heat goes to 0; save `.alog`. Open the file (or the scorecard copy) and confirm `hybridControlBackend` is `energy`. If it is `mpc`, this week does not count — the wrong method ran. Then fill the hand row.

Filename (reminder only; the `.alog` key wins if they disagree):

```text
YYYY-MM-DD_W{n}_energy_{lot-tag}_600g.alog
```

Glance notes only: sawtooth HP/FC? `fallback=True`? scary RoR near FCs? manual intervention? `hybridControlBackend` value?

`aw.hybridDiagnostics` (live, not the saved record): `backend`, `phase`, `target_ror`, `current_ror`, `pred_ror`, `energy_bias`, `hp`, `fc`, `fallback`. The saved record is the profile key `hybridControlBackend`.

---

## 5. Scorecard (hand fields)

The `.alog` already has times, BT, HP, FC, and (on saves from this build onward) `hybridControlBackend`. Copy that key onto the row so a review does not depend on opening the file. Fill what the log cannot reconstruct:

| Field | Example | Why hand |
| ----- | ------- | -------- |
| week ID | W4 | Streak label |
| .alog filename | `2026-11-01_W4_energy_gaenke_600g.alog` | Pointer |
| `hybridControlBackend` | `energy` | Copied from the `.alog`. This is which method ran |
| lot / bag open | El Socorro / day 7 | Aging |
| ambient (°F or °C) / RH% | 74 / 20 | Weather |
| pre-heat hold after SV (min) | 28 | Confounder |
| Artisan build / commit | `hybrid_control` @ … | What changed |
| one-knob since last week | "Energy Yellow heater hold" | Refinement log |
| manual intervention? | N | Invalidator for streak |
| qualitative | "smooth FC; no fan sawtooth" | Operator judgment |

---

## 6. Abort rules

Abort immediately (Machine PID if Hybrid itself is unsafe): runaway heater, stalled fan, rapid oscillation that looks unsafe, beans / equipment risk.

Mark the week **not counting** if: backend other than the **Now testing** line (`hybridControlBackend` is the check), not ~600 g, slider overrides, disconnect, charged on a cold drum, or a huge confounder you would not accept in production.

A botched week is a labeled trial. Roast Energy again next week after the note. Do not add a same-day makeup batch.

---

## 7. Light analysis (after each roast)

1. Read `hybridControlBackend` before interpreting the curve. If the key is missing, the log is from before it was stored — use the scorecard, and say so.
2. Overlay this week vs last week (same backend, or say they differ): BT, RoR, FC, HP.
3. Ask only: would I sell this roast? Did the fan sit still in drying then step up after crack, or chatter?
4. A good Energy week means roast Energy again. It does not start an MPC test. Switching the weekly method is §10, and it starts by editing **Now testing**.

Do **not** treat offline dual-backend replay of recorded BT as proof that one backend tracked better.

---

## 8. Minimal kit

- This doc, including the **Now testing** line
- Scorecard row per week, with `hybridControlBackend` copied from the `.alog`
- One 600 g charge from whatever lot you are actually drinking
- Timer for pre-heat hold after SV
- Artisan with Hybrid Controller and backend **Energy**
- Abort: leave Hybrid for Machine PID only if Hybrid itself is the problem

---

## 9. What not to do

- Don't select MPC because an older paragraph in this file, the spec, or a chat said "weekly MPC." **Now testing** is the method.
- Don't guess the backend when the `.alog` has `hybridControlBackend`. That key is the record. Filename and memory lose.
- Don't roast a second 600 g the same day "for science" if that green will go stale.
- Don't change two controller knobs in one week.
- Don't short pre-heat.
- Don't compare this Energy log to an MPC log, or to a different lot, without saying so.
- Don't hand-transcribe RoR RMSE / travel the `.alog` already has.

---

## 10. Later: MPC (not the current test)

Leave this section alone until you edit **Now testing**.

If you later want MPC as the weekly method, that is its own decision: two consecutive MPC roasts you would sell, same build, fan not sawtoothing, then consider making MPC the default in settings. Until **Now testing** names MPC, keep selecting Energy.

Useful follow-ons only when a week's Energy log warrants them: more fan damping, CHARGE-already-in dialog, FCe-without-FCs treated as FCs.
