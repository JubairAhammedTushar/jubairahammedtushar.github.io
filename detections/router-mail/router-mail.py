#!/usr/bin/env python3
"""cipherline-router-mail: the home router's log, received by email (TP-Link "Mail Log"), into the SOC.

Runs on the SOC as cipherline-router-mail.service. A small SMTP receiver on port 465 (SMTP over TLS, which TP-Link's
Mail Log uses) and on port 25 (plain), that talks only to the router's address (anything else is refused before any
encryption starts, and the firewall lets only the router in), accepts whatever sign-in the
router offers (the address is the check; nothing it sends is kept), and never sends or relays mail. Each message's
text (and any .txt/.log attachment) is split into lines. The router mails its whole log each time, so lines already
seen are skipped; new ones are added to /var/log/cipherline/router.log as
    "Mon DD HH:MM:SS router cipherline-router: <the router's line>"
exactly as the syslog route writes them, so Wazuh reads them the same way (decoder cipherline-router).
The router's Mail Log has no port or encryption setting; it tries port 465 with TLS. The certificate is the SOC's
own (self-signed, made by cipherline-node), and the mail never leaves the home network.
Settings: /etc/cipherline-router-mail.json {"router": "192.168.1.1", "port": 25, "listen": "0.0.0.0",
"tls_port": 465, "cert": ".../cert.pem", "key": ".../key.pem"}; without tls_port, plain port 25 only.
State: /var/lib/cipherline-router-mail/ (seen: fingerprints of lines already written; status.json, read by the
console). Standard library only.
"""
import asyncio
import email
import email.policy
import hashlib
import html
import ipaddress
import json
import os
import re
import socket
import ssl
import sys
import time

CONF = os.environ.get("RMAIL_CONF", "/etc/cipherline-router-mail.json")
LOG = os.environ.get("RMAIL_LOG", "/var/log/cipherline/router.log")
STATE = os.environ.get("RMAIL_STATE", "/var/lib/cipherline-router-mail")
SEEN = os.path.join(STATE, "seen")
STATUS = os.path.join(STATE, "status.json")
MAX_MAIL = 4 * 1024 * 1024        # bytes of one message; larger ones are refused (552) and nothing is written
MAX_LINE = 900                    # characters kept of one log line (Wazuh's syslog rules treat 1025+ as oversized)
MAX_LINES = 20000                 # lines taken from one message
SEEN_MAX = 50000                  # fingerprints remembered (the router's log holds far fewer lines)
MAX_SESSIONS = 4
MAX_RCPT = 50
MAX_ERRORS = 20                   # unknown or bad commands before the conversation is closed
IDLE = int(os.environ.get("RMAIL_IDLE", "60"))   # seconds to wait for each command or line of a message
TLS_WAIT = int(os.environ.get("RMAIL_TLS_WAIT", "30"))   # seconds for the TLS handshake
LIMIT = 1 << 20                   # longest line read at once
SESSION_MAX = 300                 # seconds for a whole conversation
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
SKIP = re.compile(r"^(?:[#=*_-]+|Time\s*=.*)$")           # separators, and the "Time = now" header that changes each mail
CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
TS_ISO = re.compile(r"(\d{4})[-/](\d\d)[-/](\d\d)[ T,]+(\d\d):(\d\d):(\d\d)")
TS_BSD = re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(\d\d):(\d\d):(\d\d)")
HOST = "cipherline-soc"


def now():
    return int(time.time())


def write_atomic(path, text, mode=0o640):
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def load_cfg():
    with open(CONF, encoding="utf-8") as f:
        c = json.load(f)
    router = str(c.get("router", ""))
    ip = ipaddress.ip_address(router)          # ValueError for anything that is not one address
    if ip.version != 4:
        raise ValueError("the router's address must be IPv4")
    port = int(c.get("port", 25))
    if not 0 < port < 65536:
        raise ValueError("port out of range")
    listen = str(c.get("listen", "0.0.0.0"))
    ipaddress.ip_address(listen)
    tls_port = int(c.get("tls_port") or 0)
    if tls_port and not (0 < tls_port < 65536 and tls_port != port):
        raise ValueError("tls_port out of range")
    cert, key = str(c.get("cert", "")), str(c.get("key", ""))
    if tls_port and not (os.path.isfile(cert) and os.path.isfile(key)):
        raise ValueError("tls_port needs the certificate and key files")
    return {"router": router, "port": port, "listen": listen, "tls_port": tls_port, "cert": cert, "key": key}


# ------------------------------------------------------------------ reading a message
def strip_html(text):
    text = re.sub(r"(?is)<(script|style)\b.*?</\1\s*>", "", text)
    text = re.sub(r"(?i)<br\s*/?>|</(?:p|div|tr|li|h\d|pre|table)\s*>", "\n", text)
    text = re.sub(r"(?s)<[^>]*>", "", text)
    return html.unescape(text)


