"""
PopulationSimulationEngine — 8.3B world simulation

Orchestrates the full population-scale simulation:

1. Scan real-world state for the simulation date
2. Build demographic cohort grid (3,000–8,000 cohorts = all 8.3B people)
3. For each cohort, run one LLM call with the representative agent
4. Aggregate all responses weighted by cohort population
5. Project forward in time (user-defined number of steps)
6. Return a GlobalSimulationResult with:
   - What happens globally
   - Breakdown by region / culture / income / age
   - Time-series projection of how the scenario evolves
   - Which populations are most affected / most opposed / most supportive

This is the engine behind: "what actually happens to the world if X occurs?"
"""

import json
import os
import re
import time
import concurrent.futures
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple

from ..utils.logger import get_logger
from .world_state_scanner import WorldState, scan_world
from .cohort_engine import CohortEngine, Cohort, CohortReaction, CohortReactionDomain

logger = get_logger("megafish.population_sim")


# ---------------------------------------------------------------------------
# Result structures
# ---------------------------------------------------------------------------

@dataclass
class DomainAggregate:
    """Aggregated reaction across all cohorts for one domain."""
    domain: str
    weighted_sentiment_score: float  # -2 to +2 (strongly_negative to strongly_positive)
    weighted_intensity: float        # 0.0–1.0
    top_actions: List[str]           # most common actions, sorted by weighted frequency
    population_breakdown: Dict[str, float]  # sentiment by region


SENTIMENT_SCORES = {
    "strongly_positive":  2.0,
    "positive":           1.0,
    "neutral":            0.0,
    "negative":          -1.0,
    "strongly_negative": -2.0,
}


@dataclass
class TimeStepResult:
    """Simulation state at one point in time."""
    step: int
    date: str
    scenario_evolution: str          # how the scenario changed this step
    world_state_delta: str           # what changed in the world
    global_sentiment: float          # -2 to +2
    key_developments: List[str]
    domain_aggregates: Dict[str, DomainAggregate] = field(default_factory=dict)


