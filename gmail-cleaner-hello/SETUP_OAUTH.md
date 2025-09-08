# 🔐 OAUTH SETUP REMINDER

## ⚠️ REQUIRED: Set up Google OAuth before continuing development

Your Gmail Storage Manager app needs Google OAuth credentials to access Gmail API.

---

## 📋 Quick Checklist
- [ ] Go to Google Cloud Console
- [ ] Create new project  
- [ ] Enable Gmail API
- [ ] Create OAuth2 credentials
- [ ] Download JSON file
- [ ] Move to credentials folder
- [ ] Test authentication

---

## 🔗 Step-by-Step Instructions

### 1. Open Google Cloud Console
**Link**: https://console.cloud.google.com/

### 2. Create New Project
- Click "Select a project" → "New Project"
- **Project name**: `Gmail Storage Manager`
- Click "Create"

### 3. Enable Gmail API
- Go to **"APIs & Services"** → **"Library"**
- Search: `Gmail API`
- Click on Gmail API → Click **"Enable"**

### 4. Configure OAuth Consent Screen
- Go to **"APIs & Services"** → **"OAuth consent screen"**
- Choose **"External"** (unless you have Google Workspace)
- Fill in required fields:
  - **App name**: `Gmail Storage Manager`
  - **User support email**: Your email
  - **Developer contact**: Your email
- **Scopes**: Skip for now (we'll add programmatically)
- **Test users**: Add your Gmail address

### 5. Create OAuth2 Credentials
- Go to **"APIs & Services"** → **"Credentials"**
- Click **"Create Credentials"** → **"OAuth client ID"**
- **Application type**: `Desktop application`
- **Name**: `Gmail Storage Manager Desktop`
- Click **"Create"**

### 6. Download Credentials
- After creation, you'll see a download button (⬇️)
- Click to download the JSON file
- File will be named like: `client_secret_123456-abcdef.apps.googleusercontent.com.json`

### 7. Move File to Project
```bash
# Navigate to your project
cd ~/Documents/VIBE_CODING/hello_world_projects/gmail-cleaner-hello

# Move and rename the downloaded file (replace with your actual filename)
mv ~/Downloads/client_secret_*.json ./credentials/client_secret.json
```

### 8. Verify File Location
```bash
ls -la credentials/
# Should show: client_secret.json
```

---

## ✅ Test Authentication (After Setup)
```bash
cd ~/Documents/VIBE_CODING/hello_world_projects/gmail-cleaner-hello
python gmail_client.py
```

**Expected behavior**:
1. Opens browser for Google sign-in
2. Shows permission request for Gmail access
3. Click "Allow" (you may see "unsafe app" warning - click "Advanced" → "Go to Gmail Storage Manager")
4. Returns to terminal with success message
5. Shows your Gmail email address and message count

---

## 🛡️ Security Notes
- ✅ `client_secret.json` is in `.gitignore` (won't be committed)
- ✅ Keep this file secure and private
- ✅ First run will show Google security warnings (normal for unverified apps)
- ✅ For personal use, you can bypass warnings safely

---

## 🚨 Troubleshooting

### "File not found" error
- Check file path: `./credentials/client_secret.json`
- Verify JSON format (should start with `{"installed":`)

### "Invalid client" error  
- Re-download credentials from Google Cloud Console
- Make sure Gmail API is enabled

### Browser doesn't open
- Copy the URL from terminal and paste in browser manually

---

## 📞 When Ready to Continue

After completing OAuth setup, tell the assistant:

> "I've completed the OAuth setup for Gmail Storage Manager. Ready to continue development!"

The assistant will then help you:
1. Test the authentication
2. Build the email downloader
3. Create the CLI interface
4. Complete the MVP

---

## 📍 Current Location
```
/Users/folstein/Documents/VIBE_CODING/hello_world_projects/gmail-cleaner-hello/
```

## 🎯 Next File Needed
```
./credentials/client_secret.json
```

**File should contain**:
```json
{
  "installed": {
    "client_id": "...",
    "project_id": "gmail-storage-manager",
    "client_secret": "GOCSPX-...",
    ...
  }
}
```

---

*This file will be here when you return! 📌*
