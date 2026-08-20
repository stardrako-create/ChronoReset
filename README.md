# ChronoReset

**A literature-grounded control-policy experiment for aging intervention scheduling.**

ChronoReset asks a narrow, testable question: given a patient tracked across several Hallmarks of Aging with *real* cross-hallmark coupling constraints (not made up), does the order you intervene in actually matter — and does the obvious strategy (treat whatever's worst) hold up against alternatives?

This is deliberately **not** a mechanistic aging model. It doesn't try to be biologically accurate. It's a decision-policy sandbox where the *coupling rules between hallmarks* are grounded in real papers, and the thing under test is scheduling strategy, not biology.

## The setup

All 12 canonical hallmarks (López-Otín et al. 2023, *Cell*, "Hallmarks of aging: An expanding universe"), each a dysfunction level in `[0, 1]`:

- **Deregulated nutrient-sensing** (`mtor` / `autophagy_foxo`) — the mTOR/AMPK/FOXO axis
- **Disabled macroautophagy**
- **Chronic inflammation** ("inflammaging")
- **Telomere attrition**
- **Cellular senescence**
- **Mitochondrial dysfunction**
- **Genomic instability** — added deliberately, not to complete a checklist: it's the hallmark that decides whether aggressive intervention elsewhere is safe or just trades aging for cancer sooner (see below)
- **Epigenetic alterations** — partial OSK/OSKM reprogramming. Carries the model's *largest* `cancer_risk` coupling on purpose: unlike telomerase, where cancer risk is a dose-dependent side effect of an otherwise on-target mechanism, here the same factors that produce rejuvenation are, at higher dose or longer exposure, functionally sufficient for pluripotency and teratoma formation — the therapeutic effect and the failure mode sit on the same dose-response curve
- **Loss of proteostasis** — HSF1-dependent chaperone induction / ER-UPR support. Its one hard-evidenced coupling (Hsf1 deletion breaks HSC maintenance under aging/stress) makes it mechanistically upstream of stem cell exhaustion, not just correlated with it
- **Stem cell exhaustion** — niche-level rejuvenation (PGE2-EP4 signaling, exercise-driven satellite cell activation), not stem cell transplant. Classified *integrative* in López-Otín 2023 for a reason: it mostly receives couplings from other hallmarks (proteostasis, epigenetic alterations) rather than driving them
- **Altered intercellular communication** — narrowed to what's left after chronic inflammation split out as its own hallmark in 2023: thymic involution and endocrine-immune signaling drift, modeled here as GH+DHEA+metformin thymic regeneration (TRIIM-trial-style)
- **Dysbiosis** — one of the 3 hallmarks added in 2023. Young-donor fecal microbiota transplant / high-diversity microbiome restoration, coupled to inflammation via gut-barrier LPS translocation

Each has an intervention function (rapamycin-style mTOR inhibition, fasting/spermidine-style autophagy induction, anti-inflammatory, telomerase activation, senolytic clearance, NAD+/mitophagy induction, partial reprogramming, chaperone induction, niche-level stem cell signaling, thymic regeneration, fecal microbiota transplant). Interventions don't just move their own node — they nudge coupled nodes, with **coefficients tiered by strength of evidence**, not fitted to data:

| Coefficient | Meaning |
|---|---|
| `STEP_SIZE/2` | Direct mechanistic coupling or strong human interventional data |
| `STEP_SIZE/4` | Established causal link, animal/mechanistic evidence |
| `STEP_SIZE/8` | Real but context-specific / partial effect |

## What the coupling rules are actually based on

- **mTOR ↔ autophagy (hard, `/2`)**: not a soft correlation — mTORC1 and AMPK phosphorylate the *same residue set* on ULK1 in opposite directions (Kim, Kundu, Viollet & Guan 2011, *Nat Cell Biol*). The strongest-evidenced coupling in the model.
- **Autophagy → inflammation/mitochondria (`/4`)**: mitophagy clears damaged mitochondria/mtDNA that would otherwise trigger NLRP3 (Gupta et al. 2025); mitophagy is mechanistically a subset of macroautophagy (Ryu et al. 2016, *Nat Med*).
- **Telomerase → senescence (`/2`) and → CAR-T fitness**: critically short telomeres drive replicative senescence via ATM/ATR-p53; telomerase suppresses it. Transient TERT mRNA gave CD19 CAR-T cells ~300x vs 37x expansion and ~80% survival vs near-total death in controls in xenograft models (Bai et al. 2015, *Cell Discovery*).
- **Telomerase → inflammation (small, `/8`, a *cost* not a benefit)**: TERT has documented non-canonical pro-inflammatory signaling via STING, independent of telomere length (Akincilar et al. 2025, *Nat Cell Biol*) — but whole-organism AAV9-TERT gene therapy showed no organism-level inflammatory pathology (Bernardes de Jesus et al. 2012, *EMBO Mol Med*), so this is a small penalty, not a block.
- **Inflammation → telomere attrition (small, `/8`)**: cytokine-driven ROS accelerates telomeric DNA damage; this is *not* a strict either/or with telomerase activation as originally hypothesized — two independent literature passes found the two hallmarks are described as mutually *reinforcing* on the damage side, not exclusive.
- **Senescence → inflammation (`/2`)**: best human evidence of any two-hallmark link here — 3 days of dasatinib+quercetin cut circulating IL-1α, IL-6, MMP-9/12 within 11 days (Hickson et al. 2019).
- **Mitochondrial dysfunction → senescence/inflammation (`/4`)**: MiDAS (mitochondrial dysfunction-associated senescence) and mitophagy curtailing cytosolic-mtDNA-driven cGAS-STING activation (Fang et al. 2024, *Nat Commun*).
- **Senolytic "hit-and-run" dosing**: modeled as reduced efficacy on immediate repeat, not a block — matches the intermittent dosing paradigm validated in mouse senolytic trials (Xu et al. 2018; Justice et al. 2019).
- **NAD+ floor effect**: mitochondrial intervention has reduced efficacy above a threshold, matching the finding that NAD+ repletion doesn't improve already-healthy mitochondria, only depleted ones (Mills et al. 2016, *Cell Metab*).
- **Genomic instability offsets `cancer_risk`, it doesn't just accumulate more of it**: precise FOXO3 re-engineering (biallelic knock-in removing 2 of 3 AKT phosphorylation sites, making it constitutively nuclear) gave genomic stability, oxidative/genotoxic stress resistance, and *zero* tumorigenicity over 44 weeks in aged primates (Lei et al. 2025, *Cell*; OA companion in *Cell Regeneration*). The plausible mechanism for making telomerase reactivation safer isn't avoiding it — it's pairing it with genomic-stability support. PARP-1 and mitochondrial sirtuins draw from the same NAD+ pool (PARP-1−/− mice: shorter lifespan *and* accelerated carcinogenesis, not a tradeoff-free shortcut), so this hallmark is coupled to `mitochondrial_dysfunction` as well as to `cancer_risk`.
- **Epigenetic alterations carries the model's largest `cancer_risk` cost (`/2`), on purpose**: cyclic OSK(M) partial reprogramming restored heterochromatin (H3K9me3/H4K20me3), reduced gammaH2AX DNA-damage foci, and shifted senescence/SASP genes toward younger patterns in the same dataset (Ocampo et al. 2016, *Cell*) — but Takahashi & Yamanaka 2006 established the field by using *teratoma formation* as the functional proof the same factors work at all. Dropping c-MYC (Lu et al. 2020, *Nature*; Macip et al. 2024, *Aging*) and cycling exposure reduce this risk but don't remove it: rejuvenation and tumorigenesis sit on the same dose-response curve here, unlike telomerase's separate on-target-mechanism-plus-side-effect structure.
- **Epigenetic alterations → stem cell exhaustion (`/4`)**: cyclic OSKM in 12-month wild-type mice measurably improved skeletal-muscle regeneration and pancreatic beta-cell recovery — a functional outcome on stem/progenitor competence, not a biomarker proxy (Ocampo et al. 2016, *Cell*).
- **Proteostasis → stem cell exhaustion (`/4`)**: `Hsf1` deletion directly impairs hematopoietic stem cell maintenance under aging and ex vivo culture stress (Kruta et al. 2021, PMID 34388375) — causal, not correlational, and the strongest single coupling this hallmark has.
- **Intercellular communication → inflammation (`/4`) and → `cancer_risk` (small, `/8`)**: the TRIIM trial (Fahy et al. 2019, *Aging Cell*) — 9 men, 50-65yo, 12 months of GH+DHEA+metformin — MRI-confirmed thymic regeneration and ~2.5-year epigenetic age reduction across multiple clocks including GrimAge. The inflammation coupling is a plausible mechanism (restored naive T-cell output dampening an oligoclonal repertoire), not directly cytokine-measured in the trial. The cancer-risk penalty mirrors the same GH/IGF-1 axis already in the model via the inverse Laron-syndrome evidence under deregulated nutrient-sensing — same node, opposite intervention direction.
- **Dysbiosis → inflammation (`/4`) and → mitochondrial dysfunction (`/8`)**: gut barrier dysfunction lets LPS translocate into circulation, driving TLR4/NF-κB systemic inflammation; SCFA/butyrate restoration separately supports colonocyte mitochondrial function. Every positive intervention result here is young-donor-into-aged-recipient FMT — old-donor FMT is not neutral, it actively shortens lifespan in fly/fish models and worsens cognition in rodents.

## Lifestyle levers on the same nodes (research done, not yet in the model)

The coupling rules above are the intervention-drug side of the picture. A parallel literature pass looked at **drug-free levers** — diet, exercise, temperature, light, emotional state — that push the same nodes through different doors (this pass predates the genomic instability and epigenetic alterations additions, so it covers the original six). The headline finding: almost none of these open a new axis. They're mostly additional entry points into the nodes already above (e.g. carbs and protein both drive `mtor`, just through separate arms — insulin/PI3K vs. Rag-GTPase amino acid sensing).

A few results strong enough to flag here, none of them coded into `hallmarks_model.py` yet:

- **The antioxidant paradox.** Vitamin C+E taken around exercise blocks the very insulin-sensitivity and PGC1α/antioxidant-enzyme induction that exercise is supposed to produce (Ristow et al. 2009, *PNAS*). The ROS from exercise is the signal, not just the damage — neutralizing it chemically neutralizes the adaptation too.
- **Three real antagonisms, not just opposite directions on a node.** Antioxidants, cold-water immersion, and (short-term) NSAIDs all measurably blunt exercise adaptation by suppressing the same acute stress signal (ROS / mTORC1 activation / prostaglandins) that mediates the benefit — cold-water immersion specifically cut 12-week hypertrophy from +15% to +2% in a controlled trial (Roberts et al. 2015, *J Physiol*).
- **The sauna finding doesn't fit the model's `inflammation` node as currently defined.** Frequent sauna use doesn't lower CRP — it neutralizes the mortality risk *associated with* high CRP (HR 1.28 → 1.06) (Kunutsor et al. 2022, *Eur J Epidemiol*). That's resilience/buffering, not the direct-reduction semantics `inflammation` currently has.
- **Cold exposure is the cleanest lever found, mechanistically ready to integrate**: UCP1-dependent mitophagy with net mitochondrial gain despite active mitophagy (*iScience* 2021) — maps directly onto `mitochondrial_dysfunction` and `autophagy_foxo` with no ambiguity, unlike sauna.
- **The exercise J-curve has hysteresis, not a reset.** Well-recovered training cycles shift the *chronic* inflammatory baseline down over weeks (lower resting CRP/TNF-α); under-recovered cycles shift it up, cumulatively in both directions — not a per-session reset to zero (Mathot et al. 2025, *Innovation in Aging*).

## Roadmap: possibly a routine-optimizer, not just a policy sandbox

While doing this pass, a second, more applied framing kept surfacing: instead of "which hallmark is worst, treat it," a system where a person logs their actual routine and gets flagged conflicts ("don't ice-bathe right after that lift," "space these two sessions by 24-72h, not less") is a more directly useful shape for this same body of coupling/antagonism knowledge. Not built — the current repo is still the policy-comparison sandbox described above — but worth noting as the likely next direction if this project continues past v1.

## The actual result: does ordering matter?

Five policies, same starting patient, same coupling rules, now with all 12 hallmarks:

```
policy                                  doses    burden  cancer_risk  car_t_fit
synergy-aware (1-step lookahead)           21    61.356        0.325      0.675
greedy (worst-first)                       18    69.513        0.275      0.550
round-robin                                22    71.125        0.338      0.550
random (seed=0)                            28    85.537        0.388      0.675
fixed priority (mtor/autophagy first)      29    96.888        0.325      0.675
```

**Ordering matters more, not less, as the model grows.** The gap between the best policy (synergy-aware, 21 doses) and the worst (fixed-priority, 29 doses) widened compared to the 8-hallmark result — more coupled nodes means more ways to pick badly. Greedy worst-first flips its relative position here: it now has the *fewest* doses of any policy (18, beating synergy-aware's 21) but the second-worst burden of the top three, the opposite tradeoff shape from the 8-hallmark run where it tied synergy-aware on doses. That reversal is itself informative — which policy "wins" depends on which axis you're optimizing for, and that ranking is not stable as the coupling graph gets denser. `cancer_risk` stays in the 0.28-0.39 range across every policy — no policy at 12 hallmarks manages to offset it to zero the way greedy did back when genomic instability was the only cancer-risk-coupled hallmark in the model; the more rejuvenation levers you add, the harder safety gets to buy back with genomic-stability support alone. Round-robin again stays close to greedy on doses despite using zero severity information — a repeated finding across every version of this model so far: the *existence* of the coupling structure does more work than the specific ordering strategy layered on top of it.

## Continuous aging: is "amortal" even reachable as a maintenance regime?

Everything above answers "can a policy clean up a fixed initial mess?" — it stops the moment every hallmark is under threshold and never asks what happens next. Real aging doesn't stop: damage keeps accruing while you intervene. `run_continuous()` adds a background `AGING_RATE` (`STEP_SIZE / 10`, applied uniformly to every hallmark every step, treated or not) and runs for a long horizon (200 steps) with no early stop — the question isn't "how many doses to convergence," it's "does the policy hold the line indefinitely, or does damage outpace treatment."

```
policy                                  avg_burden  final_total  #>0.1  cancer_risk
-----------------------------------------------------------------------------------
synergy-aware (1-step lookahead)             2.242        0.719      3        1.000
greedy (worst-first)                         2.421        0.744      2        1.000
random (seed=0)                              4.667        4.325      9        0.938
round-robin                                  5.472        5.306      9        1.000
fixed priority (mtor/autophagy first)        8.959        9.000      9        0.000
```

**No policy reaches "amortal." The best two (greedy, synergy-aware) hold most hallmarks near threshold but still leave 2-3 of 12 chronically above it, and both drive `cancer_risk` to the ceiling (1.000) doing so.** That's the concrete, model-level version of the tension this project keeps running into: staying young costs safety, and this experiment is the first one where that cost is paid in full, not partially offset the way genomic-instability support could partially offset telomerase's cost in the one-shot version.

**Round-robin's earlier strength — competitive with greedy despite using zero severity information — collapses under continuous aging** (5.472 avg burden vs. greedy's 2.421, 9/12 hallmarks left above threshold vs. 2/12). The finding from the one-shot comparison ("which hallmark you treat matters less than whether the coupling exists at all") does not survive contact with a maintenance regime — severity-aware policies pull dramatically ahead once damage keeps arriving instead of sitting still to be cleaned up once.

**Fixed-priority fails in a genuinely different, more informative way: it starves.** Because background aging guarantees `mtor` is essentially never at exactly zero, and the policy always returns the first non-zero hallmark in its fixed order, it ends up re-dosing `mtor` almost every single step for 200 steps and never rotates to the rest — final burden is nearly maxed (9.0) and `cancer_risk` sits at 0.000 not because the policy is safe, but because it never touches any of the levers that carry a cancer-risk cost. Zero risk here is a symptom of total neglect, not of good scheduling.

> [!warning] Reading `cancer_risk = 1.000` honestly
> The side-effect accounting (`min(1.0, ...)` clamps in every intervention function) was designed for the short one-shot regime and saturates at the ceiling for any policy that succeeds at long-term maintenance here — three of five policies hit exactly 1.000. That means this specific run **cannot currently distinguish** "greedy's cancer cost" from "synergy-aware's cancer cost" from each other once both are pegged at the ceiling; it can only tell you whether a policy hit the ceiling at all. An uncapped or cumulative-dose cancer-risk accounting would be the natural next fix if this section gets taken further — flagged here rather than papered over.
>
> `AGING_RATE` itself is a single uniform constant, not evidence-tiered like the coupling coefficients elsewhere in this model — there is no comparable per-hallmark "background aging rate" literature to draw from. Treat the *qualitative* findings above (ordering matters more under continuous aging; fixed-priority starves; no policy reaches amortal) as the result, not the specific numbers.

## Running it

No dependencies beyond the standard library.

```bash
python hallmarks_model.py
```

Runs the greedy-policy trace once, `compare_policies()` for the one-shot comparison, then `compare_policies_continuous()` for the continuous-aging comparison above.

## Limitations

- **This is a scheduling-policy sandbox, not a biological simulator.** Coupling coefficients are evidence-tier heuristics (`/2`, `/4`, `/8`), not fitted parameters. Treat the *relative* policy comparison as the finding, not the absolute numbers.
- **No hormesis / non-monotonic dose-response.** Exercise-like interventions (not yet modeled) would need a "more isn't always better" curve — e.g. AMPK-mediated p53 activation is adaptive/mitochondrial-biogenesis-promoting at moderate acute stress but drives senescence at chronic/excessive stress. The current model treats every intervention as monotonically beneficial to its target, which doesn't hold for stress-hormetic interventions.
- **FOXM1's relationship to this model is unverified.** There's a plausible mTOR→FOXM1→senescence-suppression chain (mTORC1 activity reportedly promotes FOXM1 expression in some cancer-cell contexts, and FOXM1 loss is associated with senescence entry) but this hasn't been through the same literature-verification pass as the rest of the model and is **not** encoded here.
- **Discrete-time, rule-based, not a coupled ODE/SciML system.** The node names and coupling *directions* are the part meant to be right first; a continuous dynamical system could replace the update loop later without changing the node definitions.
- **Single patient, deterministic given a policy.** No population variation, no stochastic disease progression.
- **Donor-age asymmetry in dysbiosis is not encoded.** Old-donor fecal microbiota transplant is actively harmful in the literature (shortens lifespan in fly/fish models, worsens rodent cognition, promotes colonic tumor formation), not merely a null intervention — the model only represents the beneficial young-donor direction and doesn't penalize a hypothetical wrong-direction dose.

## License

MIT — see [`LICENSE`](LICENSE).

## Citation

See [`CITATION.cff`](CITATION.cff).

## Author

Manuel Afonso de Paiva Menezes de Sequeira — biochemistry student, FCT/UNL. Built independently, not affiliated with any institution.
