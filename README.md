# Invoice → PDF (met briefpapier) — Streamlit

Een simpele webapp om `factuur.xlsx` in te lezen en een nette PDF te genereren. Optioneel wordt elke pagina samengevoegd met je **standaard briefpapier (PDF)**.

## Hoe werkt het?
1. Upload de Excel (volgens de meegeleverde `invoice_template.xlsx`).
2. Upload optioneel je briefpapier (`briefpapier.pdf`).
3. Download de gegenereerde factuur-PDF.

## Excel-structuur
- Sheet **`meta`** met kolommen: `key`, `value`  
  Voorbeelden van keys: `supplier_name`, `supplier_address`, `supplier_kvk`, `supplier_vat`, `invoice_number`, `invoice_date`, `due_date`, `client_name`, `client_address`, `payment_note`.

- Sheet **`items`** met kolommen: `description`, `qty`, `unit_price`, `vat_pct`

> Tip: Meerdere adresregels kun je in Excel scheiden met `\\n`.

## Lokaal draaien
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy op GitHub + Render.com
1. **GitHub repo**
   - Maak een nieuwe repo en upload: `app.py`, `requirements.txt`, `README.md`, `invoice_template.xlsx` en eventueel `sample_letterhead.pdf`.
2. **Render Web Service**
   - Ga naar Render → New → Web Service → kies je GitHub repo.
   - **Runtime**: Python
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Instance type**: free of starter naar wens.
3. Wacht tot de service “Live” is en open de URL.

### render.yaml (optioneel)
```yaml
services:
  - type: web
    name: invoice-to-pdf
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
    plan: free
```
