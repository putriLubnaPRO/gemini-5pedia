import os
from flask import Flask, render_template, request, jsonify
from ultimate_5pedia_ai import init_warehouses, proses_gabungan_multipedia, simpan_gudang_chat, ambil_riwayat_chat

app = Flask(__name__)

# Inisialisasi database warehouse
init_warehouses()

@app.route("/")
def index():
    riwayat = ambil_riwayat_chat(limit=20)
    return render_template("index.html", riwayat=riwayat)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "Pesan kosong tidak dapat diproses."})
    
    # Simpan chat user
    simpan_gudang_chat("User", user_input)
    
    # Proses menggunakan mesin AI & pedia
    respon = proses_gabungan_multipedia(user_input)
    
    # Simpan chat AI
    simpan_gudang_chat("AI", respon)
    
    return jsonify({"response": respon})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
