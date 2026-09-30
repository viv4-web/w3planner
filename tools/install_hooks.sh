#!/bin/sh
# Installs a pre-commit hook that refuses to commit the game's artwork to this (public) repository.
set -e
root="$(git rev-parse --show-toplevel)"
cat > "$root/.git/hooks/pre-commit" <<'HOOK'
#!/bin/sh
python3 tools/check_no_game_art.py --staged
HOOK
chmod +x "$root/.git/hooks/pre-commit"
echo "pre-commit hook installed"