def clean(line):
    line = " ".join(CTRL.sub(" ", line.replace("\t", " ")).split())
    if not line or SKIP.match(line):
        return ""
    return line[:MAX_LINE]


def stamp(line):
    """A sortable time at the start of a line, if it has one (to tell a newest-first log)."""
    head = line[:60]
    m = TS_ISO.search(head)
    if m:
        return tuple(int(x) for x in m.groups())
    m = TS_BSD.search(head)
    if m:
        return (0, MONTHS.index(m.group(1)) + 1) + tuple(int(x) for x in m.groups()[1:])
    return None


def looks_text(data):
    """An attachment without a text type or name that is plain text all the same (the router's log as 'syslog')."""
    sample = data[:4096]
    if not sample or b"\x00" in sample:
        return False
    return sum(32 <= c < 127 or c in (9, 10, 13) or c >= 128 for c in sample) / len(sample) >= 0.95 and b"\n" in data


def mail_lines(raw):
    """The log lines in one message, oldest first, and what was left out (names of parts that are not text)."""
    msg = email.message_from_bytes(raw, policy=email.policy.compat32)
    plain, htmls, other = [], [], []
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        name = part.get_filename() or ""
        texty = name.lower().endswith((".txt", ".log"))
        data = part.get_payload(decode=True)
        if not (ctype.startswith("text/") or texty or (data and looks_text(data))):
            other.append(name or ctype)
            continue
        if data is None:
            p = part.get_payload()
            data = p.encode("utf-8", "replace") if isinstance(p, str) else b""
        cs = part.get_content_charset() or "utf-8"
        try:
            text = data.decode(cs, "replace")
        except LookupError:
            text = data.decode("utf-8", "replace")
        (htmls if ctype == "text/html" and not texty else plain).append(text)
    texts = plain or [strip_html(h) for h in htmls]
    lines = []
    for t in texts:
        for ln in t.splitlines():
            ln = clean(ln)
            if ln:
                lines.append(ln)
                if len(lines) >= MAX_LINES:
                    break
    stamps = [stamp(x) for x in lines]
    stamped = [s for s in stamps if s]
    if len(stamped) >= 2 and stamped[0] > stamped[-1]:     # the router lists newest first: write in time order,
        i = next(n for n, s in enumerate(stamps) if s)     # keeping any heading lines above the entries first
        lines = lines[:i] + lines[i:][::-1]
    return lines, other


def fingerprint(line):
    return hashlib.blake2b(line.encode("utf-8", "replace"), digest_size=12).hexdigest()


def syslog_time(t=None):
    t = time.localtime(t)
    return f"{MONTHS[t.tm_mon - 1]} {t.tm_mday:2d} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"


