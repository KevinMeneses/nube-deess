-- Carga Nube De-Ess en una pestaña nueva, renderiza cada caso y cierra la pestaña.
-- Uso: REAPER -nonewinst tests/render_cases.lua   (escribe tests/out/*.wav y tests/out/log.txt)
local ROOT = os.getenv("HOME") .. "/Music/NubeDeEss/tests"
local OUT = ROOT .. "/out"
local FX = "JS:Nube De-Ess/nube_deess.jsfx"
local PRESET = 15
os.execute('mkdir -p "' .. OUT .. '"')
local logf = io.open(OUT .. "/log.txt", "w")
local function log(...) local t = {} for _, v in ipairs({...}) do t[#t+1] = tostring(v) end logf:write(table.concat(t, " "), "\n") logf:flush() end

-- slider N (1..15) = parámetro N-1. Los sliders con forma :log=mid van normalizados 0..1
local LOGP = {[3] = {1, 20, 4}, [4] = {1000, 16000, 4000}, [5] = {2000, 20000, 8000}, [6] = {0.05, 20, 2}, [7] = {5, 500, 60}}
local function to_norm(s, v)
  local mn, mx, mid = table.unpack(LOGP[s])
  local sr = (mx - mn) / (mid - mn) - 1; local r = sr * sr
  return math.log((v - mn) / (mx - mn) * (r - 1) + 1) / math.log(r)
end
local function with(a, b) local r = {} for k, v in pairs(a) do r[k] = v end for k, v in pairs(b or {}) do r[k] = v end return r end
-- base: relativa, umbral -10, rango 10, ratio 4, desde 5 kHz, sin limite, ataque 0.05, release 40
local B = {[1] = -10, [2] = 10, [3] = 4, [4] = 5000, [5] = 20000, [6] = 0.05, [7] = 40}
local ABS = with(B, {[12] = 1, [1] = -20, [2] = 30})

local CASES = {
  {"rel_1k",        "s1k_m6.wav",  B},
  {"rel_8k",        "s8k_m6.wav",  B},
  {"rel_8k_m30",    "s8k_m30.wav", B},
  {"abs_8k",        "s8k_m6.wav",  ABS},
  {"abs_8k_m30",    "s8k_m30.wav", ABS},
  {"abs_ratio2",    "s8k_m6.wav",  with(ABS, {[3] = 2})},
  {"flat_partida",  "impulse.wav", with(B, {[2] = 0})},
  {"flat_banda",    "impulse.wav", with(B, {[2] = 0, [11] = 1, [5] = 10000})},
  {"flat_ancha",    "impulse.wav", with(B, {[2] = 0, [11] = 2})},
  {"partida_15k",   "s8k_15k.wav", with(B, {[5] = 10000})},
  {"banda_15k",     "s8k_15k.wav", with(B, {[11] = 1, [5] = 10000})},
  {"ancha_1k8k",    "s1k_8k.wav",  with(B, {[11] = 2})},
  {"partida_1k8k",  "s1k_8k.wav",  B},
  {"listen_det_1k", "s1k_m6.wav",  with(B, {[14] = 1})},
  {"listen_det_8k", "s8k_m6.wav",  with(B, {[14] = 1})},
  {"delta_8k",      "s8k_m6.wav",  with(B, {[14] = 2})},
  {"solo_mid",      "s8k_m6.wav",  with(B, {[13] = 2})},
  {"solo_side",     "s8k_m6.wav",  with(B, {[13] = 3})},
  {"link100",       "lr8k.wav",    ABS},
  {"link0",         "lr8k.wav",    with(ABS, {[9] = 0})},
  {"salida6",       "s1k_m6.wav",  with(B, {[10] = 6})},
  {"timing",        "step8k.wav",  with(ABS, {[1] = -30, [2] = 30, [6] = 5, [7] = 100, [11] = 2})},
  {"la_off",        "burst8k.wav", with(ABS, {[1] = -30, [2] = 10, [6] = 0.05, [11] = 2})},
  {"la_2",          "burst8k.wav", with(ABS, {[1] = -30, [2] = 10, [6] = 0.05, [8] = 2, [11] = 2})},
  {"voz_seca",      "voz.wav",     {[2] = 0}},
  {"voz_normal",    "voz.wav",     {[15] = 2}},
  {"voz_m20",       "voz.wav",     {[15] = 2}, 2, -20},
  {"voz_m20_seca",  "voz.wav",     {[2] = 0}, 2, -20},
}
for p = 1, 10 do CASES[#CASES + 1] = {"preset" .. p, "voz.wav", {[PRESET] = p}} end

reaper.Main_OnCommand(40859, 0) -- nueva pestaña
reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 48000, true)
reaper.GetSetProjectInfo(0, "PROJECT_SRATE_USE", 1, true)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
local item = reaper.AddMediaItemToTrack(tr)
local take = reaper.AddTakeToMediaItem(item)
reaper.SetMediaItemInfo_Value(item, "D_POSITION", 0)
local only = os.getenv("NUBE_CASE")

for _, c in ipairs(CASES) do
  local name, src, params = c[1], c[2], c[3]
  if not only or name:find(only) then
    reaper.SetMediaTrackInfo_Value(tr, "I_NCHAN", c[4] or 2)
    local s = reaper.PCM_Source_CreateFromFile(ROOT .. "/signals/" .. src)
    reaper.SetMediaItemTake_Source(take, s)
    reaper.SetMediaItemTakeInfo_Value(take, "D_VOL", 10 ^ ((c[5] or 0) / 20))
    reaper.SetMediaItemInfo_Value(item, "D_LENGTH", math.min(reaper.GetMediaSourceLength(s), 30))
    reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN", 0); reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN", 0)
    reaper.UpdateItemInProject(item)
    while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
    local fx = reaper.TrackFX_AddByName(tr, FX, false, -1)
    if fx < 0 then log("ERROR no cargó el FX") break end
    if params[PRESET] then reaper.TrackFX_SetParam(tr, fx, PRESET - 1, params[PRESET]) end
    for s_, v in pairs(params) do
      if s_ ~= PRESET then
        if LOGP[s_] then reaper.TrackFX_SetParamNormalized(tr, fx, s_ - 1, to_norm(s_, v))
        else reaper.TrackFX_SetParam(tr, fx, s_ - 1, v) end
      end
    end
    local file = OUT .. "/" .. name .. ".wav"
    os.remove(file)
    reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true)
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 1, true)
    reaper.GetSetProjectInfo(0, "RENDER_SRATE", 48000, true)
    reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, true)
    reaper.GetSetProjectInfo(0, "RENDER_TAILFLAG", 0, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", OUT, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, true)
    reaper.Main_OnCommand(42230, 0)
    local vals = {}
    for k = 1, 14 do local _, v = reaper.TrackFX_GetFormattedParamValue(tr, fx, k - 1, ""); vals[#vals + 1] = v end
    log("caso", name, table.concat(vals, " | "))
  end
end
reaper.Main_SaveProjectEx(0, OUT .. "/_tmp_test.rpp", 0)
reaper.Main_openProject("noprompt:" .. OUT .. "/_tmp_test.rpp")
reaper.Main_OnCommand(40860, 0) -- cerrar pestaña
log("done")
logf:close()
