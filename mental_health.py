import os
import time
import json
import random
import pandas as pd
import streamlit as st
import google.generativeai as genai
import plotly.express as px

# ---------------- Load API Key ---------------- #

import streamlit as st
import google.generativeai as genai

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


# ---------------- Streamlit Config ---------------- #
st.set_page_config(page_title="AI Therapist", page_icon="💬", layout="wide")
st.markdown("<h1 style='text-align:center;color:teal;'>🧠 MINDFUL HAVEN 🌿: Your AI Therapist</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray;'>Safe • Confidential • Supportive • Not a replacement for a licensed therapist</p>", unsafe_allow_html=True)

# ---------------- Session State ---------------- #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_mood" not in st.session_state:
    st.session_state.user_mood = []
if "exercise_running" not in st.session_state:
    st.session_state.exercise_running = False
if "reflection_answers" not in st.session_state:
    st.session_state.reflection_answers = [""]*5
if "habits" not in st.session_state:
    if os.path.exists("habits.csv"):
        st.session_state.habits = pd.read_csv("habits.csv")
    else:
        st.session_state.habits = pd.DataFrame(columns=["Date","Habit","Done"])
if "riddle" not in st.session_state:
    st.session_state.riddle = random.choice([
        {"question":"What has keys but can't open locks?","answer":"keyboard"},
        {"question":"What can run but has no legs?","answer":"clock"}
    ])
if "stroop_word" not in st.session_state:
    st.session_state.stroop_word = random.choice(["Red","Green","Blue","Yellow"])
    st.session_state.stroop_color = random.choice(["Red","Green","Blue","Yellow"])
if "last_user_was_stressed" not in st.session_state:
    st.session_state.last_user_was_stressed = False
if "reflection_streak" not in st.session_state:
    st.session_state.reflection_streak = 0
if "exercise_streak" not in st.session_state:
    st.session_state.exercise_streak = 0
if "gratitude_list" not in st.session_state:
    st.session_state.gratitude_list = []
if "memory_sequence" not in st.session_state:
    st.session_state.memory_sequence = random.choices(["Red","Green","Blue","Yellow"], k=3)
if "show_sequence" not in st.session_state:
    st.session_state.show_sequence = True

# ---------------- Stress Detection ---------------- #
def detect_stress(text):
    stress_words = ["stress", "anxiety", "tired", "overwhelmed", "panic", "sad", "depressed"]
    return any(word in text.lower() for word in stress_words)

# ---------------- Exercises & Affirmations ---------------- #
AFFIRMATIONS = [
    "You are stronger than you think.",
    "Every step you take is progress.",
    "You deserve to take care of yourself.",
    "This too shall pass.",
    "Be gentle with yourself today."
]

def breathing_exercise(cycles=2):
    st.session_state.exercise_running = True
    stop = st.button("Stop Exercise", key="stop_exercise")
    if stop:
        st.session_state.exercise_running = False
        st.warning("Exercise stopped.")
        return
    st.info("🌿 Guided Breathing Exercise")
    display = st.empty()
    for i in range(cycles):
        if not st.session_state.exercise_running:
            break
        display.markdown("🌬️ **Inhale... (4s)**")
        time.sleep(4)
        display.markdown("😮‍💨 **Hold... (4s)**")
        time.sleep(4)
        display.markdown("💨 **Exhale... (6s)**")
        time.sleep(6)
    st.success("Great job! How do you feel now?")
    st.session_state.exercise_streak +=1

def show_affirmation():
    st.success(random.choice(AFFIRMATIONS))

# ---------------- Helplines ---------------- #
HELPLINES = [
    "KIRAN: 1800 599 0019",
    "Tele-MANAS: 080-4719 5000",
    "iCALL: 9152987821"
]
def show_helplines():
    st.subheader("🚨 Critical Alert: Please Reach Out")
    for h in HELPLINES:
        st.markdown(f"- {h}")

# ---------------- WHO-5 Reflection ---------------- #
REFLECTION_QUESTIONS = [
    "1. What was the highlight of your day?",
    "2. What challenged you today?",
    "3. Did you feel stressed or anxious, and how did you cope?",
    "4. What are you grateful for today?",
    "5. How would you rate your overall mood today (1–5)?"
]

