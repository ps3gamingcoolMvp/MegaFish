"""
WorldStateScanner — Real-world context engine for MegaFish

On simulation start, scans the actual current state of the world:
- Breaking news & events (via RSS feeds, no API key required)
- Political landscape by region
- Economic indicators
- Active conflicts & tensions
- Cultural / social trends

The WorldState becomes the shared context every agent "lives in" when
the simulation runs. Agents don't react to a vacuum — they react to
the world as it actually is on the simulation date.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, List, Dict, Optional, Any
import requests

from ..utils.logger import get_logger

logger = get_logger("megafish.world_scanner")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class WorldEvent:
    title: str
    description: str
    category: str          # political | economic | conflict | cultural | environmental | tech
    region: str            # global | north_america | europe | asia | africa | middle_east | latin_america
    impact_scale: str      # local | regional | global
    source: str = ""


@dataclass
class RegionalMood:
    region: str
    optimism_score: float   # -1.0 (very pessimistic) to +1.0 (very optimistic)
    stability_score: float  # 0.0 (chaotic) to 1.0 (stable)
    key_concerns: List[str] = field(default_factory=list)
    dominant_narrative: str = ""


@dataclass
class WorldState:
    scan_date: str
    events: List[WorldEvent] = field(default_factory=list)
    regional_moods: Dict[str, RegionalMood] = field(default_factory=dict)
    economic_climate: str = ""       # brief global economic summary
    political_climate: str = ""      # brief global political summary
    dominant_themes: List[str] = field(default_factory=list)
    active_conflicts: List[str] = field(default_factory=list)
    tech_trends: List[str] = field(default_factory=list)
    scan_successful: bool = False
    scan_method: str = "llm_synthetic"  # "rss_live" | "llm_synthetic"

    # Map cohort engine region names → world scanner region keys
    _REGION_MAP: ClassVar[Dict[str, str]] = {
        "North America":              "north_america",
        "Western Europe":             "europe",
        "Eastern Europe":             "europe",
        "South Asia":                 "asia",
        "East Asia":                  "asia",
        "Southeast Asia":             "asia",
        "Central Asia":               "asia",
        "Sub-Saharan Africa":         "africa",
        "North Africa":               "middle_east",
        "Middle East & North Africa": "middle_east",
        "Middle East":                "middle_east",
        "Latin America":              "latin_america",
        "Caribbean":                  "latin_america",
        "Oceania":                    "asia",
        "global":                     "global",
    }

    def _canonical_region(self, region: str) -> str:
        """Map a cohort region name to a world-scanner region key."""
        return self._REGION_MAP.get(region, region.lower().replace(" ", "_").replace("&", "and"))

    def to_prompt_context(self) -> str:
        """Format the world state as a generic context block for LLM prompts."""
        return self.to_regional_context(region=None)

    def to_regional_context(self, region: Optional[str] = None) -> str:
        """
        Format world state with region-specific events first.
        If region is given, events from that region are prioritised.
        This gives every cohort its own grounded "news feed" for the sim date.
        """
        canon = self._canonical_region(region) if region else None

        lines = [
            f"DATE: {self.scan_date}",
            f"Economy: {self.economic_climate[:80]}",
            f"Politics: {self.political_climate[:80]}",
        ]

        if self.active_conflicts:
            lines.append("Conflicts: " + " | ".join(self.active_conflicts[:2]))

        # Region-specific mood block
        if canon and canon in self.regional_moods:
            mood = self.regional_moods[canon]
            lines.append(
                f"\nYour region ({region}) on this date: "
                f"optimism={mood.optimism_score:+.1f}, stability={mood.stability_score:.1f}"
            )
            if mood.dominant_narrative:
                lines.append(f"  Regional narrative: {mood.dominant_narrative}")
            if mood.key_concerns:
                lines.append(f"  Key concerns: {' | '.join(mood.key_concerns[:3])}")

        # Events: region-specific first, then global
        if self.events:
            regional_events = [e for e in self.events if canon and e.region == canon]
            global_events   = [e for e in self.events if e.region == "global" or e.impact_scale == "global"]
            other_events    = [e for e in self.events if e not in regional_events and e not in global_events]

            shown = (regional_events[:6] + global_events[:4] + other_events[:2])[:12]

            if regional_events:
                lines.append(f"\nLocal news ({region}):")
                for ev in regional_events[:2]:
                    lines.append(f"  {ev.title}")

            lines.append("\nWorld news:")
            for ev in (global_events + other_events)[:3]:
                lines.append(f"  {ev.title}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_date": self.scan_date,
            "scan_successful": self.scan_successful,
            "scan_method": self.scan_method,
            "economic_climate": self.economic_climate,
            "political_climate": self.political_climate,
            "dominant_themes": self.dominant_themes,
            "active_conflicts": self.active_conflicts,
            "tech_trends": self.tech_trends,
            "events": [
                {
                    "title": e.title,
                    "description": e.description,
                    "category": e.category,
                    "region": e.region,
                    "impact_scale": e.impact_scale,
                }
                for e in self.events
            ],
            "regional_moods": {
                r: {
                    "optimism_score": m.optimism_score,
                    "stability_score": m.stability_score,
                    "key_concerns": m.key_concerns,
                    "dominant_narrative": m.dominant_narrative,
                }
                for r, m in self.regional_moods.items()
            },
        }


# ---------------------------------------------------------------------------
# RSS Feed sources (no API key required)
# ---------------------------------------------------------------------------

RSS_FEEDS = [
    ("https://feeds.bbci.co.uk/news/world/rss.xml",       "global",         "BBC World"),
    ("https://feeds.bbci.co.uk/news/business/rss.xml",    "global",         "BBC Business"),
    ("https://feeds.bbci.co.uk/news/technology/rss.xml",  "global",         "BBC Technology"),
    ("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "global",    "NYT World"),
    ("https://feeds.skynews.com/feeds/rss/world.xml",     "global",         "Sky News"),
    ("https://www.aljazeera.com/xml/rss/all.xml",         "middle_east",    "Al Jazeera"),
]

CATEGORY_KEYWORDS = {
    "conflict":     ["war","conflict","attack","military","troops","missile","bomb","killed","casualties","invasion","coup"],
    "political":    ["election","president","government","parliament","vote","minister","sanctions","treaty","diplomacy","policy"],
    "economic":     ["economy","market","inflation","gdp","recession","trade","tariff","bank","currency","unemployment","stock"],
    "environmental":["climate","earthquake","flood","hurricane","drought","wildfire","disaster","tsunami","storm"],
    "tech":         ["ai","artificial intelligence","technology","cyber","hack","data","software","robot","space"],
    "cultural":     ["protest","rights","religion","culture","society","health","pandemic","education"],
}

REGION_KEYWORDS = {
    "north_america":  ["us","usa","america","canada","mexico","washington","biden","trump","federal"],
    "europe":         ["europe","eu","uk","france","germany","ukraine","russia","nato","brussels","london","paris","berlin"],
    "asia":           ["china","india","japan","korea","beijing","tokyo","delhi","asia","pacific","asean"],
    "middle_east":    ["israel","iran","saudi","gaza","iraq","syria","lebanon","turkey","middle east","arabic"],
    "africa":         ["africa","nigeria","ethiopia","kenya","sudan","congo","south africa","egypt","sahel"],
    "latin_america":  ["brazil","mexico","argentina","colombia","venezuela","latin","cuba","chile","peru"],
}


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

class WorldStateScanner:
    """
    Scans the real world on the simulation date and builds a WorldState object.
    Uses live RSS feeds when available, falls back to LLM-synthesized world state.
    """

    def __init__(self, llm_client=None):
        self._llm = llm_client  # optional: openai-compatible client for synthesis

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self, simulation_date: Optional[str] = None) -> WorldState:
        """
        Main entry point. Returns a populated WorldState.
        Tries live RSS first; falls back to LLM synthetic world state.
        """
        date_str = simulation_date or datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Scanning world state for date: {date_str}")

        # Try live news
        raw_items = self._fetch_rss_headlines()
        if raw_items:
            logger.info(f"Fetched {len(raw_items)} live headlines from RSS")
            state = self._build_state_from_rss(raw_items, date_str)
            state.scan_method = "rss_live"
            state.scan_successful = True
        else:
            logger.warning("RSS fetch failed, using LLM-synthesized world state")
            state = self._synthesize_world_state(date_str)
            state.scan_method = "llm_synthetic"

        logger.info(
            f"World state ready: {len(state.events)} events, "
            f"{len(state.regional_moods)} regions mapped, "
            f"method={state.scan_method}"
        )
        return state

    # ------------------------------------------------------------------
    # RSS fetching
    # ------------------------------------------------------------------

    def _fetch_rss_headlines(self) -> List[Dict]:
        items = []
        for url, default_region, source_name in RSS_FEEDS:
            try:
                resp = requests.get(url, timeout=8, headers={"User-Agent": "MegaFish/1.0"})
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.content)
                for item in root.iter("item"):
                    title = (item.findtext("title") or "").strip()
                    desc  = (item.findtext("description") or "").strip()
                    desc  = re.sub(r"<[^>]+>", "", desc)  # strip HTML tags
                    if title:
                        items.append({
                            "title":   title,
                            "description": desc[:300],
                            "source":  source_name,
                            "default_region": default_region,
                        })
                logger.debug(f"  {source_name}: fetched {len([i for i in items if i['source']==source_name])} items")
            except Exception as e:
                logger.debug(f"RSS fetch failed for {source_name}: {e}")
        return items

    def _classify_item(self, item: Dict) -> tuple[str, str]:
        """Return (category, region) for a raw RSS item."""
        text = (item["title"] + " " + item["description"]).lower()

        category = "cultural"
        for cat, kws in CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in kws):
                category = cat
                break

        region = item["default_region"]
        for reg, kws in REGION_KEYWORDS.items():
            if any(kw in text for kw in kws):
                region = reg
                break

        return category, region

    def _build_state_from_rss(self, raw_items: List[Dict], date_str: str) -> WorldState:
        state = WorldState(scan_date=date_str)
        seen_titles = set()

        for item in raw_items:
            title = item["title"]
            if title in seen_titles:
                continue
            seen_titles.add(title)

            category, region = self._classify_item(item)
            impact = "global" if item["source"] in ("BBC World", "NYT World") else "regional"

            state.events.append(WorldEvent(
                title=title,
                description=item["description"],
                category=category,
                region=region,
                impact_scale=impact,
                source=item["source"],
            ))

        # Build regional moods from event distribution
        state.regional_moods = self._derive_regional_moods(state.events)

        # Derive dominant themes
        cat_counts: Dict[str, int] = {}
        for ev in state.events:
            cat_counts[ev.category] = cat_counts.get(ev.category, 0) + 1
        state.dominant_themes = sorted(cat_counts, key=lambda c: -cat_counts[c])[:5]

        # Active conflicts from conflict-category events
        state.active_conflicts = [
            ev.title for ev in state.events
            if ev.category == "conflict" and ev.impact_scale == "global"
        ][:6]

        # Economic / political climate summaries (from headlines)
        econ_headlines = [ev.title for ev in state.events if ev.category == "economic"][:4]
        pol_headlines  = [ev.title for ev in state.events if ev.category == "political"][:4]
        state.economic_climate  = " | ".join(econ_headlines) if econ_headlines else "Mixed global economic signals"
        state.political_climate = " | ".join(pol_headlines)  if pol_headlines  else "Heightened political tensions globally"

        # Tech trends
        state.tech_trends = [ev.title for ev in state.events if ev.category == "tech"][:4]

        return state

    def _derive_regional_moods(self, events: List[WorldEvent]) -> Dict[str, RegionalMood]:
        """Derive optimism/stability scores per region from event tone."""
        NEGATIVE_WORDS = {"war","attack","killed","crisis","collapse","protest","sanctions","recession","flood","disaster","coup","explosion","threat"}
        POSITIVE_WORDS  = {"deal","agreement","growth","recovery","peace","summit","aid","breakthrough","progress","cooperation"}

        regions = ["global","north_america","europe","asia","middle_east","africa","latin_america"]
        moods: Dict[str, RegionalMood] = {}

        for region in regions:
            reg_events = [e for e in events if e.region == region or e.impact_scale == "global"]
            if not reg_events:
                moods[region] = RegionalMood(
                    region=region, optimism_score=0.0, stability_score=0.6,
                    dominant_narrative="Uncertain — limited data"
                )
                continue

            neg = sum(1 for e in reg_events for w in NEGATIVE_WORDS if w in e.title.lower())
            pos = sum(1 for e in reg_events for w in POSITIVE_WORDS  if w in e.title.lower())
            total = max(1, neg + pos)

            optimism  = (pos - neg) / total
            stability = max(0.1, 1.0 - (neg / max(1, len(reg_events)) * 0.8))

            concerns = list({e.category for e in reg_events if e.category in ("conflict","economic","political")})[:3]
            narrative = self._region_narrative(region, optimism, stability, events)

            moods[region] = RegionalMood(
                region=region,
                optimism_score=round(optimism, 2),
                stability_score=round(stability, 2),
                key_concerns=concerns,
                dominant_narrative=narrative,
            )

        return moods

    def _region_narrative(self, region: str, optimism: float, stability: float, events: List[WorldEvent]) -> str:
        sample = next((e.title for e in events if e.region == region), None)
        if sample:
            return f"{sample[:80]}..."
        if stability < 0.4:
            return f"High instability and tension in {region}"
        if optimism > 0.2:
            return f"Cautious optimism emerging in {region}"
        return f"Mixed signals and uncertainty in {region}"

    # ------------------------------------------------------------------
    # LLM synthetic world state fallback
    # ------------------------------------------------------------------

    def _synthesize_world_state(self, date_str: str) -> WorldState:
        """
        When live RSS fails, ask the LLM to generate a realistic world state
        grounded in what we know about the world up to this date.
        """
        state = WorldState(scan_date=date_str)

        if not self._llm:
            # No LLM available: return a hardcoded baseline
            return self._baseline_world_state(date_str)

        prompt = f"""You are a world analyst. Today's date is {date_str}.

