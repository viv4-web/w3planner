# Releasing

The website and the offline download are built from the same files, so they cannot drift apart.

## What is the same, and what differs

| | Website | Offline download |
|---|---|---|
| `index.html` | this repository's file (the live site adds the game's art) | exactly this repository's file |
| `config.js` | `mode: "online"` | `mode: "offline"` plus the website address for share links |
| Artwork | the game's art on the live site | placeholder art from `art/` |
| `privacy.html` | hosting paragraph | offline paragraph |
| Build links | can create and open | can only open (build with `--allow-share` to change) |

## Steps for a new release

1. Change the site files (`index.html`, the pages, and so on). The version number is `APP_VERSION` near the top of the script in `index.html`; bump it.
2. Commit to GitHub.
3. Publish a GitHub Release whose tag is the version (for example `v23`). The **Offline package** workflow builds `BuildPlanner-offline-v23.zip` from the repository and attaches it to the release.
4. Deploy the website (Cloudflare Pages: upload the site folder).

The workflow also publishes `SHA256SUMS.txt` with the zip, so people can verify their download.

## Handy commands

- Build the offline zip yourself: `python tools/make_offline.py` (creates `dist/BuildPlanner-offline-<version>.zip`).
- Check that the live site runs the same code as the repository: `python tools/make_offline.py --compare path/to/live/index.html`.

## Rules the tooling enforces

- The offline package never contains the game's artwork (`assets/`) unless you pass `--allow-game-art`.
- The build stops if `index.html` refers to a file that is not in the package, or if the privacy page wording it patches has changed.
