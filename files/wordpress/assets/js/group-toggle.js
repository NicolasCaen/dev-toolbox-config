
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.group-toggle-js').forEach(function (group) {

        var toggle = group.querySelector('.group-toggle-js__toggle');
        var content = group.querySelector('.group-toggle-js__content');
        if (!toggle || !content) return;

        content.style.display = 'none';

        toggle.addEventListener('click', function () {
            var isActive = group.classList.toggle('active');
            content.style.display = isActive ? '' : 'none';
        });
    });
});
