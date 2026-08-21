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
- **Stem cell exhaustion** — niche-level rejuvenation (PGE2-EP4 signaling, exercise-driven satellite cell activation, or transplant of pharmacologically rejuvenated aged HSCs). Classified *integrative* in López-Otín 2023 for a reason: it mostly receives couplings from other hallmarks (proteostasis, epigenetic alterations) rather than driving them. Finally has a real mammalian lifespan endpoint behind it — CASIN-rejuvenated aged HSC transplants gave +24.8% median / +34.0% max lifespan in aged mice (Montserrat-Vazquez et al. 2022)
- **Altered intercellular communication** — narrowed to what's left after chronic inflammation split out as its own hallmark in 2023: thymic involution and endocrine-immune signaling drift, modeled here as GH+DHEA+metformin thymic regeneration (TRIIM-trial-style). TRIIM (n=9, no placebo) is no longer this node's main human anchor — adult thymectomy (Kooshesh et al. 2023, NEJM, n=7,441) and a >27,000-adult thymic-health cohort (Bernatz et al. 2026, *Nature*) carry that weight now
- **Dysbiosis** — one of the 3 hallmarks added in 2023. Young-donor fecal microbiota transplant / high-diversity microbiome restoration, coupled to inflammation via gut-barrier LPS translocation

Plus a **13th, non-canonical node**: `cancer_risk`. Not one of López-Otín's 12 — the resource several of the interventions above (telomerase, epigenetic reprogramming, GH-based thymic regeneration) trade against, made directly treatable rather than left as an inert tally:

