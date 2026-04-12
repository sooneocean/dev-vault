-- ╔════════════════════════════════════════════════════════════════╗
-- ║   YOLO LAB SEO - Units 4 & 6B Final Deployment SQL Script      ║
-- ║   Deploy Date: 2026-04-08                                      ║
-- ║   Target: yololab_db                                           ║
-- ╚════════════════════════════════════════════════════════════════╝

-- ============================================================
-- STEP 1: Create Footer Widget 1 - About
-- ============================================================
INSERT INTO wp_options (option_name, option_value)
VALUES (
  'widget_custom_html[1]',
  'a:2:{s:5:"title";s:5:"About";s:7:"content";s:247:"<h3>About</h3>\n<ul>\n  <li><a href=\"/about/\">About YOLO LAB</a></li>\n  <li><a href=\"/contact/\">Contact</a></li>\n  <li><a href=\"/privacy/\">Privacy Policy</a></li>\n</ul>";}'
)
ON DUPLICATE KEY UPDATE option_value = VALUES(option_value);

-- ============================================================
-- STEP 2: Create Footer Widget 2 - Categories
-- ============================================================
INSERT INTO wp_options (option_name, option_value)
VALUES (
  'widget_custom_html[2]',
  'a:2:{s:5:"title";s:10:"Categories";s:7:"content";s:273:"<h3>Categories</h3>\n<ul>\n  <li><a href=\"/category/film/\">Film</a></li>\n  <li><a href=\"/category/music/\">Music</a></li>\n  <li><a href=\"/category/tech/\">Tech</a></li>\n  <li><a href=\"/category/sports/\">Sports</a></li>\n</ul>";}'
)
ON DUPLICATE KEY UPDATE option_value = VALUES(option_value);

-- ============================================================
-- STEP 3: Create Footer Widget 3 - Popular Tags
-- ============================================================
INSERT INTO wp_options (option_name, option_value)
VALUES (
  'widget_custom_html[3]',
  'a:2:{s:5:"title";s:12:"Popular Tags";s:7:"content";s:359:"<h3>Popular Tags</h3>\n<ul>\n  <li><a href=\"/tag/ai/\">AI</a></li>\n  <li><a href=\"/tag/entertainment/\">Entertainment</a></li>\n  <li><a href=\"/tag/music-news/\">Music News</a></li>\n  <li><a href=\"/tag/movie-reviews/\">Movie Reviews</a></li>\n</ul>";}'
)
ON DUPLICATE KEY UPDATE option_value = VALUES(option_value);

-- ============================================================
-- STEP 4: Register Widgets in Footer Sidebar
-- ============================================================
UPDATE wp_options
SET option_value = 'a:5:{i:1;s:17:"custom_html-1";i:2;s:17:"custom_html-2";i:3;s:17:"custom_html-3";i:4;s:8:"archives";i:5;s:6:"recent";}'
WHERE option_name = 'sidebars_widgets'
AND option_value LIKE '%footer%'
LIMIT 1;

-- ============================================================
-- STEP 5: Configure Yoast SEO - Enable Breadcrumbs
-- ============================================================
INSERT INTO wp_options (option_name, option_value)
VALUES (
  'wpseo_titles',
  'a:20:{s:19:"breadcrumbs-enable";i:1;s:21:"breadcrumbs-display";i:1;s:18:"breadcrumbs-home";i:1;s:22:"breadcrumbs-single-post";i:1;s:20:"breadcrumbs-archive";i:1;s:10:"breadcrumbs";i:1;s:14:"breadcrumb-sep";s:3:" > ";s:21:"breadcrumb-home-label";s:4:"Home";s:19:"breadcrumb-prefix";s:0:"";s:19:"breadcrumb-single";s:0:"";s:21:"breadcrumb-archiveDate";s:0:"";s:21:"breadcrumb-archiveAuthor";s:0:"";s:23:"breadcrumb-archiveSearch";s:0:"";s:20:"breadcrumb-404-label";s:3:"404";}'
)
ON DUPLICATE KEY UPDATE option_value = VALUES(option_value);

-- ============================================================
-- STEP 6: Flush WordPress Rewrite Rules
-- ============================================================
DELETE FROM wp_options WHERE option_name = 'rewrite_rules';

-- ============================================================
-- STEP 7: Clear WordPress Cache (if using transients)
-- ============================================================
DELETE FROM wp_options WHERE option_name LIKE '%widget%cache%';
DELETE FROM wp_options WHERE option_name LIKE '%sidebars%cache%';

-- ============================================================
-- VERIFICATION QUERIES (Run after deployment)
-- ============================================================
-- Run these to verify deployment success:

-- Check Widget 1:
-- SELECT option_name, option_value FROM wp_options WHERE option_name = 'widget_custom_html[1]';

-- Check Widget 2:
-- SELECT option_name, option_value FROM wp_options WHERE option_name = 'widget_custom_html[2]';

-- Check Widget 3:
-- SELECT option_name, option_value FROM wp_options WHERE option_name = 'widget_custom_html[3]';

-- Check Sidebar Configuration:
-- SELECT option_name, option_value FROM wp_options WHERE option_name = 'sidebars_widgets';

-- Check Yoast Settings:
-- SELECT option_name, option_value FROM wp_options WHERE option_name = 'wpseo_titles';

-- ============================================================
-- DEPLOYMENT COMPLETE
-- ============================================================
-- After running these queries:
-- 1. Visit https://yololab.net - You should see:
--    - Header: 7-item menu (Home, Film, Music, Tech, Sports, Entertainment, Search)
--    - Footer: 3 sections (About, Categories, Popular Tags)
--    - Articles: Breadcrumb navigation (Home > Category > Title)
--
-- 2. Clear browser cache (Ctrl+Shift+Delete)
-- 3. Hard refresh the page (Ctrl+F5)
-- 4. Verify all 3 footer widgets are visible
-- ============================================================
