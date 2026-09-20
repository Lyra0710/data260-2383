source .venv/bin/activate

python -m uvicorn main:app --reload --port 8583

python -c "import secrets; print(secrets.token_urlsafe(32))"

imported SECRET_KEY from secret.py instead of using a visible fallback code. 

python code/rag/retrieval_experiment.py

curl -L "https://www.cupertino.gov/Parks-Recreation/Activities/Softball-League" \
  -o reports/hw03/corpus/cupertino_softball_league.html

curl -L "https://www.cupertino.gov/files/assets/city/v/3/parks-and-recreation/documents/sports-center/sports-center-policies.pdf" \
  -o reports/hw03/corpus/cupertino_sports_center_policies.pdf

curl -L "https://www.cupertino.gov/files/assets/city/v/1/parks-and-recreation/documents/parks-and-facilities/athletic-fields/athletic-field-use-policy.pdf" \
  -o reports/hw03/corpus/cupertino_athletic_field_policy.pdf

curl -L "https://www.cupertino.gov/Parks-Recreation/Parks-and-Facilities/Athletic-Fields-and-Courts" \
  -o reports/hw03/corpus/cupertino_athletic_fields.html

curl -L "https://www.cupertino.gov/Parks-Recreation/Sports-Center" \
  -o reports/hw03/corpus/cupertino_sports_center.html

curl -L "https://www.lifetimeactivities.com/wp-content/uploads/CP-FALL-2026-Adult-Tennis.pdf" \
  -o reports/hw03/corpus/cupertino_fall_2026_adult_tennis.pdf

python code/rag/create_manifest.py