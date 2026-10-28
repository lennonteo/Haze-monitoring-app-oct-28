# Haze Watch

A single-page app showing Singapore's 24-hour PSI by area, plus weather for Singapore and nine ASEAN cities.

- **Haze (PSI, PM2.5, PM10):** National Environment Agency (NEA) via [data.gov.sg](https://data.gov.sg). Singapore only.
- **Weather (all ten cities):** [Open-Meteo](https://open-meteo.com).
- **Map outline:** URA Master Plan 2019 planning area boundaries on data.gov.sg. The five PSI areas are split with straight lines, so boundaries are approximate.

The page is one static file, `index.html`, with the data embedded in it. It does not call any API in the browser, so the numbers are a snapshot taken when the file was generated (the capture time is shown in the page header).

## Deploy on Vercel

1. Import this repository in Vercel.
2. Framework preset: **Other**. Leave the build command and output directory empty.
3. Deploy. Vercel serves `index.html` from the repository root and applies `vercel.json`.

## Refresh the data

```bash
python3 scripts/refresh.py
git add index.html
git commit -m "Refresh data"
git push
```

Pushing to the connected branch triggers a new Vercel deployment. The script needs Python 3 and no extra packages. If you have a data.gov.sg API key, set `DATA_GOV_SG_API_KEY` before running it.

To keep the page current without running this by hand, schedule the script (for example with a GitHub Actions cron job that commits `index.html`) or change the page to fetch both APIs in the browser.

## Files

| Path | Purpose |
| --- | --- |
| `index.html` | The deployed page (generated) |
| `vercel.json` | Clean URLs and basic security headers |
| `.vercelignore` | Keeps `src/`, `scripts/` and this README out of the deployment |
| `scripts/refresh.py` | Fetches fresh data and rewrites `index.html` |
| `src/template.html` | Page source with a `__DATA__` placeholder |
| `src/geo.json` | Simplified Singapore outline and map layout |

## Data notes

PSI and planning area data are published under the Singapore Open Data Licence. Open-Meteo data is licensed CC BY 4.0, and its free API is for non-commercial use. The health-advice wording for each PSI band is a plain summary, not official NEA text.
