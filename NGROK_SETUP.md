# ngrok Setup Guide for MCP Servers

This guide shows you how to expose your local MCP servers to Prompt Opinion using ngrok.

## Prerequisites

- ✅ MCP servers running locally (via `start-mcp-http.sh`)
- ✅ ngrok installed ([download here](https://ngrok.com/download))
- ✅ ngrok account (free tier works fine)

## Problem: Why 404?

When you get a 404 error from Prompt Opinion, it's usually because:

1. ❌ **Missing `/mcp` path** - You need to add `/mcp` to the end of your ngrok URL
2. ❌ **Wrong port** - Make sure ngrok is tunneling the correct port
3. ❌ **Server not running** - Verify your MCP servers are actually running

## Solution: Step-by-Step Setup

### Step 1: Start Your MCP Servers

```bash
cd prior-auth-agent/scripts
bash start-mcp-http.sh
```

You should see:
```
✓ All servers started
  Payer Rules MCP (PID: xxxxx)
  Patient Records MCP (PID: xxxxx)
  Document Generation MCP (PID: xxxxx)

INFO:     Uvicorn running on http://0.0.0.0:9001 (Press CTRL+C to quit)
INFO:     Uvicorn running on http://0.0.0.0:9002 (Press CTRL+C to quit)
INFO:     Uvicorn running on http://0.0.0.0:9003 (Press CTRL+C to quit)
```

### Step 2: Start ngrok Tunnels

You need **3 separate ngrok tunnels** (one for each server).

#### Option A: Using 3 Terminal Windows

**Terminal 1 - Payer Rules MCP:**
```bash
ngrok http 9001
```

**Terminal 2 - Patient Records MCP:**
```bash
ngrok http 9002
```

**Terminal 3 - Document Generation MCP:**
```bash
ngrok http 9003
```

#### Option B: Using ngrok Configuration File (Recommended)

Create `~/.ngrok2/ngrok.yml`:

```yaml
version: "2"
authtoken: YOUR_NGROK_AUTH_TOKEN

tunnels:
  payer-rules:
    proto: http
    addr: 9001
  patient-records:
    proto: http
    addr: 9002
  document-generation:
    proto: http
    addr: 9003
```

Then start all tunnels at once:
```bash
ngrok start --all
```

### Step 3: Get Your ngrok URLs

From each ngrok terminal, copy the **Forwarding** URL:

```
Forwarding   https://abc123.ngrok.io -> http://localhost:9001
```

You'll get 3 URLs like:
- `https://abc123.ngrok.io` (Payer Rules)
- `https://def456.ngrok.io` (Patient Records)
- `https://ghi789.ngrok.io` (Document Generation)

### Step 4: Test Your URLs

**IMPORTANT:** Add `/mcp` to the end of each URL!

```bash
cd prior-auth-agent/scripts
bash test-ngrok-urls.sh https://abc123.ngrok.io https://def456.ngrok.io https://ghi789.ngrok.io
```

You should see:
```
Testing: Server 1 (Payer Rules)
URL: https://abc123.ngrok.io
  Without /mcp path: ❌ 404 (expected - need /mcp path)
  With /mcp path: ✅ 200 (SUCCESS!)
  Server response: "name":"payer-rules-mcp"
```

### Step 5: Configure Prompt Opinion

In Prompt Opinion, configure your MCP servers with the **full URL including `/mcp`**:

```json
{
  "mcpServers": {
    "payer-rules": {
      "url": "https://abc123.ngrok.io/mcp"
    },
    "patient-records": {
      "url": "https://def456.ngrok.io/mcp"
    },
    "document-generation": {
      "url": "https://ghi789.ngrok.io/mcp"
    }
  }
}
```

## Common Issues & Solutions

### Issue 1: 404 Error

**Problem:** Prompt Opinion returns 404

**Solution:** Make sure you include `/mcp` in the URL:
- ❌ Wrong: `https://abc123.ngrok.io`
- ✅ Correct: `https://abc123.ngrok.io/mcp`

### Issue 2: Connection Refused

**Problem:** ngrok shows "connection refused"

**Solution:** 
1. Check if MCP servers are running: `ps aux | grep server.py`
2. Verify ports are listening: `netstat -tlnp | grep 900`
3. Restart servers: `bash start-mcp-http.sh`

### Issue 3: ngrok Session Expired

**Problem:** ngrok tunnel stops working after a while

**Solution:**
- Free ngrok tunnels expire after 2 hours
- Restart ngrok to get new URLs
- Consider ngrok paid plan for persistent URLs

### Issue 4: Wrong Port

**Problem:** ngrok is tunneling the wrong port

**Solution:** Make sure ngrok port matches your server:
- Payer Rules: port 9001
- Patient Records: port 9002
- Document Generation: port 9003

## Testing Checklist

Before configuring Prompt Opinion, verify:

- [ ] All 3 MCP servers are running
- [ ] All 3 ngrok tunnels are active
- [ ] Each ngrok URL + `/mcp` returns 200 status
- [ ] Test script shows "SUCCESS" for all servers
- [ ] URLs are copied correctly (including `/mcp`)

## Quick Test Commands

Test each server locally first:

```bash
# Test Payer Rules (port 9001)
curl -s http://localhost:9001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  | grep -o '"name":"[^"]*"'

# Test Patient Records (port 9002)
curl -s http://localhost:9002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  | grep -o '"name":"[^"]*"'

# Test Document Generation (port 9003)
curl -s http://localhost:9003/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  | grep -o '"name":"[^"]*"'
```

All should return the server name.

## Example: Complete Setup

Here's a complete example from start to finish:

```bash
# 1. Start MCP servers
cd prior-auth-agent/scripts
bash start-mcp-http.sh

# 2. In new terminals, start ngrok (or use config file)
ngrok http 9001  # Terminal 1
ngrok http 9002  # Terminal 2
ngrok http 9003  # Terminal 3

# 3. Copy the ngrok URLs (example):
# https://abc123.ngrok.io
# https://def456.ngrok.io
# https://ghi789.ngrok.io

# 4. Test the URLs
bash test-ngrok-urls.sh \
  https://abc123.ngrok.io \
  https://def456.ngrok.io \
  https://ghi789.ngrok.io

# 5. Configure Prompt Opinion with URLs + /mcp
```

## Troubleshooting Commands

```bash
# Check if servers are running
ps aux | grep "server.py"

# Check if ports are listening
netstat -tlnp | grep -E "9001|9002|9003"

# Check server logs
cd prior-auth-agent/scripts
# Look at the terminal where start-mcp-http.sh is running

# Restart everything
# Ctrl+C to stop servers
bash start-mcp-http.sh
# Restart ngrok tunnels
```

## Success Indicators

You know everything is working when:

✅ MCP servers show "Uvicorn running" messages
✅ ngrok shows "Session Status: online"
✅ Test script shows "✅ 200 (SUCCESS!)" for all servers
✅ Prompt Opinion connects without 404 errors
✅ You can see the MCP tools in Prompt Opinion

## Need Help?

If you're still getting 404 errors:

1. Run the test script and share the output
2. Check the ngrok web interface at http://127.0.0.1:4040
3. Verify the exact URL you're using in Prompt Opinion
4. Make sure `/mcp` is at the end of the URL

---

**Remember:** The key is adding `/mcp` to your ngrok URLs! 🔑
