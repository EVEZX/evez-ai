# Auth Setup for Steven — Do These 3 Things

## 1. ClawHub (Skills)
```bash
clawhub login
```

## 2. Twitter (Posting)
```bash
xurl auth oauth2
```
If it says "no apps" first, go to https://developer.x.com, create an app, then run:
```bash
xurl auth apps add
# Enter your API Key and API Secret when asked
xurl auth oauth2
```

## 3. Gmail (Email)
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" → "OAuth client ID" → "Desktop app"
3. Download the JSON
4. Save it as: `~/Downloads/credentials.json`
5. Run:
```bash
gog auth credentials ~/Downloads/credentials.json
gog auth add Rubikspubes70@gmail.com --services gmail,calendar
```

---

## Quick Test
After each, tell me and I'll test:
- `clawhub whoami`
- `xurl whoami`  
- `gog gmail list`

Run any of these and come back. 🔥