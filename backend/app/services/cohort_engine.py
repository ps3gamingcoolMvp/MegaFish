"""
CohortEngine — Demographic cohort system for 8.3B population simulation

The core problem: you cannot run 8.3 billion individual LLM calls.
The solution: cluster the 8.3B into ~3,000-8,000 demographic cohorts,
              simulate ONE representative agent per cohort,
              then weight results by cohort population size.

A cohort is a unique combination of:
  country × age_group × gender × income_band × internet_access

Each cohort gets:
  - a representative agent profile (generated from agent_registry)
  - a population weight (how many real humans this cohort represents)
  - cultural metadata (culture_type, personality distribution, etc.)

This gives statistically accurate 8.3B coverage with ~5,000 LLM calls.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
import math

from ..utils.logger import get_logger
from .agent_registry import (
    COUNTRY_DATA, AgentRegistry, get_registry,
    PERSONALITY_ARCHETYPES, CULTURE_TYPES,
    COUNTRY_PROFILES, REGION_PROFILES,
)

logger = get_logger("megafish.cohort_engine")


# ---------------------------------------------------------------------------
# Cohort definition
# ---------------------------------------------------------------------------

AGE_GROUPS = [
    ("children",   0,  14, 0.229),   # 22.9% of global population
    ("youth",     15,  29, 0.229),   # 22.9%
    ("adult",     30,  59, 0.386),   # 38.6%
    ("elder",     60,  95, 0.157),   # 15.7%
]

INCOME_BANDS = [
    ("extreme_poverty",  0.084),   # <$2.15/day
    ("low_income",       0.337),   # $2.15–$8.85/day  (largest single group)
    ("middle_income",    0.349),   # $8.85–$40/day
    ("high_income",      0.145),   # >$40/day
    ("wealthy",          0.085),   # top tier
]

# Minimum cohort population to be included (filter out tiny slivers)
MIN_COHORT_POPULATION = 50_000


@dataclass
class Cohort:
    """A demographic cohort representing a slice of the 8.3B population."""
    cohort_id: str
    country: str
    region: str
    age_group: str          # children | youth | adult | elder
    age_min: int
    age_max: int
    gender: str             # male | female
    income_band: str        # extreme_poverty | low | middle | high | wealthy
    internet_access: bool
    population: int         # how many real humans this cohort represents
    culture_type: str
    dominant_personality: str
    # A fully-resolved agent profile dict from agent_registry
    representative_agent: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CohortReactionDomain:
    """One domain of reaction from a cohort."""
    sentiment: str      # strongly_positive | positive | neutral | negative | strongly_negative
    intensity: float    # 0.0–1.0
    action: str         # what people in this cohort would DO
    reasoning: str      # why


@dataclass
class CohortReaction:
    """Full multi-domain reaction from one cohort."""
    cohort_id: str
    population_weight: int
    # Domain reactions
    social:     CohortReactionDomain = None   # social media / word of mouth
    political:  CohortReactionDomain = None   # voting, protest, political action
    economic:   CohortReactionDomain = None   # buying, boycott, investment
    physical:   CohortReactionDomain = None   # migration, protest march, violence risk
    cultural:   CohortReactionDomain = None   # opinion shift, identity expression
    # Summary
    summary: str = ""
    raw_llm_response: str = ""


# ---------------------------------------------------------------------------
# CohortEngine
# ---------------------------------------------------------------------------

class CohortEngine:
    """
    Builds and manages the demographic cohort grid for 8.3B simulation.
    """

    TOTAL_POPULATION = 8_300_000_000

    def __init__(self):
        self._registry: Optional[AgentRegistry] = None
        self._cohorts: Optional[List[Cohort]] = None

    @property
    def registry(self) -> AgentRegistry:
        if self._registry is None:
            self._registry = get_registry()
        return self._registry

    # ------------------------------------------------------------------
    # Cohort construction
    # ------------------------------------------------------------------

    def build_cohorts(self) -> List[Cohort]:
        """
        Build the full cohort grid. Returns ~3,000–8,000 cohorts
        that together represent all 8.3 billion people on Earth.
        """
        if self._cohorts is not None:
            return self._cohorts

        logger.info("Building demographic cohort grid for 8.3B population...")
        cohorts: List[Cohort] = []
        skipped = 0

        for country, region, country_pop_raw, stats in COUNTRY_DATA:
            # Scale country population to the 8.3B total
            actual_total = sum(pop for _, _, pop, _ in COUNTRY_DATA)
            scale = self.TOTAL_POPULATION / actual_total
            country_pop = int(country_pop_raw * scale)

            profile = COUNTRY_PROFILES.get(country) or REGION_PROFILES.get(region) or REGION_PROFILES["North America"]
            culture_type = profile["culture_type"]

            for age_label, age_min, age_max, age_frac in AGE_GROUPS:
                age_pop = int(country_pop * age_frac)

                for gender, gender_frac in [
                    ("male",   stats["gender_ratio"][0] / 100),
                    ("female", stats["gender_ratio"][1] / 100),
                ]:
                    gender_pop = int(age_pop * gender_frac)

                    for income_label, income_frac in INCOME_BANDS:
                        income_pop = int(gender_pop * income_frac)

                        for internet_access, internet_frac in [
                            (True,  stats["internet_rate"]),
                            (False, 1.0 - stats["internet_rate"]),
                        ]:
                            cohort_pop = int(income_pop * internet_frac)

                            if cohort_pop < MIN_COHORT_POPULATION:
                                skipped += 1
                                continue

                            cohort_id = (
                                f"{country[:8]}_{age_label[:3]}_{gender[0]}_"
                                f"{income_label[:3]}_{'on' if internet_access else 'off'}"
                            ).replace(" ", "_").lower()

                            # Get the dominant personality for this profile
                            pw = profile["personality_weights"]
                            dominant_personality = PERSONALITY_ARCHETYPES[pw.index(max(pw))]

                            # Pick a representative agent_id from this country's range
                            rep_id = self._pick_representative_id(
                                country, age_min, age_max, gender, internet_access
                            )
                            try:
                                rep_agent = self.registry.get_agent(rep_id)
                            except Exception:
                                rep_agent = {}

                            cohorts.append(Cohort(
                                cohort_id=cohort_id,
                                country=country,
                                region=region,
                                age_group=age_label,
                                age_min=age_min,
                                age_max=age_max,
                                gender=gender,
                                income_band=income_label,
                                internet_access=internet_access,
                                population=cohort_pop,
                                culture_type=culture_type,
                                dominant_personality=dominant_personality,
                                representative_agent=rep_agent,
                            ))

        self._cohorts = cohorts
        total_covered = sum(c.population for c in cohorts)
        logger.info(
            f"Cohort grid built: {len(cohorts):,} cohorts, "
            f"{total_covered:,} people covered ({total_covered/self.TOTAL_POPULATION*100:.1f}% of 8.3B), "
            f"{skipped} tiny cohorts skipped"
        )
        return cohorts

    def _pick_representative_id(
        self, country: str, age_min: int, age_max: int,
        gender: str, internet: bool
    ) -> int:
        """
        Find an agent_id in the registry that represents this cohort well.
        Uses a deterministic sampling approach.
        """
        import random
        # Find the country range in the registry
        for start, end, c, region, stats in self.registry._ranges:
            if c == country:
                # Sample within this range, using a stable seed
                seed = hash(f"{country}_{age_min}_{gender}_{internet}") & 0xFFFFFFFF
                rng = random.Random(seed)
                # Try up to 20 times to find an age/gender match
                for _ in range(20):
                    agent_id = rng.randint(start, end)
                    agent = self.registry.get_agent(agent_id)
                    if age_min <= agent["age"] <= age_max and agent["gender"] == gender:
                        return agent_id
                # Fallback: just return a stable ID in range
                return start + (seed % (end - start + 1))
        # Country not found: return a global fallback
        return 0

    # ------------------------------------------------------------------
    # Cohort queries
    # ------------------------------------------------------------------

    def get_cohorts(self) -> List[Cohort]:
        """Return all cohorts (builds if not yet built)."""
        return self.build_cohorts()

    def get_population_summary(self) -> Dict[str, Any]:
        cohorts = self.get_cohorts()
        by_region: Dict[str, int] = {}
        by_culture: Dict[str, int] = {}
        by_age: Dict[str, int] = {}
        by_income: Dict[str, int] = {}

        for c in cohorts:
            by_region[c.region]   = by_region.get(c.region, 0)   + c.population
            by_culture[c.culture_type] = by_culture.get(c.culture_type, 0) + c.population
            by_age[c.age_group]   = by_age.get(c.age_group, 0)   + c.population
            by_income[c.income_band] = by_income.get(c.income_band, 0) + c.population

        return {
            "total_cohorts":    len(cohorts),
            "total_population": sum(c.population for c in cohorts),
            "by_region":  dict(sorted(by_region.items(),  key=lambda x: -x[1])),
            "by_culture": dict(sorted(by_culture.items(), key=lambda x: -x[1])),
            "by_age":     dict(sorted(by_age.items(),     key=lambda x: -x[1])),
            "by_income":  dict(sorted(by_income.items(),  key=lambda x: -x[1])),
        }

    def select_representative_cohorts(
        self,
        max_cohorts: int = 500,
        strategy: str = "population_stratified"
    ) -> List[Cohort]:
        """
        Select a manageable subset of cohorts for simulation.
        Ensures every major demographic group is represented.

        strategy: "population_stratified" — select top cohorts by population,
                  ensuring all regions/cultures/income levels are covered.
        """
        all_cohorts = self.get_cohorts()

        if len(all_cohorts) <= max_cohorts:
            return all_cohorts

        # Ensure coverage across key dimensions
        seen_keys: set = set()
        selected: List[Cohort] = []

        # First pass: one cohort per (region, culture, income, age_group)
        for c in sorted(all_cohorts, key=lambda x: -x.population):
            key = (c.region, c.income_band, c.age_group)
            if key not in seen_keys:
                seen_keys.add(key)
                selected.append(c)

        # Second pass: fill remaining slots by population weight
        remaining = [c for c in all_cohorts if c not in selected]
        remaining.sort(key=lambda x: -x.population)
        selected.extend(remaining[: max_cohorts - len(selected)])

        # Sort by population descending
        selected.sort(key=lambda x: -x.population)
        return selected[:max_cohorts]

    # ------------------------------------------------------------------
    # Cohort → LLM prompt
    # ------------------------------------------------------------------

    def build_cohort_prompt(self, cohort: Cohort, scenario: str, world_context: str) -> str:
        """
        Build the LLM prompt for a cohort's representative agent.
        The agent must react across all life domains.
        """
        agent = cohort.representative_agent
        if not agent:
            agent_desc = (
                f"A {cohort.age_group} {cohort.gender} from {cohort.country} "
                f"({cohort.income_band} income, internet={'yes' if cohort.internet_access else 'no'})"
            )
        else:
            agent_desc = (
                f"You are {agent.get('name','this person')}. "
                f"Age: {agent.get('age','?')}. Gender: {agent.get('gender','?')}. "
                f"Country: {agent.get('country','?')} ({agent.get('region','?')}). "
                f"Culture: {agent.get('culture_type','?').replace('_',' ')}. "
                f"Religion: {agent.get('religion','?')}. "
                f"Education: {agent.get('education','?')}. "
                f"Income: ${agent.get('income_usd_annual',0):,}/year. "
                f"Internet access: {'yes' if agent.get('internet_access') else 'no'}. "
                f"Personality: {agent.get('personality','?').replace('_',' ')}. "
                f"Political orientation: {agent.get('political_orientation','?').replace('_',' ')}. "
                f"Power level: {agent.get('power_level','?').replace('_',' ')}. "
                f"Conflict exposure: {agent.get('conflict_exposure','?').replace('_',' ')}. "
                f"Living situation: {agent.get('living_situation','?').replace('_',' ')}. "
                f"Employment: {agent.get('employment_type','?').replace('_',' ')}. "
                f"Health: {agent.get('health_status','?').replace('_',' ')}. "
                f"Info access: {agent.get('info_access','?').replace('_',' ')}. "
                f"Tech access: {agent.get('tech_access','?').replace('_',' ')}."
            )

        return f"""You are {agent_desc}
You represent {cohort.population:,} people.

{world_context}

EVENT: {scenario}

React as this person. JSON only:
{{"social":{{"sentiment":"positive|neutral|negative","intensity":0.0-1.0,"action":"brief action"}},"political":{{"sentiment":"...","intensity":0.0-1.0,"action":"brief action"}},"economic":{{"sentiment":"...","intensity":0.0-1.0,"action":"brief action"}},"physical":{{"sentiment":"...","intensity":0.0-1.0,"action":"brief action"}},"cultural":{{"sentiment":"...","intensity":0.0-1.0,"action":"brief action"}},"summary":"1 sentence"}}"""
