/**
 * multi_lan_ip.js
 *
 * Adds a "+ Add LAN IP" button below the primary LAN IP field.
 * Rows are managed directly in the DOM.
 * The hidden field is only written on form submit.
 *
 * Uses [name="..."] selectors — Django overwrites custom widget id= attrs
 * with its own auto-generated id_<FieldName>, so IDs are unreliable.
 */

(function () {
  'use strict';

  function init() {
    var primaryInput = document.querySelector('[name="LAN_IP_Address_And_Subnet_Mask"]');
    var hiddenInput  = document.querySelector('[name="Additional_LAN_IPs"]');

    if (!primaryInput || !hiddenInput) {
      console.warn('multi_lan_ip.js: could not find LAN fields');
      return;
    }

    // -----------------------------------------------------------------------
    // Container that holds the extra-IP rows
    // -----------------------------------------------------------------------
    var rowContainer = document.createElement('div');
    rowContainer.id = 'lan-extra-rows';

    // Insert container + button right after the primary input element itself
    primaryInput.insertAdjacentElement('afterend', rowContainer);

    var addBtn = document.createElement('button');
    addBtn.type        = 'button';
    addBtn.className   = 'btn btn-sm btn-outline-secondary';
    addBtn.style.marginTop = '6px';
    addBtn.textContent = '+ Add LAN IP';
    addBtn.title = 'Add an extra LAN IP (stored in NetBox, not used in configs)';
    rowContainer.insertAdjacentElement('afterend', addBtn);

    // -----------------------------------------------------------------------
    // Add a single new empty row directly into the DOM
    // -----------------------------------------------------------------------
    function addRow(value) {
      var row = document.createElement('div');
      row.style.cssText = 'display:flex;align-items:center;gap:6px;margin-top:4px;';

      var inp = document.createElement('input');
      inp.type        = 'text';
      inp.className   = 'form-control form-control-sm';
      inp.value       = value || '';
      inp.placeholder = '10.0.0.1/24';

      inp.addEventListener('blur', function () {
        var v = inp.value.trim();
        var valid = !v || /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/.test(v);
        inp.style.borderColor = valid ? '' : '#dc3545';
        inp.title = valid ? '' : 'Must be a valid CIDR, e.g. 10.0.0.1/24';
        // Remove the row if left blank
        if (!v) {
          row.parentNode && row.parentNode.removeChild(row);
        }
      });

      var removeBtn = document.createElement('button');
      removeBtn.type      = 'button';
      removeBtn.innerHTML = '&times;';
      removeBtn.title     = 'Remove';
      removeBtn.className = 'btn btn-sm btn-outline-danger';

      removeBtn.addEventListener('click', function () {
        row.parentNode && row.parentNode.removeChild(row);
      });

      row.appendChild(inp);
      row.appendChild(removeBtn);
      rowContainer.appendChild(row);
      return inp;
    }

    // -----------------------------------------------------------------------
    // "+ Add LAN IP" click — just add a row and focus it
    // -----------------------------------------------------------------------
    addBtn.addEventListener('click', function () {
      var inp = addRow('');
      inp.focus();
    });

    // -----------------------------------------------------------------------
    // On submit: collect all row values → write to hidden field
    // -----------------------------------------------------------------------
    var form = primaryInput.closest('form');
    if (form) {
      form.addEventListener('submit', function () {
        var values = [];
        rowContainer.querySelectorAll('input[type="text"]').forEach(function (inp) {
          var v = inp.value.trim();
          if (v) values.push(v);
        });
        hiddenInput.value = values.join(';');
      });
    }

    // -----------------------------------------------------------------------
    // Edit mode: restore previously saved extra IPs from hidden field
    // -----------------------------------------------------------------------
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