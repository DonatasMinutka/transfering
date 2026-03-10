document.addEventListener('DOMContentLoaded', function () {
    const siteField = document.querySelector('#id_site');

    if (!siteField) return;
    let editingSiteId = null;
    const addButton = document.createElement('a');
    addButton.href = '#';
    addButton.className = 'btn btn-sm btn-success';
    addButton.innerHTML = '<i class="mdi mdi-plus-thick"></i> Add Site';
    const editButton = document.createElement('a');
    editButton.href = '#';
    editButton.className = 'btn btn-sm btn-success';
    editButton.innerHTML = '<i class="mdi mdi-plus-thick"></i> Edit Site';
    const hintBtn = document.createElement('button');
    hintBtn.type = 'button';
    hintBtn.innerHTML = '<i class="mdi mdi-information-outline"></i>';
    hintBtn.style.cssText = `
        width: 28px;
        height: 28px;
        border: none;
        border-radius: 50%;
        background: transparent;
        color: #000000;
        cursor: pointer;
        font-size: 18px;
        flex-shrink: 0;
        transition: color 0.15s;
        vertical-align: middle;
        margin-left: 4px;
    `;

    const tooltip = document.createElement('div');
    tooltip.style.cssText = `
        position: fixed;
        z-index: 99999;
        background: #fff;
        color: #333;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 10px 14px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.18);
        min-width: 260px;
        max-width: 320px;
        font-size: 0.85rem;
        display: none;
        pointer-events: none;
    `;
    tooltip.innerHTML = `
        <div style="font-weight:600; margin-bottom:6px;">
            <i class="mdi mdi-map-marker"></i> Adreso pavyzdžiai
        </div>
        <p style="margin:0 0 6px; color:#6c757d; font-size:0.78rem;">
            Kaip turi atrodyti tvarkingas adresas:
        </p>
        <code style="display:block; background:#f0f4ff; color:#3a5bd9; padding:4px 8px; border-radius:4px; margin-bottom:4px; font-family:monospace; font-size:0.82rem; white-space:normal;">
            J. Basanavičiaus g. 93, Kėdainiai
        </code>
        <code style="display:block; background:#f0f4ff; color:#3a5bd9; padding:4px 8px; border-radius:4px; margin-bottom:4px; font-family:monospace; font-size:0.82rem; white-space:normal;">
            Žarijų g. 2C, Vilnius
        </code>
        <code style="display:block; background:#f0f4ff; color:#3a5bd9; padding:4px 8px; border-radius:4px; margin-bottom:0; font-family:monospace; font-size:0.82rem; white-space:normal;">
            Bausko g. 11, Ventos m., Ventos sen., Akmenės rajono sav.
        </code>
    `;
    document.body.appendChild(tooltip);

    function showTooltip() {
        const rect = hintBtn.getBoundingClientRect();
        tooltip.style.display = 'block';
        tooltip.style.top  = (rect.top + window.scrollY - 10) + 'px';
        tooltip.style.left = (rect.right + window.scrollX + 10) + 'px';
    }

    function hideTooltip() {
        tooltip.style.display = 'none';
    }

    hintBtn.addEventListener('mouseenter', showTooltip);
    hintBtn.addEventListener('mouseleave', hideTooltip);
    hintBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        if (tooltip.style.display === 'none') {
            showTooltip();
            tooltip.style.pointerEvents = 'auto'; 
        } else {
            hideTooltip();
        }
    });
    document.addEventListener('click', hideTooltip);

    const tomSelectWrapper = siteField.parentNode.querySelector('.ts-wrapper');
    const select2Container = siteField.parentNode.querySelector('.select2-container');
    const widget = tomSelectWrapper || select2Container || siteField;

    const rowWrapper = document.createElement('div');
    rowWrapper.style.cssText = `
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: nowrap;
    `;

    widget.parentNode.insertBefore(rowWrapper, widget);
    rowWrapper.appendChild(widget);
    rowWrapper.appendChild(hintBtn);
    rowWrapper.parentNode.insertBefore(addButton, rowWrapper.nextSibling);
    rowWrapper.parentNode.insertBefore(editButton, addButton.nextSibling);

    addButton.addEventListener('click', function (e) {
        e.preventDefault();

        editingSiteId = null;

        const popup = window.open(
            '/plugins/kak-Form/add_site/',
            'addSite',
            'width=900,height=900,scrollbars=yes,resizable=yes'
        );

        const checkSuccess = setInterval(function () {
            if (popup.closed) {
                clearInterval(checkSuccess);
                return;
            }
            try {
                if (popup.location.pathname.match(/\/dcim\/sites\/\d+\/$/)) {
                    setTimeout(() => popup.close(), 300);
                    clearInterval(checkSuccess);
                    refreshSiteDropdown();
                }
            } catch (e) { }
        }, 300);
    });
    editButton.addEventListener('click', function (e) {
        e.preventDefault();

        const siteId = siteField.value;
        
        if (!siteId) {
            showErrorMessage('Please select a site to edit');
            return;
        }

        editingSiteId = siteId;  

        const popup = window.open(
            '/plugins/kak-Form/site/' + siteId + '/edit/',
            'editSite',
            'width=900,height=900,scrollbars=yes,resizable=yes'
        );

        const checkSuccess = setInterval(function () {
            if (popup.closed) {
                clearInterval(checkSuccess);
                return;
            }
            try {
                if (popup.location.pathname.match(/\/dcim\/sites\/\d+\/$/)) {
                    setTimeout(() => popup.close(), 300);
                    clearInterval(checkSuccess);
                    refreshSiteDropdown();
                }
            } catch (e) { }
        }, 300);
    });
function refreshSiteDropdown() {
    const cacheBreaker = new Date().getTime();
    
    fetch('/api/dcim/sites/?limit=0&_=' + cacheBreaker)
        .then(r => r.json())
        .then(data => {
            if (siteField.tomselect) {
                const ts = siteField.tomselect;
                siteField.innerHTML = '';
                data.results.forEach(site => {
                    const option = document.createElement('option');
                    option.value = site.id;
                    option.textContent = site.display;
                    siteField.appendChild(option);
                });

                const siteToSelect = editingSiteId || 
                    (data.results.length > 0 ? 
                        data.results.reduce((a, b) =>
                            new Date(a.created) > new Date(b.created) ? a : b
                        ).id 
                    : null);

                ts.sync();  
                ts.clearOptions();  
                
                data.results.forEach(site => {
                    ts.addOption({ value: site.id, text: site.display });
                });

                if (siteToSelect) {
                    ts.setValue(siteToSelect);
                }
                
                if (editingSiteId) {
                    editingSiteId = null;
                }
            }
            
            siteField.dispatchEvent(new Event('change', { bubbles: true }));
            showSuccessMessage('Site list updated.');
        })
        .catch(err => {
            console.error('Fetch error:', err);
            showErrorMessage('Failed to refresh site list');
        });
}
    function makeAlert(message, bg) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-dismissible';
        alert.style.cssText = `
            position: fixed;
            top: 20px; right: 20px;
            z-index: 99999;
            min-width: 300px;
            color: black;
            background-color: ${bg};
        `;
        alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
    }

    function showSuccessMessage(msg) { makeAlert(msg, 'lime'); }
    function showErrorMessage(msg)   { makeAlert(msg, 'red'); }
});