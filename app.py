import streamlit as st
import sqlite3
import bcrypt
import requests
import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import plotly.express as px
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    
# Connect to SQLite database
conn = sqlite3.connect('users1.db')
c = conn.cursor()

# Create table
def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS usertable(username TEXT, password TEXT,name TEXT,age INTEGER,weight REAL,sports TEXT,gender TEXT)')

# Add userdata to table
def add_userdata(username, password,name,age,weight,sports,gender):
    c.execute('INSERT INTO usertable(username, password,name,age,weight,sports,gender) VALUES (?,?,?,?,?,?,?)', (username, password,name,age,weight,sports,gender))
    conn.commit()

# Login function
def login_user(username, password):
    c.execute('SELECT * FROM usertable WHERE username = ?', (username,))
    data = c.fetchone()
    if data is not None:
        return bcrypt.checkpw(password.encode('utf-8'), data[1])
    return False

# Hash a password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def get_nutrition_data(query):
    api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(query)
    headers = {'X-Api-Key': 'WW9jWbpZewIbt8wkJOc67g==MXhMa7y4spD4cwQj'}  # Replace with your actual API key
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise exception for unsuccessful requests
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

# Load data
data = pd.read_csv('food1.csv')

# Define function to get sports profile
def get_sport_profile(sport):
    profiles = {
        'endurance': {'Kilocalories': 400, 'Protein': 20, 'Carbohydrate': 70, 'SaturatedFat': 10, 'Fiber': 5},
        'strength': {'Kilocalories': 500, 'Protein': 50, 'Carbohydrate': 20, 'SaturatedFat': 25, 'Fiber': 5},
        'cricket': {'Kilocalories': 650, 'Protein': 30, 'Carbohydrate': 70, 'SaturatedFat': 15, 'Fiber': 20},
        'football': {'Kilocalories': 800, 'Protein': 40, 'Carbohydrate': 100, 'SaturatedFat': 16, 'Fiber': 25},
        'swimming': {'Kilocalories': 500, 'Protein': 20, 'Carbohydrate': 60, 'SaturatedFat': 10, 'Fiber': 5},
    'wrestling': {'Kilocalories': 800, 'Protein': 50, 'Carbohydrate': 40, 'SaturatedFat': 25, 'Fiber': 15},
    'badminton': {'Kilocalories': 400, 'Protein': 15, 'Carbohydrate': 50, 'SaturatedFat': 5, 'Fiber': 5}
    }
    return profiles.get(sport, None)

def calculate_bmi(weight, height):
    if height <= 0:
        return 0
    return weight / ((height / 100) ** 2)

# Prepare data scaling
features = ['Kilocalories', 'Protein', 'Carbohydrate', 'SaturatedFat', 'Fiber']
data_scaled = MinMaxScaler().fit_transform(data[features])

# Define function to recommend meals
def recommend_meals(sport,bmi):
    profile = get_sport_profile(sport)
    if not profile:
        st.error(f"No profile available for sport: {sport}")
        return
    if bmi < 18.5:
        profile['Kilocalories'] *= 1.1  # increase caloric intake for underweight
    elif bmi > 25:
        profile['Kilocalories'] *= 0.9
    # Convert profile to DataFrame and scale
    profile_df = pd.DataFrame([profile])
    profile_scaled = MinMaxScaler().fit(data[features]).transform(profile_df)

    # Calculate cosine similarity
    similarity_scores = cosine_similarity(profile_scaled, data_scaled)

    # Get the top 5 most similar meals
    top_indices = np.argsort(similarity_scores[0])[::-1][:5]
    results = []
    for index in top_indices:
        description=data.iloc[index]['Description']
        weight=data.iloc[index]['Weight']
        weight_des=data.iloc[index]["WeightDescription"]
        results.append((description,weight,weight_des, similarity_scores[0][index]))
    return results

def log_meal(username, filename, date, meal, calories, protein, carbs, fats, fiber):
    with open(filename, 'a') as file:
        file.write(f"{username},{date},{meal},{calories},{protein},{carbs},{fats},{fiber}\n")

# Function to read meal history and nutrition data
def read_nutrition_history(filename):
    try:
        return pd.read_csv(filename, names=['Username','Date', 'Meal', 'Calories', 'Protein', 'Carbohydrates', 'Fats', 'Fiber'])
    except FileNotFoundError:
        return pd.DataFrame()

# Function to delete a meal
def delete_meal(filename, selected_indices):
    data = read_nutrition_history(filename)
    if not data.empty:
        data = data.drop(data.index[selected_indices])
        data.to_csv(filename, index=False, header=False)
        return data

