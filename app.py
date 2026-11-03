import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from authlib.integrations.flask_client import OAuth
from ultimate_5pedia_ai import init_warehouses, proses_gabungan_multipedia, simpan_gudang_chat, ambil_riwayat_chat

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "gemini-secret-key-12345")

init_warehouses()

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_scope='openid email profile'
)

@app.route("/")
def index():
    if 'user' not in session:
        return render_template("login.html")
    
    user = session['user']
    riwayat = ambil_riwayat_chat(user['email'], limit=20)
    return render_template("index.html", user=user, riwayat=riwayat)

@app.route("/login")
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/authorize")
def authorize():
    token = google.authorize_access_token()
    resp = google.get('https://www.googleapis.com/oauth2/v2/userinfo')
    user_info = resp.json()
    session['user'] = {
        'name': user_info.get('name'),
        'email': user_info.get('email'),
        'picture': user_info.get('picture')
    }
    return redirect(url_for('index'))

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route("/chat", methods=["POST"])
def chat():
    if 'user' not in session:
        return jsonify({"response": "Sesi habis, silakan login ulang."}), 401
    
    user_email = session['user']['email']
    data = request.get_json()
    user_input = data.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "Pesan kosong."})
    
    simpan_gudang_chat(user_email, "User", user_input)
    respon = proses_gabungan_multipedia(user_input)
    simpan_gudang_chat(user_email, "AI", respon)
    
    return jsonify({"response": respon})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
     
