# Build Planner (unofficial)

A free, open-source skill, mutation and build planner for the new skill system of The Witcher 3. Live at **https://w3planner.pages.dev**.

- Skill trees with the game's own prerequisites, values and tooltip formulas
- Ability slots, mutagen sockets and mutation slots that unlock like in the game
- Nine regular and 27 special mutagens; mutations with costs, prerequisites and the colour rule
- Builds are stored entirely in the link: share it, bookmark it. No accounts, no cookies, no analytics, no third-party requests
- Locked down by default: a strict Content-Security-Policy blocks anything loading from other sites

## Run it yourself

```
pip install -r requirements.txt          # only needed for the tests
python tools/build.py --variant placeholder --out dist/placeholder
python tools/serve.py --dir dist/placeholder --port 8080     # then open http://127.0.0.1:8080/
```

The repository ships with placeholder artwork that I drew myself, so it runs as it is. The live site additionally shows the game's own artwork, which is not included here.

## Offline version

Every release has an offline download for Windows PC (it runs in your browser and needs no install): see [Releases](https://github.com/viv4-web/w3planner/releases). It is built from this repository by `tools/make_offline.py`, so it runs exactly the same code as the website. It can open build links but does not create them. See [RELEASING.md](RELEASING.md).

## Feedback

Found a wrong number or a bug? [Open an issue](https://github.com/viv4-web/w3planner/issues/new/choose) and include the build's share link.

## For contributors

[CLAUDE.md](CLAUDE.md) explains the layout, the rules and the commands. [SECURITY.md](SECURITY.md) explains how to report a vulnerability.

## License

Code and placeholder artwork: MIT (see [LICENSE](LICENSE)). The license does not cover game names, text or data, or the game's own artwork, which belong to CD PROJEKT S.A.

This is an unofficial fan project and is not approved or endorsed by CD PROJEKT RED.
