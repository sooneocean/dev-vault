<?php
/**
 * YOLO LAB Widget Auto-Deployment Plugin
 * Registers custom REST endpoints for widget deployment
 * To use: Upload to wp-content/mu-plugins/ or activate as plugin
 */

// Ensure WordPress is loaded
if (!defined('ABSPATH')) {
    exit;
}

class YOLOLabWidgetDeployer {

    public static function init() {
        add_action('rest_api_init', [__CLASS__, 'register_endpoints']);
        add_action('plugins_loaded', [__CLASS__, 'auto_deploy']);
    }

    public static function register_endpoints() {
        // Endpoint for widget deployment
        register_rest_route('yololab/v1', '/deploy-widgets', [
            'methods' => 'POST',
            'callback' => [__CLASS__, 'deploy_widgets'],
            'permission_callback' => function() {
                return current_user_can('manage_widgets') || current_user_can('manage_options');
            }
        ]);

        // Endpoint for Yoast configuration
        register_rest_route('yololab/v1', '/configure-yoast', [
            'methods' => 'POST',
            'callback' => [__CLASS__, 'configure_yoast'],
            'permission_callback' => function() {
                return current_user_can('manage_options');
            }
        ]);

        // Public endpoint (no auth required for auto-deployment)
        register_rest_route('yololab/v1', '/auto-deploy', [
            'methods' => 'POST',
            'callback' => [__CLASS__, 'auto_deploy_handler'],
            'permission_callback' => '__return_true'
        ]);
    }

    public static function deploy_widgets($request) {
        $widgets = [
            [
                'title' => 'About',
                'content' => '<h3>About</h3>
<ul>
  <li><a href="/about/">About YOLO LAB</a></li>
  <li><a href="/contact/">Contact</a></li>
  <li><a href="/privacy/">Privacy Policy</a></li>
</ul>'
            ],
            [
                'title' => 'Categories',
                'content' => '<h3>Categories</h3>
<ul>
  <li><a href="/category/film/">Film</a></li>
  <li><a href="/category/music/">Music</a></li>
  <li><a href="/category/tech/">Tech</a></li>
  <li><a href="/category/sports/">Sports</a></li>
</ul>'
            ],
            [
                'title' => 'Popular Tags',
                'content' => '<h3>Popular Tags</h3>
<ul>
  <li><a href="/tag/ai/">AI</a></li>
  <li><a href="/tag/entertainment/">Entertainment</a></li>
  <li><a href="/tag/music-news/">Music News</a></li>
  <li><a href="/tag/movie-reviews/">Movie Reviews</a></li>
</ul>'
            ]
        ];

        $results = [];

        foreach ($widgets as $widget) {
            $widget_data = self::create_widget($widget['title'], $widget['content']);
            $results[] = [
                'title' => $widget['title'],
                'success' => $widget_data !== false,
                'id' => $widget_data
            ];
        }

        return new WP_REST_Response([
            'message' => 'Widget deployment completed',
            'widgets' => $results
        ], 200);
    }

    public static function create_widget($title, $content) {
        global $wp_registered_widget_controls;

        // Find footer sidebar
        $sidebars = wp_get_sidebars_widgets();
        $footer_sidebar = false;

        foreach ($sidebars as $sidebar_id => $widgets) {
            if (strpos($sidebar_id, 'footer') !== false) {
                $footer_sidebar = $sidebar_id;
                break;
            }
        }

        if (!$footer_sidebar) {
            // Default to first available sidebar
            $footer_sidebar = 'sidebar-1';
        }

        // Get custom_html widget settings
        $option_name = 'widget_custom_html';
        $settings = get_option($option_name, []);

        // Find next widget number
        $num = 1;
        while (isset($settings[$num])) {
            $num++;
        }

        // Create widget
        $settings[$num] = [
            'title' => $title,
            'content' => $content,
            'filter' => 'content_save_pre'
        ];

        update_option($option_name, $settings);

        // Register widget in sidebar
        $sidebar_widgets = isset($sidebars[$footer_sidebar]) ? $sidebars[$footer_sidebar] : [];
        $sidebar_widgets[] = 'custom_html-' . $num;

        $sidebars[$footer_sidebar] = $sidebar_widgets;
        wp_set_sidebars_widgets($sidebars);

        return 'custom_html-' . $num;
    }

    public static function configure_yoast($request) {
        // Configure Yoast SEO settings
        $yoast_settings = [
            'wpseo_titles' => [
                'breadcrumbs-enable' => true,
                'breadcrumbs-schema' => true,
                'breadcrumbs-home' => true,
                'breadcrumbs-single-post' => true,
                'breadcrumbs-archive' => true
            ]
        ];

        foreach ($yoast_settings as $option => $value) {
            update_option($option, $value);
        }

        return new WP_REST_Response([
            'message' => 'Yoast SEO configured',
            'settings' => $yoast_settings
        ], 200);
    }

    public static function auto_deploy_handler($request) {
        // This endpoint runs without auth requirement
        // Execute both widget deployment and Yoast config

        $widget_result = self::deploy_widgets($request);
        $yoast_result = self::configure_yoast($request);

        return new WP_REST_Response([
            'status' => 'success',
            'message' => 'Full auto-deployment completed',
            'widgets' => $widget_result->get_data()['widgets'],
            'yoast' => $yoast_result->get_data()
        ], 200);
    }

    public static function auto_deploy() {
        // Auto-execute on plugins_loaded if deployment flag is set
        if (defined('YOLOLAB_AUTO_DEPLOY') && YOLOLAB_AUTO_DEPLOY) {
            self::deploy_widgets(null);
            self::configure_yoast(null);
        }
    }
}

// Initialize
YOLOLabWidgetDeployer::init();

// Make classes available
require_once(ABSPATH . 'wp-includes/rest-api.php');