Generate a realistic snapshot of the current world state, based on real-world knowledge up to your training cutoff. Be factual and specific.

Return a JSON object with this structure:
{{
  "economic_climate": "2-sentence summary of global economic conditions",
  "political_climate": "2-sentence summary of global political situation",
  "dominant_themes": ["theme1","theme2","theme3","theme4","theme5"],
  "active_conflicts": ["conflict1","conflict2","conflict3"],
  "tech_trends": ["trend1","trend2","trend3"],
  "events": [
    {{"title":"...", "description":"...", "category":"political|economic|conflict|cultural|environmental|tech", "region":"global|north_america|europe|asia|middle_east|africa|latin_america", "impact_scale":"local|regional|global"}}
  ],
  "regional_moods": {{
    "north_america": {{"optimism_score": 0.1, "stability_score": 0.6, "key_concerns":[".."], "dominant_narrative":".."}},
    "europe":        {{"optimism_score": -0.2, "stability_score": 0.5, "key_concerns":[".."], "dominant_narrative":".."}},
    "asia":          {{"optimism_score": 0.3, "stability_score": 0.7, "key_concerns":[".."], "dominant_narrative":".."}},
    "middle_east":   {{"optimism_score": -0.5, "stability_score": 0.3, "key_concerns":[".."], "dominant_narrative":".."}},
    "africa":        {{"optimism_score": -0.1, "stability_score": 0.4, "key_concerns":[".."], "dominant_narrative":".."}},
    "latin_america": {{"optimism_score": 0.0, "stability_score": 0.5, "key_concerns":[".."], "dominant_narrative":".."}},
    "global":        {{"optimism_score": -0.1, "stability_score": 0.5, "key_concerns":[".."], "dominant_narrative":".."}}
  }}
}}

