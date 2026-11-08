# Fork of wlcrs/huawei-solar-lib

This fork carries a small number of patches on top of an upstream release. Branch `k2iuh` is always
"upstream release tag + the commits below". The upstream release it is based on is in `.fork-base`.

Releases are tagged `v<upstream version>+k2iuh.<n>`, for example `v3.0.7+k2iuh.1`. The
[k2iuh/huawei_solar](https://github.com/k2iuh/huawei_solar) integration fork installs the library from
such a tag.

Each patch is exactly one commit with its code and tests, so that a patch commit can serve as the
base of an upstream pull request. The last commit holds the fork-only files (this file, the
workflows, `.fork-base`). To change a patch, amend its commit (`git commit --fixup=<commit>` and
`git rebase -i --autosquash <base tag>`) and force-push the branch. Do not add fix commits on top.
Then raise `<n>` and tag the new head.

## Patches

### Accept optimizer file 0x44 despite a mismatching device CRC

Some inverters send a complete, valid optimizer real time data file (0x44) but return a CRC in
CompleteUpload that does not belong to it. The same payload arrives with different CRCs on consecutive
reads. Upstream discards the file, so optimizer entities in Home Assistant are unavailable most of the
time.

With this patch, `get_file` raises `FileCRCMismatchError` (a subclass of `DecodeError`) carrying the
payload. `SUN2000Device.get_latest_optimizer_history_data` accepts that payload only if it decodes
completely and every data unit, newest first, holds exactly one record for each optimizer the inverter
reports in register `nb_optimizers`. All other files keep the strict CRC check.

- Upstream issue: [wlcrs/huawei-solar-lib#39](https://github.com/wlcrs/huawei-solar-lib/issues/39).
  The maintainer declined a workaround, so this patch stays in the fork.
- Drop it when Huawei fixes the CRC in firmware or upstream accepts an equivalent change.

## Updating to a new upstream release

The `Fork sync` workflow runs every Monday. When upstream has a newer release than `.fork-base`, it
rebases the fork commits onto it in a `sync/<tag>` branch, runs the tests and opens an issue with the
result. It never publishes anything. To finish an update:

1. Review the `sync/<tag>` branch and fast-forward `k2iuh` to it.
2. Tag `v<upstream version>+k2iuh.1` and push the tag.
3. Point the integration fork's `manifest.json` requirement at the new tag.

The upstream `Publish to PyPI` workflow is disabled in this fork.
