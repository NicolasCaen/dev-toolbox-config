document.addEventListener('DOMContentLoaded', function () {
    const grids = document.querySelectorAll('.expandable-grid');

    grids.forEach(function (grid) {
        const items = grid.querySelectorAll('.expandable-grid__item');

        items.forEach(function (item) {
            item.addEventListener('mouseenter', function () {
                items.forEach(function (i) { i.classList.remove('active'); });
                item.classList.add('active');
            });

            item.addEventListener('touchstart', function () {
                items.forEach(function (i) { i.classList.remove('active'); });
                item.classList.add('active');
            }, { passive: true });
        });
    });
});