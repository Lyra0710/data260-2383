source .venv/bin/activate

python -m uvicorn main:app --reload --port 8583

python -c "import secrets; print(secrets.token_urlsafe(32))"

imported SECRET_KEY from secret.py instead of using a visible fallback code. 