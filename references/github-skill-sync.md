# GitHub Skill Sync

How to push the `ai-lab-talent-crawler` skill (or any similar skill) to a remote GitHub repository without leaking collected data.

## Preconditions

- The user has provided a GitHub repository URL
- The repository already exists on GitHub

## Steps

1. **Clone the remote repo**

   ```bash
   git clone https://github.com/<user>/<repo>.git
   cd <repo>
   ```

2. **Copy skill files into the repo**

   Copy everything from the local skill directory **except** the `output/` directory:

   ```bash
   cp -r /c/Users/Administrator/AppData/Local/hermes/skills/ai-lab-talent-crawler/SKILL.md .
   cp -r /c/Users/Administrator/AppData/Local/hermes/skills/ai-lab-talent-crawler/labs.yaml .
   cp -r /c/Users/Administrator/AppData/Local/hermes/skills/ai-lab-talent-crawler/references/ .
   cp -r /c/Users/Administrator/AppData/Local/hermes/skills/ai-lab-talent-crawler/scripts/ .
   ```

3. **Add `.gitignore` to exclude `output/`**

   ```
   output/
   ```

   This keeps collected personal data local and prevents it from being published.

4. **Set git identity (if missing)**

   ```bash
   git config user.email "ai-lab-talent-crawler@example.com"
   git config user.name "AI Lab Talent Crawler"
   ```

   Use a repository-local config if the user has no global identity.

5. **Commit and push**

   ```bash
   git add -A
   git commit -m "Update skill"
   git push origin main
   ```

## Pitfalls

- Do not run `rm -rf output/` unless the user explicitly asks for it. If the user says "don't upload output but don't delete it", use `.gitignore` instead.
- If the GitHub push fails with a timeout, check network connectivity before retrying.
- If the user has a GitHub token, use the credential manager instead of embedding the token in the remote URL.

## Restoring from GitHub

```bash
git clone https://github.com/<user>/<repo>.git
cp -r <repo>/ /c/Users/Administrator/AppData/Local/hermes/skills/ai-lab-talent-crawler/
```
