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

Plus a **13th, non-canonical node**: `cancer_risk`. Not one of López-Otín's 12 — the resource several of the interventions above (telomerase, epigenetic reprogramming, GH-based thymic regeneration) trade against, made directly treatable rather than left as an inert tally:

- **CAR-T therapy** — engineered T-cell infusion targeting accumulated tumor burden. Effectiveness scales with `car_t_fitness` (a side effect boosted by telomerase since the model's first version — Bai et al. 2015 — but never spent on anything until now). Costs a real, sizeable `inflammation` penalty every dose: cytokine release syndrome (CRS) is the expected clinical consequence of CAR-T activation, not a rare edge case (Lee et al. 2014, *Blood*)

Each has an intervention function (rapamycin-style mTOR inhibition, fasting/spermidine-style autophagy induction, anti-inflammatory, telomerase activation, senolytic clearance, NAD+/mitophagy induction, partial reprogramming, chaperone induction, niche-level stem cell signaling, thymic regeneration, fecal microbiota transplant, CAR-T infusion). Interventions don't just move their own node — they nudge coupled nodes, with **coefficients tiered by strength of evidence**, not fitted to data:

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
- **CAR-T effectiveness scales with `car_t_fitness`, not a flat rate**: telomerase-boosted CAR-T cells expanded ~300x vs 37x and survived ~80% vs near-total death in xenografts (Bai et al. 2015, *Cell Discovery*) — this pillar finally spends the fitness the model has tracked since its first version. Every dose costs a real `inflammation` penalty in return: cytokine release syndrome (CRS) is the expected clinical consequence of CAR-T activation, IL-6/IFN-γ/TNF-α driven, standard-of-care-reversible with tocilizumab (Lee et al. 2014, *Blood*) — not a token side effect.

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

Five policies, same starting patient, same coupling rules, now with all 12 hallmarks plus the CAR-T pillar:

```
policy                                  doses    burden  cancer_risk  car_t_fit
synergy-aware (1-step lookahead)           28    70.075        0.000      0.675
greedy (worst-first)                       20    72.744        0.081      0.550
round-robin                                25    75.963        0.000      0.550
random (seed=0)                            31    95.922        0.000      0.550
fixed priority (mtor/autophagy first)      34   101.187        0.000      0.675
```

**Making cancer risk directly treatable closes almost all of the safety gap in this regime.** `cancer_risk` drops from a 0.28-0.39 range (12 hallmarks, no CAR-T) to 0.000-0.081 across every policy — four of five reach exactly zero. Greedy is the interesting exception: it still finishes with a small residual (0.081) because it stops the instant every hallmark crosses the 0.1 threshold, and doesn't keep dosing cancer_risk past "good enough" the way the slower policies incidentally do by running more total steps before everything converges together. Doses went up for every policy (greedy 18→20, synergy-aware 21→28) — treating a 13th node costs doses, but here it buys back almost the entire cancer-risk cost from having 12 hallmarks worth of rejuvenation levers active.

## Continuous aging: is "amortal" even reachable as a maintenance regime?

Everything above answers "can a policy clean up a fixed initial mess?" — it stops the moment every hallmark is under threshold and never asks what happens next. Real aging doesn't stop: damage keeps accruing while you intervene. `run_continuous()` adds a background `AGING_RATE` (`STEP_SIZE / 10`, applied uniformly to every hallmark every step, treated or not) and runs for a long horizon (200 steps) with no early stop — the question isn't "how many doses to convergence," it's "does the policy hold the line indefinitely, or does damage outpace treatment."

```
policy                                  avg_burden  final_total  #>0.1  cancer_risk
-----------------------------------------------------------------------------------
synergy-aware (1-step lookahead)             3.295        1.594      3        1.000
random (seed=0)                              6.520        5.044      9        1.000
round-robin                                  6.662        6.450      9        1.000
greedy (worst-first)                         8.744       10.156     13        0.900
fixed priority (mtor/autophagy first)        9.861       10.000     10        1.000
```

**No policy reaches "amortal" — and adding a treatable cancer pillar made greedy dramatically worse, not better.** This is the single most informative result to come out of this model so far. With 12 hallmarks and no CAR-T pillar, greedy was competitive (2.421 avg burden, 2/12 above threshold). Adding a 13th treatable node — one whose own treatment carries a real `inflammation` cost — flips greedy from second-best to worst-but-one: 8.744 avg burden, **13/13 hallmarks above threshold**, worse than even fixed-priority's starvation failure.

**Why: greedy has no lookahead, so it can't see that treating `cancer_risk` lights a fire it will have to put out next.** A diagnostic run confirms the mechanism directly — `cancer_risk` receives more doses than any single other hallmark (8 of ~60 doses in a 60-step trace), because every CAR-T dose's CRS-driven inflammation spike promptly makes `inflammation` the new worst node, which greedy then treats, which does nothing to stop `cancer_risk` drifting back up from background aging in the meantime. The two nodes absorb a disproportionate share of greedy's attention while the other 11 — most of which get little or no "free" collateral benefit from treating cancer_risk or inflammation directly — drift upward largely unchecked. `cellular_senescence` is the clean counter-example: it never gets directly dosed at all in the same 60-step trace, because it receives so much incoming coupling from *other* hallmarks' treatments (telomerase `/2`, mitochondrial dysfunction `/4`, genomic instability `/4`, epigenetic alterations `/4`) that it never becomes the worst node in the first place. `telomere_attrition` and `cancer_risk` are the two hallmarks with the least incoming collateral help, which is exactly why they end up the hardest to hold down under continuous load.

**Synergy-aware avoids the trap by design**: its one-step lookahead literally simulates each candidate intervention and scores it by total system-wide dysfunction change, so a CAR-T dose's inflammation cost is priced into its score *before* it's chosen, not discovered a step later. This is arguably the clearest single argument in the whole model for why naive worst-first scheduling is dangerous once a treatment has a real, priced side effect — not a hypothetical concern, a reproduced one.

**Fixed-priority still fails by starving** `mtor` re-dosing (background aging keeps it just above zero, so the fixed-order policy never rotates past it) — a different, but equally real, failure mode from greedy's reactive trap.

> [!warning] Reading `cancer_risk` at the ceiling honestly
> `cancer_risk` is now a full hallmark (clamped to `[0, 1]` like every other node), and four of five policies still peg it at exactly 1.000 over a 200-step continuous-aging horizon — only greedy differs (0.900), and for the worst possible reason: it's too busy failing everywhere else to keep dosing it. That means this specific run **cannot distinguish** "synergy-aware's cancer cost" from "fixed-priority's" once both are pegged at the ceiling; it can only tell you whether a policy hit the ceiling at all. An uncapped or cumulative-dose cancer-risk accounting would be the natural next fix if this section gets taken further — flagged here rather than papered over.
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
