document.addEventListener('DOMContentLoaded', function () {
    const checkbox = document.getElementById('enable_dhcp_helper_checkbox');
    const helperField = document.getElementById('id_dhcp_helper');

    function toggle() {
        helperField.style.display = checkbox.checked ? 'block' : 'none';
    }

    toggle();
    checkbox.addEventListener('change', toggle);
});