from flask import Flask

app = Flask(__name__)
app.secret_key = 'arac_bakim_secret_key_2024'

if __name__ == '__main__':
    app.run(debug=True)