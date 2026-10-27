# Cloud Café

A friendly café menu for Alain's beginner AWS lessons. The application uses Python and Flask, local HTML and CSS, and a small JavaScript file. It runs on a laptop and is prepared for Ubuntu 22.04 or 26.04 LTS on EC2. The installer accepts both versions; full Ubuntu deployment still needs rehearsal (see `VERIFICATION.md`).

There are eight sample items: three coffees, two teas, and three snacks. The category buttons filter the menu without loading another page. Prices are in US dollars (USD). The **Deployment information** panel shows which server answered the request and the application version.

There is **no database**, login, checkout, payment processing, or order storage. All instances use the same menu in `menu.py`. The application does not write customer data or use local saved state. It does not need AWS credentials, an IAM role, an external API, or a repository download.

## 1. Project files

| File | What it does |
| --- | --- |
| `app.py` | Flask application. Serves `/` and `/health`, reads display settings, and prevents homepage caching. |
| `menu.py` | Eight sample items and the `get_menu()` function. |
| `templates/index.html` | The page layout. Flask fills in the menu and server details. |
| `static/style.css` | Colors, cards, responsive layouts, and a CSS coffee illustration. |
| `static/script.js` | Shows or hides cards when a category button is pressed. |
| `static/cafe.svg` | Local café logo and browser icon. No image service is used. |
| `requirements.txt` | Exact versions of Flask, Gunicorn, and their supporting packages. Gunicorn is skipped on Windows. |
| `deploy/deploy.sh` | Installs the application on an existing Ubuntu 22.04 or 26.04 instance. Run with `sudo`. |
| `deploy/cloud-cafe.service` | Instructions for systemd, Ubuntu's background service manager. |
| `deploy/user-data.sh` | Complete standalone installer to paste into an EC2 launch template. |
| `tools/build_user_data.py` | Rebuilds the standalone script directly from the project files and checks its size. |
| `tests/test_app.py` | Automated application checks using Python's built-in test runner. |
| `tests/test_deployment.py` | Checks that the user-data payload exactly matches the project. |
| `tests/browser-check.cjs` | Optional Chrome browser checks; not needed to run or deploy the application. |
| `VERIFICATION.md` | Results of the checks actually run, including verification limits. |
| `.gitignore` | Keeps environments, test tools, caches, and packages out of Git. |
| `.gitattributes` | Keeps deployment scripts in Linux-compatible line endings. |
| `README.md` | This guide. |

`cloud-cafe.tar.gz` and `cloud-cafe.zip` are delivery packages containing the project. The local `.venv` folder holds installed Python packages. `.tools` contains tools used only for verification on the authoring machine. Neither folder belongs on EC2 or in the delivery packages.

## 2. Run locally on Windows PowerShell

Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/windows/) if needed. The commands below use the Python launcher, `py`. Reopen PowerShell after installing Python.

Open the project folder, then run:

