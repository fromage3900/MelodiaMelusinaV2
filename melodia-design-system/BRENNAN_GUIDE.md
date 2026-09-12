# Brennan Shepherd — Personal Brand Elements

**Created:** 2026-06-25  
**Purpose:** Editorial-styled portfolio elements for job hunting and freelance work  
**Location:** Toronto, ON

---

## Quick Start

All elements are HTML-based — no Figma required. Use them on your Wix site (fromageart.xyz) or export as images for other platforms.

---

## 1. Personal Hero Banner (`brennan-hero-embed.html`)

**Use:** Homepage hero, portfolio introduction, "About" section header

**Themes:**
- `editorial` — Clean ivory gradient, minimal stars, editorial accent line (NEW)
- `dark` — Astral Night with constellation pattern
- `nebula` — Iris/astro bloom with glowing stars
- `ivory` — Light editorial with subtle gold accents

**How to use in Wix:**
1. Editor → Add (+) → Embed Code → Embed HTML
2. Paste the entire file
3. Stretch full-width, height ~440-520px
4. Edit DATA block:
   ```javascript
   var DATA = {
     theme: "editorial",
     kicker: "3D Environment & Technical Art",
     title: "Brennan Shepherd",
     sub: "Toronto, ON · Available for Work"
   };
   ```

**URL params:** `?theme=editorial&title=...&kicker=...&sub=...`

---

## 2. Personalized Asset Passport (`brennan-passport-embed.html`)

**Use:** Project spec plates on every portfolio page — your signature branding element

**Features:**
- Your name in footer instead of "MELODIA"
- Location field (Toronto, ON)
- Same data schema as original for automation compatibility

**How to use in Wix:**
1. Editor → Add (+) → Embed Code → Embed HTML
2. Paste the entire file
3. Size ~360 × 560px
4. Edit DATA block:
   ```javascript
   var DATA = {
     theme: "dark",
     project: "Project Name",
     category: "Environment",
     version: "v1.0",
     location: "Toronto, ON",
     rows: [
       ["Triangles", "482,318"],
       ["Textures", "4K"],
       ["Materials", "12"],
       ["Software", "Blender · Unreal"],
       ["Engine", "Unreal Engine 5"],
       ["Date", "2026-06"]
     ]
   };
   ```

**URL params:** `?project=...&category=...&triangles=...&textures=...&materials=...&software=...&engine=...&date=...&version=...&location=...`

---

## 3. Project Card (`brennan-project-card.html`)

**Use:** Portfolio grids, "Featured Work" sections, project showcases

**Features:**
- Project image (or placeholder)
- Title, category, year
- Description text
- Technology tags
- Hover animation
- Click-to-link functionality

**How to use in Wix:**
1. Editor → Add (+) → Embed Code → Embed HTML
2. Paste the entire file
3. Size ~400 × 300px
4. Edit DATA block:
   ```javascript
   var DATA = {
     theme: "light",
     title: "Project Name",
     category: "Environment",
     year: "2026",
     description: "Brief description of the project...",
     tags: ["Unreal Engine", "PCG", "Houdini"],
     imageUrl: "",  // Leave empty for placeholder
     link: ""       // Optional: URL to project page
   };
   ```

**Tip:** Create multiple copies of this file, one per project, and embed them in a grid layout.

---

## 4. Email Signature (`brennan-email-signature.html`)

**Use:** Professional email signature for job applications and client communications

**How to use:**
1. Open the file in a browser
2. Copy the rendered HTML (not the source)
3. Paste into your email client's signature editor (HTML mode)
4. Update contact info in the HTML:
   ```html
   <div class="name">Brennan Shepherd</div>
   <div class="title">3D Environment & Technical Artist</div>
   <div class="contact">
     <span>📧 your@email.com</span>
     <span>📍 Toronto, ON</span>
   </div>
   ```

**Features:**
- Gold divider line
- Availability badge
- Portfolio link
- Minimal, professional design

---

## 5. LinkedIn Banner (`brennan-linkedin-banner.html`)

**Use:** LinkedIn cover photo (1584 × 396px)

**How to use:**
1. Open the file in a browser
2. Screenshot at exactly 1584 × 396px
3. Upload to LinkedIn as your cover photo
4. Edit DATA block before screenshotting:
   ```javascript
   var DATA = {
     kicker: "3D Environment & Technical Art",
     title: "Brennan Shepherd",
     sub: "Toronto, ON · Available for Work",
     availability: "Open to Opportunities"
   };
   ```

**Features:**
- Editorial ivory gradient
- Your name in large display type
- "Available for Work" badge
- Subtle gold star accents
- Professional, clean design

---

## 6. Resume/CV (`brennan-resume.html`)

**Use:** Professional resume for job applications, downloadable PDF from portfolio

**How to use:**
1. Open the file in a browser
2. Click "Print / Save PDF" button (top-right)
3. Save as PDF
4. Edit content directly in the HTML:
   - Update experience, projects, skills
   - Add your actual work history
   - Customize education section

