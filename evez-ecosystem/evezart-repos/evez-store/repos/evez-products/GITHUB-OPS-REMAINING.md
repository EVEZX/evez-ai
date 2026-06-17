# GitHub Ops — 4 Repos Need Manual Creation

Your fine-grained PAT can't create new repos. Create these manually:

1. Go to https://github.com/organizations/EvezArt/repositories/new
2. Create each:

   - **evez-liminal** — Security video game on EVEZ-OS substrate
   - **evez-products** — Digital products, blueprints, workshop kits
   - **evez-watchdog** — Self-healing service monitor
   - **evez-store** — Revenue hub for EVEZ ecosystem

3. After creating, run from server:
   ```bash
   cd /home/openclaw/.openclaw/workspace/repos
   for repo in evez-liminal evez-products evez-watchdog evez-store; do
     cd $repo
     git remote set-url origin https://github.com/EvezArt/$repo.git
     git push -u origin HEAD
     cd ..
   done
   ```

OR: Generate a classic PAT with `repo` scope at:
https://github.com/settings/tokens/new
Then I can create repos automatically.
