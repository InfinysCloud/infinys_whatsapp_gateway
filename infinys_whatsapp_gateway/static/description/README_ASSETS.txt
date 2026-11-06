Place the module's description assets here, matching the paths referenced in
__manifest__.py and the views:

  - icon.png        (referenced by manifest "icon" and the Settings <app logo=...>)
  - banner.png      (referenced by manifest "images")
  - index.html      (Apps store long description page)
  - wa_gateway1.png ... wa_gateway6.png (screenshots used by index.html)

These binary assets were not part of the source provided for the migration, so
they are not included in this rebuilt package. Copy them from the original
module's static/description/ folder before publishing.

The module installs and runs without these files; only the Apps-store imagery
and the Settings app logo will be missing until they are added.
