# Security

This is a static website plus a downloadable copy of it. There are no accounts, no server code and no stored user data.

## How build links are handled

A build link holds only numbers (levels, slots, mutagens, mutations) after the `#`. The planner treats it as untrusted: it checks the length and the characters, rejects anything malformed, and limits every value to what the game allows. Link data is never run as code and never inserted into the page as HTML. This is covered by a test that opens hundreds of malformed and hostile links.

## Downloads

Only download the offline version from this repository's Releases page. Each release includes `SHA256SUMS.txt`; compare it with the checksum of your download. Copies from anywhere else cannot be trusted, because anyone can modify and re-share the files.

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use GitHub's private reporting: the **Security** tab, then **Report a vulnerability**. (Repository owner: turn it on under Settings, Code security, Private vulnerability reporting.)
