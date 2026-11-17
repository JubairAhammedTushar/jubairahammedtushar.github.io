# Portfolio review — 13 October 2026

## Source assessed

Repository: `JubairAhammedTushar/jubairahammedtushar.github.io`, original `main` branch with a single `index.html` page and a `README.md`. The repository is public. This review used authenticated GitHub repository contents and a recovered, private historical project archive. Public-domain HTTP reachability and a Lighthouse measurement were **not** confirmed by the review tools.

## Observations on the original site

1. **Strength:** Original black/blue-violet theme and mobile media queries were a solid starting point; the name, location and GitHub were visible.
2. **Risk:** The headline and 13-project cards could be interpreted as thirteen completed hands-on projects, though source evidence supports a mix of reported work, release-candidate code and learning/roadmap items.
3. **High-priority accuracy problem:** Previous cards described a successful `vsftpd` exploit returning a root shell, detailed Nessus/Nmap findings, wireless handshake captures, EVE-NG activity and cloud IAM exercises. The available recovered work did not substantiate those specific outcomes. The redesign does **not** repeat these statements as completed results.
4. **Presentation:** Most technical content was hidden inside `<details>` cards, with no obvious featured case study or filter by evidence status.
5. **Recruiter experience:** The introduction was text-heavy and did not foreground the best-documented technical engineering work.
6. **Accessibility/SEO:** The original had a viewport and semantic heading layout, but no skip-to-content link, no filter live region or evidence-status taxonomy. Metadata and responsive layout could be stronger.
7. **Source links:** There was no public technical-code link for every project. Do not invent one; release only sanitized, reviewed files.

## Proposed changes on this branch

- New, responsive technical editorial design with a dark palette and a diagram-like JACG-2300 feature panel using CSS (no photographic assets required).
- Clear value proposition aimed at entry-level UK cybersecurity and technical apprenticeship recruiters.
- Thirteen entries rewritten with **four hands-on/reported projects, one RC1, eight practice/roadmap entries**, plus visible qualifiers.
- Interactive filter to separate those types without relying on a back-end.
- Keyboard skip link, focus states, reduced motion handling, privacy notes and mobile layout updates.
- Improved title, canonical URL, Open Graph and Twitter preview metadata.
- Automated basic site checks.
- Clearer README and statement of what remains unverified.

## Follow-up before merging or advertising on LinkedIn

- Read the new copy for accuracy and preferred public wording.
- Verify the website actually renders on mobile devices, and check on Safari/Chrome.
- Verify LinkedIn URL resolves to the correct account.
- Run actual browser audits: accessibility tooling (axe/Lighthouse), Core Web Vitals, contrast and mobile screenshots. These are not claimed as run here.
- Publish a small sanitized source-backed GitHub case study for JACG-2300 only after security review; never post private configs, backups or application trackers.
- Add actual screenshot evidence and clearly scoped exercise reports when available.
- In LinkedIn, call it a **Cybersecurity project portfolio**, not '13 completed hands-on projects'.

## Security

The PR contains only public portfolio copy, styling, the client-side filter and tests. It does not publish gateway scripts, private credentials, real network addresses or confidential apprenticeship CRM records. The deployment of JACG-2300 remains unverified and separate from this website.

## Update — 17 November 2026

- Added **JAT Cipherline 2300** (project 01) and the **Home SOC** (project 02) as running lab projects, labelled “self-reported”: the evidence is the owner’s own console screenshots and logs, and there is no independent audit or penetration test.
- Both entries state that they were built with AI-assisted engineering (the owner sets requirements, security rules and acceptance tests, and deploys, tests and operates each release; much of the code was written with an AI coding assistant).
- JACG-2300 RC1 is marked as superseded: its ideas carried into Cipherline, and the RC1 installers were never deployed.
- Hero panel, About, Focus tags and metadata now reflect the running lab; the About section names the DIPTI diploma (final examinations in autumn 2026) and the AI Agent Builder Bootcamp (September 2025).
- The training card now gives the module results in the first person (CCNA 96 and Linux 93, both A+; Ethical Hacking final 25/25) and still does not claim a Cisco certification.
- No addresses, hostnames of private services, endpoints, keys or user data are published; the site tests now also reject home-network and Tailscale addresses and private service hostnames.
- Router detection fixes and the Mail Log receiver are described as built and tested and being rolled out; update the wording once they are live.
- Added an **Experience** section (04): Trainee Manager at Popeyes, Cardiff (Team Member from April 2026, now in management training), then the Dhaka roles from 2021 to February 2026. The restaurant branch and colleagues’ names are deliberately left out.

## Update — 17 November 2026 (later)

- Headline now states the fact: “I run a home SOC from 8,000 km away”, with the five-VM lab in the intro.
- Cut to six entries: Cipherline, Home SOC, gateway history (Mark 2000 and JACG-2300 RC1 merged), GE230 WireGuard, Windows trojan recovery, diploma training (Kali, Nmap and Metasploitable practice folded in). Planned labs became one “Next” line; the filter was removed.
- Added an inline SVG map of the lab (no addresses, ports or private service names).
- Published `detections/`: Wazuh decoders and rules, the router Mail Log receiver and its 36 tests (run in GitHub Actions). Example addresses were changed to generic ones.
- Added a one-page CV (`cv/`), built only from facts the owner has stated; no phone number or address.
- Removed the list of VPN protocols from the page; a test keeps them out.
- Still to add: redacted screenshots (Wazuh rule checks, a Splunk dashboard, the console) once the owner supplies them.
- Correction from the owner: JACG-2300 was a **concept**, never built or run. The history card, About, README and CV now say so; the earlier description of it as a source-backed release candidate (from the October review) was wrong.
