<?php
/**
 * WP-CLI Batch SEO Optimizer for Yoast SEO
 *
 * Automatically generates and sets focus keyphrases for all published posts
 * that are missing one. Designed for YOLO LAB's content types (movies, music,
 * events, tech, food reviews).
 *
 * Usage (via SSH on WordPress.com Business or self-hosted):
 *
 *   # Dry run — preview generated keyphrases without saving
 *   wp eval-file wp-seo-batch.php -- --dry-run
 *
 *   # Process all posts (default batch size: 50)
 *   wp eval-file wp-seo-batch.php
 *
 *   # Custom batch size and offset (resume from post #500)
 *   wp eval-file wp-seo-batch.php -- --batch-size=100 --offset=500
 *
 *   # Process only specific category
 *   wp eval-file wp-seo-batch.php -- --category=MOVIE
 *
 *   # Export CSV report of generated keyphrases
 *   wp eval-file wp-seo-batch.php -- --export=seo-report.csv
 */

// ── Parse CLI arguments ──────────────────────────────────────────────
$args     = array_slice( $GLOBALS['argv'] ?? [], 0 );
$dry_run  = in_array( '--dry-run', $args, true );
$batch    = 50;
$offset   = 0;
$category = '';
$export   = '';

foreach ( $args as $arg ) {
    if ( preg_match( '/^--batch-size=(\d+)$/', $arg, $m ) ) $batch    = (int) $m[1];
    if ( preg_match( '/^--offset=(\d+)$/', $arg, $m ) )     $offset   = (int) $m[1];
    if ( preg_match( '/^--category=(.+)$/', $arg, $m ) )     $category = $m[1];
    if ( preg_match( '/^--export=(.+)$/', $arg, $m ) )       $export   = $m[1];
}

// ── Keyphrase generation engine ──────────────────────────────────────

/**
 * Generate a focus keyphrase from a post title.
 *
 * Strategy priority:
 * 1. Extract content inside《》brackets (movie/album/show names)
 * 2. Combine bracket content with nearby proper nouns
 * 3. Fall back to first meaningful segment of title
 */
function generate_focus_keyphrase( $title ) {
    $title = html_entity_decode( $title, ENT_QUOTES, 'UTF-8' );
    $title = trim( $title );

    // ── Strategy 1: Extract《bracket content》with context ──
    if ( preg_match( '/《([^》]+)》/', $title, $m ) ) {
        $bracket = trim( $m[1] );
        $before  = trim( mb_substr( $title, 0, mb_strpos( $title, '《' ) ) );
        $after   = '';

        // Get text after bracket
        $after_pos = mb_strpos( $title, '》' );
        if ( $after_pos !== false ) {
            $raw_after = mb_substr( $title, $after_pos + 1 );
            // Clean punctuation at start
            $raw_after = preg_replace( '/^[：:，,、\s]+/u', '', $raw_after );
            $after = $raw_after;
        }

        // If before text is a person/brand name (short, no punctuation)
        if ( mb_strlen( $before ) > 0 && mb_strlen( $before ) <= 12 ) {
            $before_clean = preg_replace( '/[！!？?。，,：:；;、\s]+$/u', '', $before );
            if ( mb_strlen( $before_clean ) > 0 ) {
                return trim( $before_clean . ' ' . $bracket );
            }
        }

        // If bracket content is very short, add context from after
        if ( mb_strlen( $bracket ) <= 4 && mb_strlen( $after ) > 0 ) {
            $after_segment = preg_split( '/[，,。！!？?：:；;、]/u', $after )[0];
            if ( mb_strlen( $after_segment ) <= 10 ) {
                return trim( $bracket . ' ' . $after_segment );
            }
        }

        // Add suffix type keywords for common categories
        $suffix = detect_content_type_suffix( $title, $after );
        if ( $suffix ) {
            return trim( $bracket . ' ' . $suffix );
        }

        return $bracket;
    }

    // ── Strategy 2: Split by Chinese/English punctuation ──
    $segments = preg_split( '/[：|｜！？!?\-—–\/]/u', $title );
    $first    = trim( $segments[0] ?? $title );

    // If first segment is too long, try to find a natural break
    if ( mb_strlen( $first ) > 15 ) {
        // Try splitting by comma or space
        $sub = preg_split( '/[，,、\s]+/u', $first );
        if ( count( $sub ) > 1 ) {
            // Take first 2 meaningful parts
            $parts = array_filter( $sub, function( $s ) {
                return mb_strlen( trim( $s ) ) > 1;
            });
            $parts = array_values( $parts );
            $first = implode( ' ', array_slice( $parts, 0, 2 ) );
        }
    }

    // If still too long, truncate intelligently
    if ( mb_strlen( $first ) > 20 ) {
        $first = mb_substr( $first, 0, 15 );
    }

    // Clean trailing punctuation
    $first = preg_replace( '/[，,。！!？?：:；;、\s]+$/u', '', $first );

    return $first;
}

/**
 * Detect content type from title context and return a search-friendly suffix.
 */
function detect_content_type_suffix( $title, $after_bracket ) {
    $full = $title . ' ' . $after_bracket;

    // Movie/Film indicators
    $movie_patterns = [
        '/影評|影帝|影后|票房|上映|院線|大銀幕|戲院|IMAX|電影|導演|演技/',
        '/movie|film|review|box.?office/i',
    ];
    foreach ( $movie_patterns as $p ) {
        if ( preg_match( $p, $full ) ) return '電影';
    }

    // Music indicators
    $music_patterns = [
        '/專輯|演唱會|巡演|搶票|新歌|單曲|歌手|樂團|音樂/',
        '/album|concert|tour|single|music/i',
    ];
    foreach ( $music_patterns as $p ) {
        if ( preg_match( $p, $full ) ) return '';  // Music titles are usually self-explanatory
    }

    // Food/Product review
    if ( preg_match( '/實測|開箱|評價|推薦|試吃|試喝|味蕾/', $full ) ) {
        return '評價';
    }

    return '';
}