@dataclass
class GlobalSimulationResult:
    """
    The complete result of a world simulation run.
    Represents how 8.3B people react to a scenario, projected over time.
    """
    simulation_id: str
    scenario: str
    simulation_date: str
    total_population_simulated: int
    cohorts_used: int
    llm_calls_made: int

    # Initial reaction (time step 0)
    initial_domain_aggregates: Dict[str, DomainAggregate] = field(default_factory=dict)
    initial_global_sentiment: float = 0.0

    # Time projection
    time_steps: List[TimeStepResult] = field(default_factory=list)

    # Breakdowns
    by_region: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    by_culture: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    by_income: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    by_age: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Most/least affected populations
    most_supportive_cohorts: List[Dict] = field(default_factory=list)
    most_opposed_cohorts: List[Dict] = field(default_factory=list)
    most_affected_cohorts: List[Dict] = field(default_factory=list)

    # World state used
    world_state: Optional[Dict] = None

    # Meta
    completed_at: str = ""
    error: Optional[str] = None

    def to_summary(self) -> str:
        """Human-readable summary of the simulation result."""
        lines = [
            f"=== MEGAFISH WORLD SIMULATION ===",
            f"Scenario: {self.scenario}",
            f"Date: {self.simulation_date}",
            f"Population simulated: {self.total_population_simulated:,} ({self.cohorts_used} cohorts)",
            f"Global initial sentiment: {self.initial_global_sentiment:+.2f} (-2=strongly opposed, +2=strongly supportive)",
            "",
            "DOMAIN BREAKDOWN:",
        ]
        for domain, agg in self.initial_domain_aggregates.items():
            lines.append(
                f"  {domain.upper()}: sentiment={agg.weighted_sentiment_score:+.2f}, "
                f"intensity={agg.weighted_intensity:.2f}"
            )
            if agg.top_actions:
                lines.append(f"    Top actions: {' | '.join(agg.top_actions[:3])}")

        if self.by_region:
            lines.append("\nREGIONAL BREAKDOWN:")
            for region, data in sorted(self.by_region.items(), key=lambda x: -abs(x[1].get("sentiment",0))):
                pop = data.get("population", 0)
                sent = data.get("sentiment", 0)
                lines.append(f"  {region} ({pop:,} people): sentiment={sent:+.2f}")

        if self.time_steps:
            lines.append("\nTIME PROJECTION:")
            for step in self.time_steps:
                lines.append(f"  [{step.date}] {step.scenario_evolution[:120]}")

        if self.most_supportive_cohorts[:3]:
            lines.append("\nMOST SUPPORTIVE POPULATIONS:")
            for c in self.most_supportive_cohorts[:3]:
                lines.append(f"  {c.get('description','')} ({c.get('population',0):,} people)")

        if self.most_opposed_cohorts[:3]:
            lines.append("\nMOST OPPOSED POPULATIONS:")
            for c in self.most_opposed_cohorts[:3]:
                lines.append(f"  {c.get('description','')} ({c.get('population',0):,} people)")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        def agg_to_dict(a: DomainAggregate):
            return {
                "domain": a.domain,
                "sentiment_score": a.weighted_sentiment_score,
                "intensity": a.weighted_intensity,
                "top_actions": a.top_actions,
                "population_breakdown": a.population_breakdown,
            }

        def step_to_dict(s: TimeStepResult):
            return {
                "step": s.step,
                "date": s.date,
                "scenario_evolution": s.scenario_evolution,
                "world_state_delta": s.world_state_delta,
                "global_sentiment": s.global_sentiment,
                "key_developments": s.key_developments,
                "domains": {d: agg_to_dict(a) for d, a in s.domain_aggregates.items()},
            }

        return {
            "simulation_id": self.simulation_id,
            "scenario": self.scenario,
            "simulation_date": self.simulation_date,
            "total_population_simulated": self.total_population_simulated,
            "cohorts_used": self.cohorts_used,
            "llm_calls_made": self.llm_calls_made,
            "initial_global_sentiment": self.initial_global_sentiment,
            "initial_domains": {d: agg_to_dict(a) for d, a in self.initial_domain_aggregates.items()},
            "time_steps": [step_to_dict(s) for s in self.time_steps],
            "by_region": self.by_region,
            "by_culture": self.by_culture,
            "by_income": self.by_income,
            "by_age": self.by_age,
            "most_supportive": self.most_supportive_cohorts,
            "most_opposed": self.most_opposed_cohorts,
            "most_affected": self.most_affected_cohorts,
            "world_state": self.world_state,
            "completed_at": self.completed_at,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PopulationSimulationEngine:
    """
    Runs the 8.3B population simulation.

    Usage:
        engine = PopulationSimulationEngine(llm_client)
        result = engine.run(
            scenario="What happens if AI replaces 30% of white-collar jobs overnight?",
            simulation_date="2026-03-30",
            time_steps=3,           # project 3 steps into the future
            time_step_unit="weeks", # each step = 1 week
            max_cohorts=500,        # use 500 representative cohorts
        )
    """

    BATCH_SIZE = 20        # cohorts per parallel LLM batch
    MAX_WORKERS = 8        # parallel workers

    def __init__(self, llm_client):
        self._llm = llm_client
        self._cohort_engine = CohortEngine()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(
        self,
        scenario: str,
        simulation_id: str = "",
        simulation_date: Optional[str] = None,
        time_steps: int = 3,
        time_step_unit: str = "days",   # hours | days | weeks | months
        max_cohorts: int = 500,
        on_progress: Optional[Any] = None,  # callback(step, total, message)
    ) -> GlobalSimulationResult:
        """
        Run a full population simulation.
        """
        sim_id = simulation_id or f"world_{int(time.time())}"
        date_str = simulation_date or datetime.now().strftime("%Y-%m-%d")

        logger.info(f"[{sim_id}] Starting 8.3B population simulation")
        logger.info(f"[{sim_id}] Scenario: {scenario[:100]}...")
        logger.info(f"[{sim_id}] Date: {date_str}, Steps: {time_steps}, Max cohorts: {max_cohorts}")

        result = GlobalSimulationResult(
            simulation_id=sim_id,
            scenario=scenario,
            simulation_date=date_str,
            total_population_simulated=0,
            cohorts_used=0,
            llm_calls_made=0,
        )

        # Step 1: Scan the real world
        self._progress(on_progress, 0, 100, "Scanning world state...")
        world_state = scan_world(date_str, llm_client=self._llm)
        result.world_state = world_state.to_dict()
        logger.info(f"[{sim_id}] World state ready: {len(world_state.events)} events")

        # Step 2: Build cohort grid
        self._progress(on_progress, 5, 100, "Building 8.3B demographic cohort grid...")
        cohorts = self._cohort_engine.select_representative_cohorts(max_cohorts=max_cohorts)
        result.cohorts_used = len(cohorts)
        result.total_population_simulated = sum(c.population for c in cohorts)
        logger.info(f"[{sim_id}] Using {len(cohorts):,} cohorts representing {result.total_population_simulated:,} people")

        # Step 3: Run initial cohort reactions (time step 0)
        self._progress(on_progress, 10, 100, f"Running scenario through {len(cohorts):,} demographic cohorts...")
        cohort_reactions = self._run_cohort_batch(cohorts, scenario, world_state, sim_id, on_progress)
        result.llm_calls_made += len(cohort_reactions)

        # Step 4: Aggregate initial results
        self._progress(on_progress, 70, 100, "Aggregating population reactions...")
        self._aggregate_initial_results(result, cohorts, cohort_reactions)

        # Step 5: Time projection
        current_world_state = world_state
        current_scenario = scenario
        current_date = datetime.strptime(date_str, "%Y-%m-%d")

        step_delta = self._parse_step_delta(time_step_unit)

        for step_num in range(1, time_steps + 1):
            step_date = current_date + step_delta * step_num
            step_date_str = step_date.strftime("%Y-%m-%d")

            progress_pct = 70 + int((step_num / time_steps) * 25)
            self._progress(on_progress, progress_pct, 100, f"Projecting time step {step_num}/{time_steps} ({step_date_str})...")

            logger.info(f"[{sim_id}] Time step {step_num}: {step_date_str}")
            step_result = self._run_time_step(
                step_num, step_date_str, current_scenario, current_world_state,
                cohort_reactions, result
            )
            result.time_steps.append(step_result)

            # Update world state and scenario for next step
            current_scenario = f"[{step_date_str}] {step_result.scenario_evolution}"
            result.llm_calls_made += 1

        result.completed_at = datetime.now().isoformat()
        self._progress(on_progress, 100, 100, "Simulation complete.")
        logger.info(
            f"[{sim_id}] Simulation complete. "
            f"{result.llm_calls_made} LLM calls, "
            f"{result.total_population_simulated:,} people simulated"
        )
        return result

    # ------------------------------------------------------------------
    # Cohort batch runner
    # ------------------------------------------------------------------

    def _run_cohort_batch(
        self,
        cohorts: List[Cohort],
        scenario: str,
        world_state: WorldState,
        sim_id: str,
        on_progress: Optional[Any],
    ) -> List[CohortReaction]:
        """Run LLM reactions for all cohorts in parallel batches."""
        reactions: List[CohortReaction] = []
        total = len(cohorts)

        def process_cohort(cohort: Cohort) -> Optional[CohortReaction]:
            # Each cohort gets region-specific world context — they see their own news first
            world_context = world_state.to_regional_context(cohort.region)
            prompt = self._cohort_engine.build_cohort_prompt(cohort, scenario, world_context)
            return self._call_llm_for_cohort(cohort, prompt)

        # Per-cohort timeout: local Ollama on CPU can take minutes per call
        try:
            COHORT_TIMEOUT = int(os.environ.get("COHORT_LLM_TIMEOUT", "240"))  # 4 min per cohort
        except ValueError:
            COHORT_TIMEOUT = 240

        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {executor.submit(process_cohort, c): c for c in cohorts}
            remaining = set(futures.keys())

            try:
                for future in concurrent.futures.as_completed(remaining, timeout=COHORT_TIMEOUT):
                    cohort = futures[future]
                    try:
                        reaction = future.result()
                    except Exception as e:
                        logger.warning(f"[{sim_id}] Cohort {cohort.cohort_id} failed ({e}), using fallback")
                        reaction = self._fallback_cohort_reaction(cohort)
                    if reaction:
                        reactions.append(reaction)
                    completed += 1
                    remaining.discard(future)
                    update_every = max(1, min(10, total // 10))
                    if completed % update_every == 0 or completed == total:
                        pct = 10 + int((completed / total) * 60)
                        self._progress(on_progress, pct, 100, f"Cohorts processed: {completed}/{total}")
                        logger.info(f"[{sim_id}] Progress: {completed}/{total} cohorts")

            except concurrent.futures.TimeoutError:
                # Remaining cohorts exceeded timeout — use fallback reactions for them
                for future in remaining:
                    cohort = futures[future]
                    logger.warning(f"[{sim_id}] Cohort {cohort.cohort_id} timed out after {COHORT_TIMEOUT}s, using fallback")
                    reactions.append(self._fallback_cohort_reaction(cohort))
                    completed += 1
                self._progress(on_progress, 70, 100, f"Cohort timeout — {len(remaining)} cohorts used fallback reactions")

        return reactions

    def _call_llm_for_cohort(self, cohort: Cohort, prompt: str) -> Optional[CohortReaction]:
        """Call LLM for one cohort and parse the response."""
        try:
            raw = self._llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
            )
            return self._parse_cohort_response(cohort, raw)
        except Exception as e:
            logger.debug(f"LLM call failed for cohort {cohort.cohort_id}: {e}")
            return self._fallback_cohort_reaction(cohort)

    def _parse_cohort_response(self, cohort: Cohort, raw: str) -> CohortReaction:
        """Parse LLM JSON response into a CohortReaction."""
        # Strip markdown fences
        raw = re.sub(r"```json\s*", "", raw)
        raw = re.sub(r"```\s*$", "", raw)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except Exception:
                    return self._fallback_cohort_reaction(cohort)
            else:
                return self._fallback_cohort_reaction(cohort)

        def parse_domain(key: str) -> CohortReactionDomain:
            d = data.get(key, {})
            return CohortReactionDomain(
                sentiment=d.get("sentiment", "neutral"),
                intensity=float(d.get("intensity", 0.5)),
                action=d.get("action", ""),
                reasoning=d.get("reasoning", ""),
            )

        return CohortReaction(
            cohort_id=cohort.cohort_id,
            population_weight=cohort.population,
            social=parse_domain("social"),
            political=parse_domain("political"),
            economic=parse_domain("economic"),
            physical=parse_domain("physical"),
            cultural=parse_domain("cultural"),
            summary=data.get("summary", ""),
            raw_llm_response=raw[:500],
        )

    def _fallback_cohort_reaction(self, cohort: Cohort) -> CohortReaction:
        """Return a neutral reaction when LLM fails."""
        neutral = CohortReactionDomain(sentiment="neutral", intensity=0.3, action="no significant change", reasoning="")
        return CohortReaction(
            cohort_id=cohort.cohort_id,
            population_weight=cohort.population,
            social=neutral, political=neutral, economic=neutral,
            physical=neutral, cultural=neutral,
            summary="No significant reaction expected."
        )

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def _aggregate_initial_results(
        self,
        result: GlobalSimulationResult,
        cohorts: List[Cohort],
        reactions: List[CohortReaction],
    ):
        cohort_map = {c.cohort_id: c for c in cohorts}
        reaction_map = {r.cohort_id: r for r in reactions}

        domains = ["social", "political", "economic", "physical", "cultural"]
        total_weight = sum(r.population_weight for r in reactions)

        for domain in domains:
            weighted_sentiment = 0.0
            weighted_intensity = 0.0
            action_weights: Dict[str, int] = {}
            region_sentiments: Dict[str, List[Tuple[float, int]]] = {}

            for reaction in reactions:
                dr: CohortReactionDomain = getattr(reaction, domain)
                if not dr:
                    continue
                w = reaction.population_weight
                score = SENTIMENT_SCORES.get(dr.sentiment, 0.0)
                weighted_sentiment += score * w
                weighted_intensity += dr.intensity * w

                if dr.action:
                    action_key = dr.action[:80]
                    action_weights[action_key] = action_weights.get(action_key, 0) + w

                cohort = cohort_map.get(reaction.cohort_id)
                if cohort:
                    region = cohort.region
                    if region not in region_sentiments:
                        region_sentiments[region] = []
                    region_sentiments[region].append((score, w))

            if total_weight > 0:
                weighted_sentiment /= total_weight
                weighted_intensity /= total_weight

            top_actions = sorted(action_weights.items(), key=lambda x: -x[1])[:5]
            region_breakdown = {
                region: sum(s * w for s, w in pairs) / sum(w for _, w in pairs)
                for region, pairs in region_sentiments.items()
            }

            result.initial_domain_aggregates[domain] = DomainAggregate(
                domain=domain,
                weighted_sentiment_score=round(weighted_sentiment, 3),
                weighted_intensity=round(weighted_intensity, 3),
                top_actions=[a for a, _ in top_actions],
                population_breakdown={r: round(s, 3) for r, s in region_breakdown.items()},
            )

        # Global sentiment (average across domains)
        if result.initial_domain_aggregates:
            result.initial_global_sentiment = round(
                sum(a.weighted_sentiment_score for a in result.initial_domain_aggregates.values())
                / len(result.initial_domain_aggregates), 3
            )

        # Regional breakdown (overall)
        self._build_regional_breakdown(result, cohorts, reactions)
        self._build_culture_breakdown(result, cohorts, reactions)
        self._build_income_breakdown(result, cohorts, reactions)
        self._build_age_breakdown(result, cohorts, reactions)
        self._find_extreme_cohorts(result, cohort_map, reactions)

    def _build_regional_breakdown(self, result, cohorts, reactions):
        cohort_map = {c.cohort_id: c for c in cohorts}
        region_data: Dict[str, Dict] = {}

        for r in reactions:
            cohort = cohort_map.get(r.cohort_id)
            if not cohort:
                continue
            reg = cohort.region
            if reg not in region_data:
                region_data[reg] = {"pop": 0, "sentiment_sum": 0.0, "top_actions": {}}

            scores = [
                SENTIMENT_SCORES.get(getattr(r, d).sentiment, 0.0)
                for d in ["social","political","economic","physical","cultural"]
                if getattr(r, d)
            ]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            region_data[reg]["pop"] += r.population_weight
            region_data[reg]["sentiment_sum"] += avg_score * r.population_weight

            if r.social and r.social.action:
                a = r.social.action[:60]
                region_data[reg]["top_actions"][a] = region_data[reg]["top_actions"].get(a, 0) + r.population_weight

        for reg, d in region_data.items():
            pop = d["pop"]
            result.by_region[reg] = {
                "population": pop,
                "sentiment": round(d["sentiment_sum"] / pop, 3) if pop else 0,
                "top_actions": [a for a, _ in sorted(d["top_actions"].items(), key=lambda x: -x[1])[:3]],
            }

    def _build_culture_breakdown(self, result, cohorts, reactions):
        cohort_map = {c.cohort_id: c for c in cohorts}
        data: Dict[str, Dict] = {}
        for r in reactions:
            cohort = cohort_map.get(r.cohort_id)
            if not cohort:
                continue
            key = cohort.culture_type
            if key not in data:
                data[key] = {"pop": 0, "sent": 0.0}
            scores = [SENTIMENT_SCORES.get(getattr(r, d).sentiment, 0.0) for d in ["social","political","economic","physical","cultural"] if getattr(r, d)]
            data[key]["pop"] += r.population_weight
            data[key]["sent"] += (sum(scores) / len(scores) if scores else 0) * r.population_weight
        result.by_culture = {k: {"population": d["pop"], "sentiment": round(d["sent"] / d["pop"], 3) if d["pop"] else 0} for k, d in data.items()}

    def _build_income_breakdown(self, result, cohorts, reactions):
        cohort_map = {c.cohort_id: c for c in cohorts}
        data: Dict[str, Dict] = {}
        for r in reactions:
            cohort = cohort_map.get(r.cohort_id)
            if not cohort:
                continue
            key = cohort.income_band
            if key not in data:
                data[key] = {"pop": 0, "sent": 0.0}
            scores = [SENTIMENT_SCORES.get(getattr(r, d).sentiment, 0.0) for d in ["social","political","economic","physical","cultural"] if getattr(r, d)]
            data[key]["pop"] += r.population_weight
            data[key]["sent"] += (sum(scores) / len(scores) if scores else 0) * r.population_weight
        result.by_income = {k: {"population": d["pop"], "sentiment": round(d["sent"] / d["pop"], 3) if d["pop"] else 0} for k, d in data.items()}

    def _build_age_breakdown(self, result, cohorts, reactions):
        cohort_map = {c.cohort_id: c for c in cohorts}
        data: Dict[str, Dict] = {}
        for r in reactions:
            cohort = cohort_map.get(r.cohort_id)
            if not cohort:
                continue
            key = cohort.age_group
            if key not in data:
                data[key] = {"pop": 0, "sent": 0.0}
            scores = [SENTIMENT_SCORES.get(getattr(r, d).sentiment, 0.0) for d in ["social","political","economic","physical","cultural"] if getattr(r, d)]
            data[key]["pop"] += r.population_weight
            data[key]["sent"] += (sum(scores) / len(scores) if scores else 0) * r.population_weight
        result.by_age = {k: {"population": d["pop"], "sentiment": round(d["sent"] / d["pop"], 3) if d["pop"] else 0} for k, d in data.items()}

    def _find_extreme_cohorts(self, result, cohort_map, reactions):
        """Find most supportive, most opposed, and most intensely affected cohorts."""
        scored = []
        for r in reactions:
            cohort = cohort_map.get(r.cohort_id)
            if not cohort:
                continue
            scores = [SENTIMENT_SCORES.get(getattr(r, d).sentiment, 0.0) for d in ["social","political","economic","physical","cultural"] if getattr(r, d)]
            intensities = [getattr(r, d).intensity for d in ["social","political","economic","physical","cultural"] if getattr(r, d)]
            avg_score = sum(scores) / len(scores) if scores else 0
            avg_intensity = sum(intensities) / len(intensities) if intensities else 0

            desc = (
                f"{cohort.age_group.title()} {cohort.gender} from {cohort.country} "
                f"({cohort.income_band}, {'online' if cohort.internet_access else 'offline'})"
            )
            scored.append({
                "cohort_id": cohort.cohort_id,
                "description": desc,
                "population": cohort.population,
                "sentiment": round(avg_score, 2),
                "intensity": round(avg_intensity, 2),
                "summary": r.summary[:200] if r.summary else "",
            })

        scored.sort(key=lambda x: -x["sentiment"])
        result.most_supportive_cohorts = scored[:10]
        result.most_opposed_cohorts = list(reversed(scored))[:10]

        scored_by_intensity = sorted(scored, key=lambda x: -x["intensity"])
        result.most_affected_cohorts = scored_by_intensity[:10]

    # ------------------------------------------------------------------
    # Time projection
    # ------------------------------------------------------------------

    def _run_time_step(
        self,
        step_num: int,
        date_str: str,
        scenario: str,
        world_state: WorldState,
        previous_reactions: List[CohortReaction],
        result: GlobalSimulationResult,
    ) -> TimeStepResult:
        """
        Ask the LLM: given how 8.3B people reacted, what happens next in the world?
        """
        # Build a summary of how the population reacted in the previous step
        reaction_summary = self._summarize_reactions(previous_reactions, result)

        prompt = f"""Forecasting AI. Date: {date_str}

SCENARIO: {scenario[:200]}

POPULATION REACTIONS:
{reaction_summary[:400]}

What happens next? JSON only:
{{"scenario_evolution":"1 sentence","world_state_delta":"1 sentence","global_sentiment":0.0,"key_developments":["dev1","dev2","dev3"]}}"""

        import threading as _threading
        STEP_TIMEOUT = int(os.environ.get("STEP_LLM_TIMEOUT", "180"))

        _raw_holder = [None]
        _err_holder = [None]
        _done = _threading.Event()

        def _do_llm_call():
            try:
                _raw_holder[0] = self._llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6,
                    max_tokens=250,
                )
            except Exception as ex:
                _err_holder[0] = ex
            finally:
                _done.set()

        t = _threading.Thread(target=_do_llm_call, daemon=True)
        t.start()

        try:
            if not _done.wait(timeout=STEP_TIMEOUT):
                logger.warning(f"Time step {step_num} timed out after {STEP_TIMEOUT}s")
                raise TimeoutError("time step timed out")
            if _err_holder[0]:
                raise _err_holder[0]
            raw = _raw_holder[0]

            raw = re.sub(r"```json\s*", "", raw)
            raw = re.sub(r"```\s*$", "", raw)
            data = json.loads(raw)

            return TimeStepResult(
                step=step_num,
                date=date_str,
                scenario_evolution=data.get("scenario_evolution", ""),
                world_state_delta=data.get("world_state_delta", ""),
                global_sentiment=float(data.get("global_sentiment", 0.0)),
                key_developments=data.get("key_developments", []),
            )
        except Exception as e:
            logger.error(f"Time step {step_num} failed: {e}")
            return TimeStepResult(
                step=step_num,
                date=date_str,
                scenario_evolution=f"Scenario continues to develop (step {step_num})",
                world_state_delta="World state evolving based on population reactions",
                global_sentiment=result.initial_global_sentiment,
                key_developments=[
                    "Global response underway",
                    "Policy makers convening",
                    "Public attention focused on scenario",
                ],
            )

    def _summarize_reactions(self, reactions: List[CohortReaction], result: GlobalSimulationResult) -> str:
        """Summarize cohort reactions for the time projection prompt."""
        lines = []

        if result.initial_domain_aggregates:
            lines.append("DOMAIN SENTIMENTS (weighted by population):")
            for domain, agg in result.initial_domain_aggregates.items():
                lines.append(
                    f"  {domain.upper()}: sentiment={agg.weighted_sentiment_score:+.2f}, "
                    f"intensity={agg.weighted_intensity:.2f}"
                )
                if agg.top_actions:
                    lines.append(f"    Most common actions: {' | '.join(agg.top_actions[:3])}")

        if result.by_region:
            lines.append("\nREGIONAL SENTIMENTS (people-weighted):")
            for region, data in sorted(result.by_region.items(), key=lambda x: -abs(x[1].get("sentiment",0))):
                lines.append(f"  {region}: {data['population']:,} people, sentiment={data['sentiment']:+.2f}")

        if result.most_affected_cohorts:
            lines.append("\nMOST IMPACTED:")
            for c in result.most_affected_cohorts[:2]:
                lines.append(f"  {c['description']}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_step_delta(self, unit: str) -> timedelta:
        return {
            "hours":  timedelta(hours=1),
            "days":   timedelta(days=1),
            "weeks":  timedelta(weeks=1),
            "months": timedelta(days=30),
        }.get(unit, timedelta(days=1))

    def _progress(self, callback, current, total, message: str):
        if callback:
            try:
                callback(current, total, message)
            except Exception:
                pass
        logger.debug(f"[{current}/{total}] {message}")


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def run_world_simulation(
    llm_client,
    scenario: str,
    simulation_date: Optional[str] = None,
    time_steps: int = 3,
    time_step_unit: str = "days",
    max_cohorts: int = 500,
    on_progress=None,
) -> GlobalSimulationResult:
    """Top-level convenience function."""
    engine = PopulationSimulationEngine(llm_client)
    return engine.run(
        scenario=scenario,
        simulation_date=simulation_date,
        time_steps=time_steps,
        time_step_unit=time_step_unit,
        max_cohorts=max_cohorts,
        on_progress=on_progress,
    )
