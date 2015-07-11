local comm = require "comm"
local nmap = require "nmap"
local stdnse = require "stdnse"

description = [[
A simple script that calculates the response time for a server. Mainly used in the identification of open ports of systems that reply with all ports as open. 
]]

---
-- @output
-- 21/tcp open  ftp
-- |_responseTime: 12.741000175476
-- 22/tcp open  ftp
-- |_responseTime: 0.10199999809265
-- 179/tcp   open  bgp
-- |_responseTime: 6.7190001010895
-- 199/tcp   open  smux
-- |_responseTime: 12.739000082016
-- 


author = "perfectlylogical"
license = "Same as Nmap--See http://nmap.org/book/man-legal.html"
categories = {"discovery", "safe"}

local portarg = stdnse.get_script_args(SCRIPT_NAME .. ".ports")
if portarg == "common" then
  portarg = "13,17,21-23,25,129,194,587,990,992,994,6667,6697"
end
---
-- Script is executed for any TCP port.
portrule = function( host, port )
  if port.protocol == "tcp" then
    if portarg then
      return stdnse.in_port_range(port, portarg)
    end
    return true
  end
  return false
end


--
-- Connects to the target on the given port and returns any data issued by a listening service.
-- @param host  Host Table.
-- @param port  Port Table.
-- @return      String or nil if data was not received.

action = function(host, port)
	local opts = {}
	opts.timeout = stdnse.parse_timespec(stdnse.get_script_args(SCRIPT_NAME .. ".timeout"))
	opts.timeout = (opts.timeout or 5) * 1000
	opts.proto = port.protocol

	local times = {}
	for run=0,2 do
		local StartTime = nmap.clock()
		local status, response = comm.get_banner(host.ip, port.number, opts)
		local StopTime = nmap.clock()
		local diff = StopTime - StartTime
		table.insert(times, diff)
	end
	
	local fastest_response = 99999
	for key,time in pairs(times) do
		if time < fastest_response then
			fastest_response = time
		end
	end
	
	local output = stdnse.output_table()
	output.responseTime = fastest_response
	local output_str = string.format("%s", output.responseTime)
	return output, output_str
end