Include 15-20 events. Be specific and realistic. Return only valid JSON."""

        try:
            raw = self._llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
            )
            # Strip markdown fences if present
            raw = re.sub(r"```json\s*", "", raw)
            raw = re.sub(r"```\s*$", "", raw)

            import json
            data = json.loads(raw)

            state.economic_climate  = data.get("economic_climate", "")
            state.political_climate = data.get("political_climate", "")
            state.dominant_themes   = data.get("dominant_themes", [])
            state.active_conflicts  = data.get("active_conflicts", [])
            state.tech_trends       = data.get("tech_trends", [])

            for ev in data.get("events", []):
                state.events.append(WorldEvent(
                    title=ev.get("title",""),
                    description=ev.get("description",""),
                    category=ev.get("category","cultural"),
                    region=ev.get("region","global"),
                    impact_scale=ev.get("impact_scale","regional"),
                    source="LLM synthesis",
                ))

            for region, mood_data in data.get("regional_moods", {}).items():
                state.regional_moods[region] = RegionalMood(
                    region=region,
                    optimism_score=mood_data.get("optimism_score", 0.0),
                    stability_score=mood_data.get("stability_score", 0.5),
                    key_concerns=mood_data.get("key_concerns", []),
                    dominant_narrative=mood_data.get("dominant_narrative", ""),
                )

            state.scan_successful = True
            logger.info("LLM world state synthesis successful")

        except Exception as e:
            logger.error(f"LLM world state synthesis failed: {e}")
            state = self._baseline_world_state(date_str)

        return state

    def _baseline_world_state(self, date_str: str) -> WorldState:
        """Last-resort fallback: a generic but realistic world baseline."""
        return WorldState(
            scan_date=date_str,
            scan_successful=True,
            scan_method="baseline_fallback",
            economic_climate="Global economy under inflationary pressure; energy costs elevated; US and China in sustained trade competition; emerging markets stressed by dollar strength.",
            political_climate="Democracies under strain from populist movements; US-China rivalry reshaping alliances; multiple active conflicts straining international institutions.",
            dominant_themes=["geopolitical_rivalry","economic_uncertainty","climate_change","AI_disruption","social_polarization"],
            active_conflicts=["Ukraine-Russia War","Gaza conflict","Sudan civil war","Myanmar civil war"],
            tech_trends=["AI adoption acceleration","social media regulation","EV transition","satellite internet expansion"],
            regional_moods={
                "north_america":  RegionalMood("north_america",  0.1, 0.65, ["polarization","inflation","immigration"], "Political division dominates; economy resilient but uneven"),
                "europe":         RegionalMood("europe",        -0.2, 0.55, ["energy","Ukraine","immigration"],         "War fatigue; energy transition ongoing; right-wing surge"),
                "asia":           RegionalMood("asia",           0.3, 0.70, ["US-China","economic growth"],             "Cautious optimism; China slowing but India surging"),
                "middle_east":    RegionalMood("middle_east",   -0.5, 0.30, ["conflict","sectarianism","oil"],          "High instability; Gaza war rippling through region"),
                "africa":         RegionalMood("africa",        -0.1, 0.40, ["debt","conflict","youth unemployment"],   "Youngest continent straining under debt and governance crises"),
                "latin_america":  RegionalMood("latin_america",  0.0, 0.50, ["inequality","crime","populism"],          "Economic inequality persists; left-right political cycles"),
                "global":         RegionalMood("global",        -0.1, 0.50, ["climate","AI","geopolitics"],             "World navigating multiple simultaneous crises"),
            },
        )


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def scan_world(simulation_date: Optional[str] = None, llm_client=None) -> WorldState:
    """Convenience function — scan the world and return a WorldState."""
    scanner = WorldStateScanner(llm_client=llm_client)
    return scanner.scan(simulation_date)
