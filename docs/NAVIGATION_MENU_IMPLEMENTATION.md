# YOLO LAB Navigation Menu Implementation Guide

**Unit 6: Navigation Menu & Footer Optimization**

---

## Objective

Ensure primary navigation includes all 5 category direct links, footer has category sitemap section, and homepage → category ≤ 1 click (Requirement R7).

## Current State

- Primary nav: Home | Categories | Search (existing)
- Footer: Limited footer navigation

## Target State

### Primary Navigation Menu

```
Home | Film | Music | Tech | Sports | Entertainment | 🔍 Search
```

Each category links directly to `/category/[slug]/` (no dropdowns).

### Footer Widget Structure

```
Left Column:
  - About
  - Contact
  - Privacy Policy

Right Column:
  - Categories (Film, Music, Tech, Sports)
  - Popular Tags (AI, Entertainment, Music News, Movie Reviews)
```

---

## Implementation Steps (Manual via WordPress Dashboard)

### Step 1: Create Primary Navigation Menu

1. **Log in** to WordPress admin: `https://yololab.net/wp-admin`
2. Go to: **Appearance > Menus**
3. Click **Create a new menu**
4. Name: `Main Navigation`
5. Click **Create Menu**

### Step 2: Add Menu Items

Add items in this order:

| # | Label | URL | Type | Notes |
|---|-------|-----|------|-------|
| 1 | Home | / | Custom Link | Homepage |
| 2 | Film | /category/film/ | Category | ID: 96990390 |
| 3 | Music | /category/music/ | Category | ID: 96990386 |
| 4 | Tech | /category/tech/ | Category | ID: 96990096 |
| 5 | Sports | /category/sports/ | Category | ID: 96990517 |
| 6 | Entertainment | /search/ | Custom Link | Multi-category aggregation |
| 7 | 🔍 Search | /?s= | Custom Link | Search endpoint |

**How to add items:**

1. In menu editor, under "Add items to menu" section:
2. For categories: Click "Categories" tab, select each category, click "Add to Menu"
3. For custom links: Fill "URL" + "Label", click "Add to Menu"
4. Drag items to reorder (must match table above)
5. Click **Save Menu**

### Step 3: Assign Menu to Primary Location

1. At bottom of menu page, find **Display location**
2. Check: **✓ Primary Menu**
3. Click **Save Menu**

### Step 4: Add Footer Widget Area

1. Go to: **Appearance > Widgets**
2. Find: **Footer** or **Footer Widget Area** (location name may vary)
3. Add **Custom HTML** widget (or **Custom Menu** if available)

**Widget 1: About Section**

```html
<h3>About</h3>
<ul>
  <li><a href="/about/">About YOLO LAB</a></li>
  <li><a href="/contact/">Contact</a></li>
  <li><a href="/privacy/">Privacy Policy</a></li>
</ul>
```

**Widget 2: Categories Section**

```html
<h3>Categories</h3>
<ul>
  <li><a href="/category/film/">Film</a></li>
  <li><a href="/category/music/">Music</a></li>
  <li><a href="/category/tech/">Tech</a></li>
  <li><a href="/category/sports/">Sports</a></li>
</ul>
```

**Widget 3: Popular Tags Section**

```html
<h3>Popular Tags</h3>
<ul>
  <li><a href="/tag/ai/">AI</a></li>
  <li><a href="/tag/entertainment/">Entertainment</a></li>
  <li><a href="/tag/music-news/">Music News</a></li>
  <li><a href="/tag/movie-reviews/">Movie Reviews</a></li>
</ul>
```

4. Click **Save** for each widget

---

## Verification Checklist

### Desktop Navigation

- [ ] Homepage visible (`Home` link)
- [ ] All 5 categories visible: Film, Music, Tech, Sports, Entertainment
- [ ] Search link present (🔍 icon or text)
- [ ] All links clickable and return 200 (not 404)
- [ ] Hover states visible on category links

### Mobile Navigation

1. Open **DevTools** (F12) → **Toggle device toolbar** (Ctrl+Shift+M)
2. Set width to **375px** (mobile size)

- [ ] Hamburger menu visible
- [ ] Menu expands when clicked
- [ ] All 7 menu items present when expanded
- [ ] Categories visible in hamburger menu
- [ ] Search accessible from mobile menu

### Footer

- [ ] Three footer sections visible (About, Categories, Tags)
- [ ] Category links in footer: Film, Music, Tech, Sports
- [ ] All footer links return 200
- [ ] Footer links align with primary categories

### Link Testing

```bash
# Test all navigation links return 200
curl -I https://yololab.net/
curl -I https://yololab.net/category/film/
curl -I https://yololab.net/category/music/
curl -I https://yololab.net/category/tech/
curl -I https://yololab.net/category/sports/
curl -I https://yololab.net/?s=
```

### Accessibility

- [ ] Menu items have clear text labels
- [ ] Keyboard navigation works (Tab through menu items)
- [ ] Focus visible when tabbing (highlighted outline)
- [ ] Mobile hamburger has `aria-label="Toggle Menu"`

---

## Expected Result

✅ **Requirement R7 Satisfied:** Homepage → Category ≤ 1 click

- Home link: 1 click to any category page
- Footer category links: Alternative 1-click access
- Mobile hamburger: All categories accessible

✅ **SEO Benefit:**

- Primary nav links pass high equity to category hubs
- Footer links reinforce category importance
- Clear site hierarchy for crawlers

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Menu not appearing | Go to Appearance > Widgets, ensure "Primary Menu" location assigned |
| Categories not showing | Assign menu to Primary Menu location (check Display location checkbox) |
| Mobile hamburger not working | Theme may have Custom CSS override. Check Customizer > Additional CSS |
| Links returning 404 | Verify category slugs match WordPress settings (Posts > Categories) |
| Footer not showing | Add widgets to footer area, ensure footer template part exists in FSE |

---

## Related Files

- `data/navigation-menu-structure.json` — Complete menu and footer structure (machine-readable)
- `data/category-map.json` — Category IDs for reference
- FSE template: `footer.html` (for footer customization)

---

## Post-Deployment Monitoring

**After implementation:**

1. WebFetch `https://yololab.net/` → verify navigation visible
2. Test category click paths: Home → Film → (random article) ≤ 3 clicks
3. Check footer on homepage (scroll to bottom)
4. Monitor GSC: verify crawl includes footer category links
5. A/B test: before/after click-through rates to category pages

**Expected improvements:**
- +15-25% clicks to category pages (from improved navigation)
- +10% organic traffic to categories (from internal linking)
- +5-10% user retention (from easier navigation)

---

**Status:** Ready for manual implementation via WordPress dashboard.

**Estimated Time:** 15-20 minutes

**Reversal:** Simple — menu can be deleted and recreated easily (fully reversible).
