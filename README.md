## Pushing the Project to GitHub

Follow these steps to upload the project to GitHub.

---

### Step 1 — Initialize Git

Open terminal in your project folder and run:

git init

---

### Step 2 — Add .gitignore File

Create a file named:

.gitignore

Add the following content:

.venv/
.env
__pycache__/
results.csv
*.pyc
.vscode/

This prevents uploading:

- Virtual environment
- API keys
- Temporary files
- Generated outputs

---

### Step 3 — Generate requirements.txt

Run:

pip freeze > requirements.txt

This records all dependencies required to run the project.

---

### Step 4 — Add Files to Git

git add .

---

### Step 5 — Commit the Project

git commit -m "Initial commit: MarketPulse LLM-based financial news classification"

---

### Step 6 — Create Repository on GitHub

Go to:

https://github.com/new

Fill:

Repository name: MarketPulse  
Visibility: Public

Do NOT check:

- Add README
- Add .gitignore
- Add license

Click:

Create repository

---

### Step 7 — Connect Local Project to GitHub

Replace YOUR_USERNAME with your GitHub username.

git remote add origin https://github.com/YOUR_USERNAME/MarketPulse.git

---

### Step 8 — Push the Code

git branch -M main

git push -u origin main

---

### Step 9 — Verify Upload

Open:

https://github.com/YOUR_USERNAME/MarketPulse

You should see:

app.py  
prompt.py  
README.md  
requirements.txt  
.gitignore  
moneycontrol_100.csv

You should NOT see:

.venv  
.env  
results.csv

---

## Updating the Repository Later

If you make changes:

git add .
git commit -m "Update project"
git push
