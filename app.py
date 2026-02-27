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
        if st.session_state["password_input"] in st.secrets["passwords"].values():
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    # Check if the user has already logged in
    if st.session_state.get("password_correct", False):
        return True

    # Display the login form
    st.text_input(
        "Please enter the password to access the test", 
        type="password", 
        on_change=password_entered, 
        key="password_input"
    )
    
    # If the password was wrong, show an error
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    
    return False

# --- ACTIVATE THE GATE ---
# This is the crucial part you were missing!
if not check_password():
    st.stop()  # Halt execution of everything below this line until authenticated

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
st.title("Water Distribution Practice Test")

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
        
      # Create a form to group the input and the submit button
        with st.form("quiz_form"):
            if not is_fill:
                lines = str(row['Question Text']).splitlines()
                choices = [l.strip() for l in lines if re.match(r'^[a-dA-D]\.', l.strip())]
                if not choices:
                    choices = [str(row['Answer Text'])]
                user_ans = st.radio("Select your answer:", choices)
            else:
                user_ans = st.text_input("Type your answer:")
            
            # This button is now safely inside the form
            submitted = st.form_submit_button("Submit Answer")

        if submitted:
            if not is_fill:
                correct_letter = str(row['Correct Answer (Letter)']).upper()
                is_correct = user_ans[0].upper() == correct_letter if user_ans else False
            else:
                # Allows multiple answers if they are separated by commas in Column C
                valid_answers = [a.strip().lower() for a in str(row['Answer Text']).split(',')]
                is_correct = user_ans.strip().lower() in valid_answers
            
            if is_correct:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error(f"❌ Incorrect. Answer: {row['Answer Text']}")
                else:
                    st.error(f"❌ Incorrect. Answer: {row['Answer Text']}")
                st.info(f"**Source:** {row['Book Title']} | **Summary:** {row['Explanation / Summary']}")
        
        if st.button("Next Question"):
            st.session_state.current_index += 1
            st.rerun()
            
    # SHOW RESULTS 
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

        if st.button("Restart Quiz"):
            st.session_state.quiz_started = False
            st.rerun()
