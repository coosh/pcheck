from flask import Flask, request, render_template

from app.contracts import contracts

app = Flask(__name__)
app.register_blueprint(contracts)