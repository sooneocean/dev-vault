<?php
/**
 * Plugin Name: YOLO LAB Auto Deploy
 * Plugin URI: https://yololab.net
 * Description: Automatically deploys Units 4 & 6B - Yoast breadcrumbs and footer widgets
 * Version: 1.0.0
 * Author: YOLO LAB SEO
 * Author URI: https://yololab.net
 * License: GPL v2 or later
 * Text Domain: yololab-auto-deploy
 * Domain Path: /languages
 *
 * This plugin automatically configures:
 * - Unit 4: Yoast SEO Breadcrumbs
 * - Unit 6B: Footer Widgets (About, Categories, Popular Tags)
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// ============================================================
// YOLO LAB Auto Deploy Class
// ============================================================
class YOLOLAB_Auto_Deploy {

    public function __construct() {
        // Run deployment on plugin activation
        register_activation_hook(__FILE__, array($this, 'activate'));

        // Also run on plugins_loaded for mu-plugin or backup execution
        add_action('plugins_loaded', array($this, 'deploy_on_load'), 1);

        // Add admin notice showing deployment status
        add_action('admin_notices', array($this, 'show_deployment_notice'));
    }

    /**
     * Activation hook - runs when plugin is activated
     */
    public function activate() {
        $this->deploy();
    }

    /**
     * Run deployment on plugins_loaded
     * Useful for mu-plugins that don't have activation hooks
     */
    public function deploy_on_load() {
        // Only run once
        if (get_option('yololab_deployment_complete')) {
            return;
        }

        $this->deploy();
        update_option('yololab_deployment_complete', time());
    }

    /**
     * Main deployment function
     */
    public function deploy() {
        // Deploy footer widgets
        $this->deploy_footer_widgets();

        // Configure Yoast SEO
        $this->configure_yoast_seo();

        // Register widgets in sidebar
        $this->register_widgets_in_sidebar();

        // Clear caches
        $this->clear_caches();

        // Log deployment
        $this->log_deployment();
    }

    /**
     * Deploy 3 footer widgets
     */
    private function deploy_footer_widgets() {
        $widgets = array(
            1 => array(
                'title'  => 'About',
                'content' => '<h3>About</h3>
<ul>
  <li><a href="/about/">About YOLO LAB</a></li>
  <li><a href="/contact/">Contact</a></li>
  <li><a href="/privacy/">Privacy Policy</a></li>
</ul>',
                'filter' => 'content_save_pre'
            ),
            2 => array(
                'title'  => 'Categories',
                'content' => '<h3>Categories</h3>
<ul>
  <li><a href="/category/film/">Film</a></li>
  <li><a href="/category/music/">Music</a></li>
  <li><a href="/category/tech/">Tech</a></li>
  <li><a href="/category/sports/">Sports</a></li>
</ul>',
                'filter' => 'content_save_pre'
            ),
            3 => array(
                'title'  => 'Popular Tags',
                'content' => '<h3>Popular Tags</h3>
<ul>
  <li><a href="/tag/ai/">AI</a></li>
  <li><a href="/tag/entertainment/">Entertainment</a></li>
  <li><a href="/tag/music-news/">Music News</a></li>
  <li><a href="/tag/movie-reviews/">Movie Reviews</a></li>
</ul>',
                'filter' => 'content_save_pre'
            )
        );

        update_option('widget_custom_html', $widgets);
    }

    /**
     * Configure Yoast SEO breadcrumbs
     */
    private function configure_yoast_seo() {
        $yoast_settings = array(
            'breadcrumbs-enable'        => 1,
            'breadcrumbs-display'       => 1,
            'breadcrumbs-home'          => 1,
            'breadcrumbs-single-post'   => 1,
            'breadcrumbs-archive'       => 1,
            'breadcrumbs-sep'           => ' > ',
            'breadcrumb-home-label'     => 'Home',
            'breadcrumb-prefix'         => '',
            'breadcrumb-single'         => '',
            'breadcrumb-archiveDate'    => '',
            'breadcrumb-archiveAuthor'  => '',
            'breadcrumb-archiveSearch'  => '',
            'breadcrumb-404-label'      => '404'
        );

        update_option('wpseo_titles', $yoast_settings);
    }

    /**
     * Register widgets in footer sidebar
     */
    private function register_widgets_in_sidebar() {
        $sidebars = wp_get_sidebars_widgets();

        // Find footer sidebar
        $footer_sidebar = false;
        foreach ($sidebars as $sidebar_id => $widgets) {
            if (strpos($sidebar_id, 'footer') !== false) {
                $footer_sidebar = $sidebar_id;
                break;
            }
        }

        // Fallback to common footer sidebar names
        if (!$footer_sidebar) {
            $footer_sidebar = 'footer-1';
        }

        // Register widgets
        if (!isset($sidebars[$footer_sidebar])) {
            $sidebars[$footer_sidebar] = array();
        }

        $sidebars[$footer_sidebar] = array(
            'custom_html-1',
            'custom_html-2',
            'custom_html-3'
        );

        wp_set_sidebars_widgets($sidebars);
    }

    /**
     * Clear all caches
     */
    private function clear_caches() {
        // Clear rewrite rules
        delete_option('rewrite_rules');
        flush_rewrite_rules(false);

        // Clear transients
        if (function_exists('wp_cache_flush')) {
            wp_cache_flush();
        }

        // Clear other cache-related options
        delete_option('widget_cache');
        delete_option('sidebars_widgets_cache');

        // Update the "needs rewrite" flag
        update_option('permalink_structure', get_option('permalink_structure'));
    }

    /**
     * Log deployment for reference
     */
    private function log_deployment() {
        update_option('yololab_deployment_log', array(
            'timestamp' => current_time('mysql'),
            'version'   => '1.0.0',
            'units'     => array('4', '6B'),
            'widgets'   => 3,
            'status'    => 'complete'
        ));
    }

    /**
     * Show admin notice
     */
    public function show_deployment_notice() {
        if (!get_option('yololab_deployment_complete')) {
            return;
        }

        // Only show on admin pages
        if (!is_admin()) {
            return;
        }

        $log = get_option('yololab_deployment_log');
        if (!$log) {
            return;
        }

        ?>
        <div class="notice notice-success is-dismissible">
            <p>
                <strong>✅ YOLO LAB SEO Deployment Complete!</strong><br>
                Units 4 & 6B successfully deployed:<br>
                • Unit 4: Yoast SEO Breadcrumbs ✅<br>
                • Unit 6B: Footer Widgets (3) ✅<br>
                <small>Deployment time: <?php echo esc_html($log['timestamp']); ?></small>
            </p>
        </div>
        <?php
    }
}

// Initialize plugin
new YOLOLAB_Auto_Deploy();

// ============================================================
// Optional: Show deployment status in frontend
// ============================================================
function yololab_get_deployment_status() {
    $log = get_option('yololab_deployment_log');
    if (!$log) {
        return 'not_deployed';
    }
    return $log['status'];
}

// ============================================================
// Optional: Verification function for debugging
// ============================================================
function yololab_verify_deployment() {
    $widgets = get_option('widget_custom_html');
    $yoast = get_option('wpseo_titles');
    $sidebars = wp_get_sidebars_widgets();

    return array(
        'widgets_created'    => count($widgets),
        'yoast_configured'   => !empty($yoast['breadcrumbs-enable']),
        'sidebars_registered' => !empty($sidebars)
    );
}
