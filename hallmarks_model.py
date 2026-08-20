"""
ChronoReset -- placeholder greedy controller for a multi-hallmark aging model.

Adult X is represented as a set of "hallmark" nodes, each with a dysfunction
level in [0, 1] (0 = healthy, 1 = maximally dysfunctional). Each step, the
controller picks the single most-dysfunctional hallmark and applies its
intervention, then moves on to whichever hallmark is now highest. This is a
discrete-time, rule-based stand-in for what should eventually be a coupled
ODE/SciML system -- the node names and coupling constraints here are the part
worth getting right first; the math engine can replace this loop later
without changing the node definitions.

Covers all 12 hallmarks (Lopez-Otin et al. 2023, Cell): deregulated
nutrient-sensing (`mtor`), disabled macroautophagy (`autophagy_foxo`), chronic
inflammation, telomere attrition, cellular senescence, mitochondrial
dysfunction, genomic instability, epigenetic alterations, loss of
proteostasis, stem cell exhaustion, altered intercellular communication, and
dysbiosis. Genomic instability was added deliberately, not just to complete a
checklist: it's the hallmark that determines whether aggressive intervention
elsewhere (telomerase reactivation especially) is safe or just trades aging
for cancer sooner. Epigenetic alterations (via partial OSK/OSKM
reprogramming) carries the model's largest `cancer_risk` coupling on purpose
-- rejuvenation and tumorigenesis sit on the same dose-response curve for this
one, not on separate ones.

`cancer_risk` is a 13th, non-canonical node: not one of López-Otín's 12, but
the resource several of the interventions above (telomerase, epigenetic
reprogramming, GH-based thymic regeneration) trade against, made directly
treatable via `intervene_car_t_therapy` rather than left as an inert tally.
Its effectiveness scales with `car_t_fitness` (a genuine side effect, boosted
by telomerase per Bai et al. 2015), and it costs a real, sizeable
inflammation penalty every dose -- cytokine release syndrome, the expected
clinical consequence of CAR-T therapy, not a rare edge case.

Coupling coefficients are tiered by strength of evidence, not tuned to data:
  STEP_SIZE/2 -- direct mechanistic coupling or strong human interventional data
  STEP_SIZE/4 -- established causal link, animal/mechanistic evidence
  STEP_SIZE/8 -- real but context-specific / partial effect
"""

import copy
import random
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Hallmark:
    name: str
    level: float  # 0 = healthy, 1 = maximally dysfunctional
    intervention: Callable[["Hallmark", "PatientState"], None]
    label: str = ""

    def __post_init__(self):
        if not self.label:
            self.label = self.name


@dataclass
class PatientState:
    hallmarks: dict[str, Hallmark]
    # side-effect metrics that are not themselves targets of intervention,
    # only moved as a consequence of intervening on a hallmark
    side_effects: dict[str, float] = field(default_factory=dict)
    # name of the hallmark intervened on in the previous step, used for
    # exclusivity and refractory-period checks
    last_intervened: str | None = None
    # cumulative doses per hallmark; some side effects are dose/duration-
    # dependent rather than presence-dependent
    doses: dict[str, int] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)
    # scratch space for policies that need to remember something between
    # calls (e.g. round-robin's cursor) without polluting `doses`
    policy_state: dict = field(default_factory=dict)
    # sum of all hallmark levels at the start of each step, accumulated --
    # a discrete proxy for "total patient burden over time" (lower is better,
    # independent of how many steps convergence took)
    cumulative_burden: float = 0.0


STEP_SIZE = 0.25


def _nudge(state: PatientState, name: str, delta: float) -> None:
    """Move a coupled hallmark's dysfunction level, clamped to [0, 1].

    Negative delta = improvement.
    """
    h = state.hallmarks.get(name)
    if h is not None:
        h.level = min(1.0, max(0.0, h.level + delta))


def _nudge_cancer_risk(state: PatientState, delta: float) -> None:
    """Like _nudge, but also accumulates an uncapped raw tally in
    side_effects["cancer_risk_uncapped"]. The clamped hallmark level is what
    policies act on and what "cancer_risk" means everywhere else in this
    module -- but once several policies all peg that clamped level at 1.0
    under continuous aging (see README), the clamped number alone can't tell
    them apart from each other. The uncapped tally can."""
    _nudge(state, "cancer_risk", delta)
    state.side_effects["cancer_risk_uncapped"] = (
        state.side_effects.get("cancer_risk_uncapped", 0.0) + delta
    )


# ---- intervention functions -------------------------------------------
# Each intervention nudges its own hallmark down and may also nudge coupled
# hallmarks/side-effects. Coupling signs and magnitudes are set from the
# literature reviewed in the ChronoReset vault notes; citations appear only
# on the lines where the direction/magnitude is non-obvious.


