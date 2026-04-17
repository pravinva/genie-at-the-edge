# FE Launchpad Account Simulator (Apps Script)

## URLs (after Web app deploy)

Use **Deploy → Manage deployments** in the [script editor](https://script.google.com/home) and ensure a deployment type **Web app** exists with the right access (e.g. “Anyone at Databricks”).

Then open:

- Simulator: `.../exec?mode=l3bootcamp`
- Facilitator: `.../exec?mode=facilitator`

## Update from repo

```bash
cd agentic_hmi/apps-script-fe-bootcamp
# refresh HTML from main app if needed:
cp ../l3_sa_bootcamp.html ./l3Bootcamp.html
cp ../l3_sa_bootcamp_facilitator_guide.html ./facilitatorGuide.html
clasp push
clasp deploy -d "describe change" -i AKfycbxlTk5WKKsv_G1k07Wb140AyhrqyBZjHx-XzDHn3AeeNd2iYa2ARi1E3G0QDOEXpv3A
```

Replace `-i` with your **Web app** deployment ID from **Manage deployments** (the `/exec` URL segment).

## Script ID

See `.clasp.json` → `scriptId`.
