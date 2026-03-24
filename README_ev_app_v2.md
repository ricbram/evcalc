# EV cost calculator web app

This package contains a polished Streamlit version of your spreadsheet-based EV cost calculator.

## Files
- `streamlit_ev_app_v2.py` - main Streamlit app
- `ev_calc_core_v2.py` - calculation logic translated from the spreadsheet
- `requirements_ev_app_v2.txt` - Python dependencies

## Run locally
```bash
pip install -r requirements_ev_app_v2.txt
streamlit run streamlit_ev_app_v2.py
```

## Deploy online
The easiest route is Streamlit Community Cloud:
1. Put these files in a GitHub repo.
2. Create a new Streamlit app.
3. Point it at `streamlit_ev_app_v2.py`.
4. Deploy.

## Notes
- Default values match the spreadsheet defaults.
- The model includes both discounted and undiscounted payback.
- Discounting follows the spreadsheet structure: upfront purchase at the start of the year, annual operating flows in the middle of the year, and sale value at the end of life.