- **Tumor-directed CAR-T therapy** — engineered T-cell infusion targeting accumulated tumor burden. Effectiveness scales with `car_t_fitness` (a side effect boosted by telomerase since the model's first version — Bai et al. 2015 — but never spent on anything until now). Costs a real, sizeable `inflammation` penalty every dose: cytokine release syndrome (CRS) is the expected clinical consequence of CAR-T activation, not a rare edge case (Lee et al. 2014, *Blood*). Deliberately distinct from the anti-uPAR *senolytic* CAR-T folded into `cellular_senescence` below — conflating the two would combine effects that point in opposite directions on genomic instability

Senolytic CAR-T lives inside the existing `cellular_senescence` intervention rather than as a separate node — same target (clear the senescent-cell burden), a mechanistically distinct route (anti-uPAR engineered T cells, Amor et al. 2024, *Nature Aging*, instead of dasatinib+quercetin) to the same endpoint, with its own measured downstream effects (see coupling rules below).

Each has an intervention function (rapamycin-style mTOR inhibition, fasting/spermidine-style autophagy induction, anti-inflammatory, telomerase activation, senolytic clearance, NAD+/mitophagy induction, partial reprogramming, chaperone induction, niche-level stem cell signaling, thymic regeneration, fecal microbiota transplant, CAR-T infusion). Interventions don't just move their own node — they nudge coupled nodes, with **coefficients tiered by strength of evidence**, not fitted to data:

| Coefficient | Meaning |
|---|---|
| `STEP_SIZE/2` | Direct mechanistic coupling or strong human interventional data |
| `STEP_SIZE/4` | Established causal link, animal/mechanistic evidence |
| `STEP_SIZE/8` | Real but context-specific / partial effect |

## What the coupling rules are actually based on

- **mTOR ↔ autophagy (hard, `/2`)**: not a soft correlation — mTORC1 and AMPK phosphorylate the *same residue set* on ULK1 in opposite directions (Kim, Kundu, Viollet & Guan 2011, *Nat Cell Biol*). The strongest-evidenced coupling in the model.
- **Autophagy → inflammation/mitochondria (`/4`)**: mitophagy clears damaged mitochondria/mtDNA that would otherwise trigger NLRP3 (Gupta et al. 2025); mitophagy is mechanistically a subset of macroautophagy (Ryu et al. 2016, *Nat Med*).
- **Autophagy/fasting-mimetic dosing is hormetic, not monotonic**: the calorie-restriction dose-response paradox is well documented — moderate/intermittent CR or fasting gives robust benefit, severe/unbroken chronic restriction shows diminishing returns and real costs. Modeled as a dosing-pattern effect: 2 consecutive doses of `autophagy_foxo` behave as coded above; a 3rd consecutive dose with no break drops the benefit and adds a `cellular_senescence` cost instead. The molecular mechanism is genuinely more context/cell-type-dependent than one clean AMPK-p53 switch — AMPK activation shifts p53 phosphorylation in *opposite* directions in fibroblasts vs. keratinocytes — so this is deliberately encoded as a pattern effect, not a single named pathway flip.
- **Telomerase → senescence (`/2`) and → CAR-T fitness**: critically short telomeres drive replicative senescence via ATM/ATR-p53; telomerase suppresses it. Transient TERT mRNA gave CD19 CAR-T cells ~300x vs 37x expansion and ~80% survival vs near-total death in controls in xenograft models (Bai et al. 2015, *Cell Discovery*).
- **Telomerase → inflammation (small, `/8`, a *cost* not a benefit)**: TERT has documented non-canonical pro-inflammatory signaling via STING, independent of telomere length (Akincilar et al. 2025, *Nat Cell Biol*) — but whole-organism AAV9-TERT gene therapy showed no organism-level inflammatory pathology (Bernardes de Jesus et al. 2012, *EMBO Mol Med*), so this is a small penalty, not a block.
- **Inflammation → telomere attrition (small, `/8`)**: cytokine-driven ROS accelerates telomeric DNA damage; this is *not* a strict either/or with telomerase activation as originally hypothesized — two independent literature passes found the two hallmarks are described as mutually *reinforcing* on the damage side, not exclusive.
- **Senescence → inflammation (`/2`)**: best human evidence of any two-hallmark link here — 3 days of dasatinib+quercetin cut circulating IL-1α, IL-6, MMP-9/12 within 11 days (Hickson et al. 2019).
- **Mitochondrial dysfunction → senescence/inflammation (`/4`)**: MiDAS (mitochondrial dysfunction-associated senescence) and mitophagy curtailing cytosolic-mtDNA-driven cGAS-STING activation (Fang et al. 2024, *Nat Commun*).
- **Senolytic "hit-and-run" dosing**: modeled as reduced efficacy on immediate repeat, not a block — matches the intermittent dosing paradigm validated in mouse senolytic trials (Xu et al. 2018; Justice et al. 2019).
- **NAD+ floor effect**: mitochondrial intervention has reduced efficacy above a threshold, matching the finding that NAD+ repletion doesn't improve already-healthy mitochondria, only depleted ones (Mills et al. 2016, *Cell Metab*).
- **Genomic instability offsets `cancer_risk`, it doesn't just accumulate more of it**: precise FOXO3 re-engineering (biallelic knock-in removing 2 of 3 AKT phosphorylation sites, making it constitutively nuclear) gave genomic stability, oxidative/genotoxic stress resistance, and *zero* tumorigenicity over 44 weeks in aged primates (Lei et al. 2025, *Cell*; OA companion in *Cell Regeneration*). The plausible mechanism for making telomerase reactivation safer isn't avoiding it — it's pairing it with genomic-stability support. PARP-1 and mitochondrial sirtuins draw from the same NAD+ pool (PARP-1−/− mice: shorter lifespan *and* accelerated carcinogenesis, not a tradeoff-free shortcut), so this hallmark is coupled to `mitochondrial_dysfunction` as well as to `cancer_risk`.
- **Genomic instability → cellular senescence, upgraded to `/2`**: FoxM1 is repressed with age, and that repression drives mitotic mis-segregation and aneuploidy-driven senescence; re-inducing FOXM1 in aged/progeroid fibroblasts prevents the aneuploidy and reverses senescence phenotypes (Macedo, Ribeiro et al. 2018, *Nat Commun* 9:2834, PMID 30026603). This mechanism was specifically checked because an earlier version of this model flagged an unverified mTOR→FOXM1 speculation — that link didn't hold up, but this genomic-stability mechanism does, with real mammalian lifespan data behind it: cyclic FOXM1 transgene induction significantly extended lifespan in both Hutchinson-Gilford progeria *and* naturally aged mice (Ribeiro, Macedo et al. 2022, *Nature Aging*, "In vivo cyclic induction of the FOXM1 transcription factor delays natural and progeroid aging phenotypes and extends healthspan", PMID 37118067). Two independent causal mechanisms — DDR-driven senescence entry and FOXM1/aneuploidy — now converge on this one edge, which is why the tier moved up, not because either mechanism alone got stronger.
- **Epigenetic alterations carries the model's largest `cancer_risk` cost (`/2`), on purpose**: cyclic OSK(M) partial reprogramming restored heterochromatin (H3K9me3/H4K20me3), reduced gammaH2AX DNA-damage foci, and shifted senescence/SASP genes toward younger patterns in the same dataset (Ocampo et al. 2016, *Cell*) — but Takahashi & Yamanaka 2006 established the field by using *teratoma formation* as the functional proof the same factors work at all. Dropping c-MYC (Lu et al. 2020, *Nature*; Macip et al. 2024, *Aging*) and cycling exposure reduce this risk but don't remove it: rejuvenation and tumorigenesis sit on the same dose-response curve here, unlike telomerase's separate on-target-mechanism-plus-side-effect structure.
- **Epigenetic alterations → stem cell exhaustion (`/4`)**: cyclic OSKM in 12-month wild-type mice measurably improved skeletal-muscle regeneration and pancreatic beta-cell recovery — a functional outcome on stem/progenitor competence, not a biomarker proxy (Ocampo et al. 2016, *Cell*).
- **Proteostasis → stem cell exhaustion (`/4`)**: `Hsf1` deletion directly impairs hematopoietic stem cell maintenance under aging and ex vivo culture stress (Kruta et al. 2021, PMID 34388375) — causal, not correlational, and the strongest single coupling this hallmark has. Reinforced by two 2025-2026 mammalian HSC papers (Bergo et al. 2026, *Nat Commun* — MDA5/inflammaging/proteostasis/HSC chain; Arif et al. 2025, *Cell Stem Cell* — lysosomal dysfunction in aged HSCs) — still no mammalian organismal-lifespan endpoint for a selective proteostasis intervention, which stays this hallmark's honest evidentiary gap.
- **Stem cell exhaustion → intercellular communication (`/4`)**: hypothalamic Sox2/Bmi1+ stem/progenitor cells control organism-wide aging speed partly via exosomal microRNAs released into cerebrospinal fluid — ablation shortened, engineered implantation extended, mouse lifespan (Zhang et al. 2017, *Nature*, n=23 vs 21 in the key survival comparison). An experimentally addressed mechanism, and literally an intercellular-communication pathway, not just a correlation between two hallmark labels.
- **Intercellular communication → inflammation (`/4`) and → `cancer_risk` (net small, two opposing terms)**: the TRIIM trial (Fahy et al. 2019, *Aging Cell*) — 9 men, 50-65yo, 12 months of GH+DHEA+metformin — MRI-confirmed thymic regeneration and ~2.5-year epigenetic age reduction across multiple clocks including GrimAge, plus a causal mouse mechanism (Kanemaru et al. 2026, *Nat Commun*: thymulin, a thymus-derived peptide, suppresses age-associated myeloid inflammation via heterochronic parabiosis experiments, with human PBMC support). The cancer-risk term is now two competing pieces, not one: a `/8` GH/IGF-1-driven cost (same axis as the inverse Laron-syndrome evidence under deregulated nutrient-sensing) and a smaller `/16` immune-surveillance offset — Kooshesh et al. 2023 (*NEJM*, 1,420 thymectomy patients vs. 6,021 controls, 1,146 matched) found adult thymus *removal* roughly doubled cancer incidence (7.4% vs 3.7%, RR 2.0) and nearly tripled 5-year mortality (8.1% vs 2.8%, RR 2.9), implying restored thymic output plausibly protects via immunosurveillance — inferred from a removal study, not an addition study, hence the smaller weight and why it offsets rather than cancels the GH cost.
- **Dysbiosis → inflammation (`/4`) and → mitochondrial dysfunction (`/8`)**: gut barrier dysfunction lets LPS translocate into circulation, driving TLR4/NF-κB systemic inflammation; SCFA/butyrate restoration separately supports colonocyte mitochondrial function. Every positive intervention result here is young-donor-into-aged-recipient FMT — old-donor FMT is not neutral, it actively shortens lifespan in fly/fish models and worsens cognition in rodents. A persistently *elevated* `dysbiosis` level (above 0.5) now also carries a small passive `inflammation` cost every step in the continuous-aging mode, whether or not it's being actively treated that step — a leaky gut barrier doesn't stop translocating LPS just because it isn't the current target, which is the passive-harm side of the same donor-age asymmetry.
- **Senolytic anti-uPAR CAR-T → stem cell exhaustion (`/4`) and → dysbiosis (`/8`)**: a mechanistically distinct route into the existing `cellular_senescence` intervention, not tumor-directed CAR-T. Eskiocak et al. 2026 (*Nature Aging*) gave therapeutic anti-uPAR CAR-T to 18-month mice: increased intestinal stem cell number/proliferation, restored aged-crypt organoid-forming capacity, and shifted the microbiome toward a more youthful configuration alongside the barrier/stem-cell rescue — the same paper measured both downstream effects together, which is why they're both coded here rather than inferred separately.
- **Tumor-directed CAR-T effectiveness scales with `car_t_fitness`, not a flat rate**: telomerase-boosted CAR-T cells expanded ~300x vs 37x and survived ~80% vs near-total death in xenografts (Bai et al. 2015, *Cell Discovery*) — this pillar finally spends the fitness the model has tracked since its first version. Every dose costs a real `inflammation` penalty in return (CRS, Lee et al. 2014, *Blood*), which now scales up further if `genomic_instability` is already elevated (>0.3) — pre-existing clonal hematopoiesis raised grade ≥2 CRS from 28% to 60% (OR 3.9, Goldsmith et al. 2024, *Transplant Cell Ther*, n=62).
- **Tumor-directed CAR-T → genomic instability (`/8`)**: the reverse direction — conventional CAR-T can accelerate pre-existing/incipient clonal hematopoiesis. Small clones (<1% VAF) expanded ~3.37x after CD30 CAR-T vs ~1.20x for larger clones (p=0.0014, Kapadia et al. 2024, *Cytotherapy*, n=26, 154 longitudinal samples); CAR-T-driven bone-marrow inflammation, not lymphodepletion alone, was required to reproduce clonal selection in immunocompetent mice (Ben Khelil et al. 2025, *Sci Transl Med*). This is expansion/selection of existing abnormal clones, not proof CAR-T mutagenizes the host — deliberately modest and generic-context weighted, since the underlying evidence is specifically hematologic-malignancy CAR-T.

## Refractory periods: not every intervention is redosable every step

Three interventions have a hard minimum interval between doses (`REFRACTORY_STEPS`), because their underlying evidence explicitly describes non-continuous dosing, not because every intervention should have one — most of the model's interventions (rapamycin, senolytics, anti-inflammatories, FMT) don't specify a hard redosing constraint the way these three do:

- `telomere_attrition` (4 steps) — Bernardes de Jesus et al. 2012 used a single AAV9-TERT injection, not a repeatable pill.
- `cancer_risk` / tumor-directed CAR-T (3 steps) — a manufactured cell product that persisted long-term (>1 year) in the underlying mouse study (Amor et al. 2024); re-infusing weekly has no basis in the evidence.
- `epigenetic_alterations` (2 steps) — the underlying protocols are explicitly cyclic (2 days on/5 off in Ocampo et al. 2016; 1 week on/1 week off in Macip et al. 2024), so a hard minimum reflects the OFF half of that cycle.

This is a translation of a real-world constraint into abstract model steps, not a calendar-time claim — the model has no explicit step-to-days/weeks conversion, so treat the specific step counts as illustrative, not calibrated.

**This changed which policy wins, not just by how much.** Before refractory periods, deeper lookahead was a clean win in the one-shot regime (2-step beat 1-step on both doses and burden). With refractory periods active, that reverses: **1-step synergy-aware now has the fewest doses of any policy (25), beating both 2-step (30) and 3-step (28)** — deeper lookahead "wants" to redose something that's refractory-blocked more often than shallower lookahead does, and ends up settling for worse alternatives more frequently as a result. See the results tables below for the full picture, including what happens under continuous aging.

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

Seven policies now, same starting patient, same coupling rules, all 12 hallmarks plus the CAR-T pillar, refractory periods active — `make_policy_lookahead(depth)` generalizes synergy-aware from 1-step to N-step simulated lookahead:

```
policy                                  doses    burden  cancer_risk  car_t_fit
synergy-aware (1-step lookahead)           25    65.513        0.050      0.550
3-step lookahead                           23    67.150        0.100      0.675
2-step lookahead                           29    68.406        0.000      0.675
greedy (worst-first)                       19    71.319        0.050      0.550
round-robin                                25    73.488        0.000      0.550
random (seed=0)                            28    81.716        0.016      0.550
fixed priority (mtor/autophagy first)      31    98.447        0.084      0.675
```

**Refractory periods flipped which policy wins.** Before they existed, 2-step lookahead cleanly beat 1-step on both doses and burden. With them active, **1-step synergy-aware wins on burden (65.513)** while 3-step edges it on doses (23 vs 25) at the cost of a *higher* `cancer_risk` residual (0.100 vs 0.050) — deeper lookahead now trades safety for dose-count rather than cleanly winning on both axes the way 2-step used to. The mechanism: a deeper simulation more often "wants" to redose something that's currently refractory-blocked, and has to settle for a worse real alternative when it can't — a cost that only grows with simulated depth, though hormesis (see below) and the FOXM1-driven senescence-coupling upgrade also reshuffled these numbers from the pre-audit version.

## Continuous aging: is "amortal" even reachable as a maintenance regime?

Everything above answers "can a policy clean up a fixed initial mess?" — it stops the moment every hallmark is under threshold and never asks what happens next. Real aging doesn't stop: damage keeps accruing while you intervene. `run_continuous()` adds a background `AGING_RATE` (`STEP_SIZE / 10`, applied uniformly to every hallmark every step, treated or not) and runs for a long horizon (200 steps) with no early stop — the question isn't "how many doses to convergence," it's "does the policy hold the line indefinitely, or does damage outpace treatment."

```
policy                                  avg_burden  final_total  #>0.1  cancer_risk  uncapped
-----------------------------------------------------------------------------------------------
synergy-aware (1-step lookahead)             2.969        1.756      4        1.000    14.028
2-step lookahead                             3.159        1.844      4        1.000    15.219
3-step lookahead                             3.765        2.288      5        1.000    13.978
round-robin                                  6.638        6.275      9        1.000     5.625
random (seed=0)                              6.822        6.006     10        0.850     4.153
greedy (worst-first)                         9.232       10.128     12        0.866     2.569
fixed priority (mtor/autophagy first)        9.895       10.000     10        1.000     5.000
```

**No policy reaches "amortal."** Adding a 13th treatable node whose own treatment carries a real `inflammation` cost still flips greedy toward near-total failure: 9.232 avg burden, **12/13 hallmarks above threshold**, still worse than fixed-priority's starvation failure. Why: greedy has no lookahead, so it can't see that treating `cancer_risk` lights an inflammation fire it will have to put out next, and gets trapped reactively cycling between the two while the other hallmarks — most of which get little or no free collateral benefit from treating either — drift upward largely unchecked.

**Lookahead depth still shows more-is-worse on burden, but the uncapped column is no longer perfectly monotonic.** 1-step (2.969 / 1.756) still clearly beats 2-step (3.159 / 1.844), which still clearly beats 3-step (3.765 / 2.288) on avg_burden and final_total — that part of the finding holds up even after the hormesis and FOXM1 changes reshuffled the underlying dynamics. But on `cancer_risk_uncapped` specifically, 3-step (13.978) actually comes in *below* both 1-step (14.028) and 2-step (15.219) this run — not the clean staircase seen before. Read this as: deeper lookahead reliably costs more burden under continuous aging, but its effect on true cancer-risk exposure is noisier than the burden effect, not a second guaranteed cost stacking on top of the first.

**The uncapped column remains the real finding of this round.** `cancer_risk` still hits exactly 1.000 for four of seven policies. `cancer_risk_uncapped` answers what the clamped number can't: **all three lookahead-based policies still run up far more true cancer-risk exposure (14.0-15.2) than any non-lookahead policy (2.6-5.6)** — roughly 3-6x more. Greedy, despite catastrophic overall failure, still has the *smallest* uncapped cancer-risk tally of all seven (2.569) — its failure is neglecting everything else, not mismanaging cancer risk specifically.

**Why lookahead policies rack up more raw cancer-risk exposure while still winning on burden**: they're willing to let `cancer_risk` swing higher between treatments — trading a temporarily worse cancer-risk trajectory for a better whole-system trajectory — and they have the treatment throughput to bring the *visible*, clamped number back to the ceiling by the time it's measured. The clamp doesn't lie, but it hides how much larger a debt was run up and paid back versus never run up at all.

**Fixed-priority still fails by starving** `mtor` re-dosing (background aging keeps it just above zero, so the fixed-order policy never rotates past it) — a different, but equally real, failure mode from greedy's reactive trap. Its uncapped cancer-risk (5.000) sits in the same moderate range as round-robin.

**The honest summary**: no single number in this table tells you "the best policy" — burden-optimal and cancer-risk-conservative are in real tension regardless of how far ahead a policy looks, and looking further ahead makes the burden side of that tension worse, not better, even if its effect on cancer-risk exposure specifically is less predictable than that.

## Population variation: does the ranking hold across patients?

Every comparison above runs exactly one canonical starting patient — deterministic given a policy. `compare_policies_population()` runs the one-shot comparison across 20 patients with independently jittered starting hallmark levels (±0.1, a simple stand-in for individual variation, not a validated population model):

```
policy                                  doses_mean  doses_sd  burden_mean  burden_sd
synergy-aware (1-step lookahead)             24.50      1.43        64.36       3.45
greedy (worst-first)                         21.35      1.28        70.24       3.76
round-robin                                  26.10      1.97        73.68       4.44
random (seed=0)                              29.00      2.95        81.14       6.77
fixed priority (mtor/autophagy first)        33.35      1.98        98.98       5.56
```

**The one-shot ranking holds up.** Synergy-aware still wins on burden, greedy still wins on doses, fixed-priority still loses on both — across 20 different starting patients, not just the one canonical starting point every other table in this README uses. Standard deviations are modest relative to the means (roughly 5-10% coefficient of variation on burden) — individual variation shifts the exact numbers but doesn't scramble which policy is better than which. Lookahead-depth policies (2-step, 3-step) are deliberately excluded here to keep 20-patient runs fast; see `compare_policies()` for those on the single canonical patient.

> [!warning] What's still a simplifying assumption, not a researched parameter
> `AGING_RATE` is a single uniform constant, not evidence-tiered like the coupling coefficients elsewhere in this model. A literature pass *did* turn up candidate native-unit background rates for a few hallmarks (telomere attrition ~25-35 bp/year, genomic instability ~40 new somatic mutations/year in sampled adult stem cells, thymic output a ~15.7-year half-life) — but converting incommensurable units (base pairs, mutation counts, an exponential half-life) into one shared `[0,1]` dysfunction scale per hallmark, and doing it in a way that isn't itself a hidden, unvalidated assumption, was judged not worth doing yet: real background aging rate varies enormously person-to-person and by far more factors than the model currently represents, and a differentiated-but-wrong set of constants would be worse than an honestly uniform one. `cancer_risk_uncapped` fixes the ceiling-saturation problem but is still built on the same evidence-tiered coupling coefficients as everything else, so its *relative* ranking across policies is more trustworthy than its absolute values. Treat the qualitative findings above (ordering matters more under continuous aging; fixed-priority starves; lookahead depth trades cancer-risk exposure for burden reduction and gets worse, not better, past 1 step; no policy reaches amortal) as the result, not the specific numbers.

## Running it

No dependencies beyond the standard library.

```bash
python hallmarks_model.py
```

Runs the greedy-policy trace once, `compare_policies()` for the one-shot comparison (now including 1/2/3-step lookahead), `compare_policies_continuous()` for the continuous-aging comparison, then `compare_policies_population()` for the 20-patient variation check. Full run takes ~40s, almost entirely the 3-step lookahead's `branching_factor^3` simulations per decision under continuous aging's 200-step horizon.

## Limitations

- **This is a scheduling-policy sandbox, not a biological simulator.** Coupling coefficients are evidence-tier heuristics (`/2`, `/4`, `/8`), not fitted parameters. Treat the *relative* policy comparison as the finding, not the absolute numbers.
- **Discrete-time, rule-based, not a coupled ODE/SciML system.** The node names and coupling *directions* are the part meant to be right first; a continuous dynamical system could replace the update loop later without changing the node definitions.
- **`AGING_RATE` is still one uniform constant.** A deep-research evidence audit (August 2026) turned up candidate native-unit background rates for a few hallmarks (telomere attrition ~25-35 bp/year, genomic instability ~40 new somatic mutations/year, thymic output a ~15.7-year half-life) but converting incommensurable units into one shared `[0,1]` scale per hallmark, in a way that isn't itself a hidden unvalidated assumption, was deliberately deferred — real background aging rate depends on far more factors than this model represents, and a differentiated-but-wrong set of constants would be worse than an honestly uniform one.
- **`cancer_risk_uncapped` is a diagnostic tally, not an independently validated metric.** It fixes the ceiling-saturation problem (several policies pegging clamped `cancer_risk` at the same 1.000) but is still built from the same evidence-tiered coupling coefficients as everything else — its *relative* ranking across policies is more trustworthy than its absolute value.

**Resolved since the last version of this list** (kept here briefly so the fix is traceable, not silently dropped):

- ~~No hormesis / non-monotonic dose-response~~ — `intervene_autophagy_foxo` now tracks consecutive same-target dosing and inverts past 2 doses in a row: reduced benefit and a real `cellular_senescence` cost appear, modeling the well-documented calorie-restriction dose-response paradox (moderate/intermittent CR or fasting: robust benefit; severe/unbroken chronic restriction: diminishing returns and real costs). The precise molecular switch (AMPK-p53) is genuinely more context/cell-type-dependent than one clean mechanism — search results showed AMPK shifting p53 phosphorylation in *opposite* directions in fibroblasts vs. keratinocytes — so this is modeled as a dosing-pattern effect, not a single named pathway flip.
- ~~FOXM1's relationship to this model is unverified~~ — verified, and the original speculation was wrong. No good evidence turned up for an mTOR→FOXM1 link; what does exist is a *different*, better-evidenced mechanism now encoded in `intervene_genomic_instability`: FoxM1 repression with age drives aneuploidy-driven senescence, and re-inducing it prevents this (Macedo, Ribeiro et al. 2018, *Nat Commun* 9:2834) — with real mammalian lifespan data behind it (cyclic FOXM1 transgene induction significantly extended lifespan in both Hutchinson-Gilford progeria *and* naturally aged mice, Ribeiro, Macedo et al. 2022, *Nature Aging*, "In vivo cyclic induction of the FOXM1 transcription factor delays natural and progeroid aging phenotypes and extends healthspan"). This upgraded the `genomic_instability → cellular_senescence` coupling from `/4` to `/2`: two independent causal mechanisms now converge on the same edge.
- ~~Single patient, deterministic~~ — `compare_policies_population()` runs the one-shot comparison across 20 patients with independently jittered starting hallmark levels (±0.1), not one canonical starting point. The ranking holds: synergy-aware wins on burden (64.36 ± 3.45), greedy wins on doses (21.35 ± 1.28), fixed-priority loses on both (98.98 ± 5.56) — a simple stand-in for individual variation, not a validated population model, but enough to show the earlier findings aren't an artifact of the one specific starting patient.
- ~~Donor-age asymmetry in dysbiosis is not encoded~~ — `_accrue_aging()` now applies a small passive `inflammation` cost whenever `dysbiosis` sits above 0.5, representing ongoing LPS translocation from a persistently leaky gut barrier left untreated, not just a missed-benefit gap. This only matters in the continuous-aging mode (short one-shot horizons rarely leave dysbiosis elevated long enough to trigger it).

## License

MIT — see [`LICENSE`](LICENSE).

## Citation

See [`CITATION.cff`](CITATION.cff).

## Author

Manuel Afonso de Paiva Menezes de Sequeira — biochemistry student, FCT/UNL. Built independently, not affiliated with any institution.