def intervene_autophagy_foxo(h: Hallmark, state: PatientState) -> None:
    """Fasting-mimetic / spermidine / AMPK-FOXO activation."""
    h.level = max(0.0, h.level - STEP_SIZE)
    # NOT an antagonism between the two *interventions*: the ULK1 antagonism is
    # between mTOR activity and autophagy, so AMPK/FOXO activation drives mTOR
    # down as well. Strongest coupling in the model -- both arms phosphorylate
    # the same residue set on one shared node.
    # Kim, Kundu, Viollet & Guan 2011, Nat Cell Biol -- mTORC1 Ser757 vs AMPK
    # Ser317/555/777 on ULK1.
    _nudge(state, "mtor", -STEP_SIZE / 2)
    # Autophagy/mitophagy clears damaged mitochondria, mtDNA and ROS that would
    # otherwise trigger NLRP3 (Gupta et al. 2025, Immunol Rev); restored flux
    # also destabilises GATA4, cutting NF-kB-driven SASP (Kang et al. 2015,
    # Genes & Dev).
    _nudge(state, "inflammation", -STEP_SIZE / 4)
    # Mitophagy is a subset of macroautophagy -- same PINK1/Parkin cargo into
    # canonical autophagosomal machinery (Ryu et al. 2016, Nat Med).
    _nudge(state, "mitochondrial_dysfunction", -STEP_SIZE / 4)
    # FOXO3 is the same molecule Lei et al. 2025 re-engineered for genomic
    # stability (constitutively-nuclear via AKT-phosphosite knock-in) -- a
    # weaker, non-engineered FOXO activation plausibly nudges the same axis,
    # just without the precision of removing only 2 of 3 AKT-controlled
    # switches. Animal/mechanistic tier, not the primate-trial tier the
    # dedicated intervention below gets.
    _nudge(state, "genomic_instability", -STEP_SIZE / 4)
    # Deliberately no senescence coupling: the autophagy-senescence axis is
    # sign-ambiguous -- autophagy suppresses senescence onset pre-arrest but is
    # co-opted to sustain SASP synthesis once senescence is established.


def intervene_mtor(h: Hallmark, state: PatientState) -> None:
    """Rapamycin / rapalog -- inhibits mTORC1 hyperactivity."""
    h.level = max(0.0, h.level - STEP_SIZE)
    # Relieving mTORC1 inhibition of ULK1/TFEB restores autophagic flux
    # (Kim et al. 2011, Nat Cell Biol).
    _nudge(state, "autophagy_foxo", -STEP_SIZE / 2)
    # Senomorphic, not senolytic: rapamycin blocks MAPKAPK2/IL1A translation and
    # so suppresses SASP output without reversing the arrest, which is why this
    # hits `inflammation` and leaves `cellular_senescence` untouched
    # (Herranz et al. 2015; Laberge et al. 2015, Nat Cell Biol).
    _nudge(state, "inflammation", -STEP_SIZE / 4)


def intervene_inflammation(h: Hallmark, state: PatientState) -> None:
    """Canakinumab / NLRP3 inhibition / metformin-style anti-inflammatory."""
    h.level = max(0.0, h.level - STEP_SIZE)
    # Cytokine-driven ROS oxidises guanine-rich telomeric DNA faster than
    # replicative loss alone, so damping inflammation slows the attrition
    # *rate*. Small coefficient: this does not restore length, unlike
    # telomerase activation.
    _nudge(state, "telomere_attrition", -STEP_SIZE / 8)


def intervene_telomere_attrition(h: Hallmark, state: PatientState) -> None:
    """AAV9-TERT / TA-65-style telomerase activation."""
    h.level = max(0.0, h.level - STEP_SIZE)
    # Critically short telomeres drive replicative senescence via ATM/ATR-p53-
    # p21; telomerase suppresses it (beta-gal reduction, Bai et al. 2015,
    # Cell Discovery). One of the most direct hallmark-to-hallmark links.
    _nudge(state, "cellular_senescence", -STEP_SIZE / 2)
    # Replaces the previous hard `inflammation` exclusivity. TERT has genuine
    # non-canonical pro-inflammatory signalling -- STING/type-I IFN in a myeloid
    # subpopulation, independent of telomere lengthening (Akincilar et al. 2025,
    # Nat Cell Biol) and TERT-NF-kB in injured liver macrophages (Wu et al.
    # 2016, Sci Rep) -- but systemic AAV9-TERT produced no organism-level
    # inflammatory pathology (Bernardes de Jesus et al. 2012), so this is a
    # small partial-antagonism penalty, not a blocking constraint.
    _nudge(state, "inflammation", +STEP_SIZE / 8)
    # Transient TERT mRNA gave CD19 CAR-T ~300x vs 37x expansion and ~15 extra
    # population doublings (Bai et al. 2015, Cell Discovery). This is the
    # resource intervene_car_t_therapy below actually spends.
    state.side_effects["car_t_fitness"] = min(
        1.0, state.side_effects.get("car_t_fitness", 0.0) + STEP_SIZE / 2
    )
    # Dose/duration, not mere presence, is what separates the safe mouse
    # protocols (single AAV9, non-integrating, physiological TERT) from the
    # promoter-mutant reactivation ~85-90% of human cancers use: the first dose
    # is free, sustained activity is not.
    extra_doses = max(0, state.doses.get("telomere_attrition", 1) - 1)
    _nudge_cancer_risk(state, extra_doses * STEP_SIZE / 10)


