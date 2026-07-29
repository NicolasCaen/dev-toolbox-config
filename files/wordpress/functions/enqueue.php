<?php
/**
 * Enqueue des scripts et styles pour {{projectName}}
 *
 * @author {{author}}
 * @package {{projectName}}
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Charge les assets du thème.
 */
function {{functionPrefix}}_enqueue_assets() {
	wp_enqueue_style(
		'{{projectName}}-style',
		get_stylesheet_uri(),
		array(),
		wp_get_theme()->get( 'Version' )
	);

	wp_enqueue_script(
		'{{projectName}}-script',
		get_template_directory_uri() . '/assets/js/script.js',
		array(),
		wp_get_theme()->get( 'Version' ),
		true
	);
}
add_action( 'wp_enqueue_scripts', '{{functionPrefix}}_enqueue_assets' );
