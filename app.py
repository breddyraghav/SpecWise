import html
import os
import sys

import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from main import inr, recommend_bike, recommend_laptop, recommend_mobile

st.set_page_config(page_title="SpecWise", page_icon="◉", layout="wide")

esc = html.escape


# =========================================================
# STYLE  (your CSS lives in style.css; small additions below)
# =========================================================

EXTRA_CSS = """
.spec-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
             gap:8px 28px; margin-bottom:10px; }
.bar-row { display:flex; align-items:center; gap:14px; padding:6px 0; font-size:14px; color:#333; }
.bar-label { width:110px; }
.bar-track { flex:1; height:6px; background:#eee; border-radius:3px; overflow:hidden; }
.bar-fill { height:100%; background:#111; }
.bar-value { width:58px; text-align:right; color:#777; font-size:13px; }
.rej-row { display:flex; justify-content:space-between; padding:8px 0;
           border-bottom:1px solid #eee; font-size:14px; color:#444; }
.rej-reason { color:#999; }

/* ---------- intro: large serif ---------- */
.nav, .hero, .section-title, .section-text, .logo, .nav-right,
.hero-small, .hero-title, .hero-text {
    font-family: "Times New Roman", Times, "Liberation Serif", serif !important;
}
.nav { padding: 18px 0 22px 0; margin-bottom: 90px; }
.logo { display:flex; align-items:center; gap:14px; font-size:34px; font-weight:700;
        letter-spacing:-0.5px; color:#111; }
.logo img { height:46px; width:auto; display:block; }
.nav-right { font-size:20px; font-style:italic; color:#666; }
.hero { margin-bottom:100px; }
.hero-small { font-size:20px; font-style:italic; letter-spacing:0; text-transform:none;
              color:#777; margin-bottom:18px; font-weight:400; }
.hero-title { font-size:112px; line-height:1.02; font-weight:700; letter-spacing:-2px;
              color:#111; }
.hero-text { font-size:28px; line-height:1.45; max-width:760px; color:#555; margin-top:32px; }
.section-title { font-size:44px; font-weight:700; letter-spacing:-0.5px; margin-bottom:8px; }
.section-text { font-size:20px; color:#777; margin-bottom:28px; }
div[data-testid="stRadio"] label p { font-family:"Times New Roman", Times, serif; font-size:20px; }
@media (max-width: 700px) {
    .hero-title { font-size:56px; }
    .hero-text { font-size:21px; }
    .logo { font-size:26px; }
    .nav-right { display:none; }
}
"""


def load_css():
    css = ""
    path = os.path.join(BASE_DIR, "style.css")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            css = f.read()
    st.markdown(f"<style>{css}{EXTRA_CSS}</style>", unsafe_allow_html=True)


def section(title, text):
    st.markdown(
        f'<div class="section-title">{title}</div>'
        f'<div class="section-text">{text}</div>',
        unsafe_allow_html=True,
    )


load_css()

def logo_html():
    """Shows assets/logo.png (or .jpg/.svg/.webp) next to the name if it exists."""
    import base64
    for ext, mime in [("png", "image/png"), ("jpg", "image/jpeg"),
                      ("jpeg", "image/jpeg"), ("webp", "image/webp"),
                      ("svg", "image/svg+xml")]:
        path = os.path.join(BASE_DIR, "assets", f"logo.{ext}")
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            return f'<img src="data:{mime};base64,{data}" alt="SpecWise logo">'
    return ""


