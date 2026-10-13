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
