import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import datetime

st.set_page_config(page_title="Roommate Matcher", page_icon="🏠", layout="wide")

# 1. Cache Resources
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
    st.error(f"Error loading assets: {e}. Please ensure model.joblib, students_model.csv, and meta.json are in the app directory.")
    st.stop()

st.title("🏠 Lifestyle-Only Roommate Finder")
st.markdown("""
Find your compatible roommates using our machine learning model. 
**Clustering is based purely on lifestyle preferences (gender is never used to group or score similarity!).**
""")

# Get all unique interests across dataset for multiselect list
all_interests = set()
for interests_str in df_students['interests'].dropna():
    for item in interests_str.split('|'):
        clean_item = item.strip()
        if clean_item:
            all_interests.add(clean_item)
all_interests = sorted(list(all_interests))

# Form columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("☀️ Lifestyle & Habits")
    sleep_schedule = st.selectbox("Sleep Schedule", ['early_bird', 'flexible', 'night_owl'])
    wake_time = st.time_input("Normal Wake-up Time", datetime.time(7, 30))
    smoking = st.selectbox("Smoking Preference", ['non_smoker', 'occasional', 'smoker'])
    drinking = st.selectbox("Drinking Preference", ['non_drinker', 'social', 'drinker'])
    cleanliness = st.slider("Cleanliness Level (1: Low, 5: High)", 1, 5, 4)
    noise = st.slider("Noise Tolerance (1: Low, 5: High)", 1, 5, 2)
    guests = st.selectbox("Guest Frequency Preference", ['rarely', 'sometimes', 'frequently'])
    study_habit = st.selectbox("Study Habit Environment", ['quiet', 'background_noise_ok', 'group_study', 'rarely_studies_at_home'])

with col2:
    st.subheader("💰 Budget & Demographics")
    budget_min = st.number_input("Your Minimum Monthly Budget (NPR)", value=5000, step=500)
    budget_max = st.number_input("Your Maximum Monthly Budget (NPR)", value=15000, step=500)
    own_gender = st.selectbox("Your Gender", ['female', 'male', 'non_binary', 'prefer_not_to_say'])
    pref_gender = st.selectbox("Preferred Roommate Gender", ['any', 'female', 'male', 'non_binary'])
    food_pref = st.selectbox("Food Preference", ['no_preference', 'vegetarian', 'vegan', 'non_vegetarian'])
    pets = st.selectbox("Pets Preference", ['no_pets', 'has_pets', 'okay_with_pets', 'not_okay_with_pets'])

    with st.expander("✨ Optional Profile Filters (City, Room & Interests)"):
        selected_interests = st.multiselect("Select your Interests", all_interests)
        location = st.text_input("Preferred Location (e.g. Kathmandu, Lalitpur, Bhaktapur)", "Kathmandu")
        room_type = st.selectbox("Room Type Preference", ['any', 'single_room', 'shared_room', 'entire_place', 'private_room'])

