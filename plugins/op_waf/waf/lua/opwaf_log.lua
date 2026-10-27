-- Real-time request statistics for the WAF dashboard.
-- Runs in the log phase, so the finished request already knows its response
-- size and upstream response time.

local dict = ngx.shared.waf_limit
if not dict then
    return
end

local BUCKET = 10
local TTL = 640

local bucket = math.floor(ngx.now() / BUCKET)

local function bump(key, value)
    -- add is atomic: it fails when another worker already created the key
    if not dict:add(key, value, TTL) then
        dict:incr(key, value)
    end
end

bump('rt_c:' .. bucket, 1)

local bytes = tonumber(ngx.var.body_bytes_sent) or 0
if bytes > 0 then
    bump('rt_b:' .. bucket, bytes)
end

local ms = 0
local upstream_time = ngx.var.upstream_response_time
if upstream_time and upstream_time ~= '' and upstream_time ~= '-' then
    -- several values when the request was retried upstream
    for v in string.gmatch(upstream_time, '[%d%.]+') do
        ms = ms + (tonumber(v) or 0) * 1000
    end
else
    -- static files and cached responses have no upstream
    ms = (tonumber(ngx.var.request_time) or 0) * 1000
end

if ms > 0 then
    bump('rt_t:' .. bucket, math.floor(ms))
end
