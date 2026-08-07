<?php

function enqueue_theme_styles() {
  wp_enqueue_style('main-style', get_stylesheet_uri());
}

add_action('wp_enqueue_scripts', 'enqueue_theme_styles');


function ajouter_css_editor_gutenberg() {
  wp_enqueue_style('editor-css', get_template_directory_uri() . '/editor.css', array(), filemtime(get_template_directory() . '/editor.css'));
}

add_action('enqueue_block_editor_assets', 'ajouter_css_editor_gutenberg');