CRITICAL_SCORE = 2

def save_reflection():
    entry = {"answers": st.session_state.reflection_answers, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
    if os.path.exists("checkins.json") and os.path.getsize("checkins.json") > 0:
        with open("checkins.json", "r") as f:
            try:
                data = json.load(f)
            except:
                data = []
    else:
        data = []
    data.append(entry)
    with open("checkins.json", "w") as f:
        json.dump(data, f, indent=2)
    try:
        mood = int(st.session_state.reflection_answers[4])
        st.session_state.user_mood.append(mood)
        st.session_state.reflection_streak +=1
        if mood <= CRITICAL_SCORE:
            show_helplines()
    except:
        pass

# ---------------- Mood Graph ---------------- #
def plot_mood_trends():
    if st.session_state.user_mood:
        days = list(range(1, len(st.session_state.user_mood)+1))
        df = pd.DataFrame({"Day": days, "Mood": st.session_state.user_mood})
        fig = px.line(df, x="Day", y="Mood", markers=True, title="Mood Trend Over Days",
                      line_shape="spline", color_discrete_sequence=["teal"])
        fig.update_layout(yaxis=dict(range=[0,5]), xaxis=dict(dtick=1))
        st.plotly_chart(fig, use_container_width=True)

# ---------------- Habit Tracker ---------------- #
def habit_tracker():
    st.subheader("📋 Habit Tracker")
    habit_name = st.text_input("Enter new habit", key="habit_input")
    if st.button("Add Habit", key="add_habit"):
        if habit_name:
            df = st.session_state.habits
            df = pd.concat([df,pd.DataFrame([{"Date":time.strftime("%Y-%m-%d"),"Habit":habit_name,"Done":0}])],ignore_index=True)
            st.session_state.habits = df
            df.to_csv("habits.csv", index=False)
            st.success("Habit added!")
    df = st.session_state.habits
    for idx,row in df.iterrows():
        done = st.checkbox(f"{row['Date']} - {row['Habit']}", value=bool(row["Done"]), key=f"habit_{idx}")
        df.at[idx,"Done"]=int(done)
    df.to_csv("habits.csv", index=False)

# ---------------- Games ---------------- #
def mood_check_game():
    st.subheader("🎯 Quick Mood Check")
    st.write("Select how you feel right now:")

    moods = {
        "😊 Happy": "Great! Keep smiling and doing what you love. 🌟",
        "😔 Sad": "It's okay to feel sad. Take a deep breath and be gentle with yourself. 💛",
        "😡 Angry": "Anger is natural. Try some deep breaths or a quick walk to calm down. 🌿",
        "😰 Anxious": "Notice your anxiety, breathe slowly, and remind yourself it will pass. 🌬️",
        "😴 Tired": "Rest is important. Take a short break or a power nap. 💤"
    }

    col1, col2, col3 = st.columns(3)
    for idx, (mood, advice) in enumerate(moods.items()):
        col = [col1, col2, col3][idx % 3]
        if col.button(mood, key=f"mood_{idx}"):
            st.success(advice)
            st.session_state.user_mood.append(4 if mood=="😊 Happy" else 2)

def stroop_game():
    st.subheader("🎨 Stroop Color-Word Game")
    word = st.session_state.stroop_word
    color = st.session_state.stroop_color
    st.write(f"Word: **{word}** (in color: {color})")
    for c in ["Red","Green","Blue","Yellow"]:
        if st.button(c, key=f"stroop_{c}"):
            if c==color:
                st.success("✅ Correct!")
            else:
                st.error("❌ Incorrect")
            st.session_state.stroop_word = random.choice(["Red","Green","Blue","Yellow"])
            st.session_state.stroop_color = random.choice(["Red","Green","Blue","Yellow"])

def riddle_quiz():
    st.subheader("🧩 Riddle Quiz")
    riddle = st.session_state.riddle
    ans = st.text_input(riddle["question"], key="riddle_input")
    if ans.lower()==riddle["answer"]:
        st.success("🎉 Correct!")
        st.session_state.riddle = random.choice([
            {"question":"What has keys but can't open locks?","answer":"keyboard"},
            {"question":"What can run but has no legs?","answer":"clock"}
        ])


def memory_game():
    st.subheader("🧠 Memory Game: Color Sequence")
    
    # Step 1: Show sequence
    if st.session_state.show_sequence:
        st.info("Memorize this sequence:")
        st.write(" - ".join(st.session_state.memory_sequence))
        if st.button("I've memorized, hide sequence"):
            st.session_state.show_sequence = False
    else:
        # Step 2: User input
        user_seq = [st.selectbox(f"Step {i+1}", ["Red","Green","Blue","Yellow"], key=f"mem_{i}") 
                    for i in range(len(st.session_state.memory_sequence))]
        if st.button("Check Sequence"):
            if user_seq == st.session_state.memory_sequence:
                st.success("🎉 Correct sequence!")
            else:
                st.error(f"❌ Wrong! Correct was: {', '.join(st.session_state.memory_sequence)}")
            # Reset for next round
            st.session_state.memory_sequence = random.choices(["Red","Green","Blue","Yellow"], k=3)
            st.session_state.show_sequence = True

# ---------------- Sidebar ---------------- #
with st.sidebar:
    st.header("📂 Features")
    # Reflection
    st.subheader("Daily Reflection")
    for idx,q in enumerate(REFLECTION_QUESTIONS):
        st.session_state.reflection_answers[idx] = st.text_input(q, key=f"sidebar_reflection_{idx}")
    if st.button("Save Reflection", key="sidebar_save_reflection"):
        save_reflection()
        st.success("Reflection saved.")

    # Graphs
    plot_mood_trends()

    # Habits & Games
    habit_tracker()
    mood_check_game()
    stroop_game()
    riddle_quiz()
    memory_game()

    # Gratitude
    st.subheader("🌸 Gratitude Wall")
    gratitude_input = st.text_input("What are you grateful for today?", key="gratitude_input")
    if st.button("Add Gratitude", key="add_gratitude"):
        st.session_state.gratitude_list.append(f"{time.strftime('%Y-%m-%d')}: {gratitude_input}")
    st.write("\n".join(st.session_state.get("gratitude_list", [])))

    # Micro-Challenges
    st.subheader("🎯 Daily Micro-Challenges")
    challenges = ["Take a 2-min walk", "Drink a glass of water", "Stretch for 1 minute"]
    for idx, c in enumerate(challenges):
        done = st.checkbox(c, key=f"challenge_{idx}")

    # Streaks & Affirmation
    st.info(f"Reflection Streak: {st.session_state.reflection_streak} days")
    st.info(f"Exercise Streak: {st.session_state.exercise_streak} days")
    st.info(f"Habits tracked: {len(st.session_state.habits)}")
    st.info(f"Gratitude entries: {len(st.session_state.get('gratitude_list', []))}")
    st.subheader("💛 Daily Affirmation")
    st.info(random.choice(AFFIRMATIONS))

# ---------------- Main Chat Area ---------------- #
model = genai.GenerativeModel("gemini-2.5-flash")
user_input = st.chat_input("How are you feeling today?")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    response = model.generate_content(
        f"You are an empathetic AI therapist. Respond kindly and supportively to: {user_input}"
    )
    bot_reply = response.text
    st.session_state.chat_history.append(("bot", bot_reply))
    st.session_state.last_user_was_stressed = detect_stress(user_input)

# Render chat
for role,msg in st.session_state.chat_history:
    if role=="user":
        st.chat_message("user").write(msg)
    else:
        st.chat_message("assistant").write(msg)

# Suggested activities if stressed
if st.session_state.get("last_user_was_stressed",False):
    st.subheader("💡 Suggested Activities")
    col1, col2 = st.columns(2)
    if col1.button("🌿 Breathing Exercise", key="suggest_breath"):
        breathing_exercise()
    if col2.button("💛 Positive Affirmation", key="suggest_affirm"):
        show_affirmation()
