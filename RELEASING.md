# Releasing

The website and the offline download are built from the same source, so they cannot drift apart.

| | Website | Offline download |
|---|---|---|
| Code | `src/` + `data/` | identical |
| `config.js` | `mode: "online"` | `mode: "offline", share: false` |
| Artwork | the game's art (live site) | placeholder art |
| Build links | creates and opens | opens only (`--allow-share` to change) |

## Steps
1. Work on a branch. Run `python tests/run_all.py` until it passes.
2. Bump `APP_VERSION` at the top of `src/app.js` and update `static/help.html` if behaviour changed.
3. Open a pull request and merge it (the `CI` workflow runs the same tests).
4. Publish a GitHub Release tagged with the version. The `Offline package` workflow builds `BuildPlanner-offline-<version>.zip` and `SHA256SUMS.txt` and attaches them.
5. Deploy the live site from the server: `python tools/deploy.py --art-dir ~/work/w3planner-art` (try `--dry-run` first).

## Rules the tooling enforces
- The offline package never contains the game's artwork unless `--allow-game-art` is passed.
- `tools/check_no_game_art.py` fails if any file is one of the game's images.
- The build stops if an art slot, data file or token is missing.
