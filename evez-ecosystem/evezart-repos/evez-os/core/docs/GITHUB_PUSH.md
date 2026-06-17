# Push to GitHub

This repo is prepared locally. To publish it, you (on your phone/desktop) log into GitHub and create a new repository.

Then, on any machine with git:

```bash
git init
git add .
git commit -m "initial import: game agent infra + maps + continuity"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

If you want it private, set the repo visibility to **Private** when creating it.