def intervene_cellular_senescence(h: Hallmark, state: PatientState) -> None:
    """Senolytic D+Q / fisetin -- clears the senescent-cell burden."""
    # "Hit-and-run": senolytics transiently push senescent cells past an
    # apoptotic threshold, so a back-to-back dose clears little extra before the
    # burden rebuilds (Xu et al. 2018, Nat Med; Justice et al. 2019, 3-days-on/
    # off schedule). Modelled as reduced efficacy on immediate repeat rather
    # than as a block.
    effect = STEP_SIZE / 2 if state.last_intervened == h.name else STEP_SIZE
    h.level = max(0.0, h.level - effect)
    # Best human evidence linking any two hallmarks here: 3 days of D+Q cut
    # circulating IL-1a, IL-6, MMP-9/12 within 11 days (Hickson et al. 2019).
    _nudge(state, "inflammation", -STEP_SIZE / 2)
    # No reverse coupling to telomere_attrition: clearing senescent cells does
    # not lengthen telomeres in the surviving population.


def intervene_mitochondrial_dysfunction(h: Hallmark, state: PatientState) -> None:
    """NAD+ precursors (NMN/NR) / urolithin A mitophagy induction."""
    # Floor effect, not continuous dose-response: NAD+ repletion does not make
    # already-healthy mitochondria healthier (Mills et al. 2016, Cell Metab --
    # young mice given NMN do not become healthier young mice).
    effect = STEP_SIZE if h.level > 0.4 else STEP_SIZE / 2
    h.level = max(0.0, h.level - effect)
    # Mitophagy curtails cytosolic mtDNA leakage sensed by cGAS-STING; urolithin
    # A attenuates this axis directly (Fang et al. 2024, Nat Commun).
    _nudge(state, "inflammation", -STEP_SIZE / 4)
    # MiDAS: mitochondrial impairment raises NAD+/NADH, activating AMPK-p53 to
    # drive a distinct senescence program (Wiley et al. 2016, Cell Metab). Its
    # SASP lacks the IL-1 arm, which is why the inflammation coupling above is
    # kept smaller than the senescence one.
    _nudge(state, "cellular_senescence", -STEP_SIZE / 4)
    # PARP-1 (DNA repair) and sirtuins (mito health) draw from the same NAD+
    # pool -- real resource competition, not two independent declines
    # (PARP-1-/- mice: shorter lifespan AND accelerated carcinogenesis,
    # PMC2672038). NAD+ repletion for mitochondria plausibly helps repair
    # capacity too, from the one pool, not "more NAD+" out of nowhere.
    _nudge(state, "genomic_instability", -STEP_SIZE / 8)


def intervene_epigenetic_alterations(h: Hallmark, state: PatientState) -> None:
    """Cyclic OSK(M) partial reprogramming -- interrupted before pluripotency
    (Ocampo et al. 2016; Lu et al. 2020; Macip et al. 2024, AAV9-OSK)."""
    h.level = max(0.0, h.level - STEP_SIZE)
    # Cyclic OSKM restored H3K9me3/H4K20me3 heterochromatin and reduced gammaH2AX
    # foci in the same dataset -- heterochromatin loss is itself a mechanism of
    # genomic instability, not just a correlate (Ocampo et al. 2016, Cell).
    _nudge(state, "genomic_instability", -STEP_SIZE / 4)
    # Same dataset: senescence-associated genes (p21, p53-pathway, SASP factors
    # MMP13/IL6) shifted toward younger patterns after cyclic OSKM.
    _nudge(state, "cellular_senescence", -STEP_SIZE / 4)
    # Reduced mitochondrial ROS accompanied the epigenetic remodeling in the
    # same senescent/progeroid cells (Ocampo et al. 2016) -- smaller coefficient
    # since the paper doesn't resolve direct vs. downstream causation.
    _nudge(state, "mitochondrial_dysfunction", -STEP_SIZE / 8)
    # The strongest cancer_risk coupling in the model, deliberately. Unlike
    # telomerase (an on-target mechanism with a dose-dependent side effect),
    # OSK(M) rejuvenation and OSKM-driven pluripotency/teratoma formation sit on
    # the *same* dose-response curve -- Takahashi & Yamanaka 2006 used teratoma
    # formation as the functional proof the factors worked at all. Dropping
    # c-MYC and cycling exposure (every study above) reduce but do not remove
    # this; "no gross teratomas observed" in a finite cohort is not "safe."
    _nudge_cancer_risk(state, STEP_SIZE / 2)
    # Cyclic OSKM in 12-month WT mice improved skeletal-muscle regeneration
    # (PAX7+ satellite cell activation after cardiotoxin injury) and pancreatic
    # beta-cell recovery after induced injury -- a measured functional effect
    # on stem/progenitor competence, not just a plausible narrative (Ocampo
    # et al. 2016, Cell).
    _nudge(state, "stem_cell_exhaustion", -STEP_SIZE / 4)


