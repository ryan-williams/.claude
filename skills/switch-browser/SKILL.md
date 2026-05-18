---
name: switch-browser
description: Broadcast a Chrome connection request to all browsers running the Claude extension so the user can click "Connect" in a different Chrome profile / window. Use when the user says "switch chrome", "connect to a different browser", "use my other chrome profile", "i want to use chrome X instead", or similar. The default MCP-spawned tab lands in whichever Chrome happens to respond first — this lets the user redirect to their preferred profile.
---

# Switch Chrome browser

Invokes `mcp__claude-in-chrome__switch_browser`, which broadcasts a connection request to every Chrome window that has the Claude extension installed. The user clicks "Connect" in the desired window; subsequent browser-automation calls route to that browser.

## Procedure

1. **Snapshot the current browser's tabs first** via `mcp__claude-in-chrome__tabs_context_mcp`. Record `tabGroupId` + the set of `tabId`s. This is your "before" reference.
2. Call `mcp__claude-in-chrome__switch_browser` (no args). It broadcasts a connection request to every Chrome window running the extension.
3. If it returns a connection error / timeout, ask the user to:
   - Ensure Chrome is open with the Claude extension installed
   - Bring Chrome to the foreground (the broadcast prompt may be suppressed in background windows)
   - Retry — the tool can be called again immediately. Confirmation messages like "Connected to browser \"X\"" mean a click landed, but **do not yet confirm the swap took effect** (the user may have clicked "Connect" in the same browser, or the broadcast may have been auto-accepted).
4. **Verify the swap by re-snapshotting** with `tabs_context_mcp`. Compare against step 1:
   - **Different `tabGroupId`** → swap succeeded; report the new browser name (from the switch confirmation) and the new tab list.
   - **Same `tabGroupId` and same tabs** → swap didn't take effect. Re-broadcast (loop to step 2) and tell the user which browser to click "Connect" in next.
   - **Same `tabGroupId` but tabs changed** → likely the user just opened/closed tabs in the same browser. Re-broadcast.
5. Only after step 4 confirms a different browser should you create new tabs or run automation against the new profile.

## Notes

- The default browser-automation flow uses whichever Chrome responded first when the MCP session started. This skill is the recovery hatch when that's the wrong profile.
- Don't preemptively create tabs in the new browser before step 4 confirms the swap landed.
- If the user just wants a different *tab* in the current Chrome, use `tabs_create_mcp` instead.
