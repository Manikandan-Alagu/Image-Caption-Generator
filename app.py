import sqlite3
import streamlit as st
from passlib.hash import bcrypt
from PIL import Image
from model import get_caption_model, generate_caption
from googletrans import Translator
import requests

# Initialize Streamlit app
st.set_page_config(page_title="Image Caption Generator", layout="wide")

# Initialize Translator
translator = Translator()

# Function to create the SQLite table if it doesn't exist
@st.cache(allow_output_mutation=True)
def create_table():
    with sqlite3.connect("login.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')

# Function to handle user signup
def signup():
    st.title("Signup")
    st.markdown("<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px; text-align: center;'>Signup</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please fill in the details to sign up:</p>", unsafe_allow_html=True)
    
    new_username = st.text_input("New Username", help="Choose a unique username")
    new_password = st.text_input("New Password", type="password", help="Password should be at least 8 characters long")
    new_email = st.text_input("Email", help="Enter a valid email address")

    if st.button("Signup", style='margin-top: 10px;'):
        if not new_username or not new_password or not new_email:
            st.error("All fields are required for signup.")
            return

        role = "user"
        hashed_password = bcrypt.hash(new_password)

        try:
            with sqlite3.connect("login.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                               (new_username, hashed_password, new_email, role))
            st.success("Signup successful! You can now login.")
            st.balloons()
        except sqlite3.IntegrityError:
            st.error("Username already exists. Please choose a different username.")

# Function to handle user login
def login():
    st.title("Login")
    st.markdown("<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px; text-align: center;'>Login</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please enter your login details:</p>", unsafe_allow_html=True)
    
    username = st.text_input("Username", help="Enter your username")
    password = st.text_input("Password", type="password", help="Enter your password")

    if st.button("Login", style='margin-top: 10px;'):
        if not username or not password:
            st.error("Username and password are required for login.")
            return
        
        try:
            with sqlite3.connect("login.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()

            if user and bcrypt.verify(password, user[2]):
                st.success("Login successful!")
                st.write(f"You are logged in as: {user[1]}")
                st.image("profile_image_placeholder.jpg", caption="Your Profile Image", width=100)

                st.session_state.username = username
                st.session_state.selected_tab = "Generate Caption"
                st.balloons()
            else:
                st.error("Login failed. Invalid username or password.")
        except sqlite3.OperationalError as e:
            st.error(f"An error occurred while trying to log in: {e}")

# Rest of the code remains the same...

if __name__ == "__main__":
    main()
