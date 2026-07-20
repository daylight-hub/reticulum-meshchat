# LCS MeshChat - version correction 2.3.0 -> 1.3.0

Just changes the app version from 2.3.0 to 1.3.0. Nothing else.

## Files
- package.json, package-lock.json

## Apply + push
    Copy-Item -Path lcs-ver\* -Destination . -Recurse -Force
    git add package.json package-lock.json
    git commit -m "Correct version to 1.3.0"
    git config http.version HTTP/1.1
    git push origin lcs

Note: the two remaining "2.3.0" strings in package-lock.json are npm dependencies
(binary-extensions, pify) - those are correct and must stay.