st.markdown(
    f"""
    <div class="nav">
        <div class="logo">{logo_html()}<span>SpecWise</span></div>
        <div class="nav-right">Smart Product Recommendation</div>
    </div>
    <div class="hero">
        <div class="hero-small">Smart Product Discovery</div>
        <div class="hero-title">Find what fits.</div>
        <div class="hero-text">Tell SpecWise what you need.
        We'll find products that match your requirements.</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FORMS  (each returns a dict of recommend_* arguments, or None)
# =========================================================

PERFORMANCE = ["Basic", "Medium", "High", "Extreme"]


def laptop_form():
    section("Laptop requirements", "Tell us what you need from your laptop.")
    with st.form("laptop_form"):
        c1, c2 = st.columns(2)
        with c1:
            budget = st.number_input("Maximum budget (₹)", min_value=1.0,
                                     value=100000.0, step=5000.0, key="l_budget")
            purpose = st.selectbox("Main purpose", [
                "Programming", "Gaming", "Editing", "AI", "Study", "Office", "Portable"],
                key="l_purpose")
            ram = st.number_input("Minimum RAM (GB)", min_value=1.0, value=8.0,
                                  step=4.0, key="l_ram")
        with c2:
            storage = st.number_input("Minimum storage (GB)", min_value=1.0, value=512.0,
                                      step=128.0, key="l_storage")
            level = st.selectbox("Performance level", PERFORMANCE, key="l_level")
            gpu = st.selectbox("Dedicated GPU required?", ["No", "Yes"], key="l_gpu")
        display = st.selectbox("Display preference",
                               ["High Refresh Rate", "Large Screen", "Normal"], key="l_display")
        submitted = st.form_submit_button("Find my laptop")

    if not submitted:
        return None
    return dict(budget=budget, purpose=purpose, minimum_ram=ram, minimum_storage=storage,
                gpu_required=gpu, performance_level=level, display_preference=display)


def mobile_form():
    section("Mobile requirements", "Tell us what matters most to you.")
    with st.form("mobile_form"):
        c1, c2 = st.columns(2)
        with c1:
            budget = st.number_input("Maximum budget (₹)", min_value=1.0,
                                     value=90000.0, step=5000.0, key="m_budget")
            os_ = st.selectbox("Operating system", ["Android", "iOS"], key="m_os")
            ram = st.number_input("Minimum RAM (GB)", min_value=1.0, value=8.0,
                                  step=2.0, key="m_ram")
            storage = st.number_input("Minimum storage (GB)", min_value=1.0, value=128.0,
                                      step=64.0, key="m_storage")
        with c2:
            priority = st.selectbox("Main priority", [
                "Camera", "Gaming", "Battery", "Performance", "Display", "AI", "Daily Use"],
                key="m_priority")
            cam = st.slider("Camera importance", 1, 10, 5, key="m_cam")
            gam = st.slider("Gaming importance", 1, 10, 5, key="m_gam")
            bat = st.slider("Battery importance", 1, 10, 5, key="m_bat")
            per = st.slider("Performance importance", 1, 10, 5, key="m_per")
        submitted = st.form_submit_button("Find my mobile")

    if not submitted:
        return None
    return dict(budget=budget, operating_system=os_, minimum_ram=ram, minimum_storage=storage,
                priority=priority, camera_importance=cam, gaming_importance=gam,
                battery_importance=bat, performance_importance=per)


def bike_form():
    section("Bike requirements", "Tell us what kind of bike you are looking for.")
    with st.form("bike_form"):
        c1, c2 = st.columns(2)
        with c1:
            budget = st.number_input("Maximum budget (₹)", min_value=1.0,
                                     value=250000.0, step=5000.0, key="b_budget")
            bike_type = st.selectbox("Bike type", [
                "Commuter", "Sports", "Cruiser", "Adventure", "Roadster", "Naked"],
                key="b_type")
            purpose = st.selectbox("Main purpose", [
                "Daily Commute", "Performance", "Long Ride", "Touring",
                "Adventure", "City", "Sport"], key="b_purpose")
            level = st.selectbox("Performance level", PERFORMANCE, key="b_level")
        with c2:
            mil = st.slider("Mileage importance", 1, 10, 5, key="b_mil")
            com = st.slider("Comfort importance", 1, 10, 5, key="b_com")
            tec = st.slider("Technology importance", 1, 10, 5, key="b_tec")
            abs_ = st.selectbox("ABS required?", ["No", "Yes"], key="b_abs")
        submitted = st.form_submit_button("Find my bike")

    if not submitted:
        return None
    return dict(budget=budget, bike_type=bike_type, purpose=purpose, performance_level=level,
                mileage_importance=mil, comfort_importance=com,
                technology_importance=tec, abs_required=abs_)


# =========================================================
# RESULT RENDERING  (one function for all categories)
# =========================================================

SPECS = {
    "mobile": lambda p: [
        ("OS", p["os"]), ("Processor", p["processor"]),
        ("RAM", f'{p["ram"]} GB'), ("Storage", f'{p["storage"]} GB'),
        ("Display", f'{p["display_size"]}" · {p["refresh_rate"]} Hz'),
    ],
    "laptop": lambda p: [
        ("Processor", p["processor"]), ("RAM", f'{p["ram"]} GB'),
        ("Storage", f'{p["storage"]} GB'), ("GPU", p["gpu"]),
        ("Display", f'{p["display_size"]}" · {p["refresh_rate"]} Hz'),
    ],
    "bike": lambda p: [
        ("Engine", f'{p["engine_cc"]} cc'), ("Type", p["type"]),
        ("ABS", "Yes" if p["abs"] else "No"),
        ("Mileage", f'{p["mileage_score"]}/100'), ("Comfort", f'{p["comfort_score"]}/100'),
    ],
}


def name_of(p):
    return f'{esc(str(p["brand"]))} {esc(str(p["model"]))}'


def render_results(kind, results, rejected):
    best = results[0]
    p = best["product"]

    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-label">Your match</div>
            <div class="result-name">{name_of(p)}</div>
            <div class="result-description">Recommended based on your requirements</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cells = [("Match", f'<div class="score-number">{best["score"]:.1f}%</div>'),
             ("Price", f'<div class="spec-value">{inr(p["price"])}</div>')]
    cells += [(label, f'<div class="spec-value">{esc(str(value))}</div>')
              for label, value in SPECS[kind](p)]
    grid = "".join(
        f'<div class="spec-box"><div class="spec-label">{label}</div>{value}</div>'
        for label, value in cells
    )
    st.markdown(f'<div class="spec-grid">{grid}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="match-title">Why this {kind}?</div>', unsafe_allow_html=True)
    for reason in best["reasons"]:
        st.markdown(
            f'<div class="reason"><span class="check">✓</span> {esc(reason)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="match-title">How the score was built</div>',
                unsafe_allow_html=True)
    rows = ""
    for part in best["breakdown"]:
        pct = 100 * part["earned"] / part["max"] if part["max"] else 0
        rows += (
            f'<div class="bar-row"><div class="bar-label">{part["label"]}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%"></div></div>'
            f'<div class="bar-value">{part["earned"]:.1f}/{part["max"]:.1f}</div></div>'
        )
    st.markdown(rows, unsafe_allow_html=True)

    st.markdown('<div class="match-title">Top matches</div>', unsafe_allow_html=True)
    for i, item in enumerate(results[:5], start=1):
        q = item["product"]
        st.markdown(
            f'<div class="match-row"><div class="match-name">{i}. {name_of(q)}'
            f' <span class="rej-reason">· {inr(q["price"])}</span></div>'
            f'<div class="match-score">{item["score"]:.1f}%</div></div>',
            unsafe_allow_html=True,
        )

    if len(results) > 1:
        st.markdown('<div class="match-title">Compare the top 3</div>',
                    unsafe_allow_html=True)
        table = {}
        for item in results[:3]:
            q = item["product"]
            column = {"Match": f'{item["score"]:.1f}%', "Price": inr(q["price"])}
            column.update({k: str(v) for k, v in SPECS[kind](q)})
            table[f'{q["brand"]} {q["model"]}'] = column
        st.table(pd.DataFrame(table))

    show_rejected(rejected)


def show_rejected(rejected):
    if not rejected:
        return
    with st.expander(f"Why were {len(rejected)} other products excluded?"):
        rows = "".join(
            f'<div class="rej-row"><span>{name_of(r["product"])}</span>'
            f'<span class="rej-reason">{esc(r["reason"])}</span></div>'
            for r in rejected
        )
        st.markdown(rows, unsafe_allow_html=True)


# =========================================================
# PAGE FLOW
# =========================================================

section("What are you looking for?", "Select a category to begin.")
category = st.radio("Category", ["Laptop", "Mobile", "Bike"],
                    horizontal=True, label_visibility="collapsed")
st.markdown("<br>", unsafe_allow_html=True)

PAGES = {
    "Laptop": (laptop_form, recommend_laptop, "laptop"),
    "Mobile": (mobile_form, recommend_mobile, "mobile"),
    "Bike": (bike_form, recommend_bike, "bike"),
}
form_fn, recommend_fn, kind = PAGES[category]

args = form_fn()
if args is not None:
    st.session_state["last"] = {"category": category, "data": recommend_fn(**args)}

last = st.session_state.get("last")
if last and last["category"] == category:
    results, rejected = last["data"]
    if results:
        render_results(kind, results, rejected)
    else:
        st.warning(
            f"No {kind} matches all your mandatory requirements. "
            "See below why each product was excluded, then try raising "
            "your budget or lowering a minimum."
        )
        show_rejected(rejected)

st.markdown(
    '<div class="footer">SpecWise · Smart Product Recommendation</div>',
    unsafe_allow_html=True,
)