def intervene_genomic_instability(h: Hallmark, state: PatientState) -> None:
    """NAD+/PARP-1 support in a DNA-repair-limited context (NR/NA in
    progeroid, repair-deficient mice, PMC9596940) -- distinct emphasis from
    the mitochondrial NAD+ intervention above (repair capacity, not
    bioenergetics), same shared pool."""
    h.level = max(0.0, h.level - STEP_SIZE)
    # Same shared-pool logic in reverse -- PARP-1 support plausibly helps
    # sirtuin-dependent mitochondrial maintenance too, smaller effect since
    # this is the repair-focused, not biogenesis-focused, intervention.
    _nudge(state, "mitochondrial_dysfunction", -STEP_SIZE / 8)
    # Unresolved DNA damage response signaling (persistent gammaH2AX/53BP1)
    # is the direct trigger for p53/p21-dependent senescence entry -- this
    # hallmark is causally upstream of cellular_senescence, not just
    # correlated with it.
    _nudge(state, "cellular_senescence", -STEP_SIZE / 4)
    # The offsetting term to telomere_attrition's cancer_risk cost. Lei et al.
    # 2025: precise FOXO3 re-engineering gave genomic stability + zero
    # tumorigenicity over 44 weeks in aged primates -- the plausible mechanism
    # for *why* telomerase reactivation can be made safer is pairing it with
    # genomic-stability support, not avoiding telomerase. Deliberately modest:
    # this offsets, it doesn't cancel out repeated telomerase dosing for free.
    _nudge_cancer_risk(state, -STEP_SIZE / 4)


def intervene_proteostasis(h: Hallmark, state: PatientState) -> None:
    """HSF1-dependent chaperone induction / ER-UPR support (chemical
    chaperones, XBP1s-boosting therapy)."""
    h.level = max(0.0, h.level - STEP_SIZE)
    # Hsf1 deletion directly impairs HSC maintenance and proteostasis under ex
    # vivo culture stress and aging -- causal, not just correlational
    # (Kruta et al. 2021, PMID 34388375).
    _nudge(state, "stem_cell_exhaustion", -STEP_SIZE / 4)
    # Chaperone-mediated folding/proteasomal clearance and macroautophagy are
    # distinct but overlapping routes for misfolded/aggregated protein --
    # partial reinforcement, not redundant machinery (Hipp, Kasturi & Hartl
    # 2019, Nat Rev Mol Cell Biol).
    _nudge(state, "autophagy_foxo", -STEP_SIZE / 8)
    # Protein aggregate accumulation is a documented proteotoxic-stress trigger
    # for senescence entry -- context-specific, not a general mechanism.
    _nudge(state, "cellular_senescence", -STEP_SIZE / 8)


def intervene_stem_cell_exhaustion(h: Hallmark, state: PatientState) -> None:
    """Niche-level rejuvenation -- PGE2-EP4 signaling restoring aged muscle
    stem cell chromatin accessibility and cell-cycle re-entry (Cell Stem Cell
    2025), exercise-driven satellite cell activation. Not stem cell transplant,
    a distinct and far more invasive intervention category not modeled here."""
    h.level = max(0.0, h.level - STEP_SIZE)
    # Restoring a functional niche overlaps with clearing the senescent
    # supporting cells that disrupt it -- partial, context-specific, not the
    # direct human-RCT tier of the senolytic->inflammation coupling elsewhere.
    _nudge(state, "cellular_senescence", -STEP_SIZE / 8)


def intervene_intercellular_communication(h: Hallmark, state: PatientState) -> None:
    """GH + DHEA + metformin thymic regeneration, TRIIM-trial-style (Fahy
    et al. 2019) -- the endocrine-immune signaling axis left over once
    inflammaging split out as its own hallmark (chronic_inflammation) in the
    2023 revision."""
    h.level = max(0.0, h.level - STEP_SIZE)
    # TRIIM: 9 men, 50-65yo, 12 months of GH+DHEA+metformin -- MRI-confirmed
    # thymic fat-to-lymphoid regeneration, epigenetic age reduced ~2.5 years
    # across multiple clocks including GrimAge (Fahy et al. 2019, Aging Cell).
    # A regenerated thymus restoring naive T-cell output plausibly dampens the
    # oligoclonal, pro-inflammatory repertoire aging leaves behind -- causal
    # narrative is established, but TRIIM measured epigenetic age and thymic
    # imaging, not inflammatory cytokines directly, hence /4 not /2.
    _nudge(state, "inflammation", -STEP_SIZE / 4)
    # GH is proliferative and raises IGF-1; the model already treats elevated
    # IGF-1/GH signaling as a cancer-risk driver via the inverse finding cited
    # in intervene_mtor's Laron-syndrome evidence (GHR-deficient humans: ~17%
    # cancer prevalence in matched relatives vs. 1 non-lethal case in the
    # deficient group). Small, context-specific penalty: TRIIM itself was too
    # small and short to detect a cancer signal, but the mechanism is real.
    _nudge_cancer_risk(state, STEP_SIZE / 8)


