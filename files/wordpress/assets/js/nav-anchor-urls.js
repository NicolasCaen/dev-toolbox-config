document.addEventListener('DOMContentLoaded', function () {
  var navLinks = document.querySelectorAll('.wp-block-navigation .wp-block-navigation-item__content[href^="#"]');

  navLinks.forEach(function (link) {
    var hash = link.getAttribute('href');
    link.setAttribute('href', window.location.origin + '/' + hash);
  });
});
