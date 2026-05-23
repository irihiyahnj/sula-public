---
id: 2026-05-23T06-10-12Z--operation-rename-public-repo-to-sula-vector
time: 2026-05-23T06:10:12Z
kind: operation
refs: [2026-05-23T06-04-37Z--operation-public-release-v1-0]
tags: [public-release, github, rename, canonical-url]
author: jing
old_url: https://github.com/irihiyahnj/sula-public
new_url: https://github.com/irihiyahnj/sula-vector
---
Renamed the public canonical repo from sula-public to sula-vector.

Reason: sula-public was a historical name from when this repo paired with a
private counterpart. With v1.0 published as the recommended path forward,
the cleaner name sula-vector matches the product name, the release tag
(sula-vector-v1.0.0), and the directory tools/sula_vector/. The shorter
name 'sula' was unavailable (occupied by an unrelated private repo on the
same account).

Effect:
- New URL: https://github.com/irihiyahnj/sula-vector  (HTTP 200)
- Old URL: https://github.com/irihiyahnj/sula-public  (HTTP 301 → new URL)
- Existing git clones using the old URL continue to work via GitHub redirect
- README clone instructions updated to use the new URL

Adoption command (current):

  git clone https://github.com/irihiyahnj/sula-vector.git
  cp -r sula-vector/tools/sula_vector/ my-project/tools/sula_vector/
  cp sula-vector/tools/sula_vector/AGENTS.md my-project/AGENTS.md
  cp sula-vector/tools/sula_vector/principles/*.md my-project/fragments/
  python3 my-project/tools/sula_vector/render.py my-project --for-agent

This is a substrate-level operation (B7): GitHub provides the rename and
redirect; Sula does not need to invent anything for it. Idempotent at the
URL level — running again is a no-op since the rename has already happened.
