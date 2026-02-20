from setuptools import find_packages, setup

setup(
    name='netbox-kak-form',
    version='0.1.0',
    description='Custom device form for NetBox',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'kak_form': [
            'templates/**/*.html',
            'static/**/*.js',
        ],
    },
    zip_safe=False,
    entry_points={
        "netbox_plugins": [
            "kak_form = kak_form"
        ]
    }
)