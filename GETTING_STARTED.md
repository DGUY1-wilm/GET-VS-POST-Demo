# Getting Started: See GET vs POST for Yourself

**No technical background needed.** This guide walks you through everything one small step at a time. It takes about 15 minutes, and nothing needs to be installed except Python. There are no accounts to create and no passwords to find.

---

## What is this about?

Every time you click a button on a website, such as logging in, searching, or buying something, your browser sends a **request** to a server. There are two common kinds:

- **GET** is like writing a message on a **postcard**. Everything you write is visible on the outside, so anyone who handles the postcard can read it.
- **POST** is like putting your message in a **sealed envelope**. The envelope hides the contents from casual view.

One important catch: **neither one is locked.** On a plain (non-encrypted) connection, someone determined can still open the envelope. The real lock on the web is called **HTTPS**, which is the padlock you see in your browser's address bar.

So why does the difference matter? Because the postcard (GET) ends up written down in a lot of places: your browser history, the website's records, and more. If your password is on that postcard, it gets copied everywhere. Security analysts look at those records every day, and this project shows you exactly what they see.

### What you'll do

1. Run a tiny practice website **on your own computer**.
2. Log in with a **fake** account using both methods.
3. See the difference in your browser's address bar.
4. Look at the server's record book (called the **access log**).
5. Run a scanner that reads the log the way a security analyst would and flags suspicious activity.

### Is it safe?

Yes. The practice website only runs on **your own computer** and can't be reached by anyone else. It uses a **fake** login, so there are no real accounts. Just follow one rule:

> **Only type the fake login (`demo` and `demo123`). Never type a real password into this practice site.** The whole point is that it records and shows what you type.

---

## Before you start

You'll need:

- A computer (Windows or Mac)
- A web browser (Chrome, Edge, Firefox, or Safari)
- About 15 minutes

---

## Step 1: Put the project in a folder

1. Download the project files into a **new folder** on your computer. Call it `get-vs-post-demo`.
2. You should see these files inside: `demo_server.py`, `log_analyzer.py`, and `sample_access.log`.

---

## Step 2: Install Python

Python is the free language this project is written in. Your computer needs it to run the practice site.

**Check if you already have it:**

1. Open a **terminal** (a window where you type commands):
   - **Windows:** press the Windows key, type `cmd`, and press Enter.
   - **Mac:** press Cmd + Space, type `Terminal`, and press Enter.
2. Type this and press Enter:
   - **Windows:** `python --version`
   - **Mac:** `python3 --version`

If you see something like `Python 3.11.4`, skip to Step 3. Any version 3.8 or higher works.

**If you get an error, or the Microsoft Store opens:**

1. Go to **python.org/downloads** and download the latest version.
2. Run the installer.
3. **Windows only:** on the first screen, tick **"Add Python to PATH"** before clicking Install. This is important.
4. When it finishes, close your terminal, open a new one, and try the version check again.

---

## Step 3: Open a terminal inside your folder

**Windows:**
1. Open the `get-vs-post-demo` folder in File Explorer.
2. Click the **address bar** at the top (where the folder path is shown).
3. Type `cmd` and press Enter. A black window opens, already in the right place.

**Mac:**
1. Open Terminal.
2. Type `cd ` (the letters c, d, and a space). Don't press Enter yet.
3. Drag the `get-vs-post-demo` folder from Finder into the Terminal window. Its path appears.
4. Press Enter.

**Check you're in the right place.** Type `dir` (Windows) or `ls` (Mac) and press Enter. You should see `demo_server.py` in the list.

> **Tip:** From now on, **Mac users should type `python3`** wherever this guide says `python`.

---

## Step 4: Start the practice website

In your terminal, type:

```
python demo_server.py
```

You should see:

```
Demo running at http://127.0.0.1:8000  (press Ctrl+C to stop)
```

**Leave this window open.** It's your practice website, and it only works while this window is running. If a firewall pop-up appears, you don't need to allow access beyond your own computer, because the site only works on your machine.

---

## Step 5: Open the practice site in your browser

1. Open your web browser.
2. In the address bar, type `127.0.0.1:8000` and press Enter. (That address means "this computer.")
3. You'll see a page with **two login forms**: Form A (GET) and Form B (POST).

---

## Step 6: Try the GET form (the postcard)

1. In **Form A**, type the username `demo` and the password `demo123`.
2. Click **Log in with GET**.
3. **Look at the address bar at the top of your browser.** You should see something like:

```
127.0.0.1:8000/login?username=demo&password=demo123
```

Your password is sitting in the web address, in plain view. Anyone looking over your shoulder, or any system that records web addresses, would capture it.

The page also shows the **raw request** your browser sent, and the line the server's record book will write down.

---

## Step 7: Try the POST form (the envelope)

1. Click **Back to the forms**.
2. In **Form B**, type the same username `demo` and password `demo123`.
3. Click **Log in with POST**.
4. Look at the address bar again. It now just says:

```
127.0.0.1:8000/login
```

The password is **not** in the address. It traveled hidden inside the request instead. The page shows you where: in the "request body" part of the raw request.

