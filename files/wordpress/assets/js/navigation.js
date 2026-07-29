/**
 * Navigation mobile pour {{projectName}}
 * @author {{author}}
 */
document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.querySelector('.menu-toggle');
  const navigation = document.querySelector('.main-navigation');

  if (!toggle || !navigation) {
    return;
  }

  toggle.addEventListener('click', function () {
    navigation.classList.toggle('is-open');
    toggle.setAttribute(
      'aria-expanded',
      navigation.classList.contains('is-open') ? 'true' : 'false'
    );
  });
});
