document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.wp-block-navigation__responsive-container a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function () {
            var menuContainer = this.closest('.wp-block-navigation__responsive-container');
            if (menuContainer && menuContainer.classList.contains('is-menu-open')) {
                var closeBtn = menuContainer.querySelector('.wp-block-navigation-overlay-close');
                if (closeBtn) closeBtn.click();
            }
        });
    });
});
