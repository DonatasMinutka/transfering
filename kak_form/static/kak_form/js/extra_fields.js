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
    };
    
    function getFieldsForService(service) {
        const baseMapping = {
            'capn': ['capn','enable_dhcp'],
            'internet': ['enable_dhcp'],
            'isop': [],
            'wan_failover': ['enable_dhcp'],
            'nkdps': ['enable_dhcp'],
            'lte_5g_nokia':['enable_dhcp'],
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