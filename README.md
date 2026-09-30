# Build Planner (unofficial)

A free, open-source skill tree, mutation and build planner for the current version of the game. Live at **https://w3planner.pages.dev**.

- Skill trees with the game's own prerequisites, values and tooltip formulas
- Ability slots, mutagen sockets and mutation slots that unlock like in the game
- Mutations with research costs, prerequisites and the active-mutation colour rule
- Builds are stored entirely in the URL: share a link, no accounts, no backend
- No cookies, no analytics, no third-party requests

## Feedback

Found a wrong number or a bug? [Open an issue](https://github.com/viv4-web/w3planner/issues/new/choose) and include the build's share link.

## How it's built

A static site: plain HTML, CSS and JavaScript with no build step and no dependencies. All data (names, descriptions, values, costs, rules) is extracted from the game's own files and scripts and embedded in `index.html`.

The game artwork (`assets/`) is **not** included in this repository. It is extracted from the game files and uploaded only to the host. To run the site locally with art, extract it yourself from your own copy of the game.

## Deploy

Deployed to Cloudflare Pages by direct upload of the site folder (`index.html`, the other pages, `pages.css`, `_headers`, `fonts/`, `assets/`).

## License

Code: MIT (see [LICENSE](LICENSE)). The license does not cover game artwork, text or data, which belong to CD PROJEKT S.A.

This is an unofficial fan work and is not approved/endorsed by CD PROJEKT RED.
