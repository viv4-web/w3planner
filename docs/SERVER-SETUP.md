> **Update: what is different from the plan below (read this first).**
> - The game art stays a **plain folder** on the server, `~/work/w3planner-art`. There is **no private art repository**, so ignore the second deploy key, the `github-w3art` host and the art-repo clone in Part 5 and Part 7.
> - The GitHub settings (ruleset, deploy key, reporting, security baseline) were applied by **Claude Code through the GitHub API**, not by hand. The daily token has no Administration permission on purpose.
> - **tmux is optional.** Run `claude --allow-dangerously-skip-permissions` from `~/work/w3planner` for bypass mode on demand.
> - To get files onto the server, **drag them into VSCodium's file explorer** while connected as `w3dev`; no `scp` needed.

# Server setup: a dedicated workspace for Claude Code

For: your Hetzner server (Ubuntu 24.04). Time: about 45 minutes. Status: **written without access to your server, so every command is untested**; the "Not verified" list at the end says which parts I am least sure of.

## What your server output showed

| Item | Finding |
|---|---|
| System | Ubuntu 24.04.4, 4 CPUs, 7.6 GiB RAM (5.3 GiB available), 86 GB free disk |
| Login users | only `vivek`, who is in the **`sudo`** and **`docker`** groups |
| Hostname | `crawliq-prod`, which suggests this is a production machine |
| Home folders | `/home/vivek` is `755` (readable by every account); `~/.claude` is `775` |
| Ports listening | 22, 53, 80, 443, 3000, 8000-8003, 8080 and five high ports. I could not tell which are open to the internet |
| Firewall | the command printed nothing, so unknown |
| Software | git 2.43, Node 20.20, Python 3.12, Docker 29.5, tmux, curl, Claude Code 2.1.284. Missing: `jq`, `unzip` |

## Why a separate user

