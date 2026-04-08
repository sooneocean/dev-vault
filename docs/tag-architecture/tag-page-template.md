# Tag Page Template for YOLO LAB

**Purpose:** Block-editor structure for tag pages with rich metadata, descriptions, and content recommendations

**Platform:** WordPress.com Block Editor (compatible with Gutenberg)

---

## Block Structure

This template should be applied to each super-tag page for consistent UX and SEO optimization.

### 1. Header Section

```
<!-- wp:group {"backgroundColor":"black","textColor":"white","padding":{"top":"48px","bottom":"48px"}} -->
<div class="wp-block-group">

  <!-- wp:heading {"level":1,"fontSize":"large"} -->
  <h1 class="wp-block-heading has-large-font-size">{TAG_NAME}</h1>
  <!-- /wp:heading -->

  <!-- wp:paragraph -->
  <p>{TAG_DESCRIPTION_FIRST_SENTENCE}</p>
  <!-- /wp:paragraph -->

</div>
<!-- /wp:group -->
```

**Purpose:** Immediately establish tag topic and value proposition

**Editable Fields:**
- `{TAG_NAME}` — Cluster name (e.g., "Music", "Entertainment")
- `{TAG_DESCRIPTION_FIRST_SENTENCE}` — Opening hook from tag descriptions (50-100 chars)

---

### 2. Content Overview Section

```
<!-- wp:columns -->
<div class="wp-block-columns">

  <!-- wp:column -->
  <div class="wp-block-column">
    <!-- wp:heading {"level":2} -->
    <h2 class="wp-block-heading">What's Here</h2>
    <!-- /wp:heading -->

    <!-- wp:list -->
    <ul>
      <li>News & analysis on {TOPIC}</li>
      <li>Deep dives into {SPECIFIC_AREA_1}</li>
      <li>Profiles of {SPECIFIC_AREA_2}</li>
      <li>Cultural context & industry trends</li>
    </ul>
    <!-- /wp:list -->
  </div>
  <!-- /wp:column -->

  <!-- wp:column -->
  <div class="wp-block-column">
    <!-- wp:heading {"level":2} -->
    <h2 class="wp-block-heading">Recent Articles</h2>
    <!-- /wp:heading -->

    <!-- wp:latest-posts {"postsToShow":5,"excerptLength":20} /-->
  </div>
  <!-- /wp:column -->

</div>
<!-- /wp:columns -->
```

**Purpose:** Help readers understand tag scope and find recent content

**Dynamic Blocks:**
- `<!-- wp:latest-posts -->` — Automatically displays 5 most recent articles tagged with this cluster

---

### 3. Featured Content Section

```
<!-- wp:group {"backgroundColor":"light-gray","padding":{"top":"32px","left":"32px","right":"32px","bottom":"32px"}} -->
<div class="wp-block-group">

  <!-- wp:heading {"level":2} -->
  <h2 class="wp-block-heading">Featured Deep Dives</h2>
  <!-- /wp:heading -->

  <!-- wp:columns -->
  <div class="wp-block-columns">

    <!-- wp:column -->
    <div class="wp-block-column">
      <!-- wp:image {"url":"{FEATURED_IMAGE_1}","sizeSlug":"large"} /-->
      <!-- wp:heading {"level":3,"fontSize":"medium"} -->
      <h3>{FEATURED_TITLE_1}</h3>
      <!-- /wp:heading -->
      <!-- wp:paragraph {"fontSize":"small"} -->
      <p>{FEATURED_EXCERPT_1}</p>
      <!-- /wp:paragraph -->
      <!-- wp:buttons -->
      <div class="wp-block-buttons">
        <!-- wp:button -->
        <div class="wp-block-button">
          <a class="wp-block-button__link" href="{FEATURED_URL_1}">Read More →</a>
        </div>
        <!-- /wp:button -->
      </div>
      <!-- /wp:buttons -->
    </div>
    <!-- /wp:column -->

    <!-- [Repeat for Featured Items 2-3] -->

  </div>
  <!-- /wp:columns -->

</div>
<!-- /wp:group -->
```

**Purpose:** Highlight 3-5 best articles to drive engagement

**Manual Setup:**
- Select 3-5 highest-quality/most-relevant articles for this cluster
- Use their title, featured image, and excerpt
- Update quarterly as new content publishes

---

### 4. Related Tags Section

```
<!-- wp:group {"backgroundColor":"off-white"} -->
<div class="wp-block-group">

  <!-- wp:heading {"level":2} -->
  <h2 class="wp-block-heading">Related Topics</h2>
  <!-- /wp:heading -->

  <!-- wp:paragraph -->
  <p>Explore related clusters:</p>
  <!-- /wp:paragraph -->

  <!-- wp:group {"className":"tag-links"} -->
  <div class="wp-block-group">

    <!-- [Template for each related tag] -->
    <!-- wp:paragraph -->
    <p><a href="/tag/{RELATED_TAG_SLUG}/">{RELATED_TAG_NAME}</a></p>
    <!-- /wp:paragraph -->

  </div>
  <!-- /wp:group -->

</div>
<!-- /wp:group -->
```

