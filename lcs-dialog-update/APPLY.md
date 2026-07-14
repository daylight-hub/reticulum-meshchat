# LCS MeshChat — dialog + interface updates

Verified: frontend builds (vite ✓), python compiles ✓. Apply on the lcs branch.

## Changed files (3)
- meshchat.py                          - interface renames/ports + dialog backend + serial-port finder
- src/frontend/components/App.vue      - polished Add-LCS-Interfaces dialog + attribution link removed
- README.md                            - documents the LCS fork + all changes

## Apply (repo root, on lcs branch)
Windows PowerShell:
    Copy-Item -Path lcs-dialog-update\meshchat.py -Destination . -Force
    Copy-Item -Path lcs-dialog-update\README.md -Destination . -Force
    Copy-Item -Path lcs-dialog-update\src\frontend\components\App.vue -Destination src\frontend\components\App.vue -Force

Then (if you have working npm) verify:
    npm run build-frontend      # want: ✓ built

Commit + push:
    git add -A
    git commit -m "Polished Add-LCS-Interfaces dialog, interface renames (LCS Gateway Client:4243, IP RNode iprnode.local:4545), remove attribution link, README"
    git push origin lcs

## What changed
1. Interface: [[LCS Gateway Client: public.lcs.network]] port 4243 (was TCP Client ...:1776)
2. Interface: [[IP RNode]] host iprnode.local port 4545 (was rnode.local)
3. Attribution: "built on MeshChat by Liam Cottle" now plain text, link removed
   (LICENSE file with Liam Cottle's copyright is UNCHANGED - still required by MIT)
4. Polished dialog on the Add LCS Interfaces button:
   - checkboxes to pick which of the 3 interfaces to add
   - "Enable interface(s) immediately" toggle
   - RNode serial-port finder: "Find Port" button scans connected serial devices
     (via backend /api/v1/reticulum/serial-ports), click a detected port to use it
5. README updated to document the LCS fork and all features

## Honest caveats (couldn't test in build env)
- The serial-port finder lists ports the SERVER process can see (pyserial). In Docker
  with no USB passthrough, it will find nothing - that's expected; the user can still
  type the port manually. On desktop builds it sees the machine's real ports.
- The dialog's live add/enable + restart-to-apply needs a running instance to confirm.
- Ringtone (from the prior update) still needs a live call to verify.
