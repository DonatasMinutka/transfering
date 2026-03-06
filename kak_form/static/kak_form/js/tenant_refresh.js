document.addEventListener('DOMContentLoaded', function() {
    const tenantField = document.querySelector('#id_tenant');
    
    if (!tenantField) return;
    let editingTenantId = null;
    const addButton = document.createElement('a');
    addButton.href = '#';
    addButton.className = 'btn btn-sm btn-success';
    addButton.innerHTML = '<i class="mdi mdi-plus-thick"></i> Add Tenant';
    const editButton = document.createElement('a');
    editButton.href = '#';
    editButton.className = 'btn btn-sm btn-success';
    editButton.innerHTML = '<i class="mdi mdi-plus-thick"></i> Edit Tenant';         


    const tomSelectWrapper = tenantField.parentNode.querySelector('.ts-wrapper');
    const select2Container = tenantField.parentNode.querySelector('.select2-container');
    const widget = tomSelectWrapper || select2Container || tenantField;
    const rowWrapper = document.createElement('div');
    rowWrapper.style.cssText = `
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: nowrap;
    `;

    widget.parentNode.insertBefore(rowWrapper, widget);
    rowWrapper.appendChild(widget);
    rowWrapper.parentNode.insertBefore(addButton, rowWrapper.nextSibling);
    rowWrapper.parentNode.insertBefore(editButton, addButton.nextSibling);
    addButton.addEventListener('click', function(e) {
        e.preventDefault();
        
        editingTenantId = null;
        const popup = window.open(
            '/plugins/kak-Form/add_tenant/',
            'addTenant',
            'width=900,height=900,scrollbars=yes,resizable=yes'
        );
        
        const checkSuccess = setInterval(function() {
            if (popup.closed) {
                clearInterval(checkSuccess);
                return;
            }
            
            try {
                if (popup.location.pathname.match(/\/tenancy\/tenants\/\d+\/$/)) {
                    setTimeout(() => {
                        popup.close();
                    }, 300);
                    clearInterval(checkSuccess);
                    refreshTenantDropdown();
                }
            } catch (e) {
            }
        }, 300);
    });
    editButton.addEventListener('click', function (e) {
        e.preventDefault();

        const tenantId = tenantField.value;
        
        if (!tenantId) {
            showErrorMessage('Please select a Tenant to edit');
            return;
        }

        editingTenantId = tenantId;  

        const popup = window.open(
            '/plugins/kak-Form/tenant/' + tenantId + '/edit/',
            'editTenant',
            'width=900,height=900,scrollbars=yes,resizable=yes'
        );

        const checkSuccess = setInterval(function () {
            if (popup.closed) {
                clearInterval(checkSuccess);
                return;
            }
            try {
                if (popup.location.pathname.match(/\/tenancy\/tenants\/\d+\/$/)) {
                    setTimeout(() => popup.close(), 300);
                    clearInterval(checkSuccess);
                    refreshTenantDropdown();
                }
            } catch (e) { }
        }, 300);
    });
    function refreshTenantDropdown() {
        const cacheBreaker = new Date().getTime();
        fetch('/api/tenancy/tenants/?limit=0&_=' + cacheBreaker)
            .then(response => response.json())
            .then(data => {
                if (tenantField.tomselect) {
                    const ts = tenantField.tomselect;
                    tenantField.innerHTML = '';
                    data.results.forEach(tenant => {
                            const option = document.createElement('option');
                            option.value = tenant.id;
                            option.text = tenant.display;
                            tenantField.appendChild(option);
                        });


                        const tenantToSelect = editingTenantId || 
                            (data.results.length > 0 ? 
                                data.results.reduce((a, b) =>
                                    new Date(a.created) > new Date(b.created) ? a : b
                                ).id 
                            : null);

                        ts.sync();  
                        ts.clearOptions();  
                        
                        data.results.forEach(tenant => {
                            ts.addOption({ value: tenant.id, text: tenant.display });
                        });

                        if (tenantToSelect) {
                            ts.setValue(tenantToSelect);
                            console.log('Selected tenant:', tenantToSelect);
                        }
                        
                        if (editingTenantId) {
                            editingTenantId = null;
                        }
                    }
                    
                    tenantField.dispatchEvent(new Event('change', { bubbles: true }));
                    showSuccessMessage('Tenant list updated.');
                })
                .catch(err => {
                    console.error('Fetch error:', err);
                    showErrorMessage('Failed to refresh Tenant list');
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