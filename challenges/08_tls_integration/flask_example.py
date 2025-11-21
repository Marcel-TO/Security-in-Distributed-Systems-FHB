from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify(
        {"message": "Hello! This is a secure Flask app running with TLS.", "status": "success"}
    )


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "secure": True})


@app.route("/api/info")
def info():
    return jsonify({"app": "Flask TLS Demo", "version": "1.0", "protocol": "HTTPS"})


if __name__ == "__main__":
    # Run with TLS/SSL
    app.run(
        host="0.0.0.0",
        port=1111,
        ssl_context=(
            "../07_pki_certificates/certificate.crt",
            "../07_pki_certificates/private_key.key",
        ),
        # debug=False,  # Set to False in production
    )