def intervene_dysbiosis(h: Hallmark, state: PatientState) -> None:
    """Young-donor fecal microbiota transplant (FMT) / high-diversity
    microbiome restoration. Old-donor FMT does the reverse -- shortens
    lifespan in fly/fish models and impairs cognition in rodents (Boehme
    et al. 2021, Nat Aging) -- an asymmetry worth remembering even though it
    isn't a separate branch in this model."""
    h.level = max(0.0, h.level - STEP_SIZE)
    # Restored gut barrier integrity reduces LPS/endotoxin translocation into
    # circulation, which drives TLR4/NF-kB-dependent systemic inflammation.
    # A 2025 human RCT (prebiotics, n=200, JCI) improved frailty status, and a
    # separate 12-month Mediterranean-diet human trial found microbiome shifts
    # negatively correlated with CRP/IL-17 -- real human data now exists here,
    # though not yet at the controlled-cytokine-endpoint tier of the
    # senolytic->inflammation coupling elsewhere in the model.
    _nudge(state, "inflammation", -STEP_SIZE / 4)
    # SCFA/butyrate restoration supports colonocyte mitochondrial function --
    # real but tissue-localized, not organism-wide bioenergetics.
    _nudge(state, "mitochondrial_dysfunction", -STEP_SIZE / 8)


def intervene_car_t_therapy(h: Hallmark, state: PatientState) -> None:
    """Engineered CAR-T cell infusion targeting accumulated tumor burden.
    This is the pillar that actually *spends* `car_t_fitness` instead of just
    tracking it -- every other intervention in this model that raises
    `cancer_risk` (telomerase, epigenetic reprogramming, GH-based thymic
    regeneration) has been implicitly betting this pillar would eventually
    exist to pay it back. `cancer_risk` itself is not one of the 12 canonical
    hallmarks -- it's the resource-consuming node those other interventions
    trade against, made directly treatable rather than left as an inert
    side-effect tally."""
    # Effectiveness scales with car_t_fitness, not a flat STEP_SIZE: transient
    # TERT mRNA gave CD19 CAR-T cells ~300x vs 37x expansion and ~80% vs
    # near-total-death survival in xenografts (Bai et al. 2015, Cell
    # Discovery) -- telomerase-boosted fitness is a real, measured multiplier
    # on how much a CAR-T dose actually achieves, not just flavour text.
    # Baseline fitness (0.3, unboosted) still gives a real but weaker effect;
    # fully boosted fitness (1.0) gives full STEP_SIZE strength.
    fitness = state.side_effects.get("car_t_fitness", 0.3)
    effect = STEP_SIZE * (0.5 + fitness / 2)
    h.level = max(0.0, h.level - effect)
    state.side_effects["cancer_risk_uncapped"] = (
        state.side_effects.get("cancer_risk_uncapped", 0.0) - effect
    )
    # Cytokine release syndrome (CRS) is not a rare edge case of CAR-T therapy,
    # it is the expected, extensively documented on-target/off-tumor
    # inflammatory response -- IL-6-driven, standard of care is tocilizumab
    # (anti-IL-6R blockade). Modelled as a direct, sizeable inflammation cost
    # every dose, not a small penalty, because that is what CRS actually is in
    # clinical CAR-T practice.
    _nudge(state, "inflammation", STEP_SIZE / 2)


# ---- exclusivity rules ---------------------------------------------------
# Pairs of hallmarks that cannot both be the target of intervention in
# consecutive steps. Currently empty.
#
# The former ("inflammation", "telomere_attrition") pair was removed: two
# independent literature passes found no support for strict either/or. The
# reviews describe the two as mutually *reinforcing* (inflammation-driven ROS
# accelerates attrition; attrition-driven senescence feeds SASP into
# inflammaging), and the real TERT-STING/NF-kB tension is myeloid- and
# injury-context-specific. It is now encoded as the small bidirectional
# interaction terms in the two intervention functions above.
#
# The `mtor`/`autophagy_foxo` pair was never a candidate for this set either:
# the ULK1 antagonism holds between mTOR *activity* and autophagy, so the two
# interventions push the same direction and are co-beneficial, not exclusive.
MUTUALLY_EXCLUSIVE_THIS_STEP: set[tuple[str, str]] = set()


