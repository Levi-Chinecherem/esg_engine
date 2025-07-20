run the system with the following command once installations are complete: 

```bash
python esg_system/main.py --report btg-pactual.pdf --standards ifrs_s1.pdf --requirements UNCTAD_requirements.csv --output output --company "BTG Pactual"
```

You need to specify `--company "BTG Pactual"` to provide the company name for the PDF report's title, headers, and content, as the system dynamically uses this for personalized branding and context, and it cannot reliably extract the exact company name from `btg-pactual.pdf` alone.

This assumes `btg-pactual.pdf` is in `C:\Developments\Solutions\ESG Engine\o2\input`, `ifrs_s1.pdf` is in `standards`, `UNCTAD_requirements.csv` is in `requirements`, and outputs will be saved to `output`.