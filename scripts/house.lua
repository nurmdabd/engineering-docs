--[[
house.lua -- pandoc Lua filter: Markdown AST -> house-style LaTeX body (see references/latex-rules.md, Sections 1-12).
Driven by md2tex.py; not meant to be called directly. Metadata options:
  house_class     extarticle | extreport
  house_fontsize  e.g. 12pt (table width estimates)
]]

local stringify = pandoc.utils.stringify
local CLASS, FONTPT, TEXTW = "extarticle", 12, 17.4
local GFM = {}            -- GitHub anchors of the top-level headings, in order (meta house_gfm)
local CMDS = {}           -- registered commands usable from Markdown (meta house_cmds, scripts/commands.py)
local PREFIX = ""         -- label prefix for every label of this file (meta house_prefix), e.g. "d03_"
local SHIFT = 0           -- heading levels to move up (meta house_shift): 1 when the file has no # heading
local STRUCT = "notes"    -- "past-paper" (meta house_structure): see types/past-paper/guide.md

local function latex(blocks_or_inlines, is_inline)
  local doc
  if is_inline then doc = pandoc.Pandoc({ pandoc.Plain(blocks_or_inlines) })
  else doc = pandoc.Pandoc(blocks_or_inlines) end
  local out = pandoc.write(doc, "latex", { wrap_text = "wrap-none" })
  return (out:gsub("%s+$", ""))
end

local function raw(s) return pandoc.RawInline("latex", s) end
local function rawb(s) return pandoc.RawBlock("latex", s) end

-- ---------- labels ----------
local used = {}
local function slug(s)
  s = s:lower():gsub("[^%w%-_ ]", ""):gsub("[%s%-]+", "_"):gsub("_+", "_"):gsub("^_", ""):gsub("_$", "")
  if s == "" then s = "s" end   -- e.g. a heading written only in Bangla; unique() numbers them
  return s
end
local function unique(lbl)
  if PREFIX ~= "" then lbl = lbl:gsub("^(%a+):", "%1:" .. PREFIX, 1) end   -- sec:x -> sec:d03_x
  local base, i = lbl, 2
  while used[lbl] do lbl = base .. "_" .. i; i = i + 1 end
  used[lbl] = true
  return lbl
end
local function id_to_label(id) return "sec:" .. slug(id) end

-- ---------- Unicode -> font-safe LaTeX (references/latex-rules.md, Section 10) ----------
local MATHCH = {
  ["β"] = "\\beta", ["δ"] = "\\delta", ["θ"] = "\\theta", ["λ"] = "\\lambda", ["π"] = "\\pi",
  ["σ"] = "\\sigma", ["τ"] = "\\tau", ["φ"] = "\\varphi", ["ω"] = "\\omega", ["α"] = "\\alpha",
  ["γ"] = "\\gamma", ["ε"] = "\\varepsilon", ["η"] = "\\eta", ["ρ"] = "\\rho", ["ψ"] = "\\psi",
  ["μ"] = "\\mu", ["Ω"] = "\\Omega", ["Φ"] = "\\Phi", ["Θ"] = "\\Theta", ["Λ"] = "\\Lambda",
  ["′"] = "^{\\prime}", ["⅓"] = "\\tfrac13", ["↔"] = "\\leftrightarrow", ["∈"] = "\\in",
  ["∝"] = "\\propto", ["∫"] = "\\int", ["≈"] = "\\approx", ["≠"] = "\\neq", ["≤"] = "\\le",
  ["≥"] = "\\ge", ["≪"] = "\\ll", ["≫"] = "\\gg", ["⊕"] = "\\oplus", ["⇒"] = "\\Rightarrow",
  ["⇔"] = "\\Leftrightarrow", ["∞"] = "\\infty", ["∑"] = "\\sum", ["∂"] = "\\partial",
  ["☐"] = "\\square", ["☒"] = "\\boxtimes",
}
local SUP = { ["⁰"]="0", ["¹"]="1", ["²"]="2", ["³"]="3", ["⁴"]="4", ["⁵"]="5", ["⁶"]="6", ["⁷"]="7", ["⁸"]="8", ["⁹"]="9", ["⁻"]="-", ["⁺"]="+" }
local SUB = { ["₀"]="0", ["₁"]="1", ["₂"]="2", ["₃"]="3", ["₄"]="4", ["₅"]="5", ["₆"]="6", ["₇"]="7", ["₈"]="8", ["₉"]="9" }
local TEXTCH = {
  ["⚠"] = "\\warnmark{}", ["✅"] = "\\okmark{}", ["✔"] = "\\okmark{}", ["✓"] = "\\okmark{}",
  ["❌"] = "\\nomark{}", ["✘"] = "\\nomark{}", ["🎯"] = "\\exammark{}", ["📌"] = "\\pinmark{}",
  ["★"] = "{\\emojifont ★}", ["⭐"] = "{\\emojifont ★}", ["➕"] = "{\\bfseries +}",
  ["①"] = "\\textcircled{\\scriptsize 1}", ["②"] = "\\textcircled{\\scriptsize 2}",
  ["③"] = "\\textcircled{\\scriptsize 3}", ["④"] = "\\textcircled{\\scriptsize 4}",
  ["\u{FE0F}"] = "", ["💡"] = "", ["📝"] = "", ["📘"] = "", ["🖼"] = "", ["✍"] = "",
}
local COMBINING_HAT = "\u{0302}"

