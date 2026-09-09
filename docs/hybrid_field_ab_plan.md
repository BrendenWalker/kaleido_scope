# Hybrid field refinement — weekly 600 g

**Audience:** Operator who roasts **one ~600 g batch per week** on a Kaleido M6.  
**Goal:** Keep Lite MPC as the daily driver if each week’s roast looks production-good (RoR shape + quiet fan), and change **one** thing between weeks when it doesn’t.  
**Canonical control docs:** [kaleido_mpc_spec.md](kaleido_mpc_spec.md) §19.4, [README.md](../README.md).

Same-day Energy vs MPC pairs are **not** the default anymore. A second 600 g the same day ages the leftover green and makes cupping / next-week comparison worse than the extra A/B precision is worth. Study 1 already showed RoR is in the right neighborhood; the remaining work is sequential (fan hunting first).

---

## 0. Study 1 (done) — what we learned

Three live pairs (Jul–Sep 2026). Spreadsheet / filenames are truth (P2 ran MPC first). Algorithm changed after P1.

| Finding | Implication |
| -------- | ----------- |
| Post-fix RoR shape was in typical declining-best-practice range | Do not freeze the study waiting for more matched pairs |
| Post-fix MPC fan travel ~3× Energy (sawtooth FC) | Fix FC hunting in software, then roast weekly MPC |
| P1 heat-after-DROP and missed Start Heating | Appear fixed on P2/P3 logs |
| Dual-batch weeks leave stale green | Sequential one-batch refinement from here |

Energy stays the abort / fallback backend. MPC is what you refine.

---

## 1. Success criteria (per roast, then a short streak)

Judge **this week’s roast** against last week and against a frozen Energy reference of the same lot when you have one. Do not wait for three matched pairs.


| Outcome | What you do next week |
| -------- | --------------------- |
| RoR declining, no scary FC-window peak, **fan not sawtoothing**, DROP cuts heat | Keep MPC. Optionally ship it as default after **two consecutive** good weeks on the same build |
| RoR still fine, fan still hunting or HP twitching | Stay on MPC only if you just landed a fan/HP patch; otherwise Energy until the patch exists |
| RoR crash, runaway HP, oscillation that feels unsafe | Abort to Energy / Machine PID; file notes; do not “tune through” it mid-roast |
| New lot, late CHARGE, missed FCs, or a build change | Count as a **labeled trial**, not a streak toward defaulting MPC |


**Primary (from the `.alog`, CHARGE→DROP):**

1. **RoR shape** — does it decline through Maillard / FC the way you would accept in production? RMSE vs the built-in M6 schedule is supporting evidence, not a gate by itself.
2. **FC travel / hunting** — visual sawtooth plus ∑\|ΔFC\|. Target: in the same neighborhood as a good Energy roast of similar length (Study 1 Energy was ~900–1400), not 2–4× that.
3. **HP after DROP** — should snap toward 0, not linger.

**Secondary:** DROP BT & time, FCs time/BT, development time, cup notes if you cup that week.

---

## 2. Weekly cadence (one batch)

| Week | What you roast | Backend |
| ---- | -------------- | ------- |
| N | One 600 g Hybrid roast | **MPC** (unless last week was unsafe) |
| N+1 | One 600 g Hybrid roast | MPC on the **same** build if week N was good; otherwise the one-knob change you noted |


Optional Energy roast: only when you need a sanity check on a **new lot** or after an abort. Never required the same day as MPC.

Put last week’s `.alog` (and/or a favorite Energy log of the same lot) on the Artisan **background** for eyes. Background must not drive control.

### One knob per week

Between weeks you **may** change the controller (that is the point). Record the commit / note. Examples of “one knob”: fan-hunting patch, then later a schedule tweak — not both in the same roast.

Do **not** retune Hybrid PID / slews mid-roast because the curve looked weird.

---

## 3. What to freeze vs what to record

You are not running a frozen three-week A/B. Freeze only what would make this week’s roast uninterpretable.


| Variable | Rule |
| -------- | ---- |
| Charge weight | **600 g** |
| Machine | Same roaster, drum, probe paths |
| Control mode | **Hybrid Controller** for the comparison window (not Machine PID / Software PID) |
| Schedule | Built-in M6 shape unless the one-knob change *is* the schedule |
| Background | Eyes only; same file for a streak if you can |
| DROP habit | Same intent (e.g. drop at FCs+… or BT …) during a streak toward defaulting MPC |


