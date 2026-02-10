import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import random
import re
import os

# --- 1. PASSWORD PROTECTION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 Password Required")
        user_input = st.text_input("Enter Temporary Password", type="password")
        if st.button("Unlock Test"):
            if user_input in st.secrets["passwords"]["active_list"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Invalid password.")
        return False
    return True

# --- 2. LOAD DATA ---
@st.cache_data
def load_data():
    file_name = "quiz_bank.xlsx"
    if not os.path.exists(file_name):
        return pd.DataFrame()
    try:
        df = pd.read_excel(file_name)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

# Start the App Logic
if check_password():
    df = load_data()

    # Initialize Session State
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
        st.session_state.score = 0
        st.session_state.current_index = 0
        st.session_state.questions = None

    def start_quiz(n):
        if df.empty: return
        fill_blank = df[df['Correct Answer (Letter)'].isna()].dropna(subset=['Question Text','Answer Text'])
        multi = df[df['Correct Answer (Letter)'].notna()].dropna(subset=['Question Text','Correct Answer (Letter)','Answer Text'])
        n_fill = min(int(n * 0.2), len(fill_blank))
        n_multi = n - n_fill
        s_fill = fill_blank.sample(n=n_fill) if n_fill else pd.DataFrame()
        s_multi = multi.sample(n=n_multi) if n_multi else pd.DataFrame()
        st.session_state.questions = pd.concat([s_fill, s_multi]).sample(frac=1).reset_index(drop=True)
        st.session_state.quiz_started = True
        st.session_state.current_index = 0
        st.session_state.score = 0

    st.title("Distribution One Practice Test")

    if not st.session_state.quiz_started:
        st.write("### Choose number of questions:")
        col1, col2, col3 = st.columns(3)
        if col1.button("25 Questions"): start_quiz(25)
        if col2.button("50 Questions"): start_quiz(50)
        if col3.button("100 Questions"): start_quiz(100)
    
    else:
        idx = st.session_state.current_index
        questions = st.session_state.questions
        
        # --- QUIZ IN PROGRESS ---
        if idx < len(questions):
            row = questions.iloc[idx]
            st.write(f"**Question {idx + 1} of {len(questions)}**")
            st.write(row['Question Text'])
            is_fill = pd.isna(row['Correct Answer (Letter)'])
            
            with st.form(key=f"q_{idx}"):
                if not is_fill:
                    lines = str(row['Question Text']).splitlines()
                    choices = [l.strip() for l in lines if re.match(r'^[a-dA-D]\.', l.strip())]
                    user_ans = st.radio("Select your answer:", choices)
                else:
                    user_ans = st.text_input("Type your answer:")
                
                if st.form_submit_button("Submit Answer"):
                    if not is_fill:
                        correct = str(row['Correct Answer (Letter)']).upper()
                        is_correct = user_ans[0].upper() == correct if user_ans else False
                    else:
                        is_correct = user_ans.strip().lower() in str(row['Answer Text']).lower()
                    
                    if is_correct:
                        st.success("✅ Correct!")
                        st.session_state.score += 1
                    else:
                        st.error(f"❌ Incorrect. Answer: {row['Answer Text']}")
                    st.info(f"**Source:** {row['Book Title']} | **Summary:** {row['Explanation / Summary']}")
            
            if st.button("Next Question"):
                st.session_state.current_index += 1
                st.rerun()

        # --- QUIZ FINISHED (Correctly Indented) ---
        else:
            score = st.session_state.score
            total = len(questions)
            percent_score = (score / total) * 100

            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = percent_score,
                title = {'text': "System Pressure (%)"},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 70], 'color': "#ff4b4b"},
                        {'range': [70, 100], 'color': "#09ab3b"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': 70
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

            if percent_score >= 70:
                st.success("✅ PASS: System Integrity Maintained")
                st.write("### 🚒 Fire Hydrant Secured")
            else:
                st.error("❌ FAIL")
                st.info("Looks like we are still working on that leak... 🌊")
                st.snow()
                
            if st.button("Restart Quiz"):
                st.session_state.quiz_started = False
                st.rerun()
