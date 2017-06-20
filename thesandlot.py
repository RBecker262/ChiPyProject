# Starts the web server for the MLB GameDay Retrieval
from webapp import webapp

webapp.run(host='127.0.0.1', port=5000, debug=True)
