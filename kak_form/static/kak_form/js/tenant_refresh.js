document.addEventListener('DOMContentLoaded', function() {
    const tenantField = document.querySelector('#id_tenant');
    
    if (tenantField) {
        const addButton = document.createElement('a');
        addButton.href = '#';
        addButton.className = 'btn btn-sm btn-success';
        addButton.innerHTML = '<i class="mdi mdi-plus-thick"></i> Add Tenant';

        let insertPoint = tenantField.nextSibling;
        const select2Container = tenantField.parentNode.querySelector('.select2-container');
        const tomSelectWrapper = tenantField.parentNode.querySelector('.ts-wrapper');
        
        if (tomSelectWrapper) {
            insertPoint = tomSelectWrapper;
        } else if (select2Container) {
            insertPoint = select2Container;
        }
        
        if (insertPoint) {
            insertPoint.parentNode.insertBefore(addButton, insertPoint.nextSibling);
        } else {
            tenantField.parentNode.appendChild(addButton);
        }
        
        addButton.addEventListener('click', function(e) {
            e.preventDefault();
            
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
        
        function refreshTenantDropdown() {
            fetch('/api/tenancy/tenants/?limit=0')
                .then(response => response.json())
                .then(data => {
                    if (tenantField.tomselect) {
                        const tomselect = tenantField.tomselect;
                        tomselect.getValue();
                        tomselect.clearOptions();
                        data.results.forEach(tenant => {
                            tomselect.addOption({
                                value: tenant.id,
                                text: tenant.display
                            });
                        });
                        if (data.results.length > 0) {
                            const newestTenant = data.results.reduce((latest, tenant) => {
                                return new Date(tenant.created) > new Date(latest.created) ? tenant : latest;
                            });
                            tomselect.setValue(newestTenant.id);
                        }
                        
                        tomselect.refreshOptions(false);
                        showSuccessMessage('Tenant list updated. Newest tenant selected.');
                        return;
                    }
                    tenantField.dispatchEvent(new Event('change', { bubbles: true }));
                    showSuccessMessage('Tenant list updated. Newest tenant selected.');
                })
                .catch(error => {
                    console.error('Error refreshing tenants:', error);
                    showErrorMessage('Failed to refresh tenant list. Please refresh the page.');
                });
        }
        
        function showSuccessMessage(message) {
            const alert = document.createElement('div');
            alert.className = 'alert alert-success alert-dismissible';
            alert.style.position = 'fixed';
            alert.style.top = '20px';
            alert.style.right = '20px';
            alert.style.zIndex = '9999';
            alert.style.color = 'black'
            alert.style.backgroundColor = 'lime'
            alert.style.minWidth = '300px';
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.body.appendChild(alert);
            
            setTimeout(() => alert.remove(), 5000);
        }
        
        function showErrorMessage(message) {
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger alert-dismissible';
            alert.style.position = 'fixed';
            alert.style.top = '20px';
            alert.style.right = '20px';
            alert.style.zIndex = '9999';
            alert.style.color = 'black'
            alert.style.backgroundColor = 'red'
            alert.style.minWidth = '300px';
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.body.appendChild(alert);
            
            setTimeout(() => alert.remove(), 5000);
        }
    }
});