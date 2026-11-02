local root='__PROJECT_ROOT__/'
local out=root..'captures/qa_digits/'
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
 end
end,emu.callbackType.exec,0,65535)
local n=0
local buttons={'up','down','left','right','start','select','b','a'}
emu.addEventCallback(function()
 if not loaded then return end
 n=n+1
 local str=inputs[n] or '........'
 local t={}
 for i,key in ipairs(buttons) do t[key]=str:sub(i,i)~='.' end
 emu.setInput(t,0)
end,emu.eventType.inputPolled)
emu.addEventCallback(function()
 if not loaded then return end
 if n>=120 and n<280 then
  local value=math.floor((n-120)/16)
  local digits={{0x3f,0x40,0x49,0x4a},{0x2a,0x42,0x4b,0x4c},{0x45,0x46,0x49,0x4e},{0x41,0x46,0x4d,0x4a},{0x47,0x48,0x4b,0x4c},{0x43,0x44,0x4d,0x4a},{0x43,0x44,0x49,0x4a},{0x3f,0x40,0x4b,0x4c},{0x43,0x46,0x49,0x4a},{0x43,0x46,0x4d,0x4a}}
  for _,base in ipairs({0x65a,0x65c}) do
   for q=0,3 do emu.write(base+(q%2)+math.floor(q/2)*32,digits[value+1][q+1],emu.memType.nesNametableRam) end
  end
  if n>=122 and (n-122)%16==0 then save(out..tostring(value)..'.png',emu.takeScreenshot()) end
 end
 if n>=285 then emu.stop(0) end
end,emu.eventType.endFrame)
