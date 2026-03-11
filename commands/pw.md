Push to remote, then watch the resulting CI run.

Steps:
1. **Push** using the same logic as the `p` phase in `/c`:
   - Check if branch has a remote tracking branch (`git rev-parse --abbrev-ref @{u}`)
   - If yes: `git push`
   - If no: `gpu` to push to user branch namespace
   - If the most recent commit is an amend (check if HEAD was force-pushed or user says so), use force push (`git push -f` / `gpuf`)
2. **Watch** per `/w`: find the most recent CI run on this branch and `gh run watch` it
