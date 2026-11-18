# Figma Design Spec: Bug Tracker Dashboard

**Ready-made screens are in [`design/`](design/).** Drag the `.svg` files into Figma, then follow the steps below to turn them into a proper design file (components, styles, Auto Layout).

Design every screen below in Figma first, then build the React UI to match it. Use this as the brief a product designer would hand you.

## Screens to design

| # | Screen | Desktop (1440) | Mobile (375) |
| --- | --- | --- | --- |
| 1 | Sign in | Centred card, 380 wide, vertically centred | Card fills the width with 16 px margin |
| 2 | Register | Same card with a "Create your account" title | Same |
| 3 | Dashboard, user view | Header, 3 summary cards in a row, then 2 columns (form 1/3, list 2/3) | One column: cards stacked, form, then list |
| 4 | Dashboard, admin view | Same as 3 plus an assignee dropdown and Delete button on each bug | Same stacked |
| 5 | Empty state | "No bugs here yet." | Same |
| 6 | Error state | Red message under the form | Same |

## Components to build (with variants)

| Component | Variants / states |
| --- | --- |
| Button | Primary, Danger, Text link; Default, Hover, Focus, Disabled |
| Input and Textarea | Default, Focus (2 px brand outline), Error |
| Select | Default, Focus |
| Summary card | Open, In progress, Resolved (coloured left edge, big count, label) |
| Status/priority badge | High, Medium, Low |
| Bug row | User view, Admin view (extra dropdown and Delete button) |
| Report a bug form (button: Add bug) | Default, Submitting, Error |
| Header | "Bug Tracker" title on the left, user info and Sign out on the right |

## Layout rules

- Page content max width 1000 px, centred, 16 px padding
- Summary cards: 3 equal columns with 12 px gap (1 column on mobile)
- Main area: columns 1fr and 2fr with 16 px gap (1 column below 720 px)
- Bug rows: 12 px padding, 10 px radius, 12 px gap between rows


## How to do this (about 3 to 4 hours)

1. Create a free Figma account and a new **Design file** named "Bug Tracker Dashboard".
2. Make two pages: **Design System** and **Screens**.
3. **Design System page:** create the colour, text and spacing styles from the tables below (use *Local styles* / *Variables*). Build each component once, using Auto Layout, and make variants for its states.
4. **Screens page:** make a **Desktop** frame (1440 wide) and a **Mobile** frame (375 wide) for every screen. Use Auto Layout and constraints so the layout resizes.
5. Name layers like the code (`card`, `panel`, `badge`), so the Figma file and the React code stay easy to compare.
6. Share the file: **Share > Anyone with the link can view**. Paste the link into `README.md` in place of `FIGMA_LINK_HERE`, and into your resume and LinkedIn.
7. Put a screenshot of each frame in `docs/screenshots/` so recruiters see the design without opening Figma.

## Colour styles (match the CSS variables in `frontend/styles.css`)

| Name | Hex | Used for |
| --- | --- | --- |
| Background | `#F5F7FA` | Page background |
| Panel | `#FFFFFF` | Cards, panels, inputs |
| Text | `#1B2733` | Main text |
| Muted | `#5F6F7F` | Labels, helper text |
| Brand | `#1F6FEB` | Buttons, focus ring, Open status |
| Danger | `#C62828` | Delete button, errors |
| Border | `#DDE3EA` | Outlines |
| In progress | `#E08A00` | In-progress status |
| Resolved | `#2E8B57` | Resolved status |
| High badge | bg `#FDE4E4`, text `#8E1D1D` | High priority |
| Medium badge | bg `#FFF1D6`, text `#7A4D00` | Medium priority |
| Low badge | bg `#E3F4E9`, text `#1D6B3D` | Low priority |

## Text styles

Figma cannot use the system font stack, so design with **Inter**, which looks almost identical. The code uses `system-ui`.

| Style | Size / Weight | Used for |
| --- | --- | --- |
| Heading 1 | 32 / Bold (26 on mobile for the long title) | Page title |
| Heading 2 | 24 / Bold | Panel titles |
| Count | 29 / Bold | Numbers on summary cards |
| Body | 16 / Regular | Normal text |
| Label | 14 / Regular, muted colour | Form labels |
| Small | 13 / Regular, muted colour | Timestamps, helper text |
| Badge | 12 / Regular | Status and priority badges |

## Spacing and shape

- Spacing scale: 4, 8, 12, 16, 24, 32 px (the code uses 0.25rem to 2rem)
- Corner radius: inputs and buttons 8 px, cards 10 px, panels 12 px, badges fully round
- Border: 1 px `Border` colour. Cards have a 4 to 5 px coloured edge showing their status.

## Build it exactly like Figma (the JD's preferred skill)

Do this after the design is done:

1. Open the file in **Dev Mode** (toggle top right). Click any element to see its exact size, colour, padding and font.
2. For each frame, open the running app next to Figma at the same width (1440 and 375) and compare.
3. Fix every difference in `styles.css`: spacing, font size, colours, radius, alignment.
4. Put the Figma frame and a screenshot of the finished page side by side in `docs/screenshots/` (name them `home-figma.png` and `home-app.png`).
5. Tick the issue "Match the UI to the Figma design" only when both match at 1440 and 375 px.
6. In interviews, say: *"I reviewed the mockup in Dev Mode and built the UI to match it, checking spacing, colour and type at desktop and mobile widths."*

## Accessibility checks (good UX practice)

- Text contrast of at least 4.5 to 1 (use Figma's free "Stark" or "A11y" plugin)
- Every input has a visible label, and error text is not shown by colour alone
- Buttons are at least 40 px tall on mobile
- Status is shown with text as well as colour (for example the "UP" and "DOWN" pills)

