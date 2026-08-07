<?php
add_action( 'after_setup_theme', function() {
    remove_theme_support( 'core-block-patterns' );
} );
add_filter( 'should_load_remote_block_patterns', '__return_false' );