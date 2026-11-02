local root='__PROJECT_ROOT__/'
local out=root..'captures/__CAPTURE_NAME__/'
local sync='__PROJECT_ROOT__/captures/__CAPTURE_NAME__'
local function touch(s)local f=assert(io.open(sync..s,'w'));f:write('ok');f:close()end
local function wait(s)local t=os.clock();repeat local f=io.open(sync..s,'r');if f then f:close();return end until os.clock()-t>10;error('Native recorder handshake timeout')end
local inputs={}
for line in io.lines(root..'movie/Input.txt') do table.insert(inputs,line:sub(5,12)) end
local function save(path,data) local f=assert(io.open(path,'wb'));f:write(data);f:close() end
local function mem(typ,size) local t={};for i=0,size-1 do t[#t+1]=string.char(emu.read(i,typ)) end;return table.concat(t) end
local loaded=false
local loadcb
loadcb=emu.addMemoryCallback(function()
 if not loaded then
  loaded=true
  emu.removeMemoryCallback(loadcb,emu.callbackType.exec,0,65535)
  local f=assert(io.open(root..'movie/SaveState.mss','rb'));local s=f:read('*all');f:close()
  emu.loadSavestate(s)
  touch('.go');wait('.ack')
 end
end,emu.callbackType.exec,0,65535)
local trace=assert(io.open(out..'trace.bin','wb'))
local lastPal=''
local n=0
local poses=__POSE_TABLE__
-- Test-only fixture. Write hardware OAM at the start of visible rendering;
-- Preserve sprite zero, which controls the native cockpit split timing.
-- Do not change game RAM, ROM, input or production HD pack behavior.
emu.addEventCallback(function()
 if not loaded then return end
 local pose=poses[math.min(#poses,math.floor(n/10)+1)]
 for i=1,63 do emu.write(i*4,248,emu.memType.nesSpriteRam) end
 for i,sprite in ipairs(pose) do
  local off=i*4
  emu.write(off,31+sprite[2],emu.memType.nesSpriteRam)
  emu.write(off+1,sprite[3],emu.memType.nesSpriteRam)
  emu.write(off+2,sprite[4],emu.memType.nesSpriteRam)
  emu.write(off+3,96+sprite[1],emu.memType.nesSpriteRam)
 end
end,emu.eventType.startFrame)
local buttons={'up','down','left','right','start','select','b','a'}
emu.addEventCallback(function()
 if not loaded then return end
 n=n+1
 local str='........'
 local t={}
 for i,key in ipairs(buttons) do t[key]=str:sub(i,i)~='.' end
 emu.setInput(t,0)
end,emu.eventType.inputPolled)
emu.addEventCallback(function()
 if not loaded then return end
 local pal=mem(emu.memType.nesPaletteRam,32)
 trace:write(mem(emu.memType.nesInternalRam,2048)..mem(emu.memType.nesNametableRam,2048)..mem(emu.memType.nesSpriteRam,256)..pal)
 local changed=pal~=lastPal;lastPal=pal
 if n>0 and (n%10==5) then
  local pre=out..string.format('%05d',n)
  save(pre..'.png',emu.takeScreenshot())
  save(pre..'.chr',mem(emu.memType.nesChrRam,8192))
  save(pre..'.nt',mem(emu.memType.nesNametableRam,2048))
  save(pre..'.pal',mem(emu.memType.nesPaletteRam,32))
  save(pre..'.ram',mem(emu.memType.nesInternalRam,2048))
  save(pre..'.oam',mem(emu.memType.nesSpriteRam,256))
  local t={};for k,v in pairs(emu.getState()) do table.insert(t,tostring(k)..'='..tostring(v)) end
  save(pre..'.state',table.concat(t,'\n'))
 end
 if n>=#poses*10 then trace:close();touch('.done');wait('.end');emu.stop(0) end
end,emu.eventType.endFrame)