# Function to plot daily nutritional intake
def plot_daily_nutrition(data):
    if not data.empty:
        daily_totals = data.groupby('Date').sum().reset_index()
        fig = px.line(daily_totals, x='Date', y=['Calories', 'Protein', 'Carbohydrates', 'Fats', 'Fiber'],
                      labels={'value': 'Amount', 'variable': 'Nutrient'},
                      title='Daily Nutritional Intake Over Time')
        st.plotly_chart(fig)

def main():
    
    st.title("Nutritracker")

    menu = [ "Login", "SignUp", "Get Nutrition","Meal Generation","Meal Tracker"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        new_name=st.text_input("Name")
        new_age=st.text_input("Age")
        new_weight=st.text_input("Weight")
        new_sports=st.text_input("Sports")
        new_gender=st.text_input("Gender")

        if st.button("Signup"):
            create_usertable()
            hashed_pw = hash_password(new_password)
            add_userdata(new_user, hashed_pw,new_name,new_age,new_weight,new_sports,new_gender)
            st.success("You have successfully created a valid Account")
            st.info("Go to the Login Menu to login")

    elif choice == "Login":
       left_col, right_col = st.columns([1, 1])
       with left_col:
         st.subheader("Login Section")
         username = st.text_input("Username")
         password = st.text_input("Password", type='password')
       with right_col:
           st.write("")
       if st.button("Login"):
            create_usertable()
            result = login_user(username, password)
            if result:
                st.session_state.logged_in = True  # Set logged_in session state to True
                st.success("Logged In as {}".format(username))
            else:
                st.warning("Incorrect Username/Password")


    

    elif choice == "Get Nutrition":
        st.subheader("Nutritional Information")
        query = st.text_input("Enter food or drink items")  # Define query within this section
        nutrition_data = get_nutrition_data(query)  # Call the function
        if nutrition_data:
            # Display retrieved nutritional information using Streamlit elements
            st.success("Nutritional data for '{}'".format(query))
            with st.expander("See Nutritional Values"):
                st.write_stream(nutrition_data)
            # Process and display relevant details from the JSON data (calories, fat, carbs, etc.)
        else:
            st.write("No nutritional data found. Please enter a valid query.")

    elif choice =="Meal Generation":
        if not st.session_state.logged_in:
            st.warning("Please login to generate meals!")
            return
        st.subheader("Generate Meals Based on Current Weight and Height")
        sport_input = st.selectbox('Select a Sport:', options=['endurance', 'strength', 'cricket', 'football','swimming','wrestling','badminton'])
        height = st.number_input('Enter your height in cm', min_value=100, max_value=250)
        weight = st.number_input('Enter your weight in kg', min_value=30, max_value=200)
        # Calculate BMI
        bmi = calculate_bmi(weight, height)
        recommendations = recommend_meals(sport_input, bmi)
        if recommendations:
            st.write(f"Top recommended meals for {sport_input} based on your BMI of {bmi:.2f}:")
            for desc, weight, weight_description, score in recommendations:
                st.write(f"- {desc}, {weight} g - {weight_description} ")
        else:
            st.write("No recommendations available. Check if the sport is correct or try again.")

    elif choice == "Meal Tracker":
        with st.sidebar:
            st.header('Log Your Meal')
            username_input = st.text_input('Username')
            filename = f'nutrition_tracker_{username_input}.csv'  # Create separate CSV file for each user
            date_input = st.date_input('Date', pd.to_datetime('today'))
            meal_input = st.text_input('Meal Description')
            calories_input = st.number_input('Calories', min_value=0, step=1)
            protein_input = st.number_input('Protein (g)', min_value=0.0, step=0.1)
            carbs_input = st.number_input('Carbohydrates (g)', min_value=0.0, step=0.1)
            fats_input = st.number_input('Fats (g)', min_value=0.0, step=0.1)
            fiber_input = st.number_input('Fiber (g)', min_value=0.0, step=0.1)
            if st.button('Log Meal'):
                log_meal(username_input, filename, date_input, meal_input, calories_input, protein_input, carbs_input, fats_input, fiber_input)
                st.success('Meal logged successfully!')

        # Display meal history and nutrition plots
        meal_data = read_nutrition_history(filename)
        if not meal_data.empty:
            st.header('Nutritional Intake Overview')
            st.dataframe(meal_data)

        selected_indices = st.multiselect('Select meals to delete (by index):', meal_data.index)
        if st.button('Delete Selected Meals'):
            meal_data = delete_meal(filename, selected_indices)
            st.success('Selected meals deleted successfully!')
            st.dataframe(meal_data)  

        st.header('Daily Nutritional Intake Trends')
        plot_daily_nutrition(meal_data)
    else:
        st.warning("Please login to generate meals!")
    
    if st.session_state.logged_in:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.info("Logged out successfully!")
            st.experimental_rerun()
if __name__ == '__main__':
    main()
