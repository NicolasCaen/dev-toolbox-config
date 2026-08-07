<?php
// Empêcher Contact Form 7 d'ajouter automatiquement des balises <p> et <br>
add_filter( 'wpcf7_autop_or_not', '__return_false' );

// Supprimer les balises <p> vides lors du rendu du formulaire CF7
// add_filter( 'wpcf7_form_elements', function ( $form ) {
//     $form = preg_replace( '/<p[^>]*>(?:\s|&nbsp;)*<\/p>/i', '', $form );
//     return $form;
// } );
