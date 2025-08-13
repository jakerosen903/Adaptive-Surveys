from app import create_app

app = create_app()

if __name__ == '__main__':
    # Use debug=False and host='0.0.0.0' for external access via ngrok
    # Using port 5001
    app.run(debug=False, host='0.0.0.0', port=5001)