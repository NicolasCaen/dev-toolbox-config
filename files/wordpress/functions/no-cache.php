<?php
function ng1_flush_cache() {
    wp_cache_flush();
    wp_clean_themes_cache();

}
add_filter('should_load_separate_core_block_assets', '__return_false');
function ng1_flush_gutenberg_cache() {
    delete_transient('_wp_block_patterns_cache');
    delete_transient('_wp_block_pattern_categories_cache');
    delete_transient('_wp_block_styles_cache');
    delete_transient('_wp_gutenberg_features');
    delete_transient('block_templates');
    delete_transient('global_styles');
    wp_clean_themes_cache();
}
function ng1_flush_transients_cache() {
    global $wpdb;
    $wpdb->query("DELETE FROM $wpdb->options WHERE option_name LIKE '_transient_%'");
}


function ng1_check_theme_changes_and_flush_cache() {
    $theme_dir = get_stylesheet_directory();
    $folders_to_watch = ['patterns', 'templates', 'parts'];
    $current_hash = '';

    foreach ($folders_to_watch as $folder) {
        $dir_path = trailingslashit($theme_dir) . $folder;

        if (!is_dir($dir_path)) {
            continue;
        }

        $files = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($dir_path, FilesystemIterator::SKIP_DOTS)
        );

        foreach ($files as $file) {
            // On concatène le nom + date de modification
            $current_hash .= $file->getFilename() . $file->getMTime();
        }
    }

    $current_hash = md5($current_hash);
    $stored_hash = get_transient('ng1_theme_cache_hash');

    if ($current_hash !== $stored_hash) {
        // Changement détecté, on flush le cache
        ng1_flush_gutenberg_cache();
        set_transient('ng1_theme_cache_hash', $current_hash, DAY_IN_SECONDS);
    }
}

// Appel sur chaque admin_init
add_action('init', 'ng1_check_theme_changes_and_flush_cache');