import pandas as pd
import string
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os
import nltk
from nltk.corpus import words

# Download word list
nltk.download('words')
dictionary = set(words.words())

df_cipher = pd.read_csv("cipher2.csv")
df_freq = pd.read_csv("allCharFreqs.csv")

print("Columns in df_freq:", df_freq.columns)

def rename_freq_columns(df):
    lowercase_cols = [col.lower() for col in df.columns]
    letter_cols = [letter for letter in string.ascii_lowercase if letter in lowercase_cols]
    df = df[['GroupFile'] + letter_cols]
    df.columns = ['GroupFile'] + [f'freq_{col}' for col in letter_cols]
    return df

df_freq = rename_freq_columns(df_freq)

def letter_frequency(text):
    text = text.lower()
    letter_counts = {letter: 0 for letter in string.ascii_lowercase}
    total_letters = sum(text.count(c) for c in string.ascii_lowercase)
    if total_letters > 0:
        return [text.count(letter) / total_letters for letter in string.ascii_lowercase]
    else:
        return [0] * 26

df_cipher['Frequency'] = df_cipher['Text'].apply(letter_frequency)

expected_cols = [f'freq_{letter}' for letter in string.ascii_lowercase]
freq_df = pd.DataFrame(df_cipher['Frequency'].to_list(), columns=expected_cols)
df_cipher = pd.concat([df_cipher.drop(columns=['Frequency']), freq_df], axis=1)

def estimate_shift(text):
    letter_counts = {letter: text.count(letter) for letter in string.ascii_lowercase}
    if not any(letter_counts.values()):
        return np.nan
    most_frequent = max(letter_counts, key=letter_counts.get)
    shift = (ord(most_frequent) - ord('e')) % 26
    return shift

df_cipher['Shift'] = df_cipher['Text'].apply(estimate_shift)
df_cipher = df_cipher.dropna(subset=['Shift'])

df_combined = pd.concat([df_cipher[expected_cols + ['Shift']],
                         df_freq.drop(columns=['GroupFile'], errors='ignore')],
                        axis=0, ignore_index=True)

df_combined = df_combined.dropna(subset=['Shift'])
df_combined['Shift'] = df_combined['Shift'].astype(int)

X = df_combined[expected_cols]
y = df_combined['Shift']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.2%}")

os.makedirs("./models", exist_ok=True)
try:
    joblib.dump(model, "./models/caesar_cipher_model.pkl")
    print("Model saved successfully.")
except Exception as e:
    print(f"Skipping model saving due to error: {e}")

def caesar_decrypt(text, shift):
    decrypted_text = ""
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            decrypted_text += chr((ord(char) - base - shift) % 26 + base)
        else:
            decrypted_text += char
    return decrypted_text

def is_valid_word(word):
    return word.lower() in dictionary

def predict_and_decrypt(text, model):
    freq_vector = letter_frequency(text)
    freq_df = pd.DataFrame([freq_vector], columns=expected_cols)
    predicted_shift = model.predict(freq_df)[0]
    
    decrypted_text = caesar_decrypt(text, predicted_shift)
    if all(is_valid_word(word) for word in decrypted_text.split()):
        return decrypted_text, predicted_shift
    
    for shift in range(1, 26):
        decrypted_text = caesar_decrypt(text, shift)
        if all(is_valid_word(word) for word in decrypted_text.split()):
            return decrypted_text, shift
    
    return decrypted_text, predicted_shift

test_text = "bcd"
test_shift = 1
assert caesar_decrypt(test_text, test_shift) == "abc", "Decryption logic is incorrect!"
print("Decryption logic validated.")

if not df_cipher.empty:
    sample_text = df_cipher.iloc[0]['Text']
    decrypted_text, predicted_shift = predict_and_decrypt(sample_text, model)
    print("\nSample Ciphertext:", sample_text)
    print("Predicted Shift:", predicted_shift)
    print("Decrypted Text:", decrypted_text)
else:
    print("No valid cipher texts available for testing.")

model_path = "./models/caesar_cipher_model.pkl"
if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("Model loaded successfully.")
else:
    print("Model file not found. Train and save the model first.")
    exit()

def plot_letter_frequency(text):
    text = text.lower()
    letter_counts = {letter: text.count(letter) for letter in string.ascii_lowercase}
    
    plt.figure(figsize=(10, 5))
    plt.bar(letter_counts.keys(), letter_counts.values(), color='skyblue')
    plt.xlabel("Letters")
    plt.ylabel("Frequency")
    plt.title(f"Letter Frequency Distribution for: {text}")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

def decrypt_user_input():
    user_text = input("Enter the cipher text to decrypt: ")
    if not user_text.strip():
        print("No input provided. Please enter a valid cipher text.")
        return
    
    decrypted_text, predicted_shift = predict_and_decrypt(user_text, model)
    print("\nOriginal Cipher Text:", user_text)
    print("Predicted Shift:", predicted_shift)
    print("Decrypted Text:", decrypted_text)
    
    # Plot the letter frequency graph
    plot_letter_frequency(user_text)

decrypt_user_input()