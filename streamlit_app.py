import streamlit as st
import sys
import os
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, ValidationError

# Load secrets from Streamlit secrets.toml and set as environment variables
# This allows the modules to access them via os.getenv()
try:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]
    os.environ["GOOGLE_MAPS_API_KEY"] = st.secrets["GOOGLE_MAPS_API_KEY"]
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except KeyError as e:
    st.error(f"❌ Missing API key in .streamlit/secrets.toml: {e}")
    st.info("Please ensure all required API keys are set in .streamlit/secrets.toml")
    st.stop()

sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Pydantic v2 models – input validation & result parsing
# ---------------------------------------------------------------------------

PlanVariantName = Literal["optimized", "premium", "low_budget"]


class BudgetAllocation(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_budget: float = 0.0
    flights: float = 0.0
    hotels: float = 0.0
    activities: float = 0.0
    meals: float = 0.0


class PlanVariant(BaseModel):
    model_config = ConfigDict(extra="allow")

    budget_allocation: BudgetAllocation = Field(default_factory=BudgetAllocation)
    preferences: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def coerce_allocation(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("budget_allocation"), dict):
            data["budget_allocation"] = BudgetAllocation(**data["budget_allocation"])
        return data


class TripRequest(BaseModel):
    user_prompt: str = Field(..., min_length=1)
    selected_plan: PlanVariantName = "optimized"

    @field_validator("user_prompt")
    @classmethod
    def prompt_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Trip description cannot be blank.")
        return v.strip()


class TripResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    destination: str = ""
    origin: str = ""
    budget: float = 0.0
    num_days: int = 0
    current_total_cost: float = 0.0
    selected_plan: Optional[str] = None
    plan_variants: Optional[dict[str, PlanVariant]] = None
    research_results: Optional[dict[str, Any]] = None
    itinerary: list[dict[str, Any]] = Field(default_factory=list)
    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def coerce_plan_variants(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_variants = data.get("plan_variants")
            if isinstance(raw_variants, dict):
                data["plan_variants"] = {
                    k: PlanVariant.model_validate(v) for k, v in raw_variants.items()
                }
        return data


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Trip Planner AI", page_icon="✈", layout="wide")
st.title("Trip Planner AI")
st.caption("Powered by a multi-agent LangGraph workflow")

# ---------------------------------------------------------------------------
# Input form
# ---------------------------------------------------------------------------

with st.form("trip_form"):
    raw_prompt = st.text_area(
        "Describe your trip",
        placeholder="e.g. Paris trip from New York for 5 days with $3000 budget",
        height=80,
    )
    raw_plan = st.selectbox(
        "Plan variant to execute",
        options=["optimized", "premium", "low_budget"],
        format_func=lambda x: {
            "optimized": "Optimized (best value)",
            "premium": "Premium (luxury)",
            "low_budget": "Low Budget (cheapest)",
        }[x],
    )
    submitted = st.form_submit_button("Plan My Trip", type="primary")

if not submitted:
    st.stop()

# Validate input with Pydantic
try:
    trip_request = TripRequest(user_prompt=raw_prompt, selected_plan=raw_plan)
except ValidationError as exc:
    for err in exc.errors():
        st.error(err["msg"])
    st.stop()

# ---------------------------------------------------------------------------
# Run workflow
# ---------------------------------------------------------------------------

with st.spinner("Running trip planning agents..."):
    try:
        from src.graph import app

        initial_state = {
            "messages": [],
            "user_prompt": trip_request.user_prompt,
            "destination": "",
            "origin": "",
            "budget": 0,
            "num_days": 0,
            "current_total_cost": 0,
            "itinerary": [],
            "plan_variants": None,
            "selected_plan": trip_request.selected_plan,
            "search_plan": None,
            "research_results": None,
            "is_valid": False,
            "errors": [],
            "replan_count": 0,
            "search_errors": None,
        }
        raw_result = app.invoke(initial_state)
    except Exception as exc:
        st.error(f"Workflow error: {exc}")
        st.stop()

# Parse & validate result with Pydantic
try:
    result = TripResult.model_validate(raw_result)
except ValidationError as exc:
    st.error(f"Result parsing error: {exc}")
    st.stop()

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

st.divider()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Destination", result.destination or "—")
col2.metric("Origin", result.origin or "—")
col3.metric("Duration", f"{result.num_days} days")
col4.metric(
    "Budget",
    f"${result.budget:,.0f}",
    delta=f"${result.current_total_cost - result.budget:+,.0f} vs total",
    delta_color="inverse",
)

if result.is_valid:
    st.success(f"Plan is within budget. Total cost: **${result.current_total_cost:,.2f}**")
else:
    msg = " | ".join(result.errors) if result.errors else "Plan did not pass validation."
    st.warning(f"Validation failed: {msg}  (Total: ${result.current_total_cost:,.2f})")

st.divider()

tab_variants, tab_research, tab_itinerary, tab_raw = st.tabs(
    ["Plan Variants", "Research Results", "Itinerary", "Raw State"]
)

# --- TAB 1: PLAN VARIANTS ---
with tab_variants:
    if not result.plan_variants:
        st.info("No plan variants generated.")
    else:
        labels: dict[str, str] = {
            "optimized": "Optimized",
            "premium": "Premium",
            "low_budget": "Low Budget",
        }
        cols = st.columns(len(result.plan_variants))
        for col, (name, plan) in zip(cols, result.plan_variants.items()):
            with col:
                is_selected = name == result.selected_plan
                st.markdown(
                    f"**{labels.get(name, name)}**" + (" ✓ executed" if is_selected else "")
                )
                alloc = plan.budget_allocation
                st.metric("Total Budget", f"${alloc.total_budget:,.0f}")
                for category, amount in [
                    ("Flights", alloc.flights),
                    ("Hotels", alloc.hotels),
                    ("Activities", alloc.activities),
                    ("Meals", alloc.meals),
                ]:
                    pct = (amount / alloc.total_budget * 100) if alloc.total_budget else 0
                    st.write(f"{category}: **${amount:,.0f}** ({pct:.0f}%)")
                if plan.preferences:
                    st.caption("Preferences")
                    for k, v in plan.preferences.items():
                        st.write(f"- {k}: {v}")

# --- TAB 2: RESEARCH RESULTS ---
with tab_research:
    if not result.research_results:
        st.info("No research results available.")
    else:
        for section, items in result.research_results.items():
            st.subheader(section.replace("_", " ").title())
            if isinstance(items, list) and items:
                for item in items:
                    if isinstance(item, dict):
                        name = item.get("name") or item.get("airline") or item.get("route", "—")
                        price = (
                            item.get("price")
                            or item.get("price_per_night")
                            or item.get("entry_fee")
                        )
                        return_price = item.get("return_price")
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"**{name}**")
                        if return_price is not None and price is not None:
                            # Flight round-trip: show total with breakdown
                            total = price + return_price
                            c2.write(f"${total:,.2f} RT")
                            c1.caption(f"Outbound: ${price:,.2f}  |  Return: ${return_price:,.2f}")
                        elif price is not None:
                            c2.write(f"${price:,.2f}" if isinstance(price, (int, float)) else str(price))
                        extra = {
                            k: v
                            for k, v in item.items()
                            if k not in (
                                "name", "airline", "route", "price", "price_per_night",
                                "entry_fee", "return_price", "return_route"
                            )
                        }
                        if extra:
                            with st.expander("Details"):
                                if return_price is not None:
                                    st.write(f"**return_route**: {item.get('return_route', '')}")
                                    st.write(f"**return_price**: ${return_price:,.2f}")
                                for k, v in extra.items():
                                    st.write(f"**{k}**: {v}")
                    else:
                        st.write(item)
            elif isinstance(items, dict):
                st.json(items)
            else:
                st.write(items)
            st.divider()

        if result.errors and not result.is_valid:
            st.subheader("Validation Issues")
            for err in result.errors:
                st.warning(err)

# --- TAB 3: ITINERARY ---
with tab_itinerary:
    if not result.itinerary:
        st.info("No itinerary items.")
    else:
        has_days = any(item.get("day") for item in result.itinerary)

        if has_days:
            type_label = {
                "flight": "[Flight]",
                "hotel": "[Hotel]",
                "activity": "[Activity]",
                "restaurant": "[Dinner]",
                "transport": "[Travel]",
            }

            # Group items by day number preserving insertion order
            days_map: dict[int, list] = {}
            for item in result.itinerary:
                day = item.get("day", 0)
                if day not in days_map:
                    days_map[day] = []
                days_map[day].append(item)

            for day_num in sorted(days_map.keys()):
                day_items = days_map[day_num]
                city = next(
                    (i.get("city", "") for i in day_items if i.get("city")), ""
                )
                subtype = next(
                    (i.get("subtype", "") for i in day_items), ""
                )
                header = f"Day {day_num}"
                if city:
                    header += f"  —  {city}"
                if subtype == "arrival":
                    header += "  (Arrival)"
                elif subtype == "departure":
                    header += "  (Departure)"
                st.subheader(header)

                for item in day_items:
                    itype = item.get("type", "")
                    label = type_label.get(itype, f"[{itype.title()}]")
                    name = item.get("name", "")
                    cost = item.get("cost")
                    col1, col2 = st.columns([4, 1])
                    col1.markdown(f"**{label}** {name}")
                    if cost is not None and cost > 0:
                        col2.write(f"${cost:,.2f}")

                    skip_keys = {"type", "subtype", "name", "cost", "day", "city"}
                    details = {k: v for k, v in item.items() if k not in skip_keys and v not in (None, "", [])}
                    if details:
                        with st.expander("Details"):
                            for k, v in details.items():
                                st.write(f"**{k}**: {v}")

                st.divider()
        else:
            # Fallback: flat list (old format)
            for idx, item in enumerate(result.itinerary, 1):
                name = item.get("name") or item.get("title") or f"Item {idx}"
                with st.expander(f"{idx}. {name}"):
                    for k, v in item.items():
                        st.write(f"**{k}**: {v}")

# --- TAB 4: RAW STATE ---
with tab_raw:
    st.caption("Full state returned by the workflow (for debugging).")
    st.json(result.model_dump(exclude={"messages"}, exclude_none=False))
