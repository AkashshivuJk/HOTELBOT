from flask import Flask, request, jsonify, render_template, session
import uuid
import requests
from main import calorie_database, recipes

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production
user_states = {}
API_KEY = "YOUR_GEMINI_API"  
API_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json'


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def homee():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '').strip().lower()
    choice = request.json.get('option', '').lower()

    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

    user_id = session['user_id']

    if user_id not in user_states:
        user_states[user_id] = {"state": None, "dish": None}

    user_state = user_states[user_id]

    if not user_input and user_state["state"] not in ["recipe", "calorie", "restaurant"]:
        return jsonify({"reply": "Please provide a message."})

    if user_state["state"] == "recipe":
        if user_input in recipes:
            reply = f"Here is the recipe for {user_input.capitalize()}: {recipes[user_input]}"
        else:
            reply = f"Sorry, I don't have a recipe for {user_input}. Try another dish."
        user_state["state"] = None
    elif user_state["state"] == "calorie":
        if user_input in calorie_database:
            calories = calorie_database[user_input]
            reply = f"{user_input.capitalize()} contains approximately {calories} calories."
        else:
            reply = f"Sorry, I don't have calorie information for {user_input}. Try another food item."
        user_state["state"] = None
    elif user_state["state"] == "restaurant":
        response = get_nearby_hotels(user_input)
        hotels = parse_hotel_data(response)
        if hotels:
            reply = "Here are some hotels I found:\n"
            for hotel in hotels:
                reply += f"{hotel['name']} - {hotel['address']} (Rating: {hotel['rating']}, Price Level: {hotel['price_level']})_________________________"
        else:
            reply = "Sorry, I couldn't find any hotels nearby."
        user_state["state"] = None
    elif choice == 'recipe recommendations':
        reply = "Please tell me the name of the dish you'd like a recipe for."
        user_state["state"] = "recipe"
    elif choice == "calorie tracking":
        reply = "Please enter the name of the food item to check its calorie content."
        user_state["state"] = "calorie"
    elif choice == "restaurant suggestions":
        reply = "Please tell me your CITY, and I'll suggest the best hotels nearby."
        user_state["state"] = "restaurant"
    else:
        reply = "I didn't understand that. Please choose one of the options: Recipe Recommendations, Calorie Tracking, or Restaurant Suggestions."

    return jsonify({"reply": reply})


def get_nearby_hotels(location):
    try:
        params = {
            'query': f"hotels in {location}",
            'key': API_KEY
        }
        response = requests.get(API_URL, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching hotels: {e}")
        return None


def parse_hotel_data(response):
    if response and "results" in response:
        hotels = []
        for result in response["results"]:
            hotel = {
                "name": result.get("name"),
                "address": result.get("formatted_address", "Address not available"),
                "rating": result.get("rating", "No rating"),
                "price_level": result.get("price_level", "Price not available"),
                "hotel_id": result.get("place_id")
            }
            hotels.append(hotel)
        return hotels
    return None


if __name__ == "__main__":
    app.run(debug=True)