```powershell
Set-Location 'D:\AWS-Training\Applicaion day 08'
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

If you extracted the project elsewhere, change the first line to that folder. If your Python installation provides `python` instead of `py`, use `python -m venv .venv` for the second line.

No environment activation or execution-policy change is needed: the commands call the environment's Python directly. A **virtual environment** is a folder that keeps this application's Python packages together.

**In the supplied workspace, `.venv` is already prepared. You can immediately run:**

```powershell
Set-Location 'D:\AWS-Training\Applicaion day 08'
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:8080** in your browser. `127.0.0.1` means this computer. Stop the local server with **Ctrl+C** in its terminal. The local server is for learning and previewing. EC2 uses Gunicorn, a server that runs the Flask application as a managed background process. Gunicorn runs on Unix systems, so Windows uses Flask for local preview. [Flask's Gunicorn guide](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/)

## 3. Run locally on Ubuntu 22.04 or 26.04

In the folder containing `app.py`:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Open **http://127.0.0.1:8080**. Stop with **Ctrl+C**.

To rehearse the Gunicorn command on Ubuntu instead:

```bash
.venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 2 --access-logfile - --error-logfile - app:app
```

`0.0.0.0` means listen on all network interfaces. It is not a browser address; use the machine's IP address. A **port** is a numbered connection point; this application uses port **8080**.

## 4. Check the application

With the server running, open another terminal.

Windows PowerShell:

```powershell
curl.exe -i http://127.0.0.1:8080/health
curl.exe -I http://127.0.0.1:8080/
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools/build_user_data.py --check
```

Ubuntu:

```bash
curl -i http://127.0.0.1:8080/health
curl -I http://127.0.0.1:8080/
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/build_user_data.py --check
```

`/health` must return **HTTP 200** and the exact plain-text body **OK**. HTTP 200 means the request succeeded. This endpoint needs no authentication and does not call the menu function, a database, or any external service. Its purpose is to show that the web process can answer a request; it is not a test of every page feature.

The homepage headers include `Cache-Control: no-store`. This tells the browser and intermediate caches not to save a copy of the page. Click **Coffee**, **Tea**, **Snacks**, and **All**: you should see **3**, **2**, **3**, and **8** cards. **Reload page** sends a new request and returns the filter to All. Reloading can reach the same EC2 instance again; it does not guarantee a different server.

## 5. Optional display settings

| Environment variable | Default | Example |
| --- | --- | --- |
| `SERVER_NAME` | The operating system's hostname | `Alain-demo` |
| `APP_VERSION` | `1.0` | `1.1` |

An **environment variable** is a named setting passed to a running program. Empty values also use the defaults. `SERVER_NAME` is only a display label; it does not change Flask routing or the address on which Gunicorn listens.

PowerShell, before starting the server:

```powershell
$env:SERVER_NAME = 'Alain-demo'
$env:APP_VERSION = '1.1'
.\.venv\Scripts\python.exe app.py
```

After stopping it, remove overrides with:

```powershell
Remove-Item Env:SERVER_NAME -ErrorAction SilentlyContinue
Remove-Item Env:APP_VERSION -ErrorAction SilentlyContinue
```

Ubuntu local preview:

```bash
SERVER_NAME=Alain-demo APP_VERSION=1.1 .venv/bin/python app.py
```

On deployed EC2 instances, edit the service settings and restart:

```bash
sudo nano /etc/cloud-cafe.env
sudo systemctl restart cloud-cafe
```

The file accepts lines such as `APP_VERSION=1.1` and `SERVER_NAME=Alain-demo`. **Leave SERVER_NAME unset in the launch template** when demonstrating multiple instances, so their actual hostnames identify them. Giving every instance the same label would hide that difference.

## 6. Deploy on one Ubuntu EC2 instance

These are rehearsal instructions for you to carry out. This project does not create or modify AWS resources.

1. Use an **Ubuntu Server 22.04 or 26.04 LTS** EC2 instance. An EC2 instance is a virtual computer. For the simple direct-access exercise, it needs a public IPv4 address and a subnet with an internet gateway route.
2. Its **security group** (AWS's network firewall rules) should allow TCP **8080 from your own public IP**, and TCP **22 from your own public IP** if you use SSH. SSH is a secure terminal connection. Keep this direct-access rule separate from the later ALB exercise.
3. Package installation needs **outbound internet access**, DNS resolution, and access to Ubuntu package mirrors and PyPI over HTTP/HTTPS. A public instance needs a public IP and internet gateway route; a private instance needs an outbound route such as a NAT gateway. An ALB does not provide outbound internet access to instances.
4. Copy `cloud-cafe.tar.gz` to the instance and connect using the commands below.

In PowerShell or an Ubuntu terminal on your laptop, replace `KEY_FILE.pem` with your key file path and `PUBLIC_IP` with the instance's public IPv4 address:

```text
scp -i "KEY_FILE.pem" cloud-cafe.tar.gz ubuntu@PUBLIC_IP:~/cloud-cafe.tar.gz
ssh -i "KEY_FILE.pem" ubuntu@PUBLIC_IP
```

Now in the Ubuntu SSH terminal:

```bash
mkdir -p ~/cloud-cafe
tar -xzf ~/cloud-cafe.tar.gz -C ~/cloud-cafe
cd ~/cloud-cafe
sudo bash deploy/deploy.sh
```

If the project is already extracted or cloned on your instance, skip the copy and extraction steps. For example:

```bash
cd ~/app/AWS-Training-Cafeapp
sudo bash deploy/deploy.sh
```

Running `sudo bash` does not require the script's executable permission bit. There is no need to use `chmod 777`; if you previously did, restore ordinary script permissions with `chmod 755 deploy/deploy.sh`.

Ubuntu 26.04 uses Python 3.14. The pinned dependencies have been resolved for Linux Python 3.14 on x86-64 and ARM64, but a full Ubuntu 26.04 deployment has not been run in the authoring environment. [Ubuntu 26.04 development changes](https://documentation.ubuntu.com/release-notes/26.04/summary-for-lts-users/)

The installer:

- Installs Python, virtual-environment support, certificate files, and curl.
- Creates the dedicated `cloud-cafe` user, which cannot log in interactively.
- Copies the app to `/opt/cloud-cafe` and installs its pinned packages in `.venv` there.
- Creates `/etc/cloud-cafe.env` if it does not exist.
- Installs and enables `cloud-cafe.service`, then starts Gunicorn with two workers on **0.0.0.0:8080**. Workers are processes that answer requests.
- Checks `/health` and reports success only after it returns `OK`.

The Gunicorn process runs as the non-root `cloud-cafe` user, with Flask debug mode disabled. The application files belong to root and the service has read-only access. The service starts automatically after reboot.

You can rerun `sudo bash deploy/deploy.sh` from the uploaded source folder. It refreshes the same files, preserves `/etc/cloud-cafe.env`, and restarts the existing service. It does not duplicate users or services. A restart can cause a brief interruption. Keep the uploaded source outside `/opt/cloud-cafe`.

Open **http://PUBLIC_IP:8080** in a browser. Use `http://` for this exercise.

Check from the instance:

```bash
curl -i http://127.0.0.1:8080/health
curl -I http://127.0.0.1:8080/
sudo systemctl status cloud-cafe --no-pager
sudo systemctl is-enabled cloud-cafe
```

Expected: `OK`, homepage HTTP 200, service `active (running)`, and `enabled`.

## 7. Service status and logs

```bash
# Current status
sudo systemctl status cloud-cafe --no-pager

# Last 80 log lines
sudo journalctl -u cloud-cafe -n 80 --no-pager

# Watch new log lines (Ctrl+C stops watching, not the service)
sudo journalctl -u cloud-cafe -f

# Restart after changing settings or application files
sudo systemctl restart cloud-cafe

# Verify which address and port are listening
sudo ss -ltnp 'sport = :8080'
```

`systemd` keeps the application running. `journalctl` reads its logs. Request logs and errors both go to this journal. The application itself does not save data; system and request logs are operational records.

## 8. Use the standalone user-data script in a launch template

A **launch template** saves settings for new EC2 instances. **User data** is a startup script that Ubuntu's cloud-init service runs as root on an instance's first boot. By default, user data does not run on every reboot; the enabled systemd service handles later starts. EC2 limits raw user data to 16 KiB before its transport encoding. [AWS user-data guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html)

1. Open `deploy/user-data.sh` in a text editor and copy the **whole file**, beginning with `#!/bin/bash`.
2. In the launch template, choose Ubuntu 22.04 or 26.04 LTS and an instance type compatible with that AMI. Use the EC2 security group described in the next section.
3. Under **Advanced details → User data**, paste the file as ordinary text. **Do not select the option saying that the entire user data is already base64 encoded.** The compressed text inside the script is an internal payload, not the encoding of the whole script.
4. Save the launch template version. Launch a test instance from that version and allow several minutes for package installation.
5. Check the application or the target group's health status. The installer needs no manual SSH steps, repository URL, AWS credentials, or database.

The script contains all runtime files plus the service and installer. It decodes those files into `/var/lib/cloud-cafe/source` and runs the same `deploy.sh` used for manual deployment. Compression keeps it below the EC2 size limit. Do not edit the encoded payload by hand.

If you do connect to investigate first-boot installation:

```bash
sudo cloud-init status --long
sudo tail -n 100 /var/log/cloud-init-output.log
sudo journalctl -u cloud-cafe -n 80 --no-pager
```

The standalone script is safe to run again. For example, if you copied it to the instance:

```bash
sudo bash ~/cloud-cafe/deploy/user-data.sh
```

If its files were already decoded but package installation failed, retry after fixing network access:

```bash
sudo bash /var/lib/cloud-cafe/source/deploy/deploy.sh
```

## 9. Settings for the later ALB lesson

An **Application Load Balancer (ALB)** accepts browser requests and forwards them to healthy application instances. A **listener** receives connections on a chosen port. A **target group** is the set of instances and the port to which the ALB forwards requests.

```text
Browser → ALB HTTP :80 → target group HTTP :8080 → EC2 / Gunicorn / Flask
                              health check → /health
```

Use these settings when you configure AWS yourself:

| Setting | Value |
| --- | --- |
| ALB scheme | Internet-facing for this browser-based lesson |
| ALB subnets | At least two public subnets in different Availability Zones in the same VPC |
| Listener | HTTP, port **80** |
| Listener default action | Forward to the Cloud Café target group |
| Target type | **Instances** |
| Target protocol and port | **HTTP :8080**, HTTP/1.1 |
| Health-check protocol | **HTTP** |
| Health-check port | **Traffic port** (8080) |
| Health-check path | **/health** |
| Health-check success code | **200** |
| Other health settings | Default interval 30 seconds, timeout 5 seconds, healthy threshold 5, unhealthy threshold 2 are suitable for this exercise |
| Stickiness | Leave disabled for the demonstration |

A health check is a small request the ALB makes to see whether an instance responds. Register the EC2 instance on port 8080 for the single-instance exercise, and ensure its Availability Zone is enabled on the ALB. Wait for the target to become healthy. [AWS health-check documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html)

Use two security groups:

| Security group | Direction | Rule |
| --- | --- | --- |
| ALB security group | Inbound | TCP **80** from the lesson's client IP range, or `0.0.0.0/0` if intentionally making the demo public |
| ALB security group | Outbound | TCP **8080** to the **EC2 security group** |
| EC2 security group | Inbound | TCP **8080** with the **ALB security group ID** as its source |
| EC2 security group | Inbound, optional | TCP **22** from your own public IP for SSH |
| EC2 security group | Outbound | Permit package installation and DNS; the default allow-all outbound rule is simplest for this lesson |

The same port 8080 rule carries both application requests and ALB health checks. Once using the ALB, remove the earlier direct public-IP rule for port 8080 so application traffic enters through the ALB security group. [AWS ALB security-group guide](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-update-security-groups.html)

Open **http://YOUR-ALB-DNS-NAME** and **http://YOUR-ALB-DNS-NAME/health**. There is no `:8080` in the browser's ALB URL: the listener uses port 80. Reload a few times and inspect **Served by**. Requests may go to the same instance, even with more than one healthy target.

## 10. How the Auto Scaling Group uses this application

An **Auto Scaling Group (ASG)** maintains a chosen number of EC2 instances. It creates replacements and additional instances from your launch template. Each fresh Ubuntu instance runs the template's user-data script, installs this exact application, and starts the service.

When configuring the ASG later:

1. Choose the saved launch template **version containing the complete user-data script**.
2. Select subnets in the VPC and Availability Zones served by the ALB. Each instance still needs outbound internet access for installation.
3. Attach the Cloud Café target group. The ASG then registers and deregisters its own instances.
4. For a two-server demonstration, choose desired capacity 2 and minimum capacity 2, with maximum capacity at least 2. Increasing capacity or a scaling policy is what adds more instances; this app does not configure scaling policies.
5. Enable load-balancer health checks for the ASG. Start with a **300-second health-check grace period**, then increase it if installation takes longer in your environment. This gives new instances time to install before the ASG judges them unhealthy.

Keep the same application files and `APP_VERSION` across the group. Leave `SERVER_NAME` unset. Every server has the same menu, and category selections only live in the current browser page, so no shared database or sticky sessions are needed.

Changing a launch template does not rewrite applications on existing instances. After updating the project, rebuild user data, save a new launch template version, point the ASG at that version, and deliberately replace existing instances using an instance refresh when you are ready. [AWS launch-template update guide](https://docs.aws.amazon.com/autoscaling/ec2/userguide/update-auto-scaling-group.html)

## 11. Troubleshooting

| Problem | What to check |
| --- | --- |
| Service will not start | Read `sudo journalctl -u cloud-cafe -n 80 --no-pager`. Check `/opt/cloud-cafe/app.py`, `/opt/cloud-cafe/.venv/bin/gunicorn`, and `/etc/cloud-cafe.env`. Rerun the installer from the uploaded source folder if installation did not finish. |
| Port already in use | Run `sudo ss -ltnp 'sport = :8080'`. Stop a local preview with Ctrl+C before starting the managed service on that machine. |
| Missing Python package | Run `sudo /opt/cloud-cafe/.venv/bin/python -m pip check`. Fix package-download access, then rerun the installer. Do not install application packages into Ubuntu's system Python. |
| Installer rejects Ubuntu 26.04 | An older copy only accepted 22.04. Use the updated installer and regenerate user data after any deployment-script change. Confirm the version with `cat /etc/os-release`. |
| User-data install failed | Check `/var/log/cloud-init-output.log`. Check Ubuntu 22.04 or 26.04, outbound routing, public IP or NAT as appropriate, DNS, and HTTP/HTTPS egress. An ALB is not an outbound gateway. |
| `bash\r` or `$'\r'` errors | A shell script was saved with Windows line endings. Save it as UTF-8 with LF endings, or run `sed -i 's/\r$//' deploy/deploy.sh`, then retry. The supplied scripts use LF. |
| Browser cannot reach the single instance | Confirm service status and local `/health`, then check the public IP, port 8080 inbound rule from your IP, and subnet route. Use `http://PUBLIC_IP:8080`. |
| ALB target is unhealthy | Start with `curl -i http://127.0.0.1:8080/health` on the instance. Confirm HTTP, port 8080, path `/health`, and success code 200. Check the target-health reason in the EC2 console. |
| `Target.Timeout` | Confirm Gunicorn listens on `0.0.0.0:8080`, ALB outbound and EC2 inbound rules allow port 8080, and subnet network ACLs allow request and return traffic. If enabled, check Ubuntu's firewall with `sudo ufw status`. |
| `Target.ResponseCodeMismatch` | Check the exact health path `/health` and HTTP protocol. It should return 200, with no login or redirect. |
| Target is `unused` | Check that it is registered, the listener forwards to this target group, and its Availability Zone is enabled on the ALB. |
| New instances keep being replaced | Look for installation failures and allow enough ASG health-check grace time. Compare the launch template version with the one containing this user data. |
| Same server on every reload | Confirm there are multiple healthy targets and distinct hostnames, and no shared SERVER_NAME override. Check stickiness. Reaching the same target is still possible. |
| Version does not change | Restart the service after editing `/etc/cloud-cafe.env`. A launch template change affects new instances, not existing ones. |

## 12. Update the menu and rebuild deployment files

Edit the list in `menu.py`. In a future RDS lesson, replace the body of **`get_menu()`** with a data lookup returning the same fields (`name`, `description`, `category`, `price`). No database connectivity is implemented now. Keep `/health` independent.

After changing any runtime or deployment file, regenerate the standalone script:

```powershell
.\.venv\Scripts\python.exe tools/build_user_data.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On Ubuntu, use `.venv/bin/python` instead. The builder checks the 16 KiB limit and creates a deterministic archive; tests compare every embedded file with the project. The builder is only needed after edits, not at EC2 startup.

To refresh the upload package from the project directory (PowerShell and Ubuntu both support this `tar` command):

```text
tar --exclude=__pycache__ -czf cloud-cafe.tar.gz app.py menu.py requirements.txt templates static deploy tools tests README.md VERIFICATION.md .gitignore .gitattributes
```

The included verification report describes what was actually tested. Rehearse the Ubuntu installation and ALB/ASG behavior in your account before teaching; those environments were not provisioned by this project.
