(function () {
  'use strict';

  var CIDR_RE = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;

  function hostOnly(cidr) {
    return cidr && cidr.indexOf('/') !== -1 ? cidr.split('/')[0] : cidr;
  }

  function validateCidr(inp) {
    var v = inp.value.trim();
    var valid = !v || CIDR_RE.test(v);
    if (valid) {
      if (inp.dataset.errorType !== 'duplicate') {
        inp.style.borderColor = '';
        inp.title = '';
      }
    } else {
      inp.style.borderColor = '#dc3545';
      inp.title = 'Must be a valid CIDR, e.g. 10.0.0.1/24';
      inp.dataset.errorType = 'format';
    }
    return valid;
  }

  function checkDuplicates(rowContainer, primaryInput, wanInput) {
    function markInput(inp, isDup, msg) {
      if (isDup) {
        inp.style.borderColor = '#dc3545';
        inp.title = msg || 'Duplicate IP — already used in this form';
        inp.dataset.errorType = 'duplicate';
      } else if (inp.dataset.errorType === 'duplicate') {
        inp.style.borderColor = '';
        inp.title = '';
        delete inp.dataset.errorType;
      }
    }

    var primaryVal = primaryInput.value.trim();
    var wanVal     = wanInput ? wanInput.value.trim() : '';
    var extraInputs = Array.from(rowContainer.querySelectorAll('input[type="text"]'));

    // Primary LAN vs WAN
    if (primaryVal && wanVal && hostOnly(primaryVal) === hostOnly(wanVal)) {
      markInput(primaryInput, true, 'LAN and WAN IP addresses cannot be the same.');
      markInput(wanInput,     true, 'LAN and WAN IP addresses cannot be the same.');
    } else {
      markInput(primaryInput, false);
      if (wanInput) markInput(wanInput, false);
    }

    // Extra rows vs primary LAN, WAN, and each other
    extraInputs.forEach(function (inp) {
      var v = inp.value.trim();
      if (!v) return;

      var isDup = false;
      var msg   = '';

      if (primaryVal && hostOnly(v) === hostOnly(primaryVal)) {
        isDup = true; msg = 'Same as the primary LAN IP.';
      } else if (wanVal && hostOnly(v) === hostOnly(wanVal)) {
        isDup = true; msg = 'Conflicts with the WAN IP.';
      } else {
        extraInputs.forEach(function (other) {
          if (other !== inp && other.value.trim() && hostOnly(other.value.trim()) === hostOnly(v)) {
            isDup = true; msg = 'Duplicate IP — already used in this form.';
          }
        });
      }

      markInput(inp, isDup, msg);
    });
  }

  function init() {
    var primaryInput = document.querySelector('[name="LAN_IP_Address_And_Subnet_Mask"]');
    var hiddenInput  = document.querySelector('[name="Additional_LAN_IPs"]');
    var wanInput     = document.querySelector('[name="Given_WAN_Address"]');

    if (!primaryInput || !hiddenInput) {
      console.warn('multi_lan_ip.js: could not find LAN fields');
      return;
    }

    var rowContainer = document.createElement('div');
    rowContainer.id = 'lan-extra-rows';
    primaryInput.insertAdjacentElement('afterend', rowContainer);

    function runChecks() {
      checkDuplicates(rowContainer, primaryInput, wanInput);
    }

    // Primary LAN field
    primaryInput.addEventListener('blur',  function () { validateCidr(primaryInput); runChecks(); });
    primaryInput.addEventListener('input', function () {
      if (primaryInput.dataset.errorType) validateCidr(primaryInput);
      runChecks();
    });

    // WAN field — wire up duplicate checks from here too
    if (wanInput) {
      wanInput.addEventListener('blur',  function () { validateCidr(wanInput); runChecks(); });
      wanInput.addEventListener('input', function () {
        if (wanInput.dataset.errorType) validateCidr(wanInput);
        runChecks();
      });
    }

    var addBtn = document.createElement('button');
    addBtn.type        = 'button';
    addBtn.className   = 'btn btn-sm btn-outline-secondary';
    addBtn.style.marginTop = '6px';
    addBtn.textContent = '+ Add LAN IP';
    addBtn.title = 'Add an extra LAN IP (stored in NetBox, not used in configs)';
    rowContainer.insertAdjacentElement('afterend', addBtn);

    function addRow(value) {
      var row = document.createElement('div');
      row.style.cssText = 'display:flex;align-items:center;gap:6px;margin-top:4px;';

      var inp = document.createElement('input');
      inp.type        = 'text';
      inp.className   = 'form-control form-control-sm';
      inp.value       = value || '';
      inp.placeholder = '10.0.0.1/24';

      inp.addEventListener('blur', function () {
        validateCidr(inp);
        if (!inp.value.trim()) {
          row.parentNode && row.parentNode.removeChild(row);
        }
        runChecks();
      });
      inp.addEventListener('input', function () {
        if (inp.dataset.errorType) validateCidr(inp);
        runChecks();
      });

      var removeBtn = document.createElement('button');
      removeBtn.type      = 'button';
      removeBtn.innerHTML = '&times;';
      removeBtn.title     = 'Remove';
      removeBtn.className = 'btn btn-sm btn-outline-danger';
      removeBtn.addEventListener('click', function () {
        row.parentNode && row.parentNode.removeChild(row);
        runChecks();
      });

      row.appendChild(inp);
      row.appendChild(removeBtn);
      rowContainer.appendChild(row);
      return inp;
    }

    addBtn.addEventListener('click', function () {
      addRow('').focus();
    });

    var form = primaryInput.closest('form');
    if (form) {
      form.addEventListener('submit', function (e) {
        var blocked = false;

        [primaryInput, wanInput].forEach(function (f) {
          if (f && f.value.trim()) {
            if (!validateCidr(f)) blocked = true;
            if (f.dataset.errorType)  blocked = true;
          }
        });

        rowContainer.querySelectorAll('input[type="text"]').forEach(function (inp) {
          if (inp.value.trim()) {
            if (!validateCidr(inp))  blocked = true;
            if (inp.dataset.errorType) blocked = true;
          }
        });

        if (blocked) { e.preventDefault(); return; }

        var values = [];
        rowContainer.querySelectorAll('input[type="text"]').forEach(function (inp) {
          var v = inp.value.trim();
          if (v) values.push(v);
        });
        hiddenInput.value = values.join(';');
      });
    }

    var existing = hiddenInput.value.trim();
    if (existing) {
      existing.split(';').forEach(function (ip) {
        ip = ip.trim();
        if (ip) addRow(ip);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();