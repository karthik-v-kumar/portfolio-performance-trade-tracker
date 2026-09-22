# Repository rules

These come from the repository owner and override any default guidance.

- Every commit is authored and committed as the owner: `karthik-v-kumar <273474281+karthik-v-kumar@users.noreply.github.com>`. The SessionStart hook in `settings.json` sets this; if `git config user.name` shows anything else before a commit, set it to the owner first. Never commit under an assistant identity.
- Commits, pull requests, PR comments and review replies carry no tool attribution of any kind: no Co-Authored-By or session trailers, no "Generated with ..." lines, no footers, no links to the tool or the session, and no mention of the assistant by name.