**Features:**
- Clean, editorial layout with gold accents
- Print-optimized (removes print button)
- Sections: Summary, Experience, Skills, Projects, Education
- Melodia typography (Fraunces, IBM Plex Mono, Cinzel)
- Professional footer with your branding

**Customization tips:**
- Update contact info in header
- Replace placeholder experience with your actual work history
- Add your real projects with accurate stats
- Adjust skills to match your actual toolset
- Update education with your actual degree

---

## 7. ArtStation Project Cover (`artstation-cover.html`)

**Use:** ArtStation project cover images (1920 × 1080px)

**How to use:**
1. Open the file in a browser
2. Screenshot at exactly 1920 × 1080px
3. Upload to ArtStation as project cover
4. Edit DATA block for each project:
   ```javascript
   var DATA = {
     kicker: "3D Environment Art",
     title: "Project Name",
     sub: "Unreal Engine 5 · PCG · Houdini",
     stats: [
       {label: "Triangles", value: "482K"},
       {label: "Materials", value: "12"},
       {label: "Resolution", value: "4K"}
     ]
   };
   ```

**Features:**
- Astral Night background with constellation pattern
- Large project title in Fraunces display
- Project stats (triangles, materials, resolution)
- Your branding in top-left corner
- Glowing gold star accents
- Professional, eye-catching design

**Tip:** Create a copy of this file for each project, customize the DATA, then generate covers for all your work.

---

## Color Palette (for manual editing)

**Ivory Editorial (Light):**
- Surface base: `#F7F4EF`
- Surface lift: `#FCFBF8`
- Text primary: `#241B2E`
- Text secondary: `#6E6080`
- Gold: `#A7884E`
- Gold soft: `#DDC79B`

**Astral Night (Dark):**
- Surface base: `#141A30`
- Surface raised: `#1C2340`
- Text primary: `#ECEAF4`
- Text secondary: `#A9A7C0`
- Gold: `#C9A86A`
- Gold soft: `#DDC79B`

---

## Typography

**Fonts (all load from Google Fonts):**
- Display/Titles: **Fraunces** (variable, high optical contrast)
- Wordmark: **Cinzel** (engraved celestial caps)
- Body/UI: **Inter** (neutral neo-grotesque)
- Technical/Metadata: **IBM Plex Mono** (monospace)

**Type Scale:**
- Display XL: 72px (hero titles)
- Title/Project: 40px (project names)
- Header/Section: 28px (section headers)
- Body Default: 16px (body copy)
- Label/Technical: 12px (tags, specs)
- Metadata: 11px (fine print)

---

## Suggested Website Structure

**Homepage:**
- Hero: `brennan-hero-embed.html` (editorial theme)
- Featured Work: Grid of `brennan-project-card.html` (3-4 projects)
- About: Text section with `brennan-passport-embed.html` as spec plate

**Project Pages:**
- Project image
- `brennan-passport-embed.html` (with project data)
- Description text
- Additional project cards for related work

**Contact/Commissions:**
- `brennan-hero-embed.html` (ivory theme)
- Contact info
- Email signature preview

---

## Job Hunting Tips

**Portfolio:**
- Put your personalized passport on EVERY project page
- Use project cards to show breadth of work
- Keep descriptions concise (2-3 sentences)
- Highlight technical challenges solved

**LinkedIn:**
- Use the banner template
- Update headline to "3D Environment & Technical Artist"
- Add portfolio link to featured section
- Post project updates with project card screenshots

**Email Applications:**
- Use the email signature
- Link to portfolio in signature
- Keep subject lines clear: "Application: [Role] - Brennan Shepherd"

---

## Customization

**Changing your name:**
- Search for "BRENNAN SHEPHERD" in each file and replace
- Update wordmark in hero banner

**Changing location:**
- Update `location` field in passport
- Update subtext in hero banner

**Adding new themes:**
- Copy an existing theme in the `T` object
- Adjust colors (surf, txt, sec, gold, etc.)
- Add theme name to DATA.theme options

---

## File Locations

**Wix embeds** (in `wix/` folder):
- `brennan-hero-embed.html`
- `brennan-passport-embed.html`
- `brennan-project-card.html`
- `brennan-email-signature.html`
- `brennan-linkedin-banner.html`

**Standalone templates** (in root folder):
- `brennan-resume.html`
- `artstation-cover.html`

---

## Next Steps

1. **Set up Wix site** with fonts and colors from `WIX-GUIDE.md`
2. **Add hero banner** to homepage
3. **Create project cards** for 3-4 best projects
4. **Add passport** to each project page
5. **Generate LinkedIn banner** and upload
6. **Set up email signature** in your email client
7. **Update LinkedIn profile** with new banner and headline
8. **Customize resume** with your actual experience and projects
9. **Generate ArtStation covers** for your portfolio projects

---

## Support

For issues or questions:
- Check the original `DESIGN-SYSTEM.md` for design system details
- Refer to `WIX-GUIDE.md` for Wix-specific instructions
- All HTML files have inline comments explaining usage