def append_log(lines):
    os.makedirs(os.path.dirname(LOG) or ".", mode=0o750, exist_ok=True)
    ts = syslog_time()
    fd = os.open(LOG, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.write("".join(f"{ts} router cipherline-router: {ln}\n" for ln in lines))


# ------------------------------------------------------------------ the receiver
class Receiver:
    def __init__(self):
        self.cfg = load_cfg()
        os.makedirs(STATE, mode=0o750, exist_ok=True)
        self.seen = {}
        try:
            with open(SEEN, encoding="ascii", errors="replace") as f:
                for h in f.read().split()[-SEEN_MAX:]:
                    self.seen[h] = None
        except FileNotFoundError:
            pass
        self.st = {"mails": 0, "lines": 0, "dupes": 0, "refused": 0, "last_contact": 0, "last_mail": 0, "last_new": 0,
                   "last_lines": 0, "last_refused": 0, "last_refused_ip": "", "unsupported": "", "skipped": "", "error": "",
                   "tls_error": "", "last_tls_error": 0, "last_tls": ""}
        try:
            with open(STATUS, encoding="utf-8") as f:
                old = json.load(f)
            for k in self.st:
                if isinstance(old.get(k), type(self.st[k])):
                    self.st[k] = old[k]
        except (OSError, ValueError):
            pass
        self.st.update(router=self.cfg["router"], port=self.cfg["port"], tls_port=self.cfg["tls_port"], started=now())
        self.ctx = None
        if self.cfg["tls_port"]:
            self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)        # TLS 1.2 and newer, the library's defaults
            self.ctx.load_cert_chain(self.cfg["cert"], self.cfg["key"])
        self.active = 0
        self.save_status()

    def save_status(self):
        try:
            write_atomic(STATUS, json.dumps(self.st, sort_keys=True) + "\n", 0o644)
        except OSError as e:
            print(f"cannot write {STATUS}: {e}", file=sys.stderr, flush=True)

    def take(self, raw):
        """Write the message's new lines. Returns (new, dupes), or raises OSError if the log cannot be written."""
        try:
            lines, other = mail_lines(raw)
        except Exception as e:                    # a message the parser cannot read: say so, keep running
            self.st["error"] = f"could not read a message from the router: {e}"[:200]
            return 0, 0
        new, fresh, dupes = [], set(), 0
        for ln in lines:
            h = fingerprint(ln)
            if h in self.seen or h in fresh:
                dupes += 1
                continue
            fresh.add(h)
            new.append((h, ln))
        if new:
            append_log([ln for _, ln in new])     # first written, then remembered: a failed write is tried again
            for h, _ in new:
                self.seen[h] = None
            while len(self.seen) > SEEN_MAX:
                del self.seen[next(iter(self.seen))]
            write_atomic(SEEN, "\n".join(self.seen) + "\n", 0o600)
        self.st.update(mails=self.st["mails"] + 1, lines=self.st["lines"] + len(new), dupes=self.st["dupes"] + dupes,
                       last_mail=now(), last_new=len(new), last_lines=len(lines), error="",
                       skipped=", ".join(other)[:200])
        return len(new), dupes

    def refuse(self, ip):
        self.st.update(refused=self.st["refused"] + 1, last_refused=now(), last_refused_ip=ip[:45])
        self.save_status()

    async def handle_tls(self, conn, addr):
        """Port 465: the address is checked on the bare connection, before any TLS; then the handshake, then SMTP."""
        ip = str(addr[0])
        if ip.startswith("::ffff:"):
            ip = ip[7:]
        if ip != self.cfg["router"] or self.active >= MAX_SESSIONS:
            if ip != self.cfg["router"]:
                self.refuse(ip)
            conn.close()
            return
        self.st["last_contact"] = now()
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader(limit=LIMIT)
        protocol = asyncio.StreamReaderProtocol(reader)
        try:
            transport, _ = await loop.connect_accepted_socket(lambda: protocol, conn, ssl=self.ctx,
                                                              ssl_handshake_timeout=TLS_WAIT)
        except (OSError, TimeoutError, asyncio.TimeoutError, ssl.SSLError) as e:   # wrong protocol, no shared cipher...
            self.st.update(tls_error=f"{type(e).__name__}: {e}"[:200], last_tls_error=now())
            self.save_status()
            conn.close()
            return
        so = transport.get_extra_info("ssl_object")
        self.st.update(last_tls=f"{so.version()} {so.cipher()[0]}"[:80] if so else "", tls_error="")
        writer = asyncio.StreamWriter(transport, protocol, reader, loop)
        await self.handle(reader, writer, checked=True)

    async def handle(self, reader, writer, checked=False):
        peer = writer.get_extra_info("peername") or ("?",)
        ip = str(peer[0])
        if ip.startswith("::ffff:"):
            ip = ip[7:]
        try:
            if not checked and ip != self.cfg["router"]:
                self.refuse(ip)
                writer.write(b"554 5.7.1 This receiver only takes the router's log\r\n")
                await writer.drain()
                return
            if self.active >= MAX_SESSIONS:
                writer.write(b"421 4.3.2 Busy, try again later\r\n")
                await writer.drain()
                return
            self.active += 1
            self.st["last_contact"] = now()
            try:
                await asyncio.wait_for(self.converse(reader, writer), SESSION_MAX)
            finally:
                self.active -= 1
                self.save_status()
        except (TimeoutError, asyncio.TimeoutError, ConnectionError, ValueError, asyncio.IncompleteReadError):
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except (ConnectionError, OSError):
                pass

    async def converse(self, reader, writer):
        async def say(*lines):
            writer.write("".join(x + "\r\n" for x in lines).encode())
            await writer.drain()

        async def line():
            b = await asyncio.wait_for(reader.readline(), IDLE)
            if not b:
                raise ConnectionError("closed")
            return b

        await say(f"220 {HOST} ESMTP the router log receiver (nothing is relayed)")
        sender, rcpts, errors = None, 0, 0
        while errors < MAX_ERRORS:
            raw = await line()
            cmd = raw.decode("latin-1").rstrip("\r\n")
            verb, _, arg = cmd.strip().partition(" ")
            verb = verb.upper()
            if len(raw) > 2048:
                errors += 1
                await say("500 5.5.2 Line too long")
            elif verb == "EHLO":
                sender, rcpts = None, 0
                await say(f"250-{HOST}", "250-AUTH PLAIN LOGIN CRAM-MD5", "250-AUTH=PLAIN LOGIN CRAM-MD5",
                          f"250-SIZE {MAX_MAIL}", "250-8BITMIME", "250 HELP")
            elif verb == "HELO":
                sender, rcpts = None, 0
                await say(f"250 {HOST}")
            elif verb == "AUTH":
                mech, _, first = arg.strip().partition(" ")
                mech = mech.upper()
                if mech == "PLAIN":
                    if not first.strip():
                        await say("334 ")
                        await line()
                elif mech == "LOGIN":
                    if not first.strip():
                        await say("334 VXNlcm5hbWU6")
                        await line()
                    await say("334 UGFzc3dvcmQ6")
                    await line()
                elif mech == "CRAM-MD5":
                    import base64
                    await say("334 " + base64.b64encode(f"<{os.getpid()}.{now()}@{HOST}>".encode()).decode())
                    await line()
                else:
                    errors += 1
                    await say("504 5.5.4 Use PLAIN, LOGIN or CRAM-MD5")
                    continue
                await say("235 2.7.0 Accepted")      # the router's address is the check; what it sent is not kept
            elif verb == "MAIL":
                if not arg.upper().startswith("FROM:"):
                    errors += 1
                    await say("501 5.5.4 Syntax: MAIL FROM:<address>")
                else:
                    sender, rcpts = arg[5:].strip()[:200], 0
                    await say("250 2.1.0 OK")
            elif verb == "RCPT":
                if sender is None:
                    errors += 1
                    await say("503 5.5.1 MAIL first")
                elif not arg.upper().startswith("TO:"):
                    errors += 1
                    await say("501 5.5.4 Syntax: RCPT TO:<address>")
                elif rcpts >= MAX_RCPT:
                    await say("452 4.5.3 Too many recipients")
                else:
                    rcpts += 1
                    await say("250 2.1.5 OK")
            elif verb == "DATA":
                if sender is None or not rcpts:
                    errors += 1
                    await say("503 5.5.1 MAIL and RCPT first")
                    continue
                await say("354 End with <CR><LF>.<CR><LF>")
                buf, big = bytearray(), False
                while True:
                    try:
                        b = await line()
                    except ValueError:                # one line over the 1 MB read limit: the message is too big
                        big, buf = True, bytearray()
                        continue
                    if b in (b".\r\n", b".\n", b"."):
                        break
                    if b.startswith(b"."):
                        b = b[1:]                     # dot-stuffing
                    if not big:
                        if len(buf) + len(b) > MAX_MAIL:
                            big = True
                            buf = bytearray()
                        else:
                            buf += b
                sender, rcpts = None, 0
                if big:
                    self.st["error"] = f"a message from the router was over {MAX_MAIL // 1048576} MB and was refused"
                    self.save_status()
                    await say("552 5.3.4 Message too big")
                    continue
                try:
                    new, dupes = self.take(bytes(buf))
                except OSError as e:
                    self.st["error"] = f"could not write {LOG}: {e.strerror or e}"[:200]
                    self.save_status()
                    await say("451 4.3.0 Could not store the log, try again later")
                    continue
                self.save_status()
                await say(f"250 2.0.0 OK: {new} new line(s), {dupes} already had")
            elif verb == "RSET":
                sender, rcpts = None, 0
                await say("250 2.0.0 OK")
            elif verb == "NOOP":
                await say("250 2.0.0 OK")
            elif verb == "VRFY":
                await say("252 2.5.2 Send some mail and I will try")
            elif verb == "QUIT":
                await say("221 2.0.0 Bye")
                return
            else:
                errors += 1
                self.st["unsupported"] = verb[:20]       # e.g. STARTTLS: shown in the console if mail stops arriving
                self.save_status()
                await say("502 5.5.2 Not supported here")
        await say("421 4.7.0 Too many errors")


