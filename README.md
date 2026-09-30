# Build Planner (unofficial)

A free, open-source skill tree, mutation and build planner for the current version of the game. Live at **https://w3planner.pages.dev**.

- Skill trees with the game's own prerequisites, values and tooltip formulas
- Ability slots, mutagen sockets and mutation slots that unlock like in the game
- Mutations with research costs, prerequisites and the active-mutation colour rule
- Builds are stored entirely in the URL: share a link, no accounts, no backend
- No cookies, no analytics, no third-party requests
- Locked down by default: a strict Content-Security-Policy in `_headers` blocks anything loading from other sites

## Offline version

Every release also has an offline download for Windows PC (it runs in your browser and needs no install): see [Releases](https://github.com/viv4-web/w3planner/releases). It is built from this repository by `tools/make_offline.py`, so it always contains exactly the same `index.html` as the website. The offline copy can open build links but does not create them. See [RELEASING.md](RELEASING.md).

## Feedback

Found a wrong number or a bug? [Open an issue](https://github.com/viv4-web/w3planner/issues/new/choose) and include the build's share link.

## How it's built

A static site: plain HTML, CSS and JavaScript with no build step and no dependencies. All data (names, descriptions, values, costs, rules) is extracted from the game's own files and scripts and embedded in `index.html`.

The repository ships with placeholder artwork that I drew myself (`art/`), so it runs as-is: `python3 -m http.server`, then open http://localhost:8000. The live site additionally shows the game's own artwork, which is **not** included here and is loaded from a separate folder.

## Deploy

Deployed to Cloudflare Pages by direct upload of the site folder (`index.html`, the other pages, `pages.css`, `_headers`, `fonts/` and an image folder).

## License

Code and placeholder artwork: MIT (see [LICENSE](LICENSE)). The license does not cover game names, text or data, or the game's own artwork, which belong to CD PROJEKT S.A.

This is an unofficial fan work and is not approved/endorsed by CD PROJEKT RED.
