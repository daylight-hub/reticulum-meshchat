# LCS MeshChat v2.3.0 (full) - config defaults, interface dialog, auto propagation + toggle

## All changes
1. Auto-announce -> every 6 hours (21600s)
2. Auto-resend failed messages WITH attachments -> enabled
3. Auto-send failed messages to propagation node -> enabled
4. Add LCS Interfaces dialog (non-Docker): updates enabled status of existing interface,
   no duplicates.
5. Version -> 2.3.0
6. Auto-sync with preferred propagation node -> every 6 hours (21600s)
7. Auto-select propagation node: adopts the first discovered node if none is set.
8. NEW: Settings toggle "Auto Select Propagation Node" (checkbox in Settings >
   Propagation Nodes). On by default. Turning it on re-enables auto-select; setting a
   preferred node manually turns it off.

## Files
- meshchat.py                                        (items 1,2,3,4,6,7,8 backend)
- package.json, package-lock.json                    (item 5)
- src/frontend/components/App.vue                    (item 4 dialog labels)
- src/frontend/components/settings/SettingsPage.vue  (item 8 toggle UI)

## Apply + push
    Copy-Item -Path lcs-v230\* -Destination . -Recurse -Force
    npm run build-frontend
    git add -A
    git commit -m "v2.3.0: 6h announce+sync, resend w/attachments, auto propagation node + settings toggle, interface enable-update"
    git config http.version HTTP/1.1
    git push origin lcs

## The toggle (item 8) behavior
- Settings > Propagation Nodes > "Auto Select Propagation Node" checkbox.
- ON: MeshChat adopts the first propagation node it discovers (if none set yet).
- Typing a Preferred Propagation Node hash manually turns the toggle OFF automatically
  (your explicit choice wins).
- You can turn the toggle back ON anytime to resume auto-selection.

## Same caveat as before (config DEFAULTS - items 1,2,3,6,7)
Defaults only apply to FRESH configs. Existing nodes keep their saved values. On an
existing node, set these in Settings once (the new toggle included) or use a fresh config.
The toggle itself works immediately on any build - it's the DEFAULT that only applies to
fresh configs; you can flip it in Settings on any existing node.
