# LCS MeshChat v1.4.0 - browser bridge no longer depends on frontend Docker detection

## The remaining problem
Backend is 100% correct (curl confirms "is_docker": true, bridge installs, libpulse crash
fixed). But the browser never connects its audio bridge - so no mic frames, no audio. The
browser was gating the bridge on the frontend's cached isDocker flag, which was stale.

## The fix
The backend now tells the browser, per call, whether to use browser audio - via a
"use_browser_audio" flag in the telephone_call_established websocket event. The browser
starts the bridge based on that authoritative backend flag, NOT the possibly-stale
app_info. This removes the fragile frontend-detection dependency entirely.

## CRITICAL: browser cache
Because the frontend bundle is cached, you MUST load the new JS. The backend already sends
no-cache for index.html, but your nginx reverse proxy may cache it. After deploying:
1. In the browser: DevTools (F12) > Application > Clear storage > "Clear site data", reload.
   OR use a fresh Incognito/Private window.
2. If it persists, add no-cache to the nginx proxy (on the OpenWrt router,
   /etc/nginx/conf.d/meshchat.conf, in the location / block):
       add_header Cache-Control "no-store" always;
       proxy_no_cache 1;
       proxy_cache_bypass 1;
   then: nginx -t -c /etc/nginx/uci.conf && /etc/init.d/nginx restart

## Files
- meshchat.py                            (use_browser_audio flag in established event)
- src/frontend/components/App.vue        (start bridge on backend flag, not isDocker)
- (other files unchanged from prior v1.4.0)

## Apply + push
    Copy-Item -Path lcs-v140\* -Destination . -Recurse -Force
    npm run build-frontend
    git add -A
    git commit -m "v1.4.0: backend-driven browser audio bridge (use_browser_audio flag) - no frontend docker dependency"
    git config http.version HTTP/1.1
    git push origin lcs
    # after Actions rebuilds:
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## How to confirm it FINALLY works
After deploy + clearing browser cache, make a call and watch:
    docker compose logs --tail=30 -f | grep "bridge mic"
You should NOW see:  "WebRTC bridge mic: received=N fed_to_mixer=N"  climbing.
That line = the browser is connected and sending mic audio. If you see it, audio works.
If you still DON'T see it, the browser bridge still isn't starting - open the browser
console (F12) and look for "[AudioBridge] getUserMedia failed" (means HTTPS/mic-permission
problem) or "failed to start audio bridge". Paste that.

## Note on the profile thrashing in your log
Your log showed the codec switching 60ms<->200ms repeatedly. That's the two ends
negotiating; it may settle once real audio flows. If it keeps thrashing after audio works,
tell me and I'll add a stabilization guard.