1. **The `docker` group is effectively root.** Anyone in it can start a container that mounts the whole disk. So "my Claude Code instances have no root" is only true if none of them can run `docker` or `sudo`.
2. **Per-directory permissions inside Claude Code are application rules, not operating-system walls.** All your instances run as the same Linux user `vivek`, so any of them can read anything `vivek` can read, including `~/.claude` (where the other instances' sign-ins live).
3. **`/home/vivek` is readable by every account on the machine.** A compromised web app running as another user could read it.
4. **It looks like a production machine.** Test browsers can eat memory, and a runaway job could starve a live service.

The fix is a second Linux account, `w3dev`: no sudo, no docker, a private home, its own Node and Python, its own tokens, and a memory and CPU cap. Claude Code for this project runs only as `w3dev`.

## Part 1: on your PC: make a login key for `w3dev`

Windows (PowerShell) or Mac/Linux terminal:

```
ssh-keygen -t ed25519 -f ~/.ssh/id_w3dev -C "w3dev@hetzner"
```

Show the public half and keep it for the next part (it is one line starting with `ssh-ed25519`):

```
cat ~/.ssh/id_w3dev.pub
```

(On Windows PowerShell use `type $env:USERPROFILE\.ssh\id_w3dev.pub`.)

## Part 2: on the server, as `vivek`, once (needs sudo)

**Look before changing anything:**

```bash
# 1. Which ports face the internet (0.0.0.0 or [::]) and which are local only (127.0.0.1)?
ss -tln | awk 'NR>1 {print $4}' | sort -u
# 2. Is a firewall active on the machine itself? (Hetzner may also have one in its console.)
sudo ufw status verbose 2>&1 | head -5
# 3. Does sudo ask for a password? If this prints nothing, sudo is passwordless: a bigger risk.
sudo -k; sudo -n true 2>&1 | head -1
# 4. Does anything besides you use files under /home/vivek?
ps -eo user:20,args | grep "/home/vivek" | grep -v grep | awk '{print $1}' | sort | uniq -c
# 5. Which containers publish ports?
docker ps --format '{{.Names}}  {{.Ports}}'
```

**Create the account and tools:**

```bash
sudo apt update
sudo apt install -y jq unzip python3-venv
sudo adduser --disabled-password --gecos "" w3dev
sudo chmod 700 /home/w3dev
id w3dev            # the groups must NOT include sudo or docker
```

**Let `w3dev` log in with the key from Part 1** (paste your public key line in place of the placeholder):

```bash
sudo install -d -m 700 -o w3dev -g w3dev /home/w3dev/.ssh
echo "PASTE THE ssh-ed25519 LINE HERE" | sudo tee /home/w3dev/.ssh/authorized_keys >/dev/null
sudo chown w3dev:w3dev /home/w3dev/.ssh/authorized_keys
sudo chmod 600 /home/w3dev/.ssh/authorized_keys
```

**Cap what `w3dev` can use**, so test runs cannot starve your live services:

```bash
W3UID=$(id -u w3dev)
sudo mkdir -p /etc/systemd/system/user-$W3UID.slice.d
printf '[Slice]\nMemoryMax=3G\nMemoryHigh=2500M\nCPUQuota=200%%\nTasksMax=2000\n' | sudo tee /etc/systemd/system/user-$W3UID.slice.d/limits.conf
sudo systemctl daemon-reload
```

**Optional but recommended: stop other accounts reading your home.** Only do this if check 4 above showed that nothing else needs it:

```bash
chmod 750 /home/vivek
chmod 700 ~/.claude
# If a site or service breaks, undo with:  chmod 755 /home/vivek
```

## Part 3: log in as `w3dev` and set up the tools

From your PC:

```
ssh -i ~/.ssh/id_w3dev w3dev@YOUR-SERVER
```

Then, on the server as `w3dev`:

```bash
# Node in this account only (the system Node 20 stays untouched for your other projects)
curl -fsSL https://fnm.vercel.app/install | bash
exec bash -l
fnm install --lts && fnm default lts-latest
node -v

# Python: Ubuntu 24.04 blocks system-wide pip, so use a virtual environment
python3 -m venv ~/venv
. ~/venv/bin/activate
pip install --upgrade pip

# Confirm the limits are applied to this account
systemctl show user-$(id -u).slice -p MemoryMax -p CPUQuota
```

**Claude Code:** install it the way you did for `vivek` (run `type claude` and `claude --version` as `vivek` to see how), or follow Anthropic's current install page. On a machine with no browser, signing in normally shows a link to open on another device. Sign in once as `w3dev`.

## Part 4: browser support libraries (as `vivek`, needs sudo)

Do this after the project is cloned and `pip install -r requirements.txt` has run in the `w3dev` venv (Part 7 below), because it uses Playwright from that venv:

```bash
sudo /home/w3dev/venv/bin/python -m playwright install-deps chromium firefox webkit
```

Then, as `w3dev`:

```bash
python -m playwright install chromium firefox webkit
```

The test runner currently checks only Chromium. Adding Firefox and WebKit is a good first task for Claude Code, and it closes the gap I could not test from my side.

## Part 5: GitHub access with the smallest possible permissions

As `w3dev`, make **two** keys, one per repository. GitHub deploy keys work for one repo each.

```bash
ssh-keygen -t ed25519 -C "w3dev public repo"        -f ~/.ssh/id_w3_public -N ""
ssh-keygen -t ed25519 -C "w3dev art repo (read-only)" -f ~/.ssh/id_w3_art    -N ""
cat ~/.ssh/id_w3_public.pub
cat ~/.ssh/id_w3_art.pub
```

On GitHub:
- **Public repo** `viv4-web/w3planner`: Settings, Deploy keys, Add deploy key, paste the first key, **tick "Allow write access"**.
- **Private art repo** `viv4-web/w3planner-art` (create it first, private): Deploy keys, paste the second key, **leave write access off**.
- Turn on **branch protection or a ruleset** for `main` on the public repo (require a pull request), so the write key cannot push straight to `main`.

Tell SSH which key belongs to which repo, `nano ~/.ssh/config`:

```
Host github-w3
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_w3_public
  IdentitiesOnly yes

Host github-w3art
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_w3_art
  IdentitiesOnly yes
```

```bash
chmod 600 ~/.ssh/config
mkdir -p ~/work && cd ~/work
git clone git@github-w3:viv4-web/w3planner.git
git clone git@github-w3art:viv4-web/w3planner-art.git
git config --global user.name  "YOUR NAME"
git config --global user.email "YOUR-ID+viv4-web@users.noreply.github.com"   # GitHub's private address, so no personal email
```

**Check the protection works:** make a throwaway commit and try `git push origin HEAD:main`. GitHub must refuse it. If it accepts, fix the protection before going further. I am not certain how deploy keys interact with branch rules, so this test matters.

## Part 6: the Cloudflare token and a deploy wrapper

**Create a narrow token** in the Cloudflare dashboard (labels may have moved): My Profile, API Tokens, Create Token, Custom token. Permission: **Account, Cloudflare Pages, Edit**. Account resources: your account only. **No zone or DNS permissions.** Copy it once. Your Account ID is shown in the dashboard sidebar.

As `w3dev`:

```bash
mkdir -p ~/.config/w3planner && chmod 700 ~/.config/w3planner
nano ~/.config/w3planner/env
```

Put exactly two lines in it:

```
CLOUDFLARE_API_TOKEN=paste-the-token
CLOUDFLARE_ACCOUNT_ID=paste-the-account-id
```

```bash
chmod 600 ~/.config/w3planner/env
```

**Do not** put these in `.bashrc`. A small wrapper loads them only when you deploy:

```bash
mkdir -p ~/bin
cat > ~/bin/w3-deploy <<'EOF'
#!/bin/sh
set -e
set -a; . "$HOME/.config/w3planner/env"; set +a
cd "$HOME/work/w3planner"
. "$HOME/venv/bin/activate"
exec python3 tools/deploy.py --art-dir "$HOME/work/w3planner-art" "$@"
EOF
chmod 700 ~/bin/w3-deploy
```

Use `~/bin/w3-deploy --dry-run` first (builds and checks, uploads nothing), then `~/bin/w3-deploy`.

**Be realistic about this:** anything that can run shell commands as `w3dev` can read `w3dev`'s files, including that token. The real protection is that the token can do very little (Pages only) and that everything else on the machine is out of reach.

## Part 7: get the project in (when the export zips are ready)

From your PC, copy the two zips I hand you to the server:

```
scp -i ~/.ssh/id_w3dev w3planner-source-v24.zip w3planner-art-private-v24.zip w3dev@YOUR-SERVER:
```

On the server as `w3dev`:

```bash
cd ~/work/w3planner
git checkout -b restructure-v24
git rm -r -q --ignore-unmatch .
unzip -o ~/w3planner-source-v24.zip
sh tools/install_hooks.sh                 # installs a check that blocks committing game art
git add -A && git commit -m "Restructure into a source project (v24)"
git push -u origin restructure-v24        # then open a pull request on GitHub

cd ~/work/w3planner-art
unzip -o ~/w3planner-art-private-v24.zip
git add -A && git commit -m "Game art for the live site" && git push
```

Then set up the tools once:

```bash
cd ~/work/w3planner && . ~/venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python tests/run_all.py --quick          # should end with: N checks: N passed, 0 failed
```

## Part 8: Claude Code permissions (starter)

Put this in `~/work/w3planner/.claude/settings.json`. I wrote it from memory of Claude Code's settings format, so **check it inside a session with the `/permissions` command**:

```json
{
  "permissions": {
    "allow": [
      "Bash(python3 tests/run_all.py:*)",
      "Bash(python3 tools/build.py:*)",
      "Bash(python3 tools/check_no_game_art.py:*)",
      "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)",
      "Bash(git add:*)", "Bash(git commit:*)", "Bash(git checkout -b:*)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(~/bin/w3-deploy:*)"
    ],
    "deny": [
      "Bash(sudo:*)",
      "Bash(git push --force:*)",
      "Bash(rm -rf:*)",
      "Read(~/.config/w3planner/**)",
      "Read(~/.ssh/**)"
    ]
  }
}
```

Never run Claude Code in any mode that skips permission prompts on this machine.

## Part 9: daily use

```bash
ssh -i ~/.ssh/id_w3dev w3dev@YOUR-SERVER
tmux new -s w3            # a dropped connection will not kill your session
cd ~/work/w3planner && . ~/venv/bin/activate && claude
# detach: Ctrl-b then d.   Come back later: tmux attach -t w3
```

## Part 10: check the walls are real (as `vivek`)

```bash
sudo -l -U w3dev                          # expect: "not allowed to run sudo"
id w3dev                                  # expect: only its own group
sudo -u w3dev ls /home/vivek              # expect: Permission denied (after the chmod 750)
sudo -u w3dev ls /home/vivek/.claude      # expect: Permission denied
sudo -u w3dev docker ps                   # expect: permission denied on the Docker socket
```

If any of these succeed when they should be refused, stop and fix that before using the account.

## Decisions that stay with you

- **The `docker` group for `vivek`.** Your existing instances can reach root through it. Removing yourself (`sudo gpasswd -d vivek docker`) means using `sudo docker` from then on. It is your call.
- **Open ports.** Ports 3000 and 8000-8003 and 8080 look like app or development ports. Check Part 2's first command. Anything on `0.0.0.0` is reachable unless Hetzner's cloud firewall blocks it. Docker can also publish ports around the machine's own firewall.
- **A separate small server.** If `crawliq-prod` really is production, a small extra Hetzner server for this workspace is the cleanest wall. It should cost a few euros a month (check current pricing). The steps above work unchanged on a new machine.
- **Node 20.** As far as I know it is out of support since spring 2026. Not urgent, but your other projects should move.

## Roll back

```bash
W3UID=$(id -u w3dev)                                    # do this first: the id disappears with the account
sudo rm -r /etc/systemd/system/user-$W3UID.slice.d && sudo systemctl daemon-reload
sudo deluser --remove-home w3dev
```

Also delete the two GitHub deploy keys and the Cloudflare token.

## Not verified (tell Claude Code to check these against current docs)

- How Claude Code installs and signs in on a machine with no browser.
- That the systemd limits file takes effect (Part 3 has a command that shows it).
- The exact Cloudflare dashboard labels for creating the token.
- How GitHub deploy keys interact with branch protection (Part 5 has a test).
- The Claude Code settings syntax in Part 8.
- `playwright install-deps` run through `sudo` from another user's virtual environment.
- `tools/deploy.py`: never run against Cloudflare. Check `npx wrangler pages deploy --help` before the first real deploy.
