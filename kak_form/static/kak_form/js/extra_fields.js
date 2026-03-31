document.addEventListener('DOMContentLoaded', function() {
    const serviceField = document.querySelector('select[name="Services"]');
    const deviceTypeField = document.querySelector('select[name="device_type"]');

    if (!serviceField) return;
    
    const fields = {
        capn: {
            input: document.querySelector('input[name="CAPN_Address"]'),
            get container() { return this.input?.closest('tr') || this.input?.parentElement.parentElement; }
        },
        enable_dhcp: {
            input: document.querySelector('input[name="Enable_DHCP"]'),
            get container() { return this.input?.closest('tr') || this.input?.parentElement.parentElement; }
        },
        enable_dhcp_helper: {
            input: document.querySelector('input[name="Enable_DHCP_HELPER"]'),
            get container() { return this.input?.closest('tr') || this.input?.parentElement.parentElement; }
        },
        wan: {
            input: document.querySelector('input[name="Given_WAN_Address"]'),
            get container() { return this.input?.closest('tr') || this.input?.parentElement.parentElement; }
        },       
        tunnel: {
            input: document.querySelector('input[name="Tunnel"]'),
            get container() { return this.input?.closest('tr') || this.input?.parentElement.parentElement; }
        },
              
        cellular: {
            input: document.querySelector('input[name="Cellular"]'),
            get container() { return this.input?.closest('tr') || this.input?.parentElement.parentElement; }
        },
    };
    
    function getFieldsForService(service) {
        const baseMapping = {
            'capn': ['capn','enable_dhcp','wan', 'enable_dhcp_helper'],
            'internet': ['enable_dhcp','wan','enable_dhcp_helper'],
            'isop': ['wan'],
            'wan_failover': ['enable_dhcp','wan','enable_dhcp_helper'],
            'nkdps': ['enable_dhcp','wan','enable_dhcp_helper'],
            'lte_5g_nokia':['enable_dhcp','enable_dhcp_helper'],
            '4g':['enable_dhcp','wan','cellular','tunnel','enable_dhcp_helper'],
            '4g_apn':['capn', 'enable_dhcp','wan','cellular','tunnel','enable_dhcp_helper'],
        };
        
        let fieldsToShow = baseMapping[service] || [];
        return fieldsToShow;
    }
    
    function showField(fieldName) {
        const field = fields[fieldName];
        if (field && field.container) {
            field.container.style.display = '';
            if (field.input) field.input.required = true;
        }
    }
    
    function hideField(fieldName) {
        const field = fields[fieldName];
        if (field && field.container) {
            field.container.style.display = 'none';
            if (field.input) {
                field.input.required = false;
            }
        }
    }
    
    function toggleFields() {
        const selectedService = serviceField.value;
        Object.keys(fields).forEach(hideField);
        const fieldsToShow = getFieldsForService(selectedService);
        fieldsToShow.forEach(showField);
    }

    toggleFields();
    serviceField.addEventListener('change', toggleFields);
    if (deviceTypeField) {
        deviceTypeField.addEventListener('change', toggleFields);
    }
});