# NITI and India government data source ledger
Checked 2026-10-08. Research supports adapter preparation, not dataset activation.

| Source | Publisher/type | Evidence and scope | Status |
| --- | --- | --- | --- |
| https://www.pib.gov.in/PressReleasePage.aspx?PRID=1825145 | PIB, primary announcement, 2022-05-13 | NDAP was launched for open public use. Datasets may be downloaded and merged freely; common schema. | Fetched; historical statement, not present API quota guarantee. |
| https://www.niti.gov.in/divisions/division/data-management-and-analysis | NITI, official program description | NDAP hosts government datasets and supports analytics/integration. | Fetched, no API contract. |
| https://ndap.niti.gov.in/ | NITI, current portal | Portal exists, fetch only exposes loading shell. | No current dataset download URL or public API verified. |
| https://niti.gov.in/whats-new/walkthrough-ndap-portal | NITI, current walkthrough page | Official walkthrough PDF link. | Fetched; PDF is image-only in local text extraction, not interpreted as API docs. |
| https://www.data.gov.in/apis/2ed5b97a-d5bc-404b-a8f3-2a08f20c0b8f | OGD, official API detail page | Generate API Key control. | Fetched; no full API response/quota contract in accessible text. ID is a research lead, not configured live dataset. |
| https://punjab.data.gov.in/Godl | OGD Punjab, official legal terms | Royalty-free use of covered data; mandatory provider/source/license attribution, no endorsement, no warranty/update guarantee, exemptions including personal/sensitive information. | Fetched; dataset-specific applicability still requires review. |
| https://data.gov.in/sites/default/files/NDSAP_OpenDataLicense.pdf | OGD, legal primary document | License document found in search and fetched. | Official terms independently read at Punjab OGD mirror above. |
| https://econabhishek.github.io/datagovindia/ | Open-source wrapper authors, technical implementation docs | OGD resource path, api-key, offset and limit conventions; account/key requirement. | Fetched; no wrapper dependency copied or installed, no example keys used. |
| https://puredevkit.com/api-guides/data-gov-in/ | Independent technical guide | Describes free key registration and dataset-specific quotas. | Fetched; site also labels service freemium. Official quota/free-tier endpoint not verified. Do not promise unlimited access or paid fallback. |

## Cost boundaries
New backend uses only Python standard library; no paid provider, packages or
billing rail. NDAP download/merge free statement is official but historical.
OGD key generation is visible officially; free registration/API conventions are
corroborated by independent technical documentation. Current numerical quotas,
paid-tier boundary and continued availability remain unverified. Any 401/403,
429, redirect/challenge or quota failure stops the call without retries, upgrade,
scraping workaround or payment. A 100-row page cap, 100-page cap, 10,000-row cap
and byte limits are OUR safety limits, not government-published quotas.

## Rights boundary
Push owns new code. Imported government data has its own terms. Do not remove
required provider/source/data-license attribution to satisfy code copyright
preferences. No real data is included. Set reuse_reviewed only after the actual
dataset's rights, attribution, non-sensitive status and intended use are checked.
