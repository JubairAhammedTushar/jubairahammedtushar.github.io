# Home SOC detections — JAT Cipherline 2300

Code from the SOC in my home lab (see project 02 on [jubairahammedtushar.com](https://jubairahammedtushar.com/#home-soc)): the Wazuh decoders and rules I run, and the small receiver that brings my TP-Link router's log into Wazuh.

Built with AI-assisted engineering: I set the requirements, security rules and acceptance tests, and I deploy, test and run it on my own hardware; much of the code was written with an AI coding assistant. Addresses in the examples are generic; nothing here is a secret.

## `wazuh/` — decoders and rules (IDs 100200–100299)

| What | Examples |
| --- | --- |
| Firewall (ufw) on every machine | blocked connections from the journal and from `kern.log` |
| The lab's own web console | sign-ins, failed sign-ins, security changes (MFA, passkeys, recovery codes) |
| VPN | sessions starting and ending, gateway alerts |
| Services | Pi-hole summaries, refused web requests at Traefik, Vaultwarden wrong passwords |
| Suricata | alert severity mapped to Wazuh levels |
| Home router | failed sign-ins, attacks it reports, internet drops, sign-ins |

After every install, a sample line of each kind is replayed through `wazuh-logtest`. That check expects 15 of 15 to land on the intended rule.

### The bug the self-test caught

The router's "Login failed" line kept landing on Wazuh's built-in rule **2501** ("syslog: User authentication failure", level 5) instead of my router rule. Wazuh's analysis daemon keeps top-level rules sorted by **level, highest first** (`_OS_AddRule` in `src/analysisd/rules_list.c`), and a line ends at the first top-level rule that matches, then that rule's children. My router rule was level 3, so 2501 (and 2502 at level 10) was always tried first.

The fix (`cipherline_rules.xml`, rule **100259**): a level-11 top-level rule with `noalert="1"` that only matches lines from my router's decoder, so it sorts above the generic syslog rules. Every specific router rule hangs off it as a child, with a catch-all child (100260) last. Children are also tried highest level first, so the order is: attack (8), failed sign-in (7), internet drop (5), sign-in (3), anything else (3).

## `router-mail/` — the router's Mail Log, into Wazuh

My TP-Link router has no remote syslog, only "Mail Log": it emails its whole log, with no setting for the port or encryption. The SOC's firewall log showed it tries **port 465**, the port for SMTP over TLS. `router-mail.py` is a small SMTP receiver (Python standard library, asyncio) that:

- talks only to the router's address, and refuses anyone else **before** any TLS starts;
- speaks implicit TLS on 465 (TLS 1.2 or newer; self-signed certificate) and plain SMTP on 25;
- accepts whatever sign-in the router offers, but keeps none of it, and never sends or relays mail;
- splits the mail (text, HTML or a text attachment) into lines and skips lines it has already written, because the router resends its whole log each time;
- writes new lines oldest first, in the same syslog format as the rest of the router's log, so the same Wazuh decoder reads them.

It runs as a systemd service with only the right to bind low ports (`CapabilityBoundingSet=CAP_NET_BIND_SERVICE`), a read-only system (`ProtectSystem=strict`) and a 128 MB memory ceiling; the SOC's firewall opens 465 and 25 to the router only.

### Tests

```sh
cd router-mail && python3 test-router-mail.py
```

There are 36 checks against the real receiver on 127.0.0.1, sending with `smtplib`. They cover:

- plain and TLS mail, with all the ways the router can sign in;
- skipping lines it has already written, newest-first logs, HTML and attachments;
- size limits, refused addresses and TLS older than 1.2;
- what happens when the log cannot be written, and a restart.

The site's GitHub Actions run them on every change.
