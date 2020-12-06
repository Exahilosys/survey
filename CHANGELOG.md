## Unreleased

#### Additions

#### Changes

#### Removals

#### Fixes

## v3.0.2

#### Fixes

Updated version to reflect breaking changes.

## v3.0.1

#### Fixes

- `jump` now takes proper arguments in `path`.

## v3.0.0

#### Additions

- Added `note`: A symbol coming before `prompt`.
- Added `info`: Updatable text coming after `prompt` and before `hint`.
- Added `indent` for `MultiLineEditor`: The amount of spaces for each tab.
- Added `jump` in `traverse`: A function deciding which index tab advances to.
- Added `Theme`: A data-like class used by `use` to overwrite global behavior.
- Added `auto` argument in almost every routine. Used to determine whether to respond immediately.

#### Changes

- Renamed modules and moved around classes to more specific places.
- Revamped `api.py` and modules around it to better house new features.
- `hint` is now static and cannot be updated. Use `info` instead.
- Exposed `respond` for when `auto` is `False`.
- Updated documentation to match new changes.

#### Removals

- Removed the `view`, `color` and `erase` from every routine in favor of `auto`.
- Removed `utils.py` as hints are now made directly via routines in `core.py`.

#### Fixes

- `helpers.paint` now accommodates more cases of ANSI-SGR sequence injecting.

## v2.1.6

#### Fixes

- \#8 inconsistent coloring of the default hint for `confirm`
- Installing through Github and release assets should now work.

## v2.1.5

#### Fixes

- AttributeError during version parsing in `setup.py`.

## v2.1.4

#### Changes

- README syntax is not RST.

## v2.1.3
