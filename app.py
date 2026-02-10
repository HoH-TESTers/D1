import streamlit as st
import pandas as pd
import random
import re
import os

# --- 1. PASSWORD PROTECTION ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "Dh0l#isabh0l3":  ## <--- Password Updated
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Enter Password to access the Quiz", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Enter Password to access the Quiz", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- 2. LOAD EXCEL FILE ---
@st.cache_data
def load_data():
    file_name = "quiz_bank.xlsx"
    if not os.path.exists(file_name):
        st.error(f"Error: {file_name} not found.")
        return pd.DataFrame()
    try:
        df = pd.read_excel(file_name)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- 3. SESSION STATE ---
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
    st.session_state.score = 0
    st.session_state.current_index = 0
    st.session_state.questions = None

# --- 4. START QUIZ LOGIC ---
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

# --- 5. INTERFACE ---
st.title("Protected Quiz App")

if not st.session_state.quiz_started:
    st.write("### Choose number of questions:")
    col1, col2, col3 = st.columns(3)
    if col1.button("25 Questions"): start_quiz(25)
    if col2.button("50 Questions"): start_quiz(50)
    if col3.button("100 Questions"): start_quiz(100)
else:
    idx = st.session_state.current_index
    questions = st.session_state.questions
    
    # Check if there are still questions to answer
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
            
    # SHOW RESULTS (This else matches line 87 - "if idx < len(questions)")
    else:
        if st.session_state.questions is not None:
            final_score = st.session_state.score
            total_qs = len(st.session_state.questions)
            
            st.write(f"## Quiz Complete")
            st.write(f"### Final Score: {final_score} / {total_qs}")
            
            if (final_score / total_qs) >= 0.7:
                st.success("Result: PASS")
            else:
                st.error("Result: FAIL")
        else:
            st.info("Please select a quiz size above to begin.")

        if st.button("Restart Quiz"):
            st.session_state.quiz_started = False
            st.rerun()
