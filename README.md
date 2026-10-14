# Jubair Ahammed Tushar — Cybersecurity portfolio

**Website:** https://jubairahammedtushar.github.io/

A static GitHub Pages portfolio focused on cybersecurity learning, secure Linux infrastructure, networking, personal incident recovery and documented engineering work.

## Portfolio policy

I distinguish what I have actually worked on from release candidates, reconstructed practice history and planned labs. A card appearing on the website is **not** a claim that the entire project is deployed, tested or professionally assessed.

| Status | What the label means |
| --- | --- |
| Reported build / hands-on | Personal experience reported in previous work. Historical logs are not always preserved. |
| Source-backed RC1 | Recoverable code, documentation and local automated test evidence exist. Production acceptance is not established. |
| Practice / learning / planned | Training topics or lab workflows; no claim that every exercise is completed or independently verified. |

At the time of this review, the site includes 13 entries: four historical/source-supported personal work entries, one release-candidate project and eight practice/roadmap entries.

## Projects to explore

- **JACG-2300:** Python release candidate for a security-reviewed gateway, with automated tests and restricted deployment status.
- **Mark 2000:** Earlier self-hosted Ubuntu/Xray remote-access system.
- **TP-Link GE230 WireGuard:** Router VPN troubleshooting and cross-network remote connectivity.
- **Windows Trojan recovery:** Personal 2022 incident-response experience.
- **Kali, Nmap, networking, wireless, cloud, CCTV:** Practice, methodology or roadmap, each labelled according to its evidence.

Original gateway scripts and a private handover archive are **not automatically safe to post publicly**. Review them for keys, endpoints and personal data before any repository publication.

## Site structure

- `index.html`: Complete mobile-responsive portfolio page with semantic sections, CSS graphic, accessible navigation and a small client-side status filter.
- `tests/test_site.py`: Dependency-free structural and content checks.
- `.github/workflows/site-check.yml`: Runs the checks on pushes and pull requests.
- `PORTFOLIO_REVIEW.md`: Change log and remaining actions.

No production VPN infrastructure, private client profiles, device credentials or CCTV feeds are hosted in this website repository.

## Run locally

Open `index.html` in a browser, or run a local server:

```sh
python3 -m http.server 8000
```

Then open http://localhost:8000. Run the checks with:

```sh
python3 -m unittest discover -s tests -v
```

## Visitor analytics (Cloudflare Web Analytics)

This website supports **free, privacy-first Cloudflare Web Analytics**. It can show visits/page views, referrers and countries through your private Cloudflare dashboard. It does not provide a list of named visitors, and numbers are estimates rather than an exact count of distinct people.

**Activation is not automatic:** the Cloudflare site token must be created in the site owner's Cloudflare dashboard. Until it is supplied, `analytics.js` makes no tracking requests and the site remains functional.


**Activated 14 October 2026:** The public Cloudflare Web Analytics site token is now configured in `analytics.js`. This is a website identifier, not a secret or account API token. Check the Cloudflare Web Analytics dashboard for data beginning after activation; previously untracked visits cannot be counted.

### Activate tracking

1. Sign in at https://dash.cloudflare.com and open **Web Analytics** (not Workers & Pages).
2. Choose **Add a site**, enter **`jubairahammedtushar.github.io`** as the hostname and confirm.
3. Under **Manage site**, copy the JavaScript snippet. Find the `token` value inside `data-cf-beacon` (typically 32 hexadecimal characters).
4. Edit `analytics.js` and replace the empty `CLOUDFLARE_SITE_TOKEN` value with that public **site token only**; do not paste your account API token, email, password, login cookies or Cloudflare API keys.
5. Commit and wait for GitHub Pages to deploy. Open the website in a browser without an ad blocker, then review visitor and pageview trends under **Cloudflare → Web Analytics** after a few minutes. Data prior to activation cannot be reconstructed.

This domain stays on GitHub Pages. You do **not** need to move DNS, proxy through Cloudflare, or buy a plan. The visitor statistics are visible in your Cloudflare dashboard, not publicly on the website. If the expected metrics do not appear, verify that you registered the exact hostname, disabled aggressive tracking blockers for testing, and entered the correct site token.

Reference: https://developers.cloudflare.com/web-analytics/get-started/

## Contact

- GitHub: https://github.com/JubairAhammedTushar
- LinkedIn: https://www.linkedin.com/in/jubair-ahammed-tushar
- Email: jubairahmedtushar@gmail.com

This is an educational and personal portfolio, not a production-system status dashboard.
