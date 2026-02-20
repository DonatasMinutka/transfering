document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        const deviceTypeField = document.getElementById('id_device_type')
        if (deviceTypeField && deviceTypeField.tomselect) {
            const tomselect = deviceTypeField.tomselect;
            const manufacturerData = {};
            let dataLoaded = false;
            tomselect.disable();
            fetch('/api/dcim/device-types/?brief=false&limit=0')
                .then(response => response.json())
                .then(data => {
                    data.results.forEach(dt => {
                        if (dt.manufacturer) {
                            manufacturerData[dt.id] = dt.manufacturer.name;
                        }
                    });
                    dataLoaded = true;
                    tomselect.settings.render.option = function(data, escape) {
                        let display = data.display || '';
                        const manufacturer = manufacturerData[data.id];
                        
                        if (manufacturer) {
                            display = manufacturer + ' - ' + display;
                        }
                        
                        return '<div>' + escape(display) + '</div>';
                    };
                    
                    tomselect.settings.render.item = function(data, escape) {
                        let display = data.display || '';
                        const manufacturer = manufacturerData[data.id];
                        
                        if (manufacturer) {
                            display = manufacturer + ' - ' + display;
                        }
                        
                        return '<div>' + escape(display) + '</div>';
                    };
                    
                    tomselect.enable();
                    tomselect.sync();
                    const currentOptions = tomselect.options;
                    tomselect.clearOptions();
                    Object.keys(currentOptions).forEach(key => {
                        tomselect.addOption(currentOptions[key]);
                    });
                    tomselect.refreshOptions(false);
                    })
                .catch(error => {
                    tomselect.enable();
                });
        }
    }, 1500);
});