if st.button("🎯 Find Compatible Roommates", type="primary"):
    if budget_min > budget_max:
        st.error("Error: Minimum budget cannot be greater than maximum budget.")
        st.stop()

    # 2. Categorize input variables to match model expectations
    # Cleanliness and Noise categorizations
    cleanliness_band = 'low' if cleanliness <= 2 else ('medium' if cleanliness == 3 else 'high')
    noise_band = 'low' if noise <= 2 else ('medium' if noise == 3 else 'high')

    # Wake time categorizations
    wake_hour = wake_time.hour
    if wake_hour < 6:
        wake_time_band = 'early'
    elif wake_hour <= 8:
        wake_time_band = 'mid'
    else:
        wake_time_band = 'late'

    # Budget midpoint categorization relative to training quantile boundary lines
    input_midpoint = (budget_min + budget_max) / 2.0
    if input_midpoint < budget_edges[0]:
        budget_band = 'low'
    elif input_midpoint <= budget_edges[1]:
        budget_band = 'medium'
    else:
        budget_band = 'high'

    # 3. Predict Cluster using base lifestyle features only
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

    st.success(f"✨ Profile Processed! You were placed into Lifestyle Cohort: **Cluster {predicted_cluster}**")

    # Helper functions for calculations
    def mutual_gender_filter(candidates_df, user_g, user_p):
        cond_user_satisfied = (user_p == 'any') | (candidates_df['gender'] == user_p)
        cond_cand_satisfied = (candidates_df['gender_preference'] == 'any') | (candidates_df['gender_preference'] == user_g)
        return candidates_df[cond_user_satisfied & cond_cand_satisfied].copy()

    def compute_similarity_and_details(candidates_df, target_dict, life_feats):
        target_values = [str(target_dict[f]) for f in life_feats]
        candidate_matrix = candidates_df[life_feats].values
        
        # Similarity score calculations
        sim_scores = np.mean(candidate_matrix == target_values, axis=1)
        candidates_df['similarity_score'] = sim_scores

        # Explanatory lists
        matching_list = []
        diff_list = []
        for idx, row in candidates_df.iterrows():
            matched = [f.replace('_band', '').replace('_preference', '').title() for f in life_feats if str(row[f]) == str(target_dict[f])]
            differed = [f.replace('_band', '').replace('_preference', '').title() for f in life_feats if str(row[f]) != str(target_dict[f])]
            matching_list.append(", ".join(matched))
            diff_list.append(", ".join(differed))
        
        candidates_df['matching'] = matching_list
        candidates_df['different'] = diff_list
        return candidates_df

    def compute_interests_and_filter(candidates_df, target_interests):
        target_set = set([i.lower().strip() for i in target_interests])
        
        def get_shared_count(cand_int_str):
            if pd.isna(cand_int_str):
                return 0, []
            cand_set = set([i.lower().strip() for i in str(cand_int_str).split('|') if i.strip()])
            common = target_set.intersection(cand_set)
            return len(common), list(common)
        
        results = [get_shared_count(row['interests']) for _, row in candidates_df.iterrows()]
        candidates_df['shared_interests_count'] = [r[0] for r in results]
        candidates_df['shared_interests_list'] = [r[1] for r in results]
        return candidates_df

    # 4. Search same cluster cohort pool
    cohort = df_students[df_students['cluster'] == predicted_cluster].copy()
    total_cohort_count = len(cohort)

    # Filter on location preference if entered
    if location:
        loc_cohort = cohort[cohort['location'].str.contains(location, case=False, na=False)]
        if not loc_cohort.empty:
            cohort = loc_cohort.copy()

    # Filter on room type preference if specified
    if room_type and room_type != 'any':
        room_cohort = cohort[cohort['room_type_preference'] == room_type]
        if not room_cohort.empty:
            cohort = room_cohort.copy()

    total_filtered_before_gender = len(cohort)
    
    # Apply mutual gender constraints
    eligible_cohort = mutual_gender_filter(cohort, own_gender, pref_gender)
    total_after_gender = len(eligible_cohort)
    hidden_by_gender = total_filtered_before_gender - total_after_gender

    searched_all_clusters = False
    final_matches = pd.DataFrame()

    if total_after_gender >= 5:
        # Process similarities inside our preferred cohort cluster
        eligible_cohort = compute_similarity_and_details(eligible_cohort, input_profile, base_features)
        eligible_cohort = compute_interests_and_filter(eligible_cohort, selected_interests)
        
        final_matches = eligible_cohort.sort_values(
            by=['similarity_score', 'shared_interests_count'], 
            ascending=[False, False]
        ).head(5)
    else:
        # Fallback: search all clusters if fewer than 5 candidates remain
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

    # 5. Display Recommendations
    st.subheader("🔍 Top 5 Compatible Roommates")
    
    if final_matches.empty:
        st.warning("No compatible matches found matching your filters. Try widening your filters or location search.")
    else:
        if searched_all_clusters:
            st.info("ℹ️ Note: Fewer than 5 candidates were available in your natural lifestyle cluster. We expanded our search across other cohorts to find compatible roommates.")
        else:
            st.write(f"💡 **Filter Insights**: Out of {total_cohort_count} students in your cohort, **{hidden_by_gender}** were hidden due to mutual gender constraints.")

        for idx, row in final_matches.reset_index().iterrows():
            match_percentage = int(round(row['similarity_score'] * 100))
            
            # Render match card
            with st.container(border=True):
                col_a, col_b = st.columns([1, 4])
                with col_a:
                    st.metric(label="Match Compatibility", value=f"{match_percentage}%")
                    st.write(f"👤 ID: **{row['user_id']}**")
                    st.write(f"📍 {row['location'].title()}")
                
                with col_b:
                    st.write(f"**Gender**: {row['gender'].title()} | **Room Preference**: {row['room_type_preference'].replace('_', ' ').title()}")
                    
                    # Display matching items
                    if row['matching']:
                        st.write(f"✅ **Shared Preferences**: <span style='color:#1a73e8'>{row['matching']}</span>", unsafe_allow_html=True)
                    if row['different']:
                        st.write(f"❌ **Different Preferences**: <span style='color:#80868b'>{row['different']}</span>", unsafe_allow_html=True)
                    
                    # Display shared interests
                    if selected_interests:
                        shared_ints = row['shared_interests_list']
                        if shared_ints:
                            st.write(f"✨ **Shared Interests ({row['shared_interests_count']})**: {', '.join(shared_ints)}")
                        else:
                            st.write("⚪ No shared interests selected.")
                    else:
                        # Show original hobbies if user didn't pick criteria inputs
                        raw_ints = str(row['interests']).replace('|', ', ')
                        st.write(f"🎨 **Interests**: {raw_ints}")

    st.markdown("---")
    st.info("⚠️ **Disclaimer**: These recommendations are suggestions based on lifestyle similarities. Students are encouraged to connect directly to make the final roommate decisions.")
