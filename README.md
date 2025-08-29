# PDF op briefpapier — super simpel

Deze app doet één ding: **merge je factuur-PDF met je briefpapier-PDF** (factuur erbóvenop).

## Lokaal draaien
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

## Deploy op Render
**Build command**
```bash
python -m pip install --upgrade pip setuptools wheel && python -m pip install --only-binary=:all: pypdf && python -m pip install -r requirements.txt
```

**Start command**
```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

*(Geen extra libraries nodig.)*
