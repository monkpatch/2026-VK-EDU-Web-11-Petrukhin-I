# Web HW1 — Static layout

Static HTML markup for Q&A website mockups (VK EDU Web HW1).

## How to run

No build required.

1. Open `public/index.html` in browser.
2. Or from this directory run a simple static server:

```bash
python3 -m http.server 8080
```

Then open: http://localhost:8080/public/index.html

## Pages

- `index.html` — question list
- `question.html` — single question + answers
- `ask.html` — ask question form
- `login.html` — sign in form
- `signup.html` — sign up form
- `profile.html` — profile settings form
- `hot.html` — hot questions list
- `tag.html` — questions list filtered by tag

## Static assets

All static files are local (no CDN):

- `public/static/css/bootstrap.min.css`
- `public/static/css/main.css`
- `public/static/js/bootstrap.bundle.min.js`
- `public/static/js/main.js`
- `public/static/img/*`