**Purpose:** Internal linking for SEO and navigation

**Related Tag Suggestions:**
- **Music:** Entertainment, Culture (personalities)
- **Entertainment:** Music, Culture (classics)
- **Culture:** Music (events), Entertainment (events), Tech (innovation)
- **Tech:** Culture (business personas), Sports (analytics)
- **Sports:** Culture (events), Entertainment (narratives)

---

### 5. About This Tag Section

```
<!-- wp:group {"backgroundColor":"white","borderColor":"light-gray","borderWidth":"1px"} -->
<div class="wp-block-group">

  <!-- wp:heading {"level":2} -->
  <h2 class="wp-block-heading">About {TAG_NAME}</h2>
  <!-- /wp:heading -->

  <!-- wp:paragraph -->
  <p>{TAG_FULL_DESCRIPTION}</p>
  <!-- /wp:paragraph -->

  <!-- wp:heading {"level":3,"fontSize":"small"} -->
  <h3 class="wp-block-heading">Metadata</h3>
  <!-- /wp:heading -->

  <!-- wp:table -->
  <table>
    <tbody>
      <tr>
        <td><strong>Tag Slug:</strong></td>
        <td><code>{TAG_SLUG}</code></td>
      </tr>
      <tr>
        <td><strong>Total Articles:</strong></td>
        <td>{ARTICLE_COUNT}</td>
      </tr>
      <tr>
        <td><strong>Last Updated:</strong></td>
        <td>{LAST_UPDATE_DATE}</td>
      </tr>
    </tbody>
  </table>
  <!-- /wp:table -->

</div>
<!-- /wp:group -->
```

**Purpose:** Complete description + transparency about tag scope

---

### 6. Call-to-Action Section

```
<!-- wp:group {"backgroundColor":"primary-color","textColor":"white","padding":{"top":"48px","bottom":"48px"}} -->
<div class="wp-block-group">

  <!-- wp:heading {"level":2,"textAlign":"center"} -->
  <h2 class="wp-block-heading has-text-align-center">Subscribe to {TAG_NAME} Updates</h2>
  <!-- /wp:heading -->

  <!-- wp:paragraph {"align":"center"} -->
  <p>Get new articles on {TAG_TOPIC} delivered to your inbox.</p>
  <!-- /wp:paragraph -->

  <!-- wp:shortcode -->
  [mailchimp_subscription_form list="tag_{TAG_SLUG}"]
  <!-- /wp:shortcode -->

</div>
<!-- /wp:group -->
```

**Purpose:** Encourage email subscription for community building

**Setup:** Requires integration with email service (Mailchimp, ConvertKit, etc.)

---

## CSS Styling Recommendations

```css
/* Tag page header */
.tag-page__header {
  background-color: #000;
  color: #fff;
  padding: 48px 32px;
}

.tag-page__header h1 {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 16px;
}

/* Featured content cards */
.tag-page__featured {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 32px;
}

.featured-card {
  background: #f5f5f5;
  padding: 24px;
  border-radius: 8px;
}

.featured-card img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  margin-bottom: 16px;
}

/* Related tags */
.related-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.related-tags a {
  display: inline-block;
  padding: 8px 16px;
  background: #f0f0f0;
  border-radius: 20px;
  text-decoration: none;
}

.related-tags a:hover {
  background: #e0e0e0;
}
```

---

## Metadata Setup (Jetpack SEO)

For each tag page, fill in:

| Field | Example | Source |
|-------|---------|--------|
| **SEO Title** | `Music News & Analysis \| YOLO LAB` | tag-descriptions.md |
| **Meta Description** | `Hip-hop and music industry coverage with deep analysis of artists, trends, and cultural impact.` | tag-descriptions.md (first 155 chars) |
| **Focus Keyword** | `music news` or `music analysis` | Domain expert decision |
| **Robots Meta** | `index, follow` | Default for all tag pages |
| **Canonical URL** | `https://yololab.net/tag/music/` | Auto-generated |

---

## Implementation Checklist

For each super-tag, complete:

- [ ] Create tag page using this template
- [ ] Fill in header with tag name + description
- [ ] Add featured articles (3-5 recommendations)
- [ ] Define related tags
- [ ] Enter full description from tag-descriptions.md
- [ ] Set SEO metadata (title, description, keyword)
- [ ] Set featured image/thumbnail
- [ ] Test responsive design (mobile, tablet, desktop)
- [ ] Verify 301 redirects to merged old tags
- [ ] Submit to Google Search Console

---

## Version History

| Date | Change | Status |
|------|--------|--------|
| 2026-04-08 | Initial template | Ready for implementation |
| TBD | WordPress.com block validation | Pending |
| TBD | CSS refinement + responsive testing | Pending |