def build_initial_state() -> PatientState:
    hallmarks = {
        "mtor": Hallmark("mtor", level=0.55, intervention=intervene_mtor, label="mTOR activity"),
        "autophagy_foxo": Hallmark(
            "autophagy_foxo", level=0.70, intervention=intervene_autophagy_foxo,
            label="FOXO / autophagy deficit",
        ),
        "inflammation": Hallmark(
            "inflammation", level=0.80, intervention=intervene_inflammation,
            label="Chronic inflammation (inflammaging)",
        ),
        "telomere_attrition": Hallmark(
            "telomere_attrition", level=0.65, intervention=intervene_telomere_attrition,
            label="Telomere attrition",
        ),
        "cellular_senescence": Hallmark(
            "cellular_senescence", level=0.60, intervention=intervene_cellular_senescence,
            label="Cellular senescence (SnC burden)",
        ),
        "mitochondrial_dysfunction": Hallmark(
            "mitochondrial_dysfunction", level=0.50,
            intervention=intervene_mitochondrial_dysfunction,
            label="Mitochondrial dysfunction",
        ),
        "genomic_instability": Hallmark(
            "genomic_instability", level=0.45,
            intervention=intervene_genomic_instability,
            label="Genomic instability",
        ),
        "epigenetic_alterations": Hallmark(
            "epigenetic_alterations", level=0.50,
            intervention=intervene_epigenetic_alterations,
            label="Epigenetic alterations",
        ),
        "proteostasis": Hallmark(
            "proteostasis", level=0.55,
            intervention=intervene_proteostasis,
            label="Loss of proteostasis",
        ),
        "stem_cell_exhaustion": Hallmark(
            "stem_cell_exhaustion", level=0.60,
            intervention=intervene_stem_cell_exhaustion,
            label="Stem cell exhaustion",
        ),
        "intercellular_communication": Hallmark(
            "intercellular_communication", level=0.50,
            intervention=intervene_intercellular_communication,
            label="Altered intercellular communication",
        ),
        "dysbiosis": Hallmark(
            "dysbiosis", level=0.55,
            intervention=intervene_dysbiosis,
            label="Dysbiosis",
        ),
        "cancer_risk": Hallmark(
            "cancer_risk", level=0.0,
            intervention=intervene_car_t_therapy,
            label="Cancer risk",
        ),
    }
    return PatientState(
        hallmarks=hallmarks,
        side_effects={"car_t_fitness": 0.3},
    )


# ---- policies --------------------------------------------------------
# A policy is `(state) -> Hallmark | None`: which hallmark to treat this
# step. Comparing policies is the actual point of this module right now --
# the coupling rules above only matter if *ordering* interventions around
# them changes the outcome, and greedy-worst-first was never validated
# against alternatives, just assumed.


def policy_greedy(state: PatientState) -> Hallmark | None:
    """Always treat whichever hallmark is currently worst. No lookahead."""
    candidates = [h for h in state.hallmarks.values() if h.level > 0.0]
    if not candidates:
        return None

    blocked = set()
    if state.last_intervened is not None:
        for a, b in MUTUALLY_EXCLUSIVE_THIS_STEP:
            if a == state.last_intervened:
                blocked.add(b)

    eligible = [h for h in candidates if h.name not in blocked]
    if not eligible:
        eligible = candidates  # never stall: exclusivity yields if nothing else is left

    return max(eligible, key=lambda h: h.level)


def policy_synergy_greedy(state: PatientState) -> Hallmark | None:
    """One-step lookahead: treat whichever hallmark yields the largest total
    dysfunction reduction *system-wide*, not just on itself. This is the
    natural counter-hypothesis to policy_greedy -- it can pick a hallmark
    that isn't the worst one, if treating it drags others down for free
    (e.g. autophagy_foxo pulls three other nodes down at once)."""
    candidates = [h for h in state.hallmarks.values() if h.level > 0.0]
    if not candidates:
        return None

    best, best_score = None, -1.0
    for h in candidates:
        trial = copy.deepcopy(state)
        before_total = sum(x.level for x in state.hallmarks.values())
        trial_h = trial.hallmarks[h.name]
        trial_h.intervention(trial_h, trial)
        after_total = sum(x.level for x in trial.hallmarks.values())
        score = before_total - after_total
        if score > best_score:
            best, best_score = h, score
    return best


def make_policy_lookahead(depth: int) -> Callable[[PatientState], "Hallmark | None"]:
    """Generalizes policy_synergy_greedy from 1-step to N-step lookahead: for
    each candidate this step, simulate taking it, then recursively pick the
    best continuation up to `depth` steps deep, scoring by total system-wide
    dysfunction reduction summed over the whole simulated window. depth=1
    reproduces policy_synergy_greedy exactly (just recomputed less
    efficiently) -- this exists to test whether seeing further ahead than one
    step closes more of the gap synergy-aware already opened up on greedy,
    at the cost of branching-factor^depth simulations per real decision."""

    def best_score(state: PatientState, remaining: int) -> float:
        candidates = [h for h in state.hallmarks.values() if h.level > 0.0]
        if not candidates or remaining == 0:
            return 0.0
        best = float("-inf")
        for h in candidates:
            trial = copy.deepcopy(state)
            before = sum(x.level for x in state.hallmarks.values())
            trial_h = trial.hallmarks[h.name]
            trial_h.intervention(trial_h, trial)
            after = sum(x.level for x in trial.hallmarks.values())
            score = (before - after) + best_score(trial, remaining - 1)
            best = max(best, score)
        return best

    def policy(state: PatientState) -> Hallmark | None:
        candidates = [h for h in state.hallmarks.values() if h.level > 0.0]
        if not candidates:
            return None
        best_h, best_score_val = None, float("-inf")
        for h in candidates:
            trial = copy.deepcopy(state)
            before = sum(x.level for x in state.hallmarks.values())
            trial_h = trial.hallmarks[h.name]
            trial_h.intervention(trial_h, trial)
            after = sum(x.level for x in trial.hallmarks.values())
            score = (before - after) + best_score(trial, depth - 1)
            if score > best_score_val:
                best_h, best_score_val = h, score
        return best_h

    return policy