async def main():
    try:
        r = Receiver()
    except (OSError, ValueError, TypeError) as e:
        print(f"cipherline-router-mail: bad settings in {CONF}: {e}", file=sys.stderr, flush=True)
        return 2
    c = r.cfg
    server = await asyncio.start_server(r.handle, c["listen"], c["port"], limit=LIMIT, reuse_address=True)
    ports = str(c["port"])
    tasks = [asyncio.ensure_future(server.serve_forever())]
    if c["tls_port"]:
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            lsock.bind((c["listen"], c["tls_port"]))
        except OSError as e:
            print(f"cipherline-router-mail: cannot listen on port {c['tls_port']}: {e}", file=sys.stderr, flush=True)
            return 2
        lsock.listen(16)
        lsock.setblocking(False)
        tasks.append(asyncio.ensure_future(accept_loop(r, lsock)))
        ports += f" and {c['tls_port']} (TLS)"
    print(f"cipherline-router-mail: listening on {c['listen']} port {ports} for mail from {c['router']}", flush=True)
    await asyncio.gather(*tasks)
    return 0


async def accept_loop(r, lsock):
    loop = asyncio.get_running_loop()
    while True:
        try:
            conn, addr = await loop.sock_accept(lsock)
        except OSError:                 # e.g. too many open files: wait, then carry on
            await asyncio.sleep(1)
            continue
        asyncio.ensure_future(r.handle_tls(conn, addr))


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        sys.exit(0)
