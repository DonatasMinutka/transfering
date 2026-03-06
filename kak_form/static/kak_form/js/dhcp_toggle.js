(function() {
    'use strict';
    const cidrToMask = {
        '/8': '255.0.0.0',
        '/9': '255.128.0.0',
        '/10': '255.192.0.0',
        '/11': '255.224.0.0',
        '/12': '255.240.0.0',
        '/13': '255.248.0.0',
        '/14': '255.252.0.0',
        '/15': '255.254.0.0',
        '/16': '255.255.0.0',
        '/17': '255.255.128.0',
        '/18': '255.255.192.0',
        '/19': '255.255.224.0',
        '/20': '255.255.240.0',
        '/21': '255.255.248.0',
        '/22': '255.255.252.0',
        '/23': '255.255.254.0',
        '/24': '255.255.255.0',
        '/25': '255.255.255.128',
        '/26': '255.255.255.192',
        '/27': '255.255.255.224',
        '/28': '255.255.255.240',
        '/29': '255.255.255.248',
        '/30': '255.255.255.252'
    };
    
    function updateDhcpAddresses() {
        const lanIpField = document.querySelector('[name="LAN_IP_Address_And_Subnet_Mask"]');
        const dhcpStartField = document.querySelector('[name="DHCP_Start_Address"]');
        const dhcpEndField = document.querySelector('[name="DHCP_End_Address"]');
        const checkbox = document.getElementById('enable_dhcp_checkbox');
        
        if (!lanIpField || !dhcpStartField || !dhcpEndField || !checkbox) {
            return;
        }
        
        if (!checkbox.checked) {
            return;
        }
        
        const lanIpWithMask = lanIpField.value.trim();
        if (!lanIpWithMask || !lanIpWithMask.includes('/')) {
            return;
        }

        const [lanIp, cidr] = lanIpWithMask.split('/');
        const subnetMask = cidrToMask['/' + cidr];

        if (!lanIp || !subnetMask) {
            return;
        }

        const lanIpParts = lanIp.split('.').map(Number);
        const subnetMaskParts = subnetMask.split('.').map(Number);

        if (lanIpParts.length === 4 && subnetMaskParts.length === 4 &&
            lanIpParts.every(part => part >= 0 && part <= 255) &&
            subnetMaskParts.every(part => part >= 0 && part <= 255)) {
            const networkAddressParts = lanIpParts.map((part, i) => part & subnetMaskParts[i]);
            const invertedSubnetMaskParts = subnetMaskParts.map(part => ~part & 255);
            const broadcastAddressParts = networkAddressParts.map((part, i) => part | invertedSubnetMaskParts[i]);
            const dhcpStart = networkAddressParts.slice(0, 3).concat(100).join('.');
            const dhcpEnd = networkAddressParts.slice(0, 3).concat(200).join('.');
            
            if (!dhcpStartField.value || dhcpStartField.value.trim() === '') {
                dhcpStartField.value = dhcpStart;
            }
            if (!dhcpEndField.value || dhcpEndField.value.trim() === '') {
                dhcpEndField.value = dhcpEnd;
            }
        }
    }
    
    function toggleDHCPFields() {
        const checkbox = document.getElementById('enable_dhcp_checkbox');
        if (!checkbox) {
            return;
        }
        
        const dhcpInputs = document.querySelectorAll('.dhcp-field');
        dhcpInputs.forEach(function(input) {
            let formGroup = input.closest('.form-group');
            if (!formGroup) formGroup = input.closest('.mb-3');
            if (!formGroup) formGroup = input.closest('[class*="field"]');
            if (!formGroup) formGroup = input.closest('tr');
            if (!formGroup) formGroup = input.parentElement.parentElement;
            
            if (formGroup) {
                formGroup.style.display = checkbox.checked ? '' : 'none';
            }
            
            if (checkbox.checked) {
                input.disabled = false;
                input.required = true;
            } else {
                input.disabled = true;
                input.required = false;
            }
        });
        
        if (checkbox.checked) {
            updateDhcpAddresses();
        }
    }
    
    function setupEventListeners() {
        const checkbox = document.getElementById('enable_dhcp_checkbox');
        const lanIpField = document.querySelector('[name="LAN_IP_Address_And_Subnet_Mask"]');
        
        if (checkbox) {
            checkbox.addEventListener('change', toggleDHCPFields);
        }
        
        if (lanIpField) {
            lanIpField.addEventListener('input', updateDhcpAddresses);
            lanIpField.addEventListener('blur', updateDhcpAddresses);
            lanIpField.addEventListener('change', updateDhcpAddresses);
        }
        
        toggleDHCPFields();
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupEventListeners);
    } else {
        setupEventListeners();
    }
})(); 