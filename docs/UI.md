# UI checklist

<!-- Exercise 4 hands this in. Tick an item only when you have checked it, and replace
     the "how I checked" line with what you actually did. An unticked box is not a
     failure: it is a gap you then write into READINESS.md. A ticked box you cannot
     demonstrate at the defence is worse than an unticked one. -->

"Modern" is not a style. It is a short list of things a user notices when they are
missing: the screen tells you what is happening, you can get through it with a keyboard,
the text is readable, and nothing jumps around while it loads.

## Layout and typography

- [x] **One spacing scale and one type scale.** Sizes come from a small set of design tokens, not from numbers typed where they were needed.
  - how I checked: all sizes in `app/static/css/styles.css` come from `--space-*`, `--text-*` and `--radius-*` tokens (read the file).
- [x] **Responsive at 380, 768 and 1280 pixels wide.** No horizontal scrollbar, no text running under another element.
  - how I checked: in the built-in browser I set the width to 380, 768 and 1280 on /events and /organizer and read `document.documentElement.scrollWidth`: never larger than the window (the 15 px difference at 768 and 1280 is the scrollbar).
- [ ] **Nothing jumps while the page loads.** Images and cards reserve their space before their content arrives.
  - how I checked:

## The four states, on every screen

A screen that only handles "it worked" is a screen that lies to the user on the day it matters.

- [x] **Loading.** Something tells the user the app is working, within about 100 ms.
  - how I checked: each screen shows a skeleton or spinner while `api()` runs (read the code of the six pages).
- [x] **Empty.** The screen says what this list is for and what to do next, instead of showing nothing.
  - how I checked: events, tickets and organizer lists have an empty message with a next step (read the code).
- [x] **Error.** A sentence a person can read. Never a raw JSON body, never a stack trace, never just "Error".
  - how I checked: `api()` throws the server's `error` sentence and every page prints it with a Retry or message; the server now never sends a stack trace (`test_AC_29`).
- [x] **Success.** The user can see that what they did took effect, without reloading the page to find out.
  - how I checked: buying, cancelling, creating and editing show a toast or a ticket code and redraw without reload (read the code).

## Keyboard and accessibility

- [ ] **The main flow works with the keyboard alone.** Sign in, do the core action, sign out, without touching the mouse.
  - how I checked:
- [x] **The focused element is visible.** A `:focus-visible` outline that is not switched off.
  - how I checked: `:focus-visible` rules exist in `styles.css` and nothing sets `outline: none` on its own.
- [x] **Text contrast is at least 4.5:1.** Name the tool you measured with.
  - how I checked: computed in the browser console with the WCAG formula over all text on the login, events and organizer pages: the lowest ratio is 8.6:1, against the 4.5:1 minimum.
- [x] **Every input has a label** a screen reader reads, not just placeholder text.
  - how I checked: each page has as many `<label>` as inputs (grep).
- [x] **The page has a correct `<title>` and `lang`.**
  - how I checked: every file in `app/static/` has `<title>` and `lang="en"` (grep).
- [x] **Touch targets are at least 44 pixels.**
  - how I checked: in the browser at 380 px wide I measured every button, link button and input on /events and /organizer: none is shorter than 44 px.

## The model feature

- The app has no model feature, so these items do not apply.

## Decisions

- [x] **Dark mode, or a written decision not to have one.**
  - what I decided and why: the whole UI is a dark nightclub theme (`color-scheme: dark`), so there is no light mode; chosen to match the product.

## Known gaps

- Not yet checked: keyboard-only walk through the main flow, and that nothing jumps while loading (no layout-shift measurement).
- No screenshots yet: the Evidence section below needs the four states of one screen.

## Evidence

<!-- Screenshots of at least the four states of one screen, and of the model feature
     thinking and failing. A link to them is enough; they do not have to be in the repo. -->
