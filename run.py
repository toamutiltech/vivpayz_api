from vivpayz import create_app

app = create_app()

if __name__ == "__main__":
    # Only for local dev — Render will ignore this block
    app.run(host="0.0.0.0", port=5000, debug=True)
