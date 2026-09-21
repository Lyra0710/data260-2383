# HW3 Reproducible Run Instructions

## Environment

```bash
source .venv/bin/activate
```

## Start the application

```bash
python -m uvicorn main:app --reload --port 8583

python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Import `SECRET_KEY` from `secret.py` instead of using a visible fallback code.

## Initial retrieval run

```bash
python code/rag/retrieval_experiment.py
```

## Download the corpus files

```bash
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
```

## Create the corpus manifest

```bash
python code/rag/create_manifest.py
```

## Final retrieval run

```bash
python code/rag/retrieval_experiment.py
```

## Generate summary metrics

```bash
python code/rag/summarize_results.py
```

## Self-verify script 

```bash
python code/verify_hw03.py
```