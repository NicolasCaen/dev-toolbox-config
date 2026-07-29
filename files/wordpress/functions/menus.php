<?php
/**
 * Enregistrement des menus pour {{projectName}}
 *
 * @author {{author}}
 * @package {{projectName}}
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Enregistre les emplacements de menus.
 */
function {{functionPrefix}}_register_menus() {
	register_nav_menus(
		array(
			'primary' => __( 'Menu principal', '{{projectName}}' ),
			'footer'  => __( 'Menu pied de page', '{{projectName}}' ),
		)
	);
}
add_action( 'after_setup_theme', '{{functionPrefix}}_register_menus' );
