import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import datetime
import html

# ============================================================================
# 1. PAGE CONFIGURATION & ROOMMATCH DESIGN SYSTEM (CUSTOM CSS + CLEAN SVG ICONS)
# ============================================================================
st.set_page_config(
    page_title="RoomMatch | Lifestyle Roommate Finder",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom SVG Icon Library (No AI sparkles or cartoonish emojis)
ICONS = {
    "logo": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "sun": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>',
    "wallet": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/></svg>',
    "sliders": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/><line x1="18" x2="22" y1="16" y2="16"/></svg>',
    "users": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "pin": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
    "check": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "shield": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></svg>',
    "info": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
    "send": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
    "message": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
}

# Initialize persistent session state for matches, connection requests, and chats
if "computed_matches" not in st.session_state:
    st.session_state.computed_matches = None
if "connections" not in st.session_state:
    # Maps student_id -> {"status": "pending" | "accepted", "student": dict}
    st.session_state.connections = {}
if "chat_threads" not in st.session_state:
    # Maps student_id -> list of {"sender": "me" | "them", "text": str, "time": str}
    st.session_state.chat_threads = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "selected_interests_saved" not in st.session_state:
    st.session_state.selected_interests_saved = []

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global Reset & RoomMatch Soft Slate Canvas */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1e293b;
    }

    .stApp {
        background-color: #f8fafc;
    }

    /* Hide default Streamlit top header bar & footer for a clean web app look */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1180px !important;
    }

    /* Top Navigation Bar matching your React app */
    .rm-navbar {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 14px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }
    .rm-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .rm-logo-box {
        width: 38px;
        height: 38px;
        background-color: #7c3aed;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 10px rgba(124, 58, 237, 0.25);
    }
    .rm-brand-title {
        font-size: 1.2rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.02em;
    }
    .rm-nav-badge {
        background-color: #f5f3ff;
        color: #7c3aed;
        border: 1px solid #ddd6fe;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 9999px;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    /* Dark Hero Banner matching your Dashboard Overview */
    .rm-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 65%, #2e1065 100%);
        border-radius: 24px;
        padding: 32px 36px;
        color: #ffffff;
        margin-bottom: 28px;
        box-shadow: 0 12px 28px -8px rgba(15, 23, 42, 0.22);
    }
    .rm-eyebrow {
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #c4b5fd;
        display: block;
        margin-bottom: 8px;
    }
    .rm-hero h1 {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff !important;
        margin: 0 0 10px 0;
        letter-spacing: -0.025em;
        line-height: 1.2;
    }
    .rm-hero p {
        font-size: 0.92rem;
        color: #cbd5e1;
        margin: 0;
        max-width: 680px;
        line-height: 1.55;
    }

    /* White Card Containers for Form Columns */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0 !important;
        border-radius: 22px !important;
        padding: 12px 16px !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    }

    .rm-section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding-bottom: 12px;
        margin-bottom: 14px;
        border-bottom: 1px solid #f1f5f9;
    }
    .rm-section-icon {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background-color: #f5f3ff;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .rm-section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
    }

    /* Input Labels & Widgets */
    label[data-testid="stWidgetLabel"] p {
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        color: #334155 !important;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        border-radius: 12px !important;
        border-color: #e2e8f0 !important;
        background-color: #ffffff !important;
    }

    /* Primary RoomMatch Violet Button */
    div.stButton > button[kind="primary"] {
        background-color: #7c3aed !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        box-shadow: 0 6px 18px rgba(124, 58, 237, 0.28) !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #6d28d9 !important;
        transform: translateY(-1px);
    }

    /* Cohort & Insight Summary Banner */
    .rm-cohort-banner {
        background-color: #ffffff;
        border: 1px solid #ddd6fe;
        border-left: 5px solid #7c3aed;
        border-radius: 18px;
        padding: 18px 22px;
        margin: 18px 0 24px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
        box-shadow: 0 2px 10px rgba(124, 58, 237, 0.06);
    }
    .rm-cohort-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1e293b;
    }
    .rm-cohort-sub {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 2px;
    }
    .rm-cluster-pill {
        background-color: #7c3aed;
        color: #ffffff;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 9999px;
    }

    /* Roommate Match Cards matching your React Recommendations Tab */
    .rm-match-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 22px;
        padding: 22px 24px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .rm-match-card:hover {
        border-color: #c4b5fd;
        box-shadow: 0 8px 22px rgba(124, 58, 237, 0.08);
    }
    .rm-card-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 16px;
        margin-bottom: 14px;
    }
    .rm-student-info {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .rm-avatar {
        width: 50px;
        height: 50px;
        border-radius: 9999px;
        background-color: #f3e8ff;
        color: #7c3aed;
        font-weight: 800;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .rm-student-name {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .rm-meta-pill {
        background-color: #f1f5f9;
        color: #475569;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 2px 9px;
        border-radius: 9999px;
        text-transform: capitalize;
    }
    .rm-student-sub {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 3px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .rm-score-box {
        text-align: right;
    }
    .rm-score-val {
        font-size: 1.65rem;
        font-weight: 800;
        color: #7c3aed;
        line-height: 1;
    }
    .rm-score-tag {
        font-size: 0.7rem;
        font-weight: 700;
        color: #7c3aed;
        margin-top: 4px;
    }
    .rm-tags-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
        margin-top: 10px;
    }
    .rm-tag-shared {
        background-color: #f5f3ff;
        color: #6d28d9;
        border: 1px solid #ede9fe;
        padding: 4px 11px;
        border-radius: 9999px;
        font-size: 0.74rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    .rm-tag-diff {
        background-color: #f8fafc;
        color: #64748b;
        border: 1px solid #e2e8f0;
        padding: 4px 11px;
        border-radius: 9999px;
        font-size: 0.74rem;
        font-weight: 500;
    }
    .rm-tag-interest {
        background-color: #eff6ff;
        color: #2563eb;
        border: 1px solid #dbeafe;
        padding: 4px 11px;
        border-radius: 9999px;
        font-size: 0.74rem;
        font-weight: 600;
    }
    /* Secondary Button Styling for Connect & Chat Actions */
    div.stButton > button[kind="secondary"] {
        background-color: #f5f3ff !important;
        color: #7c3aed !important;
        border: 1px solid #ddd6fe !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        padding: 0.55rem 1.2rem !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #ede9fe !important;
        border-color: #c4b5fd !important;
    }
    /* Chat Bubble Styles */
    .rm-chat-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 22px;
        padding: 20px 24px;
        margin-top: 12px;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
    }
    .rm-msg-row-me {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 10px;
    }
    .rm-msg-row-them {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 10px;
    }
    .rm-bubble-me {
        background-color: #7c3aed;
        color: #ffffff;
        padding: 10px 15px;
        border-radius: 16px 16px 4px 16px;
        max-width: 72%;
        font-size: 0.85rem;
        line-height: 1.45;
    }
    .rm-bubble-them {
        background-color: #f1f5f9;
        color: #1e293b;
        padding: 10px 15px;
        border-radius: 16px 16px 16px 4px;
        max-width: 72%;
        font-size: 0.85rem;
        line-height: 1.45;
    }
    .rm-msg-time {
        font-size: 0.66rem;
        opacity: 0.72;
        margin-top: 4px;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. CACHE & LOAD TRAINED K-MODES MODEL ASSETS
# ============================================================================
@st.cache_resource
def load_assets():
    model = joblib.load('model.joblib')
    df_students = pd.read_csv('students_model.csv')
    with open('meta.json', 'r') as f:
        meta = json.load(f)
    return model, df_students, meta

try:
    km_model, df_students, meta = load_assets()
    base_features = meta["features"]
    budget_edges = meta["budget_edges"]
except Exception as e:
    st.error(f"Error loading model assets: {e}. Please ensure model.joblib, students_model.csv, and meta.json are in the app directory.")
    st.stop()

# ============================================================================
# 3. TOP NAVIGATION & HERO BANNER
# ============================================================================
st.markdown(f"""
<div class="rm-navbar">
    <div class="rm-brand">
        <div class="rm-logo-box">{ICONS['logo']}</div>
        <span class="rm-brand-title">RoomMatch</span>
    </div>
</div>

<div class="rm-hero">
    <span class="rm-eyebrow">Lifestyle-Based Roommate Matching</span>
    <h1>Find a roommate whose routine fits yours.</h1>
    <p>
        Enter your daily habits, sleep schedule, and budget preferences below to discover roommates whose living routines naturally align with yours.
    </p>
</div>
""", unsafe_allow_html=True)

# Extract unique interests from dataset
all_interests = set()
for interests_str in df_students['interests'].dropna():
    for item in str(interests_str).split('|'):
        clean_item = item.strip()
        if clean_item:
            all_interests.add(clean_item)
all_interests = sorted(list(all_interests))

# ============================================================================
# 4. LIFESTYLE & PREFERENCES QUESTIONNAIRE FORM
# ============================================================================
col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.markdown(f"""
        <div class="rm-section-header">
            <div class="rm-section-icon">{ICONS['sun']}</div>
            <h3 class="rm-section-title">Lifestyle & Daily Routine</h3>
        </div>
        """, unsafe_allow_html=True)

        sleep_schedule = st.selectbox(
            "Sleep Schedule",
            ['early_bird', 'flexible', 'night_owl'],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        wake_time = st.time_input("Normal Wake-up Time", datetime.time(7, 30))
        smoking = st.selectbox(
            "Smoking Preference",
            ['non_smoker', 'occasional', 'smoker'],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        drinking = st.selectbox(
            "Drinking Preference",
            ['non_drinker', 'social', 'drinker'],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        cleanliness = st.slider("Cleanliness Level (1: Low, 5: High)", 1, 5, 4)
        noise = st.slider("Noise Tolerance (1: Low, 5: High)", 1, 5, 2)
        guests = st.selectbox(
            "Guest Frequency Preference",
            ['rarely', 'sometimes', 'frequently'],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        study_habit = st.selectbox(
            "Study Habit Environment",
            ['quiet', 'background_noise_ok', 'group_study', 'rarely_studies_at_home'],
            format_func=lambda x: x.replace('_', ' ').title()
        )

with col2:
    with st.container(border=True):
        st.markdown(f"""
        <div class="rm-section-header">
            <div class="rm-section-icon">{ICONS['wallet']}</div>
            <h3 class="rm-section-title">Budget & Eligibility Preferences</h3>
        </div>
        """, unsafe_allow_html=True)

        b_col1, b_col2 = st.columns(2)
        with b_col1:
            budget_min = st.number_input("Minimum Monthly Budget (NPR)", value=5000, step=500)
        with b_col2:
            budget_max = st.number_input("Maximum Monthly Budget (NPR)", value=15000, step=500)

        g_col1, g_col2 = st.columns(2)
        with g_col1:
            own_gender = st.selectbox(
                "Your Gender",
                ['female', 'male', 'non_binary', 'prefer_not_to_say'],
                format_func=lambda x: x.replace('_', ' ').title()
            )
        with g_col2:
            pref_gender = st.selectbox(
                "Preferred Roommate Gender",
                ['any', 'female', 'male', 'non_binary'],
                format_func=lambda x: x.replace('_', ' ').title()
            )

        food_pref = st.selectbox(
            "Food Preference",
            ['no_preference', 'vegetarian', 'vegan', 'non_vegetarian'],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        pets = st.selectbox(
            "Pets Preference",
            ['no_pets', 'has_pets', 'okay_with_pets', 'not_okay_with_pets'],
            format_func=lambda x: x.replace('_', ' ').title()
        )

        with st.expander("Optional Housing & Interest Filters"):
            selected_interests = st.multiselect("Select Your Interests", all_interests)
            location = st.text_input("Preferred Location (e.g. Kathmandu, Lalitpur, Bhaktapur)", "Kathmandu")
            room_type = st.selectbox(
                "Room Type Preference",
                ['any', 'single_room', 'shared_room', 'entire_place', 'private_room'],
                format_func=lambda x: x.replace('_', ' ').title()
            )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ============================================================================
# 5. RUN K-MODES PREDICTION & DISPLAY STYLED RECOMMENDATIONS
# ============================================================================
if st.button("Find Compatible Roommates", type="primary"):
    if budget_min > budget_max:
        st.error("Minimum budget cannot be greater than maximum budget.")
        st.stop()

    # Categorize input variables to match trained model schema
    cleanliness_band = 'low' if cleanliness <= 2 else ('medium' if cleanliness == 3 else 'high')
    noise_band = 'low' if noise <= 2 else ('medium' if noise == 3 else 'high')

    wake_hour = wake_time.hour
    if wake_hour < 6:
        wake_time_band = 'early'
    elif wake_hour <= 8:
        wake_time_band = 'mid'
    else:
        wake_time_band = 'late'

    input_midpoint = (budget_min + budget_max) / 2.0
    if input_midpoint < budget_edges[0]:
        budget_band = 'low'
    elif input_midpoint <= budget_edges[1]:
        budget_band = 'medium'
    else:
        budget_band = 'high'

    input_profile = {
        'sleep_schedule': sleep_schedule,
        'wake_time_band': wake_time_band,
        'smoking': smoking,
        'drinking': drinking,
        'cleanliness_band': cleanliness_band,
        'noise_band': noise_band,
        'guests_preference': guests,
        'food_preference': food_pref,
        'pets': pets,
        'study_habit': study_habit,
        'budget_band': budget_band
    }

    input_df = pd.DataFrame([input_profile])[base_features].astype(str)
    predicted_cluster = int(km_model.predict(input_df)[0])

    # Helper functions for eligibility & similarity calculations
    def mutual_gender_filter(candidates_df, user_g, user_p):
        cond_user_satisfied = (user_p == 'any') | (candidates_df['gender'] == user_p)
        cond_cand_satisfied = (candidates_df['gender_preference'] == 'any') | (candidates_df['gender_preference'] == user_g)
        return candidates_df[cond_user_satisfied & cond_cand_satisfied].copy()

    def compute_similarity_and_details(candidates_df, target_dict, life_feats):
        target_values = [str(target_dict[f]) for f in life_feats]
        candidate_matrix = candidates_df[life_feats].values

        sim_scores = np.mean(candidate_matrix == target_values, axis=1)
        candidates_df['similarity_score'] = sim_scores

        matching_list = []
        diff_list = []
        for _, row in candidates_df.iterrows():
            matched = [
                f.replace('_band', '').replace('_preference', '').replace('_', ' ').title()
                for f in life_feats if str(row[f]) == str(target_dict[f])
            ]
            differed = [
                f.replace('_band', '').replace('_preference', '').replace('_', ' ').title()
                for f in life_feats if str(row[f]) != str(target_dict[f])
            ]
            matching_list.append(matched)
            diff_list.append(differed)

        candidates_df['matching_items'] = matching_list
        candidates_df['different_items'] = diff_list
        return candidates_df

    def compute_interests_and_filter(candidates_df, target_interests):
        target_set = set([i.lower().strip() for i in target_interests])

        def get_shared_count(cand_int_str):
            if pd.isna(cand_int_str):
                return 0, []
            cand_set = set([i.lower().strip() for i in str(cand_int_str).split('|') if i.strip()])
            common = target_set.intersection(cand_set)
            return len(common), sorted([c.title() for c in common])

        results = [get_shared_count(row['interests']) for _, row in candidates_df.iterrows()]
        candidates_df['shared_interests_count'] = [r[0] for r in results]
        candidates_df['shared_interests_list'] = [r[1] for r in results]
        return candidates_df

    # Search predicted cluster cohort
    cohort = df_students[df_students['cluster'] == predicted_cluster].copy()
    total_cohort_count = len(cohort)

    if location:
        loc_cohort = cohort[cohort['location'].str.contains(location, case=False, na=False)]
        if not loc_cohort.empty:
            cohort = loc_cohort.copy()

    if room_type and room_type != 'any':
        room_cohort = cohort[cohort['room_type_preference'] == room_type]
        if not room_cohort.empty:
            cohort = room_cohort.copy()

    total_filtered_before_gender = len(cohort)
    eligible_cohort = mutual_gender_filter(cohort, own_gender, pref_gender)
    total_after_gender = len(eligible_cohort)
    hidden_by_gender = total_filtered_before_gender - total_after_gender

    searched_all_clusters = False
    final_matches = pd.DataFrame()

    if total_after_gender >= 5:
        eligible_cohort = compute_similarity_and_details(eligible_cohort, input_profile, base_features)
        eligible_cohort = compute_interests_and_filter(eligible_cohort, selected_interests)
        final_matches = eligible_cohort.sort_values(
            by=['similarity_score', 'shared_interests_count'],
            ascending=[False, False]
        ).head(5)
    else:
        searched_all_clusters = True
        all_candidates = df_students.copy()
        if location:
            all_candidates = all_candidates[all_candidates['location'].str.contains(location, case=False, na=False)]
        if room_type and room_type != 'any':
            all_candidates = all_candidates[all_candidates['room_type_preference'] == room_type]

        eligible_all = mutual_gender_filter(all_candidates, own_gender, pref_gender)
        if not eligible_all.empty:
            eligible_all = compute_similarity_and_details(eligible_all, input_profile, base_features)
            eligible_all = compute_interests_and_filter(eligible_all, selected_interests)
            final_matches = eligible_all.sort_values(
                by=['similarity_score', 'shared_interests_count'],
                ascending=[False, False]
            ).head(5)

    # Persist matches in session_state so clicking "Connect" or "Send" doesn't reset results
    st.session_state.computed_matches = final_matches.reset_index(drop=True) if not final_matches.empty else pd.DataFrame()
    st.session_state.selected_interests_saved = list(selected_interests)

# ============================================================================
# 6. DISPLAY STYLED RECOMMENDATIONS & INTERACTIVE ROOMMATE CONNECTIONS
# ============================================================================
if st.session_state.computed_matches is not None:
    final_matches_df = st.session_state.computed_matches
    saved_interests = st.session_state.selected_interests_saved

    st.markdown("""
    <div style="margin: 22px 0 14px 0;">
        <span style="font-size: 0.72rem; font-weight: 800; color: #7c3aed; letter-spacing: 0.08em; text-transform: uppercase;">RECOMMENDATIONS</span>
        <h2 style="font-size: 1.55rem; font-weight: 800; color: #0f172a; margin: 2px 0 4px 0;">Top Compatible Roommates</h2>
        <p style="font-size: 0.82rem; color: #64748b; margin: 0;">Sorted by how closely their daily routines and living preferences match yours. Request to connect with one or more matches below.</p>
    </div>
    """, unsafe_allow_html=True)

    if final_matches_df.empty:
        st.warning("No compatible matches found matching your current filters. Try widening your location or room type preferences.")
    else:
        for idx, row in final_matches_df.iterrows():
            match_percentage = int(round(row['similarity_score'] * 100))
            if match_percentage >= 85:
                tier_label = "Very high fit"
            elif match_percentage >= 70:
                tier_label = "High fit"
            elif match_percentage >= 50:
                tier_label = "Moderate fit"
            else:
                tier_label = "Low fit"

            student_id_str = str(row['user_id'])
            initials = student_id_str[-2:].upper() if len(student_id_str) >= 2 else "ST"
            gender_label = str(row['gender']).replace('_', ' ').title()
            room_label = str(row['room_type_preference']).replace('_', ' ').title()
            loc_label = str(row['location']).title()

            # Build shared & differing trait pills
            shared_pills_html = "".join([
                f'<span class="rm-tag-shared">{ICONS["check"]} {html.escape(item)}</span>'
                for item in row['matching_items']
            ])
            diff_pills_html = "".join([
                f'<span class="rm-tag-diff">{html.escape(item)}</span>'
                for item in row['different_items']
            ])

            if saved_interests:
                if row['shared_interests_list']:
                    interests_html = "".join([
                        f'<span class="rm-tag-interest">{html.escape(interest)}</span>'
                        for interest in row['shared_interests_list']
                    ])
                else:
                    interests_html = '<span class="rm-tag-diff">No overlapping selected interests</span>'
            else:
                raw_ints = [i.strip().title() for i in str(row['interests']).split('|') if i.strip()]
                interests_html = "".join([
                    f'<span class="rm-tag-interest">{html.escape(interest)}</span>'
                    for interest in raw_ints[:5]
                ])

            aligned_block = shared_pills_html if shared_pills_html else '<span class="rm-tag-diff">No exact trait matches</span>'
            diff_section_html = (
                f'<div style="margin-top: 12px;">'
                f'<div style="font-size: 0.68rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">Differing Traits</div>'
                f'<div class="rm-tags-row">{diff_pills_html}</div>'
                f'</div>'
                if diff_pills_html else ''
            )
            interests_heading = "Shared Interests" if saved_interests else "Profile Interests"

            card_html = (
                f'<div class="rm-match-card">'
                f'<div class="rm-card-top">'
                f'<div class="rm-student-info">'
                f'<div class="rm-avatar">{html.escape(initials)}</div>'
                f'<div>'
                f'<div class="rm-student-name">'
                f'Student #{html.escape(student_id_str)} '
                f'<span class="rm-meta-pill">{html.escape(gender_label)}</span> '
                f'<span class="rm-meta-pill">{html.escape(room_label)}</span>'
                f'</div>'
                f'<div class="rm-student-sub">{ICONS["pin"]} <span>{html.escape(loc_label)}</span></div>'
                f'</div>'
                f'</div>'
                f'<div class="rm-score-box">'
                f'<div class="rm-score-val">{match_percentage}%</div>'
                f'<div class="rm-score-tag">{tier_label}</div>'
                f'</div>'
                f'</div>'
                f'<div style="margin-top: 10px;">'
                f'<div style="font-size: 0.68rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">Aligned Lifestyle Traits</div>'
                f'<div class="rm-tags-row">{aligned_block}</div>'
                f'</div>'
                f'{diff_section_html}'
                f'<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #f1f5f9;">'
                f'<div style="font-size: 0.68rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">{interests_heading}</div>'
                f'<div class="rm-tags-row">{interests_html}</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            # Interactive Connect & Consent Action Bar under each match card
            conn_state = st.session_state.connections.get(student_id_str)
            act_col1, act_col2, _ = st.columns([1.6, 1.8, 3.6])

            if conn_state is None:
                with act_col1:
                    if st.button(f"Request to connect", key=f"req_{student_id_str}_{idx}", type="secondary"):
                        st.session_state.connections[student_id_str] = {
                            "status": "pending",
                            "student": {
                                "id": student_id_str,
                                "initials": initials,
                                "location": loc_label,
                                "room": room_label,
                                "score": match_percentage,
                                "shared": row["matching_items"]
                            }
                        }
                        st.rerun()
            elif conn_state["status"] == "pending":
                with act_col1:
                    st.markdown(
                        '<div style="padding: 8px 14px; background:#fefce8; border:1px solid #fef08a; border-radius:12px; color:#854d0e; font-size:0.78rem; font-weight:700; text-align:center;">Request Sent (Pending)</div>',
                        unsafe_allow_html=True
                    )
                with act_col2:
                    if st.button("Accept & Unlock Chat", key=f"acc_{student_id_str}_{idx}", type="secondary"):
                        st.session_state.connections[student_id_str]["status"] = "accepted"
                        st.session_state.active_chat_id = student_id_str
                        if student_id_str not in st.session_state.chat_threads:
                            top_shared = ", ".join(row["matching_items"][:2]).lower() if row["matching_items"] else "daily routines"
                            now_str = datetime.datetime.now().strftime("%I:%M %p")
                            st.session_state.chat_threads[student_id_str] = [
                                {
                                    "sender": "them",
                                    "text": f"Hi! Thanks for connecting — I saw we matched at {match_percentage}% and align on {top_shared}. Are you still looking around {loc_label}?",
                                    "time": now_str
                                }
                            ]
                        st.rerun()
            elif conn_state["status"] == "accepted":
                with act_col1:
                    if st.button("Open Conversation", key=f"chat_{student_id_str}_{idx}", type="secondary"):
                        st.session_state.active_chat_id = student_id_str
                        st.rerun()
                with act_col2:
                    st.markdown(
                        '<div style="padding: 8px 14px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:12px; color:#166534; font-size:0.78rem; font-weight:700; text-align:center;">Connected</div>',
                        unsafe_allow_html=True
                    )

            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

# ============================================================================
# 7. CONVERSATIONS & MESSAGING WORKSPACE (MULTI-ROOMMATE CHAT)
# ============================================================================
if st.session_state.connections:
    st.markdown("""
    <div style="margin: 34px 0 14px 0; padding-top: 24px; border-top: 1px solid #e2e8f0;">
        <span style="font-size: 0.72rem; font-weight: 800; color: #7c3aed; letter-spacing: 0.08em; text-transform: uppercase;">MESSAGES</span>
        <h2 style="font-size: 1.55rem; font-weight: 800; color: #0f172a; margin: 2px 0 4px 0;">Your Roommate Connections</h2>
        <p style="font-size: 0.82rem; color: #64748b; margin: 0;">Switch between any potential roommates you've connected with to discuss housing options.</p>
    </div>
    """, unsafe_allow_html=True)

    list_col, chat_col = st.columns([1.2, 2.3], gap="large")

    with list_col:
        with st.container(border=True):
            st.markdown(f"""
            <div class="rm-section-header">
                <div class="rm-section-icon">{ICONS['message']}</div>
                <h3 class="rm-section-title">Connections ({len(st.session_state.connections)})</h3>
            </div>
            """, unsafe_allow_html=True)

            for cid, cdata in st.session_state.connections.items():
                s_info = cdata["student"]
                status_badge = "Connected" if cdata["status"] == "accepted" else "Pending"
                btn_label = f"Student #{cid} ({s_info['score']}%) — {status_badge}"
                if st.button(btn_label, key=f"select_thread_{cid}", use_container_width=True):
                    st.session_state.active_chat_id = cid
                    st.rerun()

    with chat_col:
        active_id = st.session_state.active_chat_id
        if active_id and active_id in st.session_state.connections:
            active_conn = st.session_state.connections[active_id]
            s_info = active_conn["student"]

            with st.container(border=True):
                st.markdown(
                    f'<div style="display:flex; justify-content:space-between; align-items:center; padding-bottom:12px; border-bottom:1px solid #f1f5f9; margin-bottom:14px;">'
                    f'<div style="display:flex; align-items:center; gap:12px;">'
                    f'<div class="rm-avatar" style="width:42px; height:42px; font-size:0.85rem;">{html.escape(s_info["initials"])}</div>'
                    f'<div>'
                    f'<div style="font-weight:800; font-size:0.98rem; color:#0f172a;">Student #{html.escape(active_id)}</div>'
                    f'<div style="font-size:0.75rem; color:#64748b;">{html.escape(s_info["location"])} • {html.escape(s_info["room"])}</div>'
                    f'</div>'
                    f'</div>'
                    f'<span class="rm-nav-badge">{s_info["score"]}% Match</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                if active_conn["status"] == "pending":
                    st.info(f"Connection request sent to Student #{active_id}. Click **Accept & Unlock Chat** below to simulate mutual consent and start chatting.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Accept & Unlock Chat", key=f"panel_acc_{active_id}", type="primary"):
                            st.session_state.connections[active_id]["status"] = "accepted"
                            if active_id not in st.session_state.chat_threads:
                                now_str = datetime.datetime.now().strftime("%I:%M %p")
                                st.session_state.chat_threads[active_id] = [
                                    {
                                        "sender": "them",
                                        "text": f"Hi! Glad we connected ({s_info['score']}% compatibility). Let's chat about housing near {s_info['location']}!",
                                        "time": now_str
                                    }
                                ]
                            st.rerun()
                    with c2:
                        if st.button("Cancel Request", key=f"panel_del_{active_id}", type="secondary"):
                            del st.session_state.connections[active_id]
                            st.session_state.active_chat_id = None
                            st.rerun()
                else:
                    # Render conversation thread
                    thread = st.session_state.chat_threads.get(active_id, [])
                    bubbles_html = ""
                    for msg in thread:
                        safe_txt = html.escape(msg["text"])
                        safe_time = html.escape(msg["time"])
                        if msg["sender"] == "me":
                            bubbles_html += (
                                f'<div class="rm-msg-row-me">'
                                f'<div class="rm-bubble-me">{safe_txt}<div class="rm-msg-time">{safe_time}</div></div>'
                                f'</div>'
                            )
                        else:
                            bubbles_html += (
                                f'<div class="rm-msg-row-them">'
                                f'<div class="rm-bubble-them">{safe_txt}<div class="rm-msg-time">{safe_time}</div></div>'
                                f'</div>'
                            )

                    if not bubbles_html:
                        bubbles_html = '<div style="text-align:center; color:#94a3b8; font-size:0.8rem; padding:24px 0;">You are connected! Send a message below to introduce yourself.</div>'

                    st.markdown(
                        f'<div style="max-height:300px; overflow-y:auto; padding:6px 4px 12px 4px;">{bubbles_html}</div>',
                        unsafe_allow_html=True
                    )

                    # Message input form
                    with st.form(key=f"chat_form_{active_id}", clear_on_submit=True):
                        msg_col, send_col = st.columns([4.5, 1.2])
                        with msg_col:
                            outgoing_msg = st.text_input(
                                "Message",
                                placeholder=f"Write a message to Student #{active_id}...",
                                label_visibility="collapsed"
                            )
                        with send_col:
                            submitted = st.form_submit_button("Send", type="primary")

                        if submitted and outgoing_msg.strip():
                            now_str = datetime.datetime.now().strftime("%I:%M %p")
                            st.session_state.chat_threads.setdefault(active_id, []).append({
                                "sender": "me",
                                "text": outgoing_msg.strip(),
                                "time": now_str
                            })
                            st.rerun()
        else:
            with st.container(border=True):
                st.markdown(
                    '<div style="padding:48px 20px; text-align:center; color:#64748b; font-size:0.85rem;">'
                    'Select a roommate connection on the left to open your conversation.'
                    '</div>',
                    unsafe_allow_html=True
                )
