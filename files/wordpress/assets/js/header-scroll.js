document.addEventListener('DOMContentLoaded', function () {
    const header = document.querySelector('.site-header');

    if (!header) return;

    function updateHeaderState() {
        const headerHeight = header.offsetHeight;
        document.body.style.setProperty('--header-height', headerHeight + 'px');

        if (window.scrollY > headerHeight) {
            document.body.classList.add('not-on-top');
        } else {
            document.body.classList.remove('not-on-top');
        }
    }

    updateHeaderState();
    window.addEventListener('scroll', updateHeaderState, { passive: true });
    window.addEventListener('resize', updateHeaderState);

    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#' || targetId.length < 2) return;
            const target = document.querySelector(targetId);
            if (!target) return;
            e.preventDefault();
            var headerHeight = header.offsetHeight * 2;
            var targetPosition = target.getBoundingClientRect().top + window.scrollY - headerHeight;
            window.scrollTo({ top: targetPosition, behavior: 'smooth' });
        });
    });
});
