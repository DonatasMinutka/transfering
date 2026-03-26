(function () {
    'use strict';

    const MAX_RANGES = 10;

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

    function toInt(parts) {
        return ((parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]) >>> 0;
    }

    function toIp(n) {
        return [
            (n >>> 24) & 255,
            (n >>> 16) & 255,
            (n >>> 8) & 255,
            n & 255
        ].join('.');
    }

    function getDefaultRange(lanIpWithMask) {
        if (!lanIpWithMask || !lanIpWithMask.includes('/')) return null;
        const [lanIp, cidr] = lanIpWithMask.split('/');
        const prefix = parseInt(cidr);
        const subnetMask = cidrToMask['/' + cidr];
        if (!lanIp || !subnetMask) return null;

        const lanParts = lanIp.split('.').map(Number);
        const maskParts = subnetMask.split('.').map(Number);
        if (lanParts.length !== 4 || maskParts.length !== 4) return null;

        const networkParts = lanParts.map((p, i) => p & maskParts[i]);
        const invertedMask = maskParts.map(p => ~p & 255);
        const broadcastParts = networkParts.map((p, i) => p | invertedMask[i]);

        const networkInt = toInt(networkParts);
        const broadcastInt = toInt(broadcastParts);
        const firstHost = networkInt + 1;
        const lastHost = broadcastInt - 1;

        let start, end;
        if (prefix <= 24) {
            start = toIp(networkInt + 100);
            end   = toIp(networkInt + 200);
        } else {
            start = toIp(firstHost);
            end   = toIp(lastHost);
        }
        return { start, end };
    }


    function serializeRanges() {
        const hidden = document.getElementById('id_dhcp_ranges');
        if (!hidden) return;

        const rows = document.querySelectorAll('.dhcp-range-row');
        const parts = [];
        rows.forEach(function (row) {
            const startInput = row.querySelector('.dhcp-range-start');
            const endInput   = row.querySelector('.dhcp-range-end');
            if (!startInput || !endInput) return;
            const s = startInput.value.trim();
            const e = endInput.value.trim();
            if (s && e) parts.push(s + '-' + e);
        });
        hidden.value = parts.join(';');
    }

    function updateCounter() {
        const container = document.getElementById('dhcp-ranges-container');
        const counter   = document.getElementById('dhcp-range-counter');
        const addBtn    = document.getElementById('dhcp-add-range-btn');
        if (!container || !counter || !addBtn) return;

        const count = container.querySelectorAll('.dhcp-range-row').length;
        counter.textContent = count + ' / ' + MAX_RANGES;

        if (count >= MAX_RANGES) {
            counter.style.color = '#dc3545';
            counter.title = 'Maximum of ' + MAX_RANGES + ' ranges reached. Extra ranges will be ignored on save.';
        } else {
            counter.style.color = '';
            counter.title = '';
        }
    }

    function createRangeRow(startVal, endVal) {
        const row = document.createElement('div');
        row.className = 'dhcp-range-row d-flex align-items-center gap-2 mb-2';
        row.style.cssText = 'gap:8px; margin-bottom:6px; flex-wrap:wrap; justify-content:center;';

        const startWrap = document.createElement('div');
        startWrap.style.cssText = 'display:flex; align-items:center; gap:4px;';
        const startLabel = document.createElement('span');
        startLabel.textContent = 'Start:';
        startLabel.style.cssText = 'font-size:0.85em; white-space:nowrap; min-width:36px;';
        const startInput = document.createElement('input');
        startInput.type = 'text';
        startInput.className = 'form-control dhcp-range-start';
        startInput.placeholder = '192.168.1.100';
        startInput.value = startVal || '';
        startInput.style.cssText = 'width:155px; display:inline-block;';
        startInput.addEventListener('input', serializeRanges);
        startInput.addEventListener('blur',  serializeRanges);
        startWrap.appendChild(startLabel);
        startWrap.appendChild(startInput);

        const endWrap = document.createElement('div');
        endWrap.style.cssText = 'display:flex; align-items:center; gap:4px;';
        const endLabel = document.createElement('span');
        endLabel.textContent = 'End:';
        endLabel.style.cssText = 'font-size:0.85em; white-space:nowrap; min-width:28px;';
        const endInput = document.createElement('input');
        endInput.type = 'text';
        endInput.className = 'form-control dhcp-range-end';
        endInput.placeholder = '192.168.1.200';
        endInput.value = endVal || '';
        endInput.style.cssText = 'width:155px; display:inline-block;';
        endInput.addEventListener('input', serializeRanges);
        endInput.addEventListener('blur',  serializeRanges);
        endWrap.appendChild(endLabel);
        endWrap.appendChild(endInput);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.textContent = '✕';
        removeBtn.title = 'Remove this range';
        removeBtn.className = 'btn btn-sm btn-outline-danger dhcp-remove-btn';
        removeBtn.style.cssText = 'padding:2px 8px; font-size:0.8em;';
        removeBtn.addEventListener('click', function () {
            row.remove();
            refreshRemoveButtons();
            updateCounter();
            serializeRanges();
        });

        row.appendChild(startWrap);
        row.appendChild(endWrap);
        row.appendChild(removeBtn);
        return row;
    }

    function refreshRemoveButtons() {
        const rows = document.querySelectorAll('#dhcp-ranges-container .dhcp-range-row');
        rows.forEach(function (row, idx) {
            const btn = row.querySelector('.dhcp-remove-btn');
            if (btn) btn.style.visibility = (idx === 0) ? 'hidden' : 'visible';
        });
    }
    function buildDhcpUI() {
        const hidden = document.getElementById('id_dhcp_ranges');
        if (!hidden) return;
        if (document.getElementById('dhcp-ranges-container')) return; 

        const formRow = document.createElement('div');
        formRow.className = 'mb-3 row';

        const labelCol = document.createElement('div');
        labelCol.className = 'col-md-3';

        const inputCol = document.createElement('div');
        inputCol.className = 'col-md-9';

        const header = document.createElement('div');
        header.style.cssText = 'display:flex; align-items:center; justify-content:center; gap:10px; margin-bottom:6px; flex-wrap:wrap;';

        const counter = document.createElement('span');
        counter.id = 'dhcp-range-counter';
        counter.style.cssText = 'font-size:0.8em; color:#6c757d;';
        counter.textContent = '0 / ' + MAX_RANGES;

        const addBtn = document.createElement('button');
        addBtn.type = 'button';
        addBtn.id = 'dhcp-add-range-btn';
        addBtn.className = 'btn btn-sm btn-outline-primary';
        addBtn.innerHTML = '+ Add DHCP Range';
        addBtn.style.cssText = 'font-size:0.8em; padding:2px 10px;';
        addBtn.addEventListener('click', function () {
            const container = document.getElementById('dhcp-ranges-container');
            const rowCount = container.querySelectorAll('.dhcp-range-row').length;
            if (rowCount >= MAX_RANGES) {
                counter.style.color = '#dc3545';
                counter.title = 'Maximum of ' + MAX_RANGES + ' ranges reached.';
            }
            const row = createRangeRow('', '');
            container.appendChild(row);
            refreshRemoveButtons();
            updateCounter();
            serializeRanges();
        });

        header.appendChild(counter);
        header.appendChild(addBtn);
        inputCol.appendChild(header);

        const container = document.createElement('div');
        container.id = 'dhcp-ranges-container';
        inputCol.appendChild(container);

        formRow.appendChild(labelCol);
        formRow.appendChild(inputCol);

        const wrapper = document.createElement('div');
        wrapper.id = 'dhcp-ranges-wrapper';
        wrapper.appendChild(formRow);

        const checkbox = document.getElementById('enable_dhcp_checkbox');
        let insertAfter = checkbox;
        let checkboxGroup = checkbox ? checkbox.parentElement : null;
        while (checkboxGroup) {
            if (checkboxGroup.classList.contains('form-group') ||
                checkboxGroup.classList.contains('mb-3') ||
                checkboxGroup.tagName === 'TR') {
                break;
            }
            checkboxGroup = checkboxGroup.parentElement;
        }
        if (checkboxGroup && checkboxGroup.parentNode) {
            checkboxGroup.parentNode.insertBefore(wrapper, checkboxGroup.nextSibling);
        } else {
            let insertTarget = hidden;
            let parent = hidden.parentElement;
            while (parent) {
                if (parent.classList.contains('form-group') ||
                    parent.classList.contains('mb-3') ||
                    parent.tagName === 'TR') {
                    insertTarget = parent;
                    break;
                }
                parent = parent.parentElement;
            }
            insertTarget.parentNode.insertBefore(wrapper, insertTarget);
        }

        const existingRanges = hidden.value.trim();
        if (existingRanges) {
            const parts = existingRanges.split(';').filter(Boolean);
            parts.forEach(function (rng) {
                const dash = rng.indexOf('-');
                if (dash !== -1) {
                    const start = rng.substring(0, dash).trim();
                    const end   = rng.substring(dash + 1).trim();
                    container.appendChild(createRangeRow(start, end));
                }
            });
        }

        if (container.querySelectorAll('.dhcp-range-row').length === 0) {
            const defaults = getDefaultRange(
                document.querySelector('[name="LAN_IP_Address_And_Subnet_Mask"]')?.value || ''
            );
            container.appendChild(createRangeRow(
                defaults ? defaults.start : '',
                defaults ? defaults.end : ''
            ));
            serializeRanges();
        }

        refreshRemoveButtons();
        updateCounter();
    }


    function toggleDHCPFields() {
        const checkbox = document.getElementById('enable_dhcp_checkbox');
        const wrapper  = document.getElementById('dhcp-ranges-wrapper');
        if (!checkbox || !wrapper) return;

        const visible = checkbox.checked;
        wrapper.style.display = visible ? '' : 'none';

        wrapper.querySelectorAll('input').forEach(function (inp) {
            inp.disabled = !visible;
        });

        if (visible) {
            const container = document.getElementById('dhcp-ranges-container');
            if (container) {
                const firstRow   = container.querySelector('.dhcp-range-row');
                const firstStart = firstRow && firstRow.querySelector('.dhcp-range-start');
                const firstEnd   = firstRow && firstRow.querySelector('.dhcp-range-end');
                if (firstStart && !firstStart.value && firstEnd && !firstEnd.value) {
                    const lanField = document.querySelector('[name="LAN_IP_Address_And_Subnet_Mask"]');
                    const defaults = getDefaultRange(lanField ? lanField.value : '');
                    if (defaults) {
                        firstStart.value = defaults.start;
                        firstEnd.value   = defaults.end;
                        serializeRanges();
                    }
                }
            }
        }
    }


    function onLanIpChange() {
        const checkbox = document.getElementById('enable_dhcp_checkbox');
        if (!checkbox || !checkbox.checked) return;

        const lanField = document.querySelector('[name="LAN_IP_Address_And_Subnet_Mask"]');
        const defaults = getDefaultRange(lanField ? lanField.value : '');
        if (!defaults) return;

        const container = document.getElementById('dhcp-ranges-container');
        if (!container) return;
        const firstRow   = container.querySelector('.dhcp-range-row');
        const firstStart = firstRow && firstRow.querySelector('.dhcp-range-start');
        const firstEnd   = firstRow && firstRow.querySelector('.dhcp-range-end');
        if (firstStart && firstEnd) {
            firstStart.value = defaults.start;
            firstEnd.value   = defaults.end;
            serializeRanges();
        }
    }


    function setup() {
        buildDhcpUI();

        const checkbox = document.getElementById('enable_dhcp_checkbox');
        const lanField = document.querySelector('[name="LAN_IP_Address_And_Subnet_Mask"]');

        if (checkbox) {
            checkbox.addEventListener('change', toggleDHCPFields);
        }
        if (lanField) {
            lanField.addEventListener('input',  onLanIpChange);
            lanField.addEventListener('blur',   onLanIpChange);
            lanField.addEventListener('change', onLanIpChange);
        }

        toggleDHCPFields();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();