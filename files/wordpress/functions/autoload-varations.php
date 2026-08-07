<?php

add_action('enqueue_block_editor_assets', 'ng1_enqueue_variations');

function ng1_enqueue_variations() {
    $variation_dir = get_template_directory() . '/variations';
    $variation_uri = get_template_directory_uri() . '/variations';

    if (!is_dir($variation_dir)) return;

    $files = glob($variation_dir . '/*.js');
    foreach ($files as $file) {
        $basename = basename($file, '.js');
        wp_enqueue_script(
            'ng1-var-' . $basename,
            $variation_uri . '/' . basename($file),
            ['wp-blocks', 'wp-dom-ready', 'wp-edit-post'],
            filemtime($file),
            true
        );
    }
}