def make_policy_round_robin(order: list[str]) -> Callable[[PatientState], "Hallmark | None"]:
    """Cycle through hallmarks in a fixed order regardless of severity --
    the "no information" baseline: does knowing which hallmark is worst
    even help, or does treating everything equally do just as well?"""

    def policy(state: PatientState) -> Hallmark | None:
        candidates = {h.name for h in state.hallmarks.values() if h.level > 0.0}
        if not candidates:
            return None
        idx = state.policy_state.get("round_robin_idx", 0)
        for i in range(len(order)):
            name = order[(idx + i) % len(order)]
            if name in candidates:
                state.policy_state["round_robin_idx"] = (idx + i + 1) % len(order)
                return state.hallmarks[name]
        return None

    return policy


def make_policy_fixed_priority(order: list[str]) -> Callable[[PatientState], "Hallmark | None"]:
    """Always exhaust the strongest-coupled hallmark first (mTOR/autophagy),
    on the hypothesis that front-loading the pair with the best-evidenced
    coupling clears its "free" side benefits early and cheapens everything
    downstream."""

    def policy(state: PatientState) -> Hallmark | None:
        for name in order:
            h = state.hallmarks.get(name)
            if h is not None and h.level > 0.0:
                return h
        return None

    return policy


def make_policy_random(seed: int) -> Callable[[PatientState], "Hallmark | None"]:
    """Pick uniformly among hallmarks still above zero. The floor baseline --
    any policy that doesn't beat this isn't earning its complexity."""
    rng = random.Random(seed)

    def policy(state: PatientState) -> Hallmark | None:
        candidates = [h for h in state.hallmarks.values() if h.level > 0.0]
        if not candidates:
            return None
        return rng.choice(candidates)

    return policy


def run(
    state: PatientState,
    policy: Callable[[PatientState], "Hallmark | None"] = policy_greedy,
    threshold: float = 0.1,
    max_steps: int = 50,
) -> PatientState:
    for step in range(1, max_steps + 1):
        state.cumulative_burden += sum(h.level for h in state.hallmarks.values())

        if all(h.level <= threshold for h in state.hallmarks.values()):
            state.log.append(f"Step {step}: all hallmarks at/under target ({threshold}). Done.")
            break

        target = policy(state)
        if target is None:
            break

        before = target.level
        state.doses[target.name] = state.doses.get(target.name, 0) + 1
        target.intervention(target, state)
        state.last_intervened = target.name
        state.log.append(
            f"Step {step}: intervened on '{target.label}' "
            f"({before:.2f} -> {target.level:.2f})"
        )
    return state


def compare_policies(threshold: float = 0.1, max_steps: int = 80) -> None:
    """Run every policy from the same initial state and report what
    ordering actually buys you: fewer steps, less cumulative burden, or
    just a different side-effect bill."""
    hallmark_names = list(build_initial_state().hallmarks.keys())
    policies = {
        "greedy (worst-first)": policy_greedy,
        "synergy-aware (1-step lookahead)": policy_synergy_greedy,
        "round-robin": make_policy_round_robin(hallmark_names),
        "fixed priority (mtor/autophagy first)": make_policy_fixed_priority(
            ["mtor", "autophagy_foxo", "inflammation", "telomere_attrition",
             "cellular_senescence", "mitochondrial_dysfunction", "genomic_instability",
             "epigenetic_alterations", "proteostasis", "stem_cell_exhaustion",
             "intercellular_communication", "dysbiosis", "cancer_risk"]
        ),
        "random (seed=0)": make_policy_random(0),
        "2-step lookahead": make_policy_lookahead(2),
    }

    rows = []
    for name, policy in policies.items():
        state = run(build_initial_state(), policy=policy, threshold=threshold, max_steps=max_steps)
        total_doses = sum(state.doses.values())
        rows.append((
            name,
            total_doses,
            state.cumulative_burden,
            state.hallmarks["cancer_risk"].level,
            state.side_effects.get("car_t_fitness", 0.0),
        ))

    header = f"{'policy':<38} {'doses':>6} {'burden':>9} {'cancer_risk':>12} {'car_t_fit':>10}"
    print(header)
    print("-" * len(header))
    for name, doses, burden, cancer_risk, car_t in sorted(rows, key=lambda r: r[2]):
        print(f"{name:<38} {doses:>6} {burden:>9.3f} {cancer_risk:>12.3f} {car_t:>10.3f}")


# ---- continuous aging (steady-state maintenance) -------------------------
# `run()` and `compare_policies()` above answer "can a policy clean up a
# fixed initial mess?" -- they stop the moment every hallmark is under
# threshold and never ask what happens next. Real aging doesn't stop: damage
# keeps accruing while you intervene. This section asks the harder, more
# honest question: can a policy hold the patient near/under threshold
# *indefinitely*, when every hallmark also drifts back up a little every
# step, treated or not -- i.e. is "amortal" even reachable as a maintenance
# regime, not just as a one-time cleanup?
#
# AGING_RATE is a deliberately uniform, non-evidence-tiered constant. Unlike
# the coupling coefficients above, there is no comparable per-hallmark
# "background aging rate" literature to draw tiers from -- treat this as one
# simplifying assumption, not a researched parameter, and the single biggest
# thing to revisit if this section is taken further.
AGING_RATE = STEP_SIZE / 10


