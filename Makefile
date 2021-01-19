wfreeze:
	pip freeze | grep -v "pkg-resources" > requirements.txt

dev:
	FLASK_ENV=development python3 wsgi.py
