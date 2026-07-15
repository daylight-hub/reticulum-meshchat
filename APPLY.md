# LCS MeshChat — CORRECTED fixes (icon path + push fix)

The previous attempt put icons in build/ but electron-builder's buildResources is
electron/build/ - that's why the Windows build failed with "cannot find build/icon.ico"
AND why the old logo kept showing (electron/build/icon.png was the upstream icon).
This corrects it: LCS icons now in electron/build/ with bare-filename references.

## IMPORTANT: clean up the previous bad commit first
If you committed the lcs-fixes/ folder earlier, remove it:
    git reset --soft origin/lcs
    git restore --staged .
    Remove-Item -Recurse -Force lcs-fixes -ErrorAction SilentlyContinue
    Remove-Item APPLY.md -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue

## Apply the corrected files
    Copy-Item -Path lcs-fixes2\* -Destination . -Recurse -Force

## Verify then commit
    npm run build-frontend      # want: ✓ built
    git add -A
    git status                  # confirm NO lcs-fixes/ or top-level build/ ; DO see electron/build/icon.*
    git commit -m "Fixes v2: LCS icons in electron/build, mac retry, global ringtone, desktop restart, scroll text, updates link, Inc."

## Pushing (the 408 timeout fix)
The icon.icns is ~1.5MB and was causing HTTP 408 timeouts. Do this before pushing:
    git config http.version HTTP/1.1
    git config http.postBuffer 524288000
    git push origin lcs

If it STILL 408s, wait 10 min and retry (usually a transient GitHub issue), or set up
an SSH key (github.com/settings/keys) and push over SSH.

## What's fixed
- Item 4 (REAL fix): LCS logo now in electron/build/icon.ico|icns|png (the actual
  buildResources dir). Replaces the upstream icon.png that was showing. package.json
  points win/mac/linux/nsis at bare filenames (icon.ico etc.), resolved from electron/build.
- Added description + author to package.json (electron-builder warned they were missing).
- Items 1,2,3,5,6,7 as before (mac DMG retry, global ringtone, desktop restart button,
  scroll text, updates link -> daylight-hub, "Inc." in header).

## Verify on first build
- Windows/Linux/Mac installers should now show the LCS bell logo.
- Ringtone needs a live incoming call to confirm (and one click in the app first, for autoplay).
