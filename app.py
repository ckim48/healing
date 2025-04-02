from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pyrebase
from openai import OpenAI
import os
import sqlite3
from werkzeug.utils import secure_filename
from config import firebaseConfig
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_from_directory



# Initialize Flask App
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



# Initialize OpenAI Client


app.secret_key = 'your-secret-key'

# Init DB

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Routes
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user'] = user[1]
            return redirect('/chat')
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
            conn.close()
            session['user'] = email
            return redirect("/chat")
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Email already exists")
    return render_template("signup.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat_page():
    if 'user' not in session:
        return redirect('/login')
    return render_template('chat.html')



@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")

    if not user_input:
        return jsonify({"error": "Message cannot be empty"}), 400

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful and empathetic therapist AI."},
            {"role": "user", "content": user_input}
        ]
    )

    return jsonify({"response": response.choices[0].message.content})
@app.route('/describe-image', methods=['POST'])
def describe_image():
    filename = request.json.get("filename")
    user_email = session.get('user')

    if not filename or not user_email:
        return jsonify({"error": "Missing data"}), 400

    user_image_url = f"/uploads/{filename}"

    prompt = (
        f"A user uploaded a drawing titled '{filename}'. "
        "You are a warm and supportive art therapist. Say something kind, and give a suggestion."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are an art therapist AI helping users reflect emotionally on their art."
            },
            {"role": "user", "content": prompt}
        ]
    )

    ai_reply = response.choices[0].message.content.strip()

    dalle_prompt = "A peaceful forest path in pastel watercolor style"
    for line in reversed(ai_reply.splitlines()):
        if line.strip().startswith('"') and line.strip().endswith('"'):
            dalle_prompt = line.strip().strip('"')
            break

    image_response = client.images.generate(
        model="dall-e-3",
        prompt=dalle_prompt,
        size="1024x1024",
        n=1
    )

    ai_image_url = image_response.data[0].url

    # Save full history
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        '''INSERT INTO history (user_email, user_image_url, ai_response, ai_generated_image_url)
           VALUES (?, ?, ?, ?)''',
        (user_email, user_image_url, ai_reply, ai_image_url)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "description": ai_reply,
        "image_url": ai_image_url,
        "dalle_prompt": dalle_prompt
    })

@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        '''SELECT user_image_url, ai_response, ai_generated_image_url
           FROM history
           WHERE user_email = ?
           ORDER BY timestamp DESC''',
        (session['user'],)
    )
    rows = c.fetchall()
    conn.close()

    history = [{
        "user_image": row[0],
        "ai_response": row[1],
        "ai_image": row[2]
    } for row in rows]

    return render_template("history.html", history=history)






@app.route('/generate-image', methods=['POST'])
def generate_image():
    prompt = request.json.get("prompt")

    if not prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        n=1
    )

    return jsonify({"image_url": response.data[0].url})
@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return jsonify({"message": "Image uploaded successfully", "filename": filename})


def analyze_image(filepath):
    return "The image has been analyzed. Suggestions: Add more calming colors."

@app.route('/register', methods=["GET", "POST"])
def register():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        user = auth.create_user_with_email_and_password(email, password)
        return jsonify({"message": "Registration successful!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)