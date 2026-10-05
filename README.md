# CalloutSlip

Signature: Mourad.Soltani

After-hours call-out quote slip for emergency trades (locksmith, plumber, electrician, glazier, HVAC, appliance). A solo operator enters the job window, travel, labor, parts markup, tax, deposit, and a minimum charge. CalloutSlip returns a client-ready slip with the night or holiday premium applied.

No accounts. No database. Rates stay on the machine running the app.

## Run

```bash
python3 app.py
```

Open http://127.0.0.1:8080

## Test

```bash
python3 -m unittest tests.test_health
```

## Pricing rules

- Windows: standard 1.00, evening 1.35, night 1.60, weekend 1.75, holiday 2.00
- Travel = miles × mileage rate
- Labor = hours × labor rate
- Parts = cost × (1 + markup)
- Window multiplier applies to call-out + travel + labor + parts
- If that result is below the minimum charge, the minimum replaces it
- Tax applies after the minimum check
- Deposit is a fraction of the tax-inclusive total (0.40 means 40%)

Tax and markup must be decimals, not percents.
