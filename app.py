from flask import Flask, render_template, request, jsonify
import joblib
import string
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import numpy as np
from nltk.corpus import words
import nltk

app = Flask(__name__)

# Initialize NLTK
nltk.download('words')
dictionary = set(words.words())

# Load the trained model
model = joblib.load("./models/caesar_cipher_model.pkl")

# Define expected columns
expected_cols = [f'freq_{letter}' for letter in string.ascii_lowercase]

def letter_frequency(text):
    text = text.lower()
    letter_counts = {letter: 0 for letter in string.ascii_lowercase}
    total_letters = sum(text.count(c) for c in string.ascii_lowercase)
    if total_letters > 0:
        return [text.count(letter) / total_letters for letter in string.ascii_lowercase]
    return [0] * 26

def create_frequency_plot(text):
    freq = letter_frequency(text)
    letters = list(string.ascii_lowercase)
    
    plt.figure(figsize=(10, 5))
    bars = plt.bar(letters, freq, color='#6a8dff')
    
    # Highlight vowels
    for i, letter in enumerate(letters):
        if letter in ['a', 'e', 'i', 'o', 'u']:
            bars[i].set_color('#ff6b6b')
    
    plt.title('Letter Frequency Distribution', pad=15, fontsize=14)
    plt.xlabel('Letters', labelpad=10, fontsize=12)
    plt.ylabel('Frequency', labelpad=10, fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.4)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    
    # Save plot to bytes
    img = BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')

def caesar_decrypt(text, shift):
    decrypted_text = ""
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            decrypted_text += chr((ord(char) - base - shift) % 26 + base)
        else:
            decrypted_text += char
    return decrypted_text

def predict_and_decrypt(text):
    freq_vector = letter_frequency(text)
    freq_df = pd.DataFrame([freq_vector], columns=expected_cols)
    predicted_shift = model.predict(freq_df)[0]
    
    decrypted_text = caesar_decrypt(text, predicted_shift)
    if all(word.lower() in dictionary for word in decrypted_text.split()):
        return decrypted_text, predicted_shift
    
    for shift in range(1, 26):
        decrypted_text = caesar_decrypt(text, shift)
        if all(word.lower() in dictionary for word in decrypted_text.split()):
            return decrypted_text, shift
    
    return decrypted_text, predicted_shift

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/decrypt', methods=['POST'])
def decrypt():
    data = request.json
    cipher_text = data.get('cipher_text', '').strip()

    if not cipher_text:
        return jsonify({"error": "No input provided."}), 400

    try:
        # Generate frequency plot
        plot_data = create_frequency_plot(cipher_text)
        
        # Predict shift and decrypt
        decrypted_text, predicted_shift = predict_and_decrypt(cipher_text)
        
        return jsonify({
            "decrypted_text": decrypted_text,
            "predicted_shift": int(predicted_shift),
            "frequency_plot": plot_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)