**Record every week (expected to move):** lot / bag age, ambient, RH if you have it, pre-heat hold after SV, Artisan commit, CHARGE BT (late START is a confounder — note it), qualitative fan/RoR notes.

---

## 4. Roast-day checklist

1. Backend **MPC** (or Energy if you are in abort-recovery week). Control checkbox on; ET/BT = Kaleido.
2. Portion **one** 600 g charge. Write lot / bag-open on the scorecard.
3. Full cold-start pre-heat: warmup SV **195**, Start Heating, hold **25+ min** after SV is first reached (fixed clock, not eyeball).
4. **START** recording, then **CHARGE** at the usual hot-drum condition. If Artisan asks for beans that are already in, still mark CHARGE as you dump — late CHARGE (~90–110 °C BT) poisons drying comparison.
5. Mark **DRY / FCs / FCe / DROP** as usual. If you hit FCe by accident, note it; FCs is the one the controller wants.
6. Do **not** fight Hybrid with sliders unless aborting (§6).
7. After DROP: confirm heat goes to 0; save `.alog`; fill the hand row.

Filename (single weekly roast):

```text
YYYY-MM-DD_W{n}_{mpc|energy}_{lot-tag}_600g.alog
```

Glance notes only: sawtooth HP/FC? `fallback=True`? scary RoR near FCs? manual intervention?

`aw.hybridDiagnostics`: `backend`, `phase`, `target_ror`, `current_ror`, `pred_ror`, `energy_bias`, `hp`, `fc`, `fallback`.

---

## 5. Scorecard (hand fields)

The `.alog` already has times, BT, HP, FC. Fill what it cannot reconstruct:


| Field | Example | Why hand |
| ----- | ------- | -------- |
| week ID | W4 | Streak label |
| .alog filename | `2026-09-13_W4_mpc_eso_600g.alog` | Pointer |
| lot / bag open | El Socorro / day 7 | Aging |
| ambient (°F or °C) / RH% | 74 / 20 | Weather |
| pre-heat hold after SV (min) | 28 | Confounder |
| Artisan build / commit | `hybrid_control` @ … | What changed |
| one-knob since last week | “MPC fan deadband/slew” | Refinement log |
| manual intervention? | N | Invalidator for streak |
| qualitative | “smooth FC; no fan sawtooth” | Operator judgment |


---

## 6. Abort rules

Abort immediately (Energy or Machine PID): runaway heater, stalled fan, rapid oscillation that looks unsafe, beans / equipment risk.

Mark the week **not counting toward a default-MPC streak** if: wrong backend, not ~600 g, slider overrides, disconnect, charged on a cold drum, or a huge confounder you would not accept in production.

A botched week is just a labeled trial. Roast MPC again next week after the note; do not add a same-day makeup batch.

---

## 7. Light analysis (after each roast, not after a 3-pair freeze)

1. Overlay this week vs last week (and vs Energy reference if same lot): BT, RoR, FC, HP.
2. Ask only: would I sell this roast? Did the fan sit still in drying then step up after crack, or chatter?
3. After **two consecutive** good MPC weeks on the same build → consider defaulting MPC.
4. If a clear, consistent gap remains (fan still hunts, RoR crash), bring the `.alog` + scorecard row to a coding session — one knob, then another week.

Do **not** treat offline dual-backend replay of recorded BT as proof that one backend tracked better.

---

## 8. Minimal kit

- This doc  
- Scorecard row per week  
- One 600 g charge from whatever lot you are actually drinking  
- Timer for pre-heat hold after SV  
- Artisan `hybrid_control` with Hybrid + backend selector  
- Abort: Device → Hybrid backend → Energy (or Machine PID for warmup recovery)

---

## 9. What not to do

- Don’t roast a second 600 g the same day “for science” if that green will go stale.  
- Don’t freeze the algorithm for three more matched pairs — Study 1 already answered the big tracking question.  
- Don’t change two controller knobs in one week.  
- Don’t short pre-heat.  
- Don’t judge MPC from an Energy log on a different lot without saying so.  
- Don’t hand-transcribe RoR RMSE / travel the `.alog` already has.

---

## 10. After a good streak

If two consecutive weekly MPC roasts look like production (quiet fan, declining RoR, DROP cuts heat), bring to a coding session only if you want MPC as the **default** backend in settings. Otherwise just keep selecting MPC.

Useful follow-ons only when a week’s log warrants them: more fan damping, CHARGE-already-in dialog, FCe-without-FCs treated as FCs.
