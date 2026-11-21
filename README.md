# Jubair Ahammed Tushar — Cybersecurity portfolio

**Website:** https://jatushar.co.uk/ and https://jubairahammedtushar.com/ (both reach the same site; the old address, jubairahammedtushar.github.io, redirects there too)

A static GitHub Pages cybersecurity portfolio covering network security, security operations, identity and access, authorised ethical hacking and incident response, built around a self-hosted lab I run remotely.

## Portfolio policy

I distinguish what I have actually built and run from concepts, reconstructed practice history and planned labs. A card appearing on the website is **not** a claim that the entire project is deployed, tested or professionally assessed.

| Status | What the label means |
| --- | --- |
| Running · self-reported | Deployed and in use; evidence is my own screenshots and logs, with no independent audit. |
| Reported build / hands-on | Personal experience reported in previous work. Historical logs are not always preserved. |
| History | Earlier systems and concepts that led to the current projects; a concept was never built. |
| Practice · authorised | Offensive-security practice on systems I own or guided platforms; no reports or exploit output are claimed. |
| Training & results | Diploma module results; no claim that every exercise is preserved or independently verified. |

As of 21 November 2026, the site has eight entries, each labelled with its security domain: three running parts of the lab (Cipherline, the home SOC, and identity and access hardening), the offensive security lab, router WireGuard remote access, a personal malware recovery case, the history of the gateway, and diploma training. Planned labs are one "Next" line rather than entries.

## Projects to explore

- **JAT Cipherline 2300:** A Proxmox home lab in Bangladesh, run remotely from Cardiff: multi-protocol VPN, Nextcloud, Vaultwarden, Pi-hole, a Kali VM and one master console. Built with AI-assisted engineering.
- **Home SOC:** Wazuh with custom decoders, rules and a self-test; Splunk dashboards; Suricata IDS.
- **Identity & access hardening:** TOTP and passkey sign-in, phone-confirmed lab controls, Tailscale-only administration and SSH keys limited to fixed jobs.
- **Offensive security lab:** Kali Linux with a passed-through Wi-Fi card, Nmap, Wireshark, Metasploitable 2 and TryHackMe, on systems I own.
- **JACG-2300:** a design concept for a safer gateway; never built. Its ideas were built in JAT Cipherline 2300.

- **Mark 2000:** Earlier self-hosted Ubuntu proxy and VPN remote-access system.
- **TP-Link GE230 WireGuard:** Router VPN troubleshooting and cross-network remote connectivity.
- **Windows Trojan recovery:** Personal 2022 incident-response experience.
- **Diploma training:** CCNA, Linux and ethical hacking module results.

An **Experience** section lists work history: Trainee Manager at Popeyes (Cardiff, 2026), and earlier business development, marketing, IT and sales roles in Dhaka (2018–2026). An **Education & training** section lists the DIPTI diploma (in progress), TryHackMe intro rooms, DIPTI's AI Agent Builder Bootcamp and school certificates.

Also here: `detections/` (the Wazuh decoders and rules and the router Mail Log receiver, with tests that run in GitHub Actions), `cv/` (a two-page CV), and a lab map drawn inline in the page. The VPN's protocols are deliberately not listed.

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

**Moved 15 November 2026:** When the site moved to jubairahammedtushar.com, `analytics.js` switched to a new site token registered for that hostname. Cloudflare only accepts beacons from the hostname a token was registered for, so the old jubairahammedtushar.github.io site in the dashboard keeps its history but no longer receives visits.

### Activate tracking

1. Sign in at https://dash.cloudflare.com and open **Web Analytics** (not Workers & Pages).
2. Choose **Add a site**, enter **`jubairahammedtushar.com`** as the hostname and choose **Enable with JS Snippet installation** (the automatic option only works when traffic is proxied through Cloudflare; this site is served directly by GitHub Pages).
3. Under **Manage site**, copy the JavaScript snippet. Find the `token` value inside `data-cf-beacon` (typically 32 hexadecimal characters).
4. Edit `analytics.js` and replace the empty `CLOUDFLARE_SITE_TOKEN` value with that public **site token only**; do not paste your account API token, email, password, login cookies or Cloudflare API keys.
5. Commit and wait for GitHub Pages to deploy. Open the website in a browser without an ad blocker, then review visitor and pageview trends under **Cloudflare → Web Analytics** after a few minutes. Data prior to activation cannot be reconstructed.

This domain stays on GitHub Pages. You do **not** need to move DNS, proxy through Cloudflare, or buy a plan. The visitor statistics are visible in your Cloudflare dashboard, not publicly on the website. If the expected metrics do not appear, verify that you registered the exact hostname, disabled aggressive tracking blockers for testing, and entered the correct site token.

Reference: https://developers.cloudflare.com/web-analytics/get-started/

## Contact

- GitHub: https://github.com/JubairAhammedTushar
- LinkedIn: https://www.linkedin.com/in/jubair-ahammed-tushar
- Email: hello@jatushar.co.uk · hello@jubairahammedtushar.com · jubairahmedtushar@gmail.com (personal)

This is an educational and personal portfolio, not a production-system status dashboard.
