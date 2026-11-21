# JAT Cipherline 2300 — private backup evidence review

**Review date:** 21 November 2026 (UTC)  
**Reviewed artifact:** An owner-supplied private, compressed Cipherline gateway backup  
**Public release status:** This note only; the original archive, its contents and any private installation files are **not** part of this repository.

## Evidence and review scope

The owner supplied a compressed gateway-backup archive from the Cipherline installation. This is a **static inspection of the backup file**, not independent access to the live gateway, a successful restoration, or a penetration test.

The following checks were completed:

- The archive could be opened and enumerated without extracting its contents to a running server.
- It contained **1,043 entries**, including **991 regular files**.
- Archive entry names were relative and did not contain path-traversal components; no symbolic links were found.
- A console SQLite database and its accompanying write-ahead-log files were inspected in a temporary isolated directory.
- The SQLite `PRAGMA quick_check` and `PRAGMA integrity_check` each returned `ok`.

These results show that the supplied archive was structurally readable and that the examined database passed two consistency checks. They **do not** prove that all backed-up services could be restored or that the running installation is currently healthy.

## High-level scope of material found

The archive contains evidence of Cipherline gateway configuration and VPN profile state, firewall configuration, and web-console application/database state.

Sensitive configuration files, client profiles and cryptographic key material are present in the **private source archive**. They are neither reproduced nor linked from this public note.

## Backup coverage limitations

This archive is **not a complete backup of the Proxmox home lab**:

- Nextcloud user files were **not found**.
- Proxmox virtual-machine disk images were **not found**.
- This review found no independently verifiable full backups of Vaultwarden data, Wazuh, Splunk or the other virtual machines in this archive.
- Separate backups might exist, but they were **not supplied or checked** during this review.
- No isolated restoration into a clean system was attempted, so recoverability is **not established**.

The console SQLite integrity checks cover the database, not necessarily every linked file, VPN configuration, credential, application dependency or service state.

## Privacy and security boundary

The supplied archive is a compressed file, **not an encrypted backup**, and includes sensitive key material. Do not publish it in source control, attach it to a public issue, or include it in portfolio screenshots. Keep private backups access-controlled and encrypted in storage and transfer. If the archive is ever exposed, assess affected credentials and keys for rotation.

This public note intentionally omits actual server addresses, client identities, domain-specific internal service names, network ports, secrets and the private archive filename.

## Recommended next verification steps

1. Identify and separately protect **Nextcloud data and its database**, **Vaultwarden state**, **SOC configuration/data** and **Proxmox VM backups**.
2. Confirm that current backup jobs succeed and that backup files are encrypted and stored somewhere accessible after host failure.
3. Perform a **non-production, isolated restore** of the gateway backup, including application and network validation, without risking the live family VPN.
4. Perform equivalent recovery tests for important services, then document a safe restore procedure and the date of the last successful test.

## Responsible portfolio claim

> “A private Cipherline gateway backup has been reviewed. Its archive contents were readable and the console SQLite database passed integrity checks. It is a **partial, untested-for-restoration gateway backup**, not evidence of full disaster recovery.”

No client profiles, keys, certificate material or original backup archives are published with this evidence note.