// ── Main processing loop ─────────────────────────────────────────────

WP_CLI::log( "=== YOLO LAB SEO Batch Optimizer ===" );
WP_CLI::log( $dry_run ? "MODE: Dry Run (no changes will be saved)" : "MODE: Live (changes will be saved)" );
WP_CLI::log( "" );

// Build query args
$query_args = [
    'post_type'      => 'post',
    'post_status'    => 'publish',
    'posts_per_page' => $batch,
    'offset'         => $offset,
    'orderby'        => 'date',
    'order'          => 'DESC',
    'meta_query'     => [
        'relation' => 'OR',
        [
            'key'     => '_yoast_wpseo_focuskw',
            'compare' => 'NOT EXISTS',
        ],
        [
            'key'     => '_yoast_wpseo_focuskw',
            'value'   => '',
            'compare' => '=',
        ],
    ],
];

if ( $category ) {
    $query_args['category_name'] = $category;
}

// Count total posts needing optimization
$count_args = $query_args;
$count_args['posts_per_page'] = -1;
$count_args['fields'] = 'ids';
$count_query = new WP_Query( $count_args );
$total = $count_query->found_posts;
wp_reset_postdata();

WP_CLI::log( "Found {$total} published posts without focus keyphrase." );
WP_CLI::log( "Processing batch of {$batch} starting at offset {$offset}." );
WP_CLI::log( str_repeat( '─', 60 ) );

// CSV export setup
$csv_rows = [];
if ( $export ) {
    $csv_rows[] = [ 'post_id', 'title', 'slug', 'focus_keyphrase', 'has_meta_desc' ];
}

// Process posts
$query   = new WP_Query( $query_args );
$updated = 0;
$skipped = 0;
$errors  = 0;

if ( $query->have_posts() ) {
    $progress = WP_CLI\Utils\make_progress_bar( 'Optimizing SEO', $query->post_count );

    while ( $query->have_posts() ) {
        $query->the_post();
        $post_id = get_the_ID();
        $title   = get_the_title();
        $slug    = get_post_field( 'post_name', $post_id );

        // Generate keyphrase
        $keyphrase = generate_focus_keyphrase( $title );

        if ( empty( $keyphrase ) ) {
            WP_CLI::warning( "[#{$post_id}] Could not generate keyphrase for: {$title}" );
            $skipped++;
            $progress->tick();
            continue;
        }

        // Check if meta description exists
        $existing_desc = get_post_meta( $post_id, '_yoast_wpseo_metadesc', true );
        $has_desc = ! empty( $existing_desc );

        // Auto-generate meta description from excerpt if missing
        $meta_desc = $existing_desc;
        if ( ! $has_desc ) {
            $excerpt = get_the_excerpt();
            if ( $excerpt ) {
                $meta_desc = mb_substr( wp_strip_all_tags( $excerpt ), 0, 156 );
            }
        }

        if ( $dry_run ) {
            WP_CLI::log( "[DRY] #{$post_id} | {$keyphrase} | " . mb_substr( $title, 0, 40 ) );
        } else {
            // Update focus keyphrase
            $result = update_post_meta( $post_id, '_yoast_wpseo_focuskw', $keyphrase );

            // Update meta description if it was empty
            if ( ! $has_desc && $meta_desc ) {
                update_post_meta( $post_id, '_yoast_wpseo_metadesc', $meta_desc );
            }

            if ( $result === false ) {
                WP_CLI::warning( "[#{$post_id}] Failed to update: {$title}" );
                $errors++;
            } else {
                $updated++;
            }
        }

        // CSV export row
        if ( $export ) {
            $csv_rows[] = [ $post_id, $title, $slug, $keyphrase, $has_desc ? 'yes' : 'generated' ];
        }

        $progress->tick();
    }
    $progress->finish();
}
wp_reset_postdata();

// ── Summary ──────────────────────────────────────────────────────────

WP_CLI::log( "" );
WP_CLI::log( str_repeat( '─', 60 ) );
WP_CLI::log( "=== Summary ===" );
WP_CLI::log( "Total needing optimization: {$total}" );
WP_CLI::log( "Processed this batch:       {$query->post_count}" );

if ( $dry_run ) {
    WP_CLI::log( "Mode: DRY RUN (nothing saved)" );
} else {
    WP_CLI::success( "Updated: {$updated}" );
    if ( $skipped ) WP_CLI::warning( "Skipped: {$skipped}" );
    if ( $errors )  WP_CLI::error( "Errors:  {$errors}", false );
}

if ( $total > $offset + $batch ) {
    $next_offset = $offset + $batch;
    WP_CLI::log( "" );
    WP_CLI::log( ">>> More posts remaining. Run next batch with:" );
    WP_CLI::log( "    wp eval-file wp-seo-batch.php -- --offset={$next_offset}" );
}

// ── Export CSV ────────────────────────────────────────────────────────

if ( $export && count( $csv_rows ) > 1 ) {
    $fp = fopen( $export, 'w' );
    // UTF-8 BOM for Excel compatibility
    fwrite( $fp, "\xEF\xBB\xBF" );
    foreach ( $csv_rows as $row ) {
        fputcsv( $fp, $row );
    }
    fclose( $fp );
    WP_CLI::success( "Exported report to: {$export}" );
}