local function convert_str(text)
  local needs = false
  for _, cp in utf8.codes(text) do
    local ch = utf8.char(cp)
    if cp > 127 and (MATHCH[ch] or SUP[ch] or SUB[ch] or TEXTCH[ch] or ch == COMBINING_HAT) then needs = true; break end
  end
  if not needs then return nil end
  local chars = {}
  for _, cp in utf8.codes(text) do chars[#chars + 1] = utf8.char(cp) end
  local out, buf, i = {}, "", 1
  local function flush() if buf ~= "" then out[#out + 1] = pandoc.Str(buf); buf = "" end end
  local function mathpiece(tex, orig) flush(); out[#out + 1] = raw("\\texorpdfstring{$" .. tex .. "$}{" .. orig .. "}") end
  while i <= #chars do
    local ch = chars[i]
    if chars[i + 1] == COMBINING_HAT then
      mathpiece("\\hat{" .. ch .. "}", ch); i = i + 2
    elseif SUP[ch] or SUB[ch] then
      local map, s, orig = SUP[ch] and SUP or SUB, "", ""
      while chars[i] and map[chars[i]] do s = s .. map[chars[i]]; orig = orig .. chars[i]; i = i + 1 end
      mathpiece((map == SUP and "^{" or "_{") .. s .. "}", orig)
    elseif MATHCH[ch] then mathpiece(MATHCH[ch], ch); i = i + 1
    elseif TEXTCH[ch] then flush(); if TEXTCH[ch] ~= "" then out[#out + 1] = raw(TEXTCH[ch]) end; i = i + 1
    else buf = buf .. ch; i = i + 1 end
  end
  flush()
  return out
end

-- ---------- pass 1: metadata ----------
local meta_filter = {
  Meta = function(m)
    if m.house_class then CLASS = stringify(m.house_class) end
    if m.house_textwidth then TEXTW = tonumber(stringify(m.house_textwidth)) or 17.4 end
    if m.house_fontsize then FONTPT = tonumber((stringify(m.house_fontsize):gsub("pt", ""))) or 12 end
    if m.house_structure then STRUCT = stringify(m.house_structure) end
    if m.house_prefix then PREFIX = stringify(m.house_prefix) end
    if m.house_shift then SHIFT = tonumber(stringify(m.house_shift)) or 0 end
    if m.house_cmds then
      for entry in stringify(m.house_cmds):gmatch("[^;]+") do
        local name, kind, args, opt = entry:match("^([^|]*)|([^|]*)|([^|]*)|([^|]*)$")
        if name then
          local list = {}
          for x in args:gmatch("[^,]+") do list[#list + 1] = x end
          CMDS[name] = { kind = kind, args = list, opt = opt ~= "" and opt or nil }
        end
      end
    end
    if m.house_gfm then for w in stringify(m.house_gfm):gmatch("%S+") do GFM[#GFM + 1] = w end end
  end,
}

-- ---------- pass 2: document structure ----------
local idmap = {}          -- md anchor id -> latex label (pandoc's ids, and GitHub's anchors from md2tex.py)
local Q_PAT = "^%u%u?%d+%a?$"            -- N1, S12, L3, Q4a
local S_PAT = "^Solution%s+(%u%u?%d+%a?)$"

local function header_text(h) return stringify(h.content) end

local function strip_heading_number(h)
  local c = h.content
  if #c >= 2 and c[1].t == "Str" and c[1].text:match("^%d+[%.%d]*%.?$") and c[2].t == "Space" then
    c:remove(1); c:remove(1)
  end
  local last = c[#c]
  if last and last.t == "Str" and last.text:match(":$") then last.text = last.text:gsub(":$", "") end
end

-- visible width in "characters": Bengali vowel signs, hasanta, nukta etc. combine with the
-- previous letter and take almost no width, so they are not counted
local function vlen(text)
  local n = 0
  for _, cp in utf8.codes(text) do
    if not ((cp >= 0x0981 and cp <= 0x0983) or cp == 0x09BC or (cp >= 0x09BE and cp <= 0x09CD)
        or cp == 0x09D7 or cp == 0x200C or cp == 0x200D) then n = n + 1 end
  end
  return n
end

local function math_len(inl, mathonly)
  local n, mn = 0, 0
  inl:walk({
    Str = function(s) n = n + vlen(s.text) end,
    Space = function() n = n + 1 end,
    Math = function(m)
      local t = m.text:gsub("\\[dt]?frac", ""):gsub("\\[a-zA-Z]+", "x"):gsub("[{}%^_ ]", "")
      n = n + math.ceil(#t * 0.9); mn = mn + math.ceil(#t * 0.9)
    end,
    Code = function(c) n = n + #c.text end,
  })
  if mathonly then return mn end
  return n
end

local function table_metrics(tbl)
  local ncol = #tbl.colspecs
  local maxl, sum, cnt, msum, tall, mmax, mword = {}, {}, {}, {}, {}, {}, {}
  for j = 1, ncol do maxl[j], sum[j], cnt[j], msum[j], tall[j], mmax[j], mword[j] = 0, 0, 0, 0, 0, 0, 0 end
  local function scan(rows, is_head)
    for _, row in ipairs(rows) do
      for j, cell in ipairs(row.cells) do
        if j <= ncol then
          local l = math_len(pandoc.Blocks(cell.contents))
          -- longest unbreakable word (Bangla words cannot be hyphenated)
          pandoc.Blocks(cell.contents):walk({ Str = function(x)
            local w = vlen(x.text)
            if w > mword[j] then mword[j] = w end
          end })
          if is_head then l = l + 2 end
          if l > maxl[j] then maxl[j] = l end
          if not is_head then
            sum[j] = sum[j] + l; cnt[j] = cnt[j] + 1
            msum[j] = msum[j] + math_len(pandoc.Blocks(cell.contents), true)
            pandoc.Blocks(cell.contents):walk({ Math = function(m)
              local ml = math_len(pandoc.Inlines({ m }), true)
              if ml > mmax[j] then mmax[j] = ml end
              if m.text:match("\\[dt]?frac") or m.text:match("\\int") or m.text:match("\\sum")
                or m.text:match("\\left") or m.text:match("\\begin") or m.text:match("\\sqrt")
                or m.text:match("\\overline") or m.text:match("\\displaystyle") or m.text:match("\\boxed") then
                tall[j] = 1
              end
            end })
          end
        end
      end
    end
  end
  scan(tbl.head.rows, true)
  for _, b in ipairs(tbl.bodies) do scan(b.body, false) end
  local avg, mshare = {}, {}
  for j = 1, ncol do
    avg[j] = cnt[j] > 0 and sum[j] / cnt[j] or 0
    mshare[j] = sum[j] > 0 and msum[j] / sum[j] or 0
  end
  return maxl, avg, mshare, tall, mmax, mword
end

local function first_display_math_only(blk)
  if blk.t ~= "Para" then return false end
  local seen = false
  for _, x in ipairs(blk.content) do
    if x.t == "Math" and x.mathtype == "DisplayMath" then seen = true
    elseif x.t ~= "Space" and x.t ~= "SoftBreak" then return false end
  end
  return seen
end

local function make_equation(m, label)
  local t = m.text:gsub("^%s+", ""):gsub("%s+$", "")
  if STRUCT == "past-paper" then   -- solutions use unnumbered display maths, like the user's own files
    if t:find("\\\\") and not t:find("\\begin{") then
      local env = t:find("&") and "aligned" or "gathered"
      t = "\\begin{" .. env .. "}\n" .. t .. "\n\\end{" .. env .. "}"
    end
    return "\\[\n    " .. t:gsub("\n", "\n    ") .. "\n\\]"
  end
  local env = "equation"
  if t:find("\\\\") and not t:find("\\begin{") then   -- several lines in one $$ block: one equation, aligned at &
    local env = t:find("&") and "aligned" or "gathered"
    t = "\\begin{" .. env .. "}\n" .. t .. "\n\\end{" .. env .. "}"
  end
  return "\\begin{" .. env .. "}\n    " .. t:gsub("\n", "\n    ") .. "\n    \\label{" .. label .. "}\n\\end{" .. env .. "}"
end

-- ---------- past papers (STRUCT == "past-paper") ----------
-- "# Question 1" + a list of sub-parts -> the paper block (mainquestion);
-- "## 1(a) Title" ... -> questionblock[Title]{full question text, taken from the paper list}.
local PP = { qtext = {}, num = nil }

local function strip_marks(inls)   -- remove a trailing "[Marks: 5]" or "[5 marks]"; return the number
  local acc = ""
  for k = #inls, 1, -1 do
    acc = stringify(pandoc.Inlines({ inls[k] })) .. acc
    if acc:match("^%[") then
      local m = acc:match("^%[%s*[Mm]arks:?%s*(%d+)%s*%]%s*$") or acc:match("^%[%s*(%d+)%s*[Mm]arks?%s*%]%s*$")
      if not m then return nil end
      for _ = k, #inls do inls:remove(k) end
      while #inls > 0 and inls[#inls].t == "Space" do inls:remove(#inls) end
      return m
    end
  end
end

local function mark_items(list, top)
  for _, item in ipairs(list.content) do
    local first = item[1]
    if first and (first.t == "Plain" or first.t == "Para") and first.content[1] and first.content[1].t == "Strong" then
      local c = first.content
      local label = stringify(c[1])
      c:remove(1)
      while c[1] and c[1].t == "Space" do c:remove(1) end
      c:insert(1, raw("@@ITEM:" .. label .. "@@"))
      if top then
        PP.num = label:match("^(%d+)") or PP.num
        local letter = label:match("%((%a+)%)")
        if letter and PP.num then
          c:insert(2, raw("@@Q:" .. PP.num .. "(" .. letter .. ")@@"))
          item:insert(rawb("@@/Q@@"))
        end
      end
    end
    for _, blk in ipairs(item) do
      if blk.t == "Plain" or blk.t == "Para" then
        local m = strip_marks(blk.content)
        if m then blk.content:insert(raw(" \\hfill Marks: " .. m)) end
      elseif blk.t == "BulletList" or blk.t == "OrderedList" then
        mark_items(blk, false)
      end
    end
  end
end

local function past_paper_group(blocks, i, out)
  local h = blocks[i]; i = i + 1
  local body = pandoc.List()
  while i <= #blocks and not (blocks[i].t == "Header" and blocks[i].level <= 2) do body:insert(blocks[i]); i = i + 1 end
  if h.level == 1 then
    for _, blk in ipairs(body) do
      if blk.t == "BulletList" or blk.t == "OrderedList" then mark_items(blk, true) end
    end
    out:insert(pandoc.Div(body, pandoc.Attr("", { "paper" })))
  else
    local txt = header_text(h)
    PP.num = txt:match("^(%d+)") or PP.num
    local letter = txt:match("^%d*%s*%.?%s*%((%a+)%)")
    local key = (PP.num or "?") .. "(" .. (letter or "?") .. ")"
    local content = pandoc.List({ pandoc.Div({ pandoc.Plain(h.content) }, pandoc.Attr("", { "qtitle" })) })
    if body[1] and body[1].t == "BlockQuote" then   -- the question written out, for a part not in the paper list
      content:insert(pandoc.Div(body[1].content, pandoc.Attr("", { "qtext" })))
      body:remove(1)
    end
    content:extend(body)
    out:insert(pandoc.Div(content, pandoc.Attr("", { "qblock" }, { key = key })))
  end
  return i
end

local structure_filter = {
  Pandoc = function(doc)
    local blocks = doc.blocks
    if SHIFT > 0 then   -- a file that starts at ##: its top heading level becomes the first one
      for _, b in ipairs(blocks) do if b.t == "Header" then b.level = math.max(1, b.level - SHIFT) end end
    end
    local out = pandoc.List()
    local cur_sec, eqn, tabn, cur_title = "doc", {}, {}, ""
    -- first, labels for every header (links may point forward)
    for _, b in ipairs(blocks) do
      if b.t == "Header" then
        local txt = header_text(b)
        local q = txt:match(Q_PAT) and txt or nil
        local s = txt:match(S_PAT)
        if q then idmap[b.identifier] = unique("q:" .. slug(q))
        elseif s then idmap[b.identifier] = unique("sol:" .. slug(s))
        else idmap[b.identifier] = unique(id_to_label(b.identifier)) end
      end
    end
    -- GitHub anchors: the n-th heading md2tex.py saw is the n-th top-level Header, if the counts agree
    local heads = {}
    for _, b in ipairs(blocks) do if b.t == "Header" then heads[#heads + 1] = b end end
    if #heads == #GFM then
      for n, b in ipairs(heads) do
        if not idmap[GFM[n]] then idmap[GFM[n]] = idmap[b.identifier] end
      end
    end
    local i = 1
    while i <= #blocks do
      local b = blocks[i]
      if b.t == "HorizontalRule" then
        i = i + 1
      elseif b.t == "Header" and header_text(b):lower() == "contents" then
        local lvl = b.level; i = i + 1
        while i <= #blocks and not (blocks[i].t == "Header" and blocks[i].level <= lvl) do i = i + 1 end
      elseif STRUCT == "past-paper" and b.t == "Header" then
        if b.level <= 2 then i = past_paper_group(blocks, i, out) else out:insert(b); i = i + 1 end
      elseif b.t == "Header" then
        local txt = header_text(b)
        local q, s = txt:match(Q_PAT), txt:match(S_PAT)
        if q or s then
          local body = pandoc.List(); i = i + 1
          while i <= #blocks and blocks[i].t ~= "Header" and blocks[i].t ~= "HorizontalRule" do body:insert(blocks[i]); i = i + 1 end
          local key = q and txt or s
          local attr = pandoc.Attr("", { q and "question" or "solution" },
            { title = q and txt or ("Solution " .. s), self = idmap[b.identifier],
              other = q and ("sol:" .. slug(key)) or ("q:" .. slug(key)) })
          out:insert(pandoc.Div(body, attr))
        else
          strip_heading_number(b)
          cur_sec = idmap[b.identifier]:gsub("^sec:", "")
          cur_title = stringify(b.content)
          b.attributes["label"] = idmap[b.identifier]
          out:insert(b); i = i + 1
          if txt:lower():find("self%-check") then
            local body = pandoc.List()
            while i <= #blocks and blocks[i].t ~= "Header" and blocks[i].t ~= "HorizontalRule" do body:insert(blocks[i]); i = i + 1 end
            out:insert(pandoc.Div(body, pandoc.Attr("", { "selfcheck" })))
          end
        end
      else
        out:insert(b); i = i + 1
      end
    end
    -- equations, tables, eqnote, images: need section context
    local short = function(s) return (s:sub(1, 28):gsub("_$", "")) end
    local sec_for = {}
    local final = pandoc.List()
    local k = 1
    local function eq_label()
      local key = short(cur_sec); eqn[key] = (eqn[key] or 0) + 1
      return unique("eq:" .. key .. "_" .. eqn[key])
    end
    local function convert_display(blk)
      return blk:walk({ Math = function(m)
        if m.mathtype == "DisplayMath" then return raw(make_equation(m, eq_label())) end
      end })
    end
    local function tag_tables(blk)
      local function tag(t)
        local maxl, avg, mshare, tall, mmax, mword = table_metrics(t)
        local ms, as, sh, tl, mm, mw = {}, {}, {}, {}, {}, {}
        for j = 1, #maxl do
          ms[j] = tostring(maxl[j]); as[j] = string.format("%.1f", avg[j])
          sh[j] = string.format("%.2f", mshare[j]); tl[j] = tostring(tall[j]); mm[j] = tostring(mmax[j]); mw[j] = tostring(mword[j])
        end
        local cap = stringify(t.caption.long or {})
        if cap == "" then cap = cur_title ~= "" and cur_title or "Summary" end
        for _, e in ipairs({ "🎯", "⚠", "📌", "\u{FE0F}" }) do cap = cap:gsub(e, "") end
        cap = cap:gsub("%(%s*%)", ""):gsub("%s+$", ""):gsub("%s%s+", " ")
        tabn[cur_sec] = (tabn[cur_sec] or 0) + 1
        local at = t.attr
        at.attributes["maxl"] = table.concat(ms, ",")
        at.attributes["avg"] = table.concat(as, ",")
        at.attributes["mshare"] = table.concat(sh, ",")
        at.attributes["tall"] = table.concat(tl, ",")
        at.attributes["mmax"] = table.concat(mm, ",")
        at.attributes["mword"] = table.concat(mw, ",")
        at.attributes["cap"] = cap
        at.attributes["lab"] = unique("tab:" .. short(cur_sec) .. (tabn[cur_sec] > 1 and ("_" .. tabn[cur_sec]) or ""))
        t.attr = at
        return t
      end
      if blk.t == "Table" then return tag(blk) end
      return blk:walk({ Table = tag })
    end
    while k <= #out do
      local b = out[k]
      if b.t == "Header" then
        cur_sec = (b.attributes["label"] or ("sec:" .. cur_sec)):gsub("^sec:", ""); cur_title = stringify(b.content)
        local nxt = out[k + 1]
        if nxt and (nxt.t == "Table" or (nxt.t == "Para" and #nxt.content == 1 and nxt.content[1].t == "Image")) then
          b.attributes["keep"] = "1"
        end
        final:insert(b); k = k + 1
      elseif first_display_math_only(b) and out[k + 1] and out[k + 1].t == "Para"
          and out[k + 1].content[1] and out[k + 1].content[1].t == "Emph"
          and stringify(out[k + 1].content[1]):match("^Write also") then
        local eq = convert_display(b)
        final:insert(pandoc.Div({ eq, out[k + 1] }, pandoc.Attr("", { "eqnote" })))
        k = k + 2
      else
        local saved = cur_title
        if b.t == "Div" and b.attributes["title"] then cur_title = b.attributes["title"] end
        final:insert(tag_tables(convert_display(b))); k = k + 1
        cur_title = saved
      end
    end
    doc.blocks = final
    return doc
  end,
}

-- ---------- registered commands from Markdown ----------
local RAW_ARG = { label = true, width = true, url = true, path = true }   -- passed through untouched
local function cmd_args(spec, attrs, skip_last)
  local function value(name)
    local v = attrs[name]
    if v == nil then return nil end
    if RAW_ARG[name] then return v end
    local doc = pandoc.read(v, "markdown")
    return doc.blocks[1] and latex(doc.blocks[1].content, true) or ""
  end
  local out = ""
  if spec.opt and attrs[spec.opt] then out = out .. "[" .. value(spec.opt) .. "]" end
  local n = #spec.args - (skip_last and 1 or 0)
  for k = 1, n do out = out .. "{" .. (value(spec.args[k]) or "") .. "}" end
  return out
end

-- ---------- pass 3: inline content ----------
local inline_filter = {
  Str = function(s) return convert_str(s.text) end,
  RawInline = function(r)
    if r.format == "html" and r.text:match("^<br%s*/?>$") then return raw("\\newline ") end
  end,
  Span = function(sp)   -- [text]{.name attr="..."} -> \name[opt]{attr}...{text} for a registered command
    local spec = CMDS[sp.classes[1]]
    if spec and spec.kind == "command" then
      local head = "\\" .. sp.classes[1] .. cmd_args(spec, sp.attributes, #spec.args > 0)
      if #spec.args == 0 then return raw(head) end
      local out = pandoc.List({ raw(head .. "{") }); out:extend(sp.content); out:insert(raw("}"))
      return out
    end
  end,
  Math = function(m)
    if m.mathtype == "InlineMath" then return raw("$" .. m.text:gsub("^%s+", ""):gsub("%s+$", "") .. "$") end
  end,
  Link = function(l)
    local t = l.target
    if t:match("^https?:") or t:match("^mailto:") then return nil end
    local id = t:match("^#(.+)$")
    if id then
      local lbl = idmap[id]
      if not lbl then return l.content end
      local txt = stringify(l.content)
      if (lbl:match("^sol:") and txt:match("Solution")) or (lbl:match("^q:") and txt:match("Back")) then
        return {}   -- the box title bar carries these links
      end
      return raw("\\hyperref[" .. lbl .. "]{" .. latex(l.content, true) .. "}")
    end
    local file, frag = t:match("^([^#]-)%.md#?(.*)$")
    if file then
      local base = file:match("([^/]+)$")
      local dest = base .. ".pdf" .. (frag ~= "" and ("\\#" .. id_to_label(frag)) or "")
      return raw("\\href{" .. dest .. "}{" .. latex(l.content, true) .. "}")
    end
  end,
}

-- ---------- pass 4: paragraphs (labels, keyterms, figures, equations, examples) ----------
local STRESS_MAX_WORDS = 3
-- **bold** is a key term, except stress words: "not", "before", "the same" ... become \emph
local STRESS = {}
for w in ([[not no never only before after up down and or but yes one two three same all both each every also very
  more less much must always first last then now still even just here there without with why how what when where
  which this that these those half twice double zero none the a an is are was be do does instead rather]]):gmatch("%S+") do
  STRESS[w] = true
end
local function is_stress(txt)
  if not txt:match("^[%l][%l%s']*$") then return false end
  for w in txt:gmatch("%S+") do
    if not STRESS[w] and #w > 1 then return false end   -- single letters (r, k) count as stress, like variables
  end
  return true
end

local function is_label_strong(inls)
  local k = 1
  while inls[k] and ((inls[k].t == "RawInline" and inls[k].text:match("mark{}$")) or inls[k].t == "Space") do k = k + 1 end
  local f = inls[k]
  if not f or f.t ~= "Strong" then return false end
  local s = stringify(f)
  if s:match("[:%.%?]$") or s:match("—$") or s:match("।$") then return k end
  if STRUCT == "past-paper" and s:match("^%d*%.?%s*%(%w+%)$") then return k end   -- a part label: **(a)**, **1.(b)**
  local n = inls[k + 1]
  if n and n.t == "Str" and (n.text:match("^[:%.]") or n.text:match("^।")) then return k end
  return false
end

local function convert_emphasis(inls)
  return pandoc.Inlines(inls):walk({
    Strong = function(s)
      local txt = stringify(s)
      local words = select(2, txt:gsub("%S+", ""))
      if words <= STRESS_MAX_WORDS and is_stress(txt) then
        return raw("\\emph{" .. latex(s.content, true) .. "}")
      end
      if STRUCT == "past-paper" and txt:match("^%d*%.?%s*%(%w+%)$") then   -- a part label such as (d)
        return raw("\\textbf{" .. latex(s.content, true) .. "}")
      end
      return raw("\\keyterm{" .. latex(s.content, true) .. "}")
    end,
  })
end

local function code_to_verb(inls)
  for j, x in ipairs(inls) do
    if x.t == "Code" and not x.text:find("|", 1, true) then inls[j] = raw("\\verb|" .. x.text .. "|") end
  end
  return inls
end

local ACRO = { fm=1, pm=1, nbfm=1, wbfm=1, pcm=1, dpcm=1, adpcm=1, dm=1, adm=1, ask=1, fsk=1, psk=1, dpsk=1, qpsk=1,
  qam=1, fdm=1, tdm=1, wdm=1, gsm=1, cdma=1, pll=1, vco=1, lpf=1, bpf=1, sqnr=1, ami=1, nrz=1, rz=1, tx=1, rx=1,
  mux=1, demux=1, snr=1, psd=1, ooK=1, ook=1, pam=1, pwm=1, ppm=1, am=1, dsb=1, sc=1, nld=1, rf=1, lo=1, ssb=1,
  fhss=1, dsss=1, fdma=1, tdma=1, bts=1, bsc=1, msc=1, i=0 }
local function humanize(path)
  local name = path:match("([^/]+)%.%w+$") or path
  name = name:gsub("^%u+%d*%-?%d*_", ""):gsub("^%l%d+_", "")
  local words = {}
  for w in name:gmatch("[^_%-]+") do
    if ACRO[w:lower()] == 1 then w = w:upper() end
    words[#words + 1] = w
  end
  local s = table.concat(words, " ")
  return (s:gsub("^%l", string.upper)), slug(name)
end

local function figure_block(img)
  local cap = stringify(img.caption)
  local human, sl = humanize(img.src)
  local captex
  if cap == "" then captex = latex({ pandoc.Str(human) }, true) else captex = latex(img.caption, true) end
  local lbl = unique("fig:" .. sl)
  return rawb("\\begin{figure}[H]\n    \\centering\n    \\includegraphics[width=@@W:" .. img.src .. "@@]{@@P:" .. img.src ..
    "@@}\n    \\caption{" .. captex .. "}\n    \\label{" .. lbl .. "}\n\\end{figure}")
end

local function split_on_breaks(inls)
  -- a soft break followed by an enumerator -- (b), (iv), (10) -- or a bold label starts a new paragraph
  local parts, cur = {}, pandoc.List()
  for j, x in ipairs(inls) do
    local nxt = inls[j + 1]
    local enum = nxt and nxt.t == "Str" and (nxt.text:match("^%(%a%)") or nxt.text:match("^%([ivx]+%)")
                                         or nxt.text:match("^%(%d+%)"))   -- (b), (iv), (10)
    if x.t == "SoftBreak" and nxt and (enum or
        (nxt.t == "Strong" and (stringify(nxt):match("[:%.%?]$") or stringify(nxt):match("।$")))) then
      parts[#parts + 1] = cur; cur = pandoc.List()
    else cur:insert(x) end
  end
  parts[#parts + 1] = cur
  return parts
end

local function render_para(inls, ctor)
  local blocks = pandoc.List()
  for _, part in ipairs(split_on_breaks(inls)) do
    -- split out display equations (already RawInline \begin{equation})
    local cur = pandoc.List()
    local function flush()
      while #cur > 0 and (cur[#cur].t == "Space" or cur[#cur].t == "SoftBreak") do cur:remove(#cur) end
      while #cur > 0 and (cur[1].t == "Space" or cur[1].t == "SoftBreak") do cur:remove(1) end
      if #cur > 0 then
        local lab = is_label_strong(cur)
        if lab then
          cur[lab] = raw("\\textbf{" .. latex(cur[lab].content, true) .. "}")
        end
        blocks:insert(ctor(convert_emphasis(code_to_verb(cur))))
      end
      cur = pandoc.List()
    end
    for _, x in ipairs(part) do
      if x.t == "RawInline" and x.text:match("^\\begin{equation}") then flush(); blocks:insert(rawb(x.text))
      else cur:insert(x) end
    end
    flush()
  end
  return blocks
end

local function para(p, ctor)
  local c = p.content
  if #c == 1 and c[1].t == "Image" then return figure_block(c[1]) end
  -- worked example paragraph -> examplebox
  if c[1] and c[1].t == "Strong" and (stringify(c[1]):match("^Examples?[%s:%.—]") or stringify(c[1]):match("^Examples?$")
      or stringify(c[1]):match("^Worked example") or stringify(c[1]):match("^উদাহরণ")
      or stringify(c[1]):match("^সমাধানকৃত উদাহরণ")) then
    local title = latex(c[1].content, true):gsub("[:%.]$", ""):gsub("।$", "")
    local rest = pandoc.List(c); rest:remove(1)
    while rest[1] and (rest[1].t == "Space" or (rest[1].t == "Str" and rest[1].text == ":")) do rest:remove(1) end
    local inner = render_para(rest, ctor)
    local out = pandoc.List({ rawb("\\begin{examplebox}[" .. title .. "]") })
    out:extend(inner); out:insert(rawb("\\end{examplebox}"))
    return out
  end
  return render_para(c, ctor)
end

local para_filter = {
  Para = function(p) return para(p, pandoc.Para) end,
  Plain = function(p) return para(p, pandoc.Plain) end,
}

-- ---------- pass 5: block structure ----------
local function trimnl(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end

local function list_block(items, env, opts)
  local lines = { "\\begin{" .. env .. "}" .. (opts or "") }
  for _, it in ipairs(items) do
    local body = trimnl(latex(it, false)):gsub("\n", "\n    ")
    lines[#lines + 1] = "    \\item " .. body
  end
  lines[#lines + 1] = "\\end{" .. env .. "}"
  return rawb(table.concat(lines, "\n"))
end

local TT_ESC = { ["\\"] = "\\textbackslash{}", ["&"] = "\\&", ["%"] = "\\%", ["$"] = "\\$", ["#"] = "\\#",
  ["_"] = "\\_", ["{"] = "\\{", ["}"] = "\\}", ["~"] = "\\textasciitilde{}", ["^"] = "\\textasciicircum{}" }
local function verb_to_texttt(s)   -- \verb can't sit inside a table cell (or any argument); \texttt can
  return (s:gsub("\\verb(%p)(.-)%1", function(_, t) return "\\texttt{" .. t:gsub("[\\&%%$#_{}~^]", TT_ESC) .. "}" end))
end
local function cell_tex(cell) return verb_to_texttt(trimnl(latex(cell.contents, false)):gsub("\n+", " ")) end

local function table_block(t)
  local maxl, avg = {}, {}
  for v in (t.attr.attributes["maxl"] or ""):gmatch("[^,]+") do maxl[#maxl + 1] = tonumber(v) end
  for v in (t.attr.attributes["avg"] or ""):gmatch("[^,]+") do avg[#avg + 1] = tonumber(v) end
  local mshare, tall = {}, {}
  for v in (t.attr.attributes["mshare"] or ""):gmatch("[^,]+") do mshare[#mshare + 1] = tonumber(v) end
  for v in (t.attr.attributes["tall"] or ""):gmatch("[^,]+") do tall[#tall + 1] = tonumber(v) end
  local mmax, mword = {}, {}
  for v in (t.attr.attributes["mmax"] or ""):gmatch("[^,]+") do mmax[#mmax + 1] = tonumber(v) end
  for v in (t.attr.attributes["mword"] or ""):gmatch("[^,]+") do mword[#mword + 1] = tonumber(v) end
  local ncol = #t.colspecs
  local cw = 0.0185 * FONTPT             -- cm per character, rough
  local textw = TEXTW
  local flex, best = nil, 0
  -- flexible column: the maths-heavy column with the longest entries (maths cannot wrap like text);
  -- otherwise the column with the longest average text
  -- a "formula column": mostly maths and clearly more maths-heavy than every other column
  for j = 1, ncol do
    local other = 0
    for i = 1, ncol do if i ~= j and (mshare[i] or 0) > other then other = mshare[i] end end
    if (mshare[j] or 0) >= 0.3 and (mshare[j] or 0) >= other + 0.25 and maxl[j] > best then best, flex = maxl[j], j end
  end
  if not flex then for j = 1, ncol do if avg[j] > best then best, flex = avg[j], j end end end
  local spec, kind, width = {}, {}, {}
  local fixed_total = 0
  for j = 1, ncol do
    if j == flex then
      kind[j] = "L"
    elseif maxl[j] <= 12 and (tall[j] or 0) == 0 then
      kind[j] = "c"; fixed_total = fixed_total + maxl[j] * cw + 0.5
    else
      -- text columns wrap to 2 lines (3 when the flexible column holds maths, which cannot wrap)
      local mathflex = (mshare[flex] or 0) >= 0.5
      local lines, cap = mathflex and 3 or 2, mathflex and 4.4 or 5.2
      local w = maxl[j] * cw + 0.4
      if w > 4.2 then w = math.max(maxl[j] * cw / lines + 0.5, 2.4) end
      if w > cap then w = cap end
      -- never narrower than the longest single formula (inline maths does not wrap well)
      local mw = (mmax[j] or 0) * cw * 1.05 + 0.4
      if w < mw then w = math.min(mw, 7.0) end
      -- ...and never narrower than its longest single word
      local ww = (mword[j] or 0) * cw * 1.15 + 0.4
      if w < ww then w = math.min(ww, 7.0) end
      kind[j] = "x"; width[j] = w; fixed_total = fixed_total + w
    end
  end
  -- two prose columns that both need room share the width equally
  if ncol == 2 and kind[flex] == "L" then
    local o = (flex == 1) and 2 or 1
    if kind[o] == "x" and maxl[o] >= 30 and avg[o] >= 0.7 * avg[flex] then kind[o] = "L"; width[o] = nil end
  end
  local has_flex = false
  for j = 1, ncol do if kind[j] == "L" then has_flex = true end end
  if not has_flex and fixed_total > textw * 0.95 then
    kind[flex] = "L"; width[flex] = nil; has_flex = true
  end
  local fixed_cap = textw - (has_flex and 5 or 0.5)
  local sumw = 0
  for j = 1, ncol do if kind[j] == "x" then sumw = sumw + width[j] end end
  local scale = (sumw > fixed_cap) and fixed_cap / sumw or 1
  for j = 1, ncol do
    if kind[j] == "x" then width[j] = string.format("%.1fcm", width[j] * scale); spec[j] = "x{" .. width[j] .. "}"
    else spec[j] = kind[j] end
  end
  local lines = { "\\begin{tabularx}{\\textwidth}{|" .. table.concat(spec, "|") .. "|}", "    \\hline", "    \\rowcolor{gray!15}" }
  for _, row in ipairs(t.head.rows) do
    local cells = {}
    for j, cell in ipairs(row.cells) do
      local txt = cell_tex(cell)
      local h
      if kind[j] == "L" then h = "\\CC{" .. txt .. "}"
      elseif kind[j] == "x" then h = "\\yy{" .. txt .. "}{" .. width[j] .. "}"
      else h = "\\cc{" .. txt .. "}" end
      cells[#cells + 1] = "    " .. h
    end
    lines[#lines + 1] = table.concat(cells, " &\n") .. " \\\\ \\hline"
  end
  lines[#lines + 1] = "\\endhead"   -- repeat the header row when the table continues on the next page
  lines[#lines + 1] = ""
  for _, body in ipairs(t.bodies) do
    for _, row in ipairs(body.body) do
      local cells = {}
      for j, cell in ipairs(row.cells) do
        local tex = cell_tex(cell)
        if (tall[j] or 0) == 1 and kind[j] ~= "c" and tex:match("%$") and
          (tex:match("\\[dt]?frac") or tex:match("\\int") or tex:match("\\sum") or tex:match("\\left")
           or tex:match("\\begin") or tex:match("\\sqrt") or tex:match("\\overline") or tex:match("\\displaystyle")
           or tex:match("\\boxed")) then
          tex = "\\tallcell{" .. tex .. "}"
        end
        cells[#cells + 1] = "    " .. tex
      end
      lines[#lines + 1] = table.concat(cells, " &\n") .. " \\\\ \\hline"
      lines[#lines + 1] = ""
    end
  end
  local cap = t.attr.attributes["cap"] or "Summary"
  cap = latex(pandoc.Inlines(convert_str(cap) or { pandoc.Str(cap) }), true)
  lines[#lines + 1] = "\\rowcolor{white}"   -- keep the caption row out of the banding
  lines[#lines + 1] = "\\caption{" .. cap .. "}"
  lines[#lines + 1] = "\\label{" .. (t.attr.attributes["lab"] or unique("tab:table")) .. "}"
  lines[#lines + 1] = "\\end{tabularx}"
  return rawb(table.concat(lines, "\n"))
end

local function box(env, opt, blocks)
  local out = pandoc.List({ rawb("\\begin{" .. env .. "}" .. (opt or "")) })
  out:extend(blocks); out:insert(rawb("\\end{" .. env .. "}"))
  return out
end

local function contains_table(blocks)
  local found = false
  pandoc.Blocks(blocks):walk({ RawBlock = function(r) if r.text:match("^\\begin{tabularx}") then found = true end end })
  return found
end

-- past papers: section names -> the type preamble's commands (types/past-paper/preamble.tex)
local SECTION_CMD = { ["theory"] = "\\theory", ["answer"] = "\\answer", ["keyword explanation"] = "\\keyword",
  ["keywords"] = "\\keyword", ["notes and remarks"] = "\\notes", ["notes"] = "\\notes",
  ["final concise answer"] = "\\answersummary", ["derivation / explanation"] = "\\derivation",
  ["derivation"] = "\\derivation" }

local function question_text(key, body)   -- a paper item's LaTeX -> "1.(a) text (i) ... Marks: 5"
  local marks
  body = body:gsub("\\hfill Marks: (%d+)", function(m) marks = m; return "" end)
  body = body:gsub("\\begin{%a+}", ""):gsub("\\end{%a+}", "")
  body = body:gsub("\\item @@ITEM:(.-)@@", "%1 "):gsub("\\item%s*", "")
  body = body:gsub("%s+", " "):gsub("^%s+", ""):gsub("%s+$", "")
  return key:gsub("^(%d+)%(", "%1.(") .. " " .. body .. (marks and (" Marks: " .. marks) or "")
end

local function soul_safe(s)   -- the question is highlighted with soul, which drops these UTF-8 characters
  s = s:gsub("\\texorpdfstring(%b{})(%b{})", function(a) return a:sub(2, -2) end)
  for from, to in pairs({ ["—"] = "---", ["–"] = "--", ["‘"] = "`", ["’"] = "'", ["“"] = "``", ["”"] = "''" }) do
    s = s:gsub(from, to)
  end
  return s
end

local MARK_ENV = { ["\\warnmark{}"] = "warnbox", ["\\exammark{}"] = "exambox", ["\\pinmark{}"] = "notebox" }

local block_filter = {
  BulletList = function(l) return list_block(l.content, "itemize") end,
  OrderedList = function(l)
    local st, opts = l.listAttributes.style, nil
    if st == "LowerAlpha" then opts = "[label=(\\alph*)]" elseif st == "UpperAlpha" then opts = "[label=(\\Alph*)]"
    elseif st == "LowerRoman" then opts = "[label=(\\roman*)]" end
    if l.listAttributes.start and l.listAttributes.start ~= 1 then
      opts = opts and (opts:sub(1, -2) .. ", start=" .. l.listAttributes.start .. "]") or ("[start=" .. l.listAttributes.start .. "]")
    end
    return list_block(l.content, "enumerate", opts)
  end,
  Table = table_block,
  CodeBlock = function(c)
    local lang = c.classes[1]
    local opt = lang and ("language=" .. lang .. ", ") or ""
    local cap = c.attributes["caption"]   -- Markdown, so _ and maths come out right
    if cap then
      local doc = pandoc.read(cap, "markdown")
      cap = doc.blocks[1] and verb_to_texttt(latex(doc.blocks[1].content, true)) or ""
    end
    return rawb("\\begin{lstlisting}[" .. opt .. "caption={" .. (cap or "Listing") .. "}]\n" .. c.text .. "\n\\end{lstlisting}")
  end,
  BlockQuote = function(q)
    if contains_table(q.content) then return q.content end
    local env, title = "notebox", nil
    local first = q.content[1]
    if first and (first.t == "Para" or first.t == "Plain") then
      local c = first.content
      if c[1] and c[1].t == "RawInline" and MARK_ENV[c[1].text] then
        env = MARK_ENV[c[1].text]; c:remove(1)
        while c[1] and c[1].t == "Space" do c:remove(1) end
      end
      if c[1] and c[1].t == "RawInline" and c[1].text:match("^\\textbf{") then
        title = c[1].text:gsub("^\\textbf{", ""):gsub("}$", ""):gsub("[:%.]$", ""):gsub("।$", "")
        c:remove(1)
        while c[1] and c[1].t == "Space" do c:remove(1) end
      end
    end
    return box(env, title and ("[" .. title .. "]") or nil, q.content)
  end,
  Div = function(d)
    local cls = d.classes[1]
    if cls == "question" or cls == "solution" then
      local env = cls == "question" and "questionbox" or "solutionbox"
      local out = pandoc.List({ rawb("\\phantomsection\\label{" .. d.attributes["self"] .. "}"),
        rawb("\\begin{" .. env .. "}{" .. d.attributes["title"] .. "}{" .. d.attributes["other"] .. "}") })
      out:extend(d.content); out:insert(rawb("\\end{" .. env .. "}"))
      return out
    elseif cls == "paper" then
      local tex = trimnl(latex(d.content, false))
      for key, body in tex:gmatch("@@Q:(.-)@@(.-)@@/Q@@") do PP.qtext[key] = question_text(key, body) end
      tex = tex:gsub("@@Q:.-@@", ""):gsub("%s*@@/Q@@", ""):gsub("\\item @@ITEM:(.-)@@%s*", "\\item[%1] ")
      return rawb("\\begin{mainquestion}\n" .. tex .. "\n\\end{mainquestion}")
    elseif cls == "qblock" then
      local title = trimnl(latex(d.content[1].content, false)):gsub("\n+", " ")
      local rest = pandoc.List()
      for k = 2, #d.content do rest:insert(d.content[k]) end
      local q
      if rest[1] and rest[1].t == "Div" and rest[1].classes[1] == "qtext" then
        q = trimnl(latex(rest[1].content, false)):gsub("\n+", " ")
        rest:remove(1)
        local key = d.attributes["key"]
        if not key:find("?", 1, true) and not q:match("^%s*%d") then q = key:gsub("^(%d+)%(", "%1.(") .. " " .. q end
      end
      q = q or PP.qtext[d.attributes["key"]] or title
      local out = pandoc.List({ rawb("\\begin{questionblock}[" .. title .. "]{" .. soul_safe(q) .. "}") })
      out:extend(rest); out:insert(rawb("\\end{questionblock}"))
      return out
    elseif CMDS[cls] and CMDS[cls].kind == "environment" then   -- ::: {.name attr="..."} for a registered environment
      local out = pandoc.List({ rawb("\\begin{" .. cls .. "}" .. cmd_args(CMDS[cls], d.attributes, false)) })
      out:extend(d.content); out:insert(rawb("\\end{" .. cls .. "}"))
      return out
    elseif cls == "selfcheck" then
      if contains_table(d.content) then return d.content end
      return box("selfcheckbox", nil, d.content)
    elseif cls == "eqnote" then
      local eq = trimnl(latex({ d.content[1] }, false))
      local note = trimnl(latex({ d.content[2] }, false))
      return rawb("\\begin{eqnote}{\n" .. eq .. "\n}{" .. note .. "}\n\\end{eqnote}")
    end
  end,
  Header = function(h)
    local title = latex(h.content, true)
    if STRUCT == "past-paper" then   -- ### Answer -> \answer, other ### -> \subsection, #### -> \subsubsection*
      local name = stringify(h.content):lower():gsub("^%s+", ""):gsub("%s+$", "")
      if h.level <= 3 then return rawb(SECTION_CMD[name] or ("\\subsection{" .. title .. "}")) end
      return rawb("\\subsubsection*{" .. title .. "}")
    end
    local lbl = h.attributes["label"]
    local cmds
    if CLASS == "extreport" then cmds = { "chapter", "section", "subsection", "subsubsection" }
    else cmds = { "section", "subsection", "subsubsection" } end
    local cmd = cmds[h.level]
    if not cmd then   -- run-in label; like \addcolon, no colon after a title that ends in punctuation
      local colon = stringify(h.content):match("[%?!%.:]%s*$") or stringify(h.content):match("।%s*$")
      return rawb("\\phantomsection\\label{" .. lbl .. "}\\textbf{" .. title .. (colon and "" or ":") .. "}")
    end
    local keep = h.attributes["keep"] and "\\needspace{10\\baselineskip}\n" or ""
    return rawb(keep .. "\\" .. cmd .. "{" .. title .. "}\n\\label{" .. lbl .. "}")
  end,
}

return { meta_filter, structure_filter, inline_filter, para_filter, block_filter }