---

## Step 8: Read the server's record book

Every website keeps a log of the requests it receives. This is called the **access log**.

1. On the result page, click **View the access log**.
2. You'll see lines like these (yours will have different times):

```
127.0.0.1 - - [08/Oct/2026:00:22:55 +0000] "GET /login?username=demo&password=demo123 HTTP/1.1" 200 1298
127.0.0.1 - - [08/Oct/2026:00:23:10 +0000] "POST /login HTTP/1.1" 200 1346
```

**Compare the two lines.** The GET line has your password written right in it. The POST line doesn't.

That's the big lesson: the website's record book kept the postcard's message, but not the envelope's contents.

Now look at your **terminal window** (the one running the server). For the POST request, it printed a line starting with `POST body`. That shows the server *did* receive the password inside the envelope. It just didn't write it in the access log.

**Optional:** try a wrong password (like `demo` and `wrong`) and notice the page says "Login failed." In the log, the number after the request changes from `200` to `401`, which means "not authorized." Security analysts use those numbers to spot failed logins.

---

## Step 9: Stop the practice website

Go to the terminal window running the server and press **Ctrl + C** (hold the Ctrl key and press C). You'll see "Stopped."

You now have a file called `access.log` in your folder. That's the record book from your session.

---

## Step 10: Scan the log like a security analyst

The project includes a scanner that reads a log and flags anything suspicious. Make sure you're still in your project folder in the terminal, then run it on **your own log**:

```
python log_analyzer.py access.log
```

You'll see a finding for each time you used the GET form:

```
HIGH   127.0.0.1   Sensitive data in URL: password
```

That's the scanner noticing a password in a web address.

At the bottom you'll also see a **visibility note**. It explains that the scanner can't see inside POST requests, because the log never recorded them. This is a real challenge for security teams.

---

## Step 11: Scan a log full of suspicious activity

Your own log is pretty boring. Try the included **practice log**, which contains made-up suspicious traffic:

```
python log_analyzer.py sample_access.log
```

You should see 8 findings, including:

- Someone trying to guess a password over and over (brute force)
- Someone trying to trick a website's database (SQL injection)
- Someone trying to sneak in a script (cross-site scripting)
- Someone trying to read files they shouldn't (path traversal)
- Someone trying to run commands on the server (command injection)
- Passwords and tokens left visible in web addresses

All of this data is fabricated, so no real people or websites are involved.

---

## Step 12 (optional): Set off the alarm yourself

The scanner flags **5 failed logins within 60 seconds** as a possible brute-force attack. You can trigger it safely on your own practice site:

1. Start the server again (`python demo_server.py`) and open `127.0.0.1:8000`.
2. Use either form to log in with a **wrong** password, **5 or more times in a row, quickly**.
3. Stop the server (Ctrl + C) and run `python log_analyzer.py access.log`.

You should see a **MEDIUM** finding: "Possible brute force."

---

## Troubleshooting

| What you see | What it means | Fix |
|---|---|---|
| `'python' is not recognized` (Windows) | Python isn't installed or wasn't added to PATH | Reinstall Python and tick **"Add Python to PATH."** Open a new terminal afterward |
| `command not found: python` (Mac) | Macs use a different name | Type `python3` instead |
| `Could not start on port 8000` | Something else is using that port, or the demo is already running in another window | Close the other window, or run `python demo_server.py --port 8080` and visit `127.0.0.1:8080` |
| Browser says "This site can't be reached" | The server isn't running | Check the terminal window is still open and shows "Demo running." Restart it if needed |
| `Log file not found: access.log` | You haven't used the practice site yet, or you're in the wrong folder | Run the server, submit a form, then try again. Make sure the terminal is in your project folder |
| The log page says "no requests logged yet" | No form has been submitted yet | Go back to the forms and submit one |
| The scanner finds nothing on your log | You only used POST, or logged in with the wrong method | That's expected. Try the GET form, which puts the password in the address |

Still stuck? Copy the full message from your terminal. That text is the best clue for anyone helping you.

---

## A few words of caution

- **Never type a real password into this practice site.** It shows and records what you type.
- **Don't try to change the site to be reachable by other computers.** It's designed to stay on your machine.
- **This is a teaching tool, not a real website.** Real login pages never display passwords back to you or print them anywhere.
- **The log scanner is a helper, not a judge.** Its findings are leads for a human to check, and attackers can sometimes disguise requests so the scanner misses them.

---

## What did you learn?

1. **GET puts your data in the web address; POST puts it inside the request.**
2. **Web addresses get recorded in many places,** so secrets should never travel in them.
3. **POST isn't secure by itself.** The real protection is HTTPS (the padlock).
4. **Defenders read logs to catch attacks,** and POST requests are a blind spot, because their contents usually aren't logged.

## What next?

- Read [README.md](README.md) for the technical explanation of how everything works.
- Open your browser's **developer tools** (press F12, then the **Network** tab), submit the forms again, and look at the same requests from the browser's side.
- Curious about security careers? Reading logs like this is something SOC analysts do every day.

Happy investigating!
