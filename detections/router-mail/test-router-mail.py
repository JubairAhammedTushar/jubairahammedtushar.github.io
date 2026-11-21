#!/usr/bin/env python3
"""The router's Mail Log receiver (router-mail.py), run for real on 127.0.0.1 and spoken to with smtplib, as the
router would: what gets into router.log, what is skipped, what is refused. No network beyond this machine."""
import base64
import json
import os
import re
import shutil
import smtplib
import socket
import ssl
import subprocess
import sys
import tempfile
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

HERE = os.path.dirname(os.path.abspath(__file__))
D = tempfile.mkdtemp(prefix="rmail-")
LOG, STATE, CONF = f"{D}/var/router.log", f"{D}/state", f"{D}/conf.json"
PASS = FAIL = 0
PW = "Real0Gmail1Password2"


def t(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  PASS", label)
    else:
        FAIL += 1
        print("  FAIL", label)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


PROC = None


CERT, KEY = f"{D}/cert.pem", f"{D}/key.pem"
TLS_PORT = 0


def start(router="127.0.0.1", tls=False):
    global PROC, PORT, TLS_PORT
    stop()
    PORT = free_port()
    c = {"router": router, "port": PORT, "listen": "127.0.0.1"}
    if tls:
        TLS_PORT = free_port()
        c.update(tls_port=TLS_PORT, cert=CERT, key=KEY)
    json.dump(c, open(CONF, "w"))
    env = dict(os.environ, RMAIL_CONF=CONF, RMAIL_LOG=LOG, RMAIL_STATE=STATE, RMAIL_IDLE="5")
    PROC = subprocess.Popen([sys.executable, f"{HERE}/router-mail.py"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", PORT), 0.2).close()
            if tls:
                socket.create_connection(("127.0.0.1", TLS_PORT), 0.2).close()
            time.sleep(0.3)              # let the receiver finish with that knock
            return
        except OSError:
            time.sleep(0.05)
    raise SystemExit("receiver did not start: " + PROC.stdout.read().decode())


def stop():
    global PROC
    if PROC:
        PROC.terminate()
        PROC.wait(5)
        PROC = None


def send(msg, login=None, mech=None):
    with smtplib.SMTP("127.0.0.1", PORT, timeout=10) as s:
        s.ehlo("router")
        if login:
            if mech:
                s.user, s.password = login
                s.auth(mech, getattr(s, "auth_" + mech.lower().replace("-", "_")))
            else:
                s.login(*login)
        r = s.sendmail("router@cipherline.lan", ["soc@cipherline.lan"], msg if isinstance(msg, (str, bytes)) else msg.as_string())
        return r


def mail(body, subtype="plain", charset="us-ascii"):
    m = MIMEText(body, subtype, charset)
    m["Subject"], m["From"], m["To"] = "Log", "router@cipherline.lan", "soc@cipherline.lan"
    return m


def log_lines():
    try:
        return open(LOG).read().splitlines()
    except FileNotFoundError:
        return []


def msgs():
    return [x.split("cipherline-router: ", 1)[1] for x in log_lines()]


def status():
    return json.load(open(f"{STATE}/status.json"))


LOG1 = """System Log
Time = 2026-11-17 02:00:01 1234s
H-Ver = Archer C6 v3.2 : S-Ver = 1.0.12
#
2026-11-17 01:59:02 Login failed from 192.168.1.5
2026-11-17 01:58:40 DHCPD INFO DHCPS:Send ACK to 192.168.1.40
2026-11-17 01:50:00 WAN PPPoE down

"""

print("== a plain mail from the router")
start()
send(mail(LOG1))
L, M = log_lines(), msgs()
t("one line per log line, separators, blanks and the changing 'Time =' header left out",
  M == ["System Log", "H-Ver = Archer C6 v3.2 : S-Ver = 1.0.12", "2026-11-17 01:50:00 WAN PPPoE down",
        "2026-11-17 01:58:40 DHCPD INFO DHCPS:Send ACK to 192.168.1.40", "2026-11-17 01:59:02 Login failed from 192.168.1.5"]
  or M[2:] == ["2026-11-17 01:50:00 WAN PPPoE down", "2026-11-17 01:58:40 DHCPD INFO DHCPS:Send ACK to 192.168.1.40",
               "2026-11-17 01:59:02 Login failed from 192.168.1.5"])
t("the router lists newest first: written oldest first", M[-1].startswith("2026-11-17 01:59:02") and M[-3].startswith("2026-11-17 01:50:00"))
t("the same format as the syslog route (Wazuh's decoder cipherline-router)",
  all(re.fullmatch(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [ 1-3]\d \d\d:\d\d:\d\d router cipherline-router: \S.*", x) for x in L))
st = status()
t("status: one mail, its new lines, the router and port", st["mails"] == 1 and st["lines"] == len(L) and st["last_new"] == len(L)
  and st["router"] == "127.0.0.1" and st["port"] == PORT and st["last_mail"] >= time.time() - 30 and st["error"] == "")
t("log file only for root and its group", oct(os.stat(LOG).st_mode & 0o777) == "0o640")

print("== the whole log again, an hour later")
n = len(L)
send(mail(LOG1))
t("lines already written are skipped", len(log_lines()) == n and status()["dupes"] >= 4 and status()["last_new"] == 0)
send(mail("2026-11-17 02:10:00 DoS attack: SYN flood from 203.0.113.5\n" + LOG1))
t("only the new line is added", len(log_lines()) == n + 1 and msgs()[-1] == "2026-11-17 02:10:00 DoS attack: SYN flood from 203.0.113.5")

print("== sign-in, if the router insists on one")
for mech in (None, "PLAIN", "LOGIN", "CRAM-MD5"):
    try:
        send(mail(f"auth test {mech}\n"), login=("router@gmail.example", PW), mech=mech)
        ok = msgs()[-1] == f"auth test {mech}"
    except smtplib.SMTPException as e:
        ok = False
        print("   ", mech, e)
    t(f"accepted with {mech or 'whatever smtplib picks'}", ok)
def read_state():
    # The receiver replaces status.json via a temporary file and a rename, so a .tmp file seen
    # by listdir can be gone a moment later. Read whatever is there; skip files that vanished.
    out = []
    for f in os.listdir(STATE):
        try:
            with open(f"{STATE}/{f}") as fh:
                out.append(fh.read())
        except FileNotFoundError:
            pass
    return "".join(out)
blob = open(LOG).read() + read_state()
t("what it signed in with is not kept anywhere", PW not in blob and base64.b64encode(PW.encode()).decode() not in blob)

print("== other shapes of message")
m = MIMEMultipart()
m.attach(MIMEText("Your router's log is attached.", "plain"))
a = MIMEApplication(b"2026-11-17 02:20:00 attached line one\r\n2026-11-17 02:21:00 attached line two\r\n")
a.add_header("Content-Disposition", "attachment", filename="syslog.txt")
m.attach(a)
send(m)
t("a .txt attachment is read as well as the text", msgs()[-3:] == ["Your router's log is attached.", "2026-11-17 02:20:00 attached line one",
                                                                  "2026-11-17 02:21:00 attached line two"])
send(mail("<html><body><p>html line A</p>html line B<br>html &amp; line C<script>x()</script></body></html>", "html"))
t("an HTML-only mail: its text, line by line", msgs()[-3:] == ["html line A", "html line B", "html & line C"])
send(mail("utf-8 body: Café → ok\n", "plain", "utf-8"))
t("a base64 UTF-8 body is decoded", msgs()[-1] == "utf-8 body: Café → ok")
send(mail(".dotted line\n\x1b[31mcolour\x07 codes\tand tabs\n" + "x" * 2000 + "\n"))
t("dot-stuffing undone; control characters gone; long lines cut at 900", msgs()[-3:] == [".dotted line", "[31mcolour codes and tabs", "x" * 900])
m = MIMEMultipart()
m.attach(MIMEText("with a picture", "plain"))
m.attach(MIMEApplication(b"\x89PNG....", "png", Name="logo.png"))
send(m)
t("a part that is not text is left out and named in the status", msgs()[-1] == "with a picture" and "logo.png" in status()["skipped"])
m = MIMEMultipart()
m.attach(MIMEText("log follows", "plain"))
a = MIMEApplication(b"2026-11-17 02:40:00 from an attachment called syslog\n2026-11-17 02:41:00 second\n")
a.add_header("Content-Disposition", "attachment", filename="syslog")
m.attach(a)
send(m)
t("an attachment with no text type or name, that is text all the same, is read", msgs()[-2:] == ["2026-11-17 02:40:00 from an attachment called syslog", "2026-11-17 02:41:00 second"])

print("== refused")
n = len(log_lines())
big = []
for body in ("2026-11-17 02:30:00 a normal line of the log\n" * 120000, "x" * (5 * 1024 * 1024)):   # many lines; one huge line
    try:
        send(mail(body))
        big.append(False)
    except smtplib.SMTPDataError as e:
        big.append(e.smtp_code == 552)
t("a message over 4 MB (many lines, or one huge line): refused, nothing written, said in the status",
  big == [True, True] and len(log_lines()) == n and "over 4 MB" in status()["error"])
send(mail("after the big one\n"))
t("the next mail clears that error", status()["error"] == "" and msgs()[-1] == "after the big one")
with smtplib.SMTP("127.0.0.1", PORT, timeout=10) as s:
    s.ehlo("router")
    no_tls = not s.has_extn("starttls")
    c1 = s.docmd("STARTTLS")[0]
    c2 = s.docmd("RCPT TO:<soc@cipherline.lan>")[0]
    s.docmd("MAIL FROM:<router@cipherline.lan>")
    c3 = s.docmd("DATA")[0]
    c4 = s.docmd("VRFY root")[0]
t("no encryption offered; STARTTLS answered 'not supported' and named in the status", no_tls and c1 == 502 and status()["unsupported"] == "STARTTLS")
t("commands out of order refused; VRFY says nothing", c2 == 503 and c3 == 503 and c4 == 252)
with smtplib.SMTP("127.0.0.1", PORT, timeout=10) as s:
    s.ehlo("x")
    for _ in range(25):
        try:
            code = s.docmd("BOGUS")[0]
        except smtplib.SMTPServerDisconnected:
            code = 0
            break
t("a client that keeps sending nonsense is cut off", code in (0, 421))

print("== the log cannot be written")
os.rename(LOG, LOG + ".moved")
os.makedirs(LOG)                         # a directory where the file should be
try:
    send(mail("2026-11-17 03:00:00 written later\n"))
    tmp_fail = False
except smtplib.SMTPDataError as e:
    tmp_fail = e.smtp_code == 451
t("451 (try later), the reason in the status", tmp_fail and "could not write" in status()["error"])
os.rmdir(LOG)
os.rename(LOG + ".moved", LOG)
send(mail("2026-11-17 03:00:00 written later\n"))
t("the same line is written once the file is back (not marked as seen before)", msgs()[-1] == "2026-11-17 03:00:00 written later")

print("== after a restart")
n = len(log_lines())
start()
send(mail(LOG1))
t("still knows what it has written", len(log_lines()) == n and status()["mails"] > 10)

print("== only the router")
start(router="192.168.1.1")
r0 = status()["refused"]          # the start-up check above already knocked once
try:
    send(mail("from the wrong place\n"))
    refused = False
except smtplib.SMTPConnectError as e:
    refused = e.smtp_code == 554
except smtplib.SMTPServerDisconnected:
    refused = True
st = status()
t("any other address is refused before anything is said", refused and st["refused"] == r0 + 1 and st["last_refused_ip"] == "127.0.0.1"
  and "from the wrong place" not in open(LOG).read())

print("== port 465: the router's way (SMTP over TLS)")
subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", KEY, "-out", CERT, "-days", "3650",
                "-subj", "/CN=cipherline-soc", "-addext", "subjectAltName=IP:127.0.0.1"], check=True, capture_output=True)
start(tls=True)
NOCHECK = ssl.create_default_context()
NOCHECK.check_hostname, NOCHECK.verify_mode = False, ssl.CERT_NONE      # as the router: the SOC's own certificate
n = len(log_lines())
with smtplib.SMTP_SSL("127.0.0.1", TLS_PORT, timeout=10, context=NOCHECK) as s:
    s.ehlo("router")
    s.sendmail("router@cipherline.lan", ["soc@cipherline.lan"], mail("2026-11-17 05:20:00 sent over TLS\n").as_string())
st = status()
t("mail over TLS arrives like the plain kind", msgs()[-1] == "2026-11-17 05:20:00 sent over TLS" and len(log_lines()) == n + 1)
t("status: the TLS port, the protocol used, no error", st["tls_port"] == TLS_PORT and st["last_tls"].startswith("TLSv1.") and st["tls_error"] == "")
with smtplib.SMTP_SSL("127.0.0.1", TLS_PORT, timeout=10, context=NOCHECK) as s:
    s.login("router@gmail.example", PW)
    s.sendmail("router@cipherline.lan", ["soc@cipherline.lan"], mail("2026-11-17 05:21:00 signed in over TLS\n").as_string())
t("a sign-in over TLS works too, and is not kept", msgs()[-1] == "2026-11-17 05:21:00 signed in over TLS"
  and PW not in open(LOG).read() + open(f"{STATE}/status.json").read())
send(mail("2026-11-17 05:22:00 plain still works\n"))
t("port 25 still takes plain mail alongside", msgs()[-1] == "2026-11-17 05:22:00 plain still works")
c = socket.create_connection(("127.0.0.1", TLS_PORT), 5)
c.sendall(b"EHLO plain-text-on-the-tls-port\r\n")
time.sleep(1)
c.close()
time.sleep(0.5)
st = status()
t("plain text on port 465: the handshake error is kept for the console", st["tls_error"] and st["last_tls_error"] >= time.time() - 30)
weak = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
weak.check_hostname, weak.verify_mode = False, ssl.CERT_NONE
try:
    weak.maximum_version = ssl.TLSVersion.TLSv1_1
    weak.set_ciphers("DEFAULT:@SECLEVEL=0")
    with socket.create_connection(("127.0.0.1", TLS_PORT), 5) as raw, weak.wrap_socket(raw) as w:
        old_ok = True
except (ssl.SSLError, OSError, ValueError):
    old_ok = False
time.sleep(0.5)
t("TLS older than 1.2 is not accepted", not old_ok and status()["tls_error"])
start(router="192.168.1.1", tls=True)
r0 = status()["refused"]
try:
    with smtplib.SMTP_SSL("127.0.0.1", TLS_PORT, timeout=5, context=NOCHECK) as s:
        s.noop()
    ok = True
except (smtplib.SMTPException, ssl.SSLError, OSError):
    ok = False
time.sleep(0.3)
st = status()
t("port 465 from any other address: closed before the handshake, counted as refused", not ok and st["refused"] == r0 + 1)

print("== bad settings")
stop()
json.dump({"router": "not-an-address", "port": 25}, open(CONF, "w"))
r = subprocess.run([sys.executable, f"{HERE}/router-mail.py"], env=dict(os.environ, RMAIL_CONF=CONF, RMAIL_LOG=LOG, RMAIL_STATE=STATE),
                   capture_output=True, text=True, timeout=10)
t("refuses to start, says why", r.returncode == 2 and "bad settings" in r.stderr)
json.dump({"router": "192.168.1.1", "port": 2525, "tls_port": 4650, "cert": f"{D}/missing.pem", "key": KEY}, open(CONF, "w"))
r = subprocess.run([sys.executable, f"{HERE}/router-mail.py"], env=dict(os.environ, RMAIL_CONF=CONF, RMAIL_LOG=LOG, RMAIL_STATE=STATE),
                   capture_output=True, text=True, timeout=10)
t("TLS port without its certificate: refuses to start, says why", r.returncode == 2 and "certificate" in r.stderr)

stop()
shutil.rmtree(D, ignore_errors=True)
print(f"\nrouter mail: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