def _accrue_aging(state: PatientState, rate: float = AGING_RATE) -> None:
    """Every hallmark drifts back up a little each step, whether or not it
    was this step's target -- the generic, undifferentiated "aging keeps
    happening" process every treated hallmark is racing against."""
    for h in state.hallmarks.values():
        h.level = min(1.0, h.level + rate)
    # Keep the uncapped cancer_risk tally consistent with the clamped level:
    # background aging pushes it up here too, just like every other hallmark.
    state.side_effects["cancer_risk_uncapped"] = (
        state.side_effects.get("cancer_risk_uncapped", 0.0) + rate
    )


def run_continuous(
    state: PatientState,
    policy: Callable[[PatientState], "Hallmark | None"] = policy_greedy,
    steps: int = 200,
    aging_rate: float = AGING_RATE,
    threshold: float = 0.1,
) -> PatientState:
    """Run with background aging active every step. There is no early stop
    and no "done" state -- a policy either holds the patient near/under
    threshold for the whole horizon or it doesn't, and that failure to keep
    up *is* the finding, not an edge case to filter out."""
    for step in range(1, steps + 1):
        _accrue_aging(state, aging_rate)
        state.cumulative_burden += sum(h.level for h in state.hallmarks.values())

        target = policy(state)
        if target is None:
            break

        before = target.level
        state.doses[target.name] = state.doses.get(target.name, 0) + 1
        target.intervention(target, state)
        state.last_intervened = target.name
        if step <= 5 or step % 20 == 0:
            state.log.append(
                f"Step {step}: intervened on '{target.label}' "
                f"({before:.2f} -> {target.level:.2f})"
            )

    over = sum(1 for h in state.hallmarks.values() if h.level > threshold)
    state.log.append(
        f"After {steps} steps: {over}/{len(state.hallmarks)} hallmarks still "
        f"above threshold ({threshold})."
    )
    return state


def compare_policies_continuous(steps: int = 200, aging_rate: float = AGING_RATE) -> None:
    """Same five policies, now racing continuous background aging instead of
    cleaning up a fixed mess once. Reports time-averaged burden and how many
    hallmarks are still above threshold at the end of the horizon -- there is
    no "doses to convergence" here, by design, because nothing converges."""
    hallmark_names = list(build_initial_state().hallmarks.keys())
    policies = {
        "greedy (worst-first)": policy_greedy,
        "synergy-aware (1-step lookahead)": policy_synergy_greedy,
        "round-robin": make_policy_round_robin(hallmark_names),
        "fixed priority (mtor/autophagy first)": make_policy_fixed_priority(
            ["mtor", "autophagy_foxo", "inflammation", "telomere_attrition",
             "cellular_senescence", "mitochondrial_dysfunction", "genomic_instability",
             "epigenetic_alterations", "proteostasis", "stem_cell_exhaustion",
             "intercellular_communication", "dysbiosis", "cancer_risk"]
        ),
        "random (seed=0)": make_policy_random(0),
    }

    policies["2-step lookahead"] = make_policy_lookahead(2)

    rows = []
    for name, policy in policies.items():
        state = run_continuous(build_initial_state(), policy=policy, steps=steps, aging_rate=aging_rate)
        avg_burden = state.cumulative_burden / steps
        final_total = sum(h.level for h in state.hallmarks.values())
        over = sum(1 for h in state.hallmarks.values() if h.level > 0.1)
        rows.append((
            name,
            avg_burden,
            final_total,
            over,
            state.hallmarks["cancer_risk"].level,
            state.side_effects.get("cancer_risk_uncapped", 0.0),
        ))

    header = (
        f"{'policy':<38} {'avg_burden':>11} {'final_total':>12} {'#>0.1':>6} "
        f"{'cancer_risk':>12} {'uncapped':>9}"
    )
    print(header)
    print("-" * len(header))
    for name, avg_burden, final_total, over, cancer_risk, uncapped in sorted(rows, key=lambda r: r[1]):
        print(
            f"{name:<38} {avg_burden:>11.3f} {final_total:>12.3f} {over:>6} "
            f"{cancer_risk:>12.3f} {uncapped:>9.3f}"
        )


if __name__ == "__main__":
    state = build_initial_state()
    run(state, policy=policy_greedy)
    for line in state.log:
        print(line)
    print("\nFinal hallmark levels:")
    for h in state.hallmarks.values():
        print(f"  {h.label}: {h.level:.2f}")
    print("\nSide effects:")
    for name, value in state.side_effects.items():
        print(f"  {name}: {value:.2f}")
    print("\nDoses given:")
    for name, count in state.doses.items():
        print(f"  {name}: {count}")

    print("\n" + "=" * 60)
    print("Policy comparison (same initial state, 12 hallmarks + CAR-T)")
    print("=" * 60)
    compare_policies()

    print("\n" + "=" * 60)
    print("Continuous aging: can a policy hold the line indefinitely?")
    print("=" * 60)
    compare_policies_continuous()
