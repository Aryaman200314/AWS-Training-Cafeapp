# Cloud Café verification

Initial application and browser verification: **24 October 2026** in the supplied Windows workspace. Installer update and checks: **25 October 2026**.

## Checks actually run

| Check | Result |
| --- | --- |
| Python tests | **13 passed** using `python -m unittest discover -s tests -v`. |
| Homepage | HTTP 200 through Flask's test client and the running HTTP server in Chrome. |
| Menu | Exactly 8 cards; all names, descriptions, categories, and formatted USD prices checked. |
| Default deployment details | Hostname fallback and version `1.0` checked with the test client. The running page also displayed the machine hostname and `1.0`. |
| Environment overrides | `SERVER_NAME=Alain-demo` and `APP_VERSION=2.7` displayed correctly in tests, including a request with an ALB-style IP Host header. |
| Empty overrides | Empty values correctly used the hostname and `1.0`. |
| HTML escaping | HTML in display settings was escaped rather than executed. |
| Health endpoint | HTTP 200, exact two-byte body `OK`, and `text/plain`, through tests, curl, and Chrome's HTTP client. No redirect or session cookie. |
| Independent health | `/health` still returned `OK` when the menu and template functions were deliberately made to fail in a test. |
| Homepage caching | `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`, `Pragma: no-cache`, and `Expires: 0` checked. |
| Category filtering | Chrome confirmed Coffee **3**, Tea **2**, Snacks **3**, and All **8**, on desktop and mobile layouts. Only the selected category remained visible. |
| No filter reloads | Chrome recorded no new network requests while category buttons were used. |
| Accessible controls | Selected buttons updated `aria-pressed`; only one was selected. Keyboard Enter activated Tea. Mobile filter buttons were at least 44 pixels high. |
| Reload button | Chrome confirmed a new request for the homepage and a reset to all 8 cards. |
| Mobile layout | Checked at **375 × 812**. No horizontal overflow; screenshots visually reviewed. |
| Desktop layout | Checked at **1440 × 1000**; full-page screenshot visually reviewed. |
| No JavaScript | All 8 menu cards remained available; inactive filtering controls were hidden. |
| Local assets | CSS, JavaScript, and SVG loaded successfully. Browser requests stayed on the local origin; no page errors or failed HTTP responses. |
| Stateless menu | Changing a returned menu copy did not affect later requests' source menu. |
| Debug mode | Flask debug mode was false. |
| Dependency installation | Pinned Flask packages installed; the documented `pip install -r requirements.txt` command succeeded; `pip check` reported no broken requirements. |
| Linux dependency compatibility | The exact requirements resolved for Linux x86-64 / Python 3.10. Gunicorn 26.2.0's downloaded metadata declares Python `>=3.10`. This is a dependency check, not a Gunicorn runtime test. |
| Bash syntax | `bash -n` passed for `deploy/deploy.sh` and `deploy/user-data.sh`, using Git Bash. |
| JavaScript syntax | Node's syntax checks passed for the application script and browser test. |
| User-data synchronization | All **9 embedded deployable files** matched their source contents byte for byte after LF normalization. |
| User-data size | **12,691 bytes** after the Ubuntu 26.04 update, below the **16,384-byte** raw EC2 limit. The script begins with `#!/bin/bash` and uses LF line endings. |
| Delivery archives | ZIP and tar.gz contents checked against the project; neither includes the local Python environment or verification tools. |

Final application tests used **CPython 3.10.11**, **Flask 3.1.3**, and **Chrome 155.0.8059.86**. Earlier checks also passed on Python 3.10.22. Runtime package versions are pinned in `requirements.txt`.

The built-in browser tool could not start. Browser verification instead used a temporary Playwright installation with the machine's installed Google Chrome. These tools are not application dependencies. Screenshots are in `.tools/browser-results/` in the original workspace.

## Ubuntu 26.04 installer update — 25 October 2026

- The user's EC2 screenshot identified Ubuntu 26.04.1 LTS. The previous installer intentionally accepted only Ubuntu 22.04, which caused the reported stop.
- The installer now accepts Ubuntu 22.04 and 26.04 and includes the detected operating system in its error message for other versions.
- The pinned packages resolved for Linux **Python 3.14**, on both **x86-64 and ARM64**, without changing any package version.
- The actual Bash version guard was exercised separately: Ubuntu 22.04 and 26.04 passed; Ubuntu 20.04 and Debian were rejected. No installation commands were executed by these guard checks.
- The copy-and-paste `sed` repair for the user's old checkout was tested: it produces the same version condition as the updated installer and does not add another change when repeated.
- All **13 Python tests** passed again, and both Bash scripts passed syntax checks. User data and both delivery archives were rebuilt and checked against the final project files.
- Application and interface code did not change. Browser results above are from 24 October; browser tests were not repeated for this installer-only change.
- This is **not a completed Ubuntu 26.04 deployment test**; Python 3.14 dependency resolution is distinct from running the service on Linux.

## Not verified in this environment

- No Ubuntu machine or WSL environment was available. The installer was syntax-checked and reviewed, but **not executed on fresh Ubuntu 22.04 or 26.04**.
- Gunicorn was downloaded and its Python compatibility checked, but **not run on Linux**. It does not run natively on Windows.
- systemd startup, execution as the dedicated service user, repeated full installations, and automatic startup after a real reboot were **not exercised**.
- No live EC2 instance, launch template, ALB, target group, or ASG was created or modified. AWS networking, cloud-init first boot, real target health, load distribution, and instance replacement were **not exercised**.

Use the README's EC2 health, service, and log commands during rehearsal to complete these checks. The deployment scripts intentionally use only local application files and public package repositories.

## Repeat the checks

PowerShell, from the project directory:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools/build_user_data.py --check
.\.venv\Scripts\python.exe -m pip check
```

Optional browser checks require Node.js and Google Chrome. The application itself does not need Node.js. Start the local server in another terminal, then run:

```powershell
npm.cmd install --prefix .tools --no-save --no-package-lock playwright
node tests/browser-check.cjs
```

For Ubuntu, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`, and `npm.cmd` with `npm`. The browser test expects the default application version `1.0` at `http://127.0.0.1:8080` and uses Chrome's headless mode (no visible window).
