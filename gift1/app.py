from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import re
import os

app = Flask(__name__)

# Load the Gemini API key from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

products_schema = [
    {
        "Product_name": "Eco-friendly Water Bottle",
        "Reason": "Chosen for its environmental benefits and the growing consumer preference for sustainable products."
    },
]

# Initialize the Gemini API client
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.0-pro')

# Global list to store all generated gift ideas
all_gift_ideas = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_gift_idea', methods=['POST'])
def generate_gift_idea():
    try:
        data = request.json
        age = data.get('age', '')
        gender = data.get('gender', '')
        occasion = data.get('occasion', '')
        recipient_type = data.get('recipient_type', '')
        categories = data.get('categories', [])
        price_range = data.get('price_range', '')

        prompt = create_prompt(age, gender, occasion, recipient_type, categories, price_range)
        response = model.generate_content(prompt)
        cleaned_text = clean_text(response.text)
        gift_ideas = process_and_structure_gift_ideas(cleaned_text)
        
        # Filter out duplicate gift ideas
        unique_gift_ideas = filter_unique_gift_ideas(gift_ideas)
        
        # Append unique gift ideas to the global list of all gift ideas
        all_gift_ideas.extend(unique_gift_ideas)

        return jsonify({"gift_ideas": unique_gift_ideas})
    except Exception as e:
        print(f"Error generating gift ideas: {e}")
        return jsonify({"error": "Error generating gift ideas"}), 500

@app.route('/search_gift_idea', methods=['POST'])
def search_gift_idea():
    try:
        data = request.json
        textdata = data.get('prompt')
        
        if not textdata:
            return jsonify({"error": "'prompt' is required."}), 400

        prompt = create_search_prompt(textdata)
        response = model.generate_content(prompt)
        cleaned_text = clean_text(response.text)
        gift_ideas = process_and_structure_gift_ideas(cleaned_text)

        # Filter out duplicate gift ideas
        unique_gift_ideas = filter_unique_gift_ideas(gift_ideas)
        
        # Append unique gift ideas to the global list of all gift ideas
        all_gift_ideas.extend(unique_gift_ideas)

        return jsonify({"gift_ideas": unique_gift_ideas})
    except Exception as e:
        print(f"Error generating gift ideas: {e}")
        return jsonify({"error": "Error generating gift ideas"}), 500

@app.route('/generate_more_ideas', methods=['POST'])
def generate_more_ideas():
    try:
        # Generate more gift ideas based on the existing criteria
        response = generate_gift_idea()
        return response
    except Exception as e:
        print(f"Error generating more gift ideas: {e}")
        return jsonify({"error": "Error generating more gift ideas"}), 500

def create_prompt(age, gender, occasion, recipient_type, categories, price_range):
    prompt_parts = ["You are an expert in finding gifts for Indian people, so provide me a list of 9 popular and trending different products that can be searched using the product name."]

    if age:
        prompt_parts.append(f"for a {age}-year-old")
    if recipient_type:
        prompt_parts.append(recipient_type)
    if gender:
        prompt_parts.append(f"who is {gender}")
    if categories:
        categories_str = ', '.join(categories)
        prompt_parts.append(f"and loves {categories_str} items")
    if occasion:
        prompt_parts.append(f"suitable for {occasion}")
    if price_range:
        prompt_parts.append(f"within the price range {price_range}")

    prompt_parts.append("These gifts should be popular among Indian people and available on e-commerce websites like Amazon India. Ensure that each product is followed by its product_name, and each product is followed by a convincing reason for its selection. Ensure that the products are listed without any special characters such as *, -, or numbering. Here is an example:")
    prompt_parts.append("Product_name: Eco-friendly Water Bottle")
    prompt_parts.append("Reason: Chosen for its environmental benefits and the growing consumer preference for sustainable products.")
    prompt_parts.append("Generate 9 products with product_name and reason for selection as a gift idea. Each reason should be just below the product name.")

    return ' '.join(prompt_parts)

def create_search_prompt(textdata):
    return (
        f"You are an expert in finding gifts for Indian people. Based on the following input: '{textdata}', provide me with a list of 9 popular and trending products in India that would make excellent gifts for Indian people. "
        f"These products should be available for purchase on major Indian e-commerce websites like Amazon India. Ensure that the list includes only the product names followed by a convincing reason for selecting each product as a gift idea. "
        f"The reason should explain why the product is a good gift for Indian recipients. Provide the output in the following format:\n\n"
        f"Product_name:\nReason:\n\n"
        f"Here is an example:\n"
        f"Product_name: Eco-friendly Water Bottle\n"
        f"Reason: Chosen for its environmental benefits and the growing consumer preference for sustainable products."
    )

def filter_unique_gift_ideas(new_gift_ideas):
    # Filter out any duplicate gift ideas from the new list
    unique_gift_ideas = []
    for idea in new_gift_ideas:
        if idea not in all_gift_ideas:
            unique_gift_ideas.append(idea)
    return unique_gift_ideas

def clean_text(text):
    # Remove any asterisks, numbering, or unwanted characters
    text = re.sub(r'[*-]', '', text)
    text = re.sub(r'\d+\.\s*', '', text)  # Remove numbering (e.g., "1. ", "2. ", etc.)
    return text

def process_and_structure_gift_ideas(text):
    lines = text.split('\n')
    gift_ideas = []
    current_gift = {}

    for line in lines:
        if "Product_name:" in line:
            if current_gift and "Product_name" in current_gift and "Reason" in current_gift:
                gift_ideas.append(current_gift)
                current_gift = {}
            current_gift["Product_name"] = line.replace("Product_name:", "").strip()
        elif "Reason:" in line:
            current_gift["Reason"] = line.replace("Reason:", "").strip()

    if current_gift and "Product_name" in current_gift and "Reason" in current_gift:
        gift_ideas.append(current_gift)

    # Ensure we have exactly 9 gift ideas, pad with empty entries if necessary
    while len(gift_ideas) < 9:
        gift_ideas.append({"Product_name": "N/A", "Reason": "N/A"})

    return gift_ideas[:9]

if __name__ == '__main__':
    app.run(debug=True)
