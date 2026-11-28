#!/usr/bin/env python3
"""SRF development-only structural checks. Python 3.10+, stdlib only.
Run on an explicitly supplied, trusted local snapshot; no network or writes.
A pass is structural evidence, never permission, activation or release acceptance.
"""
import argparse
import json
import re
import stat
from pathlib import Path

CORE = {"srf.governance", "srf.collaboration", "srf.facts",
        "srf.engineering", "srf.execution", "srf.workflow"}
KINDS = {"core", "adapter", "capability", "evolution", "extension"}
TYPES = {"MUST", "SHOULD", "MAY", "REFERENCE", "TEMPLATE"}
ID = re.compile(r"srf\.[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*\Z")
RULE = re.compile(r"SRF-R-[A-Z]+-[0-9]{3}\Z")
ENTRY = "entrypoints/PROJECT_INSTRUCTIONS.md"
# Local checker resource limits, not protocol-wide limits or model token budgets.
MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 64
FEEDBACK_VALUES = {"concise", "professional", "audit"}

class Invalid(ValueError):
    pass

def need(ok, why):
    if not ok:
        raise Invalid(why)

def unique_pairs(pairs):
    obj = {}
    for k, v in pairs:
        need(k not in obj, "duplicate JSON key: " + k)
        obj[k] = v
    return obj

def strict_json(data):
    need(isinstance(data, bytes) and len(data) <= MAX_BYTES, "JSON byte limit")
    need(not data.startswith(b"\xef\xbb\xbf"), "UTF-8 BOM")
    def reject_constant(value):
        raise Invalid("nonstandard JSON constant: " + value)
    try:
        obj = json.loads(data.decode("utf-8", "strict"),
                         object_pairs_hook=unique_pairs,
                         parse_constant=reject_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise Invalid(str(exc)) from exc
    def walk(v, depth):
        need(depth <= MAX_DEPTH, "JSON depth limit")
        if isinstance(v, str):
            need(not any(0xD800 <= ord(ch) <= 0xDFFF for ch in v), "unpaired surrogate")
        elif isinstance(v, dict):
            for k, x in v.items():
                walk(k, depth + 1)
                walk(x, depth + 1)
        elif isinstance(v, list):
            for x in v:
                walk(x, depth + 1)
        elif isinstance(v, float):
            need(v == v and abs(v) != float("inf"), "nonfinite number")
    walk(obj, 0)
    need(type(obj) is dict, "JSON root must be object")
    return obj

def fields(obj, required, optional=()):
    need(type(obj) is dict and set(required) <= set(obj) <= set(required) | set(optional),
         "unexpected or missing object fields")

def version(obj):
    need(type(obj.get("schema_version")) is int and obj["schema_version"] == 1,
         "unsupported schema_version")

def nonempty(x):
    return isinstance(x, str) and bool(x.strip())

def strings(xs, pattern=None, nonzero=False):
    need(type(xs) is list and (not nonzero or xs) and all(nonempty(x) for x in xs),
         "invalid string array")
    need(len(xs) == len(set(xs)), "duplicate array entry")
    if pattern:
        need(all(pattern.fullmatch(x) for x in xs), "invalid string array value")

def safe_path(p):
    need(isinstance(p, str) and re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", p),
         "unsafe relative path")
    for part in p.split("/"):
        need(part not in {".", ".."} and not part.endswith(".")
             and not re.fullmatch(r"(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part),
             "unsafe path segment")
    return p

def path_set(paths):
    folded = [safe_path(p).lower() for p in paths]
    need(len(folded) == len(set(folded)), "duplicate or case-folded path")
    known = set(folded)
    need(not any("/".join(p.split("/")[:i]) in known
                 for p in folded for i in range(1, len(p.split("/")))),
         "file/directory prefix conflict")

def read_file(root, rel):
    safe_path(rel)
    # A stable trusted local snapshot is required; no claim of race-free filesystem access.
    p = root
    for part in rel.split("/"):
        p = p / part
        info = p.lstat()
        need(not stat.S_ISLNK(info.st_mode), "symlink: " + rel)
    need(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_BYTES, "not bounded regular file")
    with p.open("rb") as fh:
        data = fh.read(MAX_BYTES + 1)
    need(len(data) <= MAX_BYTES, "file byte limit")
    return data

def markdown(data):
    # SRF authored Markdown subset: ATX headings, fenced blocks, blockquotes,
    # indented code and HTML comments. No arbitrary CommonMark parser claim.
    need(not data.startswith(b"\xef\xbb\xbf"), "Markdown BOM")
    text = data.decode("utf-8", "strict")
    fence = None
    comment = False
    lines = []
    for line in text.splitlines():
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*", line):
                fence = None
            continue
        if comment:
            if "-->" in line:
                comment = False
            continue
        if re.match(r" {0,3}>", line) or line.startswith(("    ", "\t")):
            continue
        # Reject unsupported nested list fences instead of interpreting their bodies.
        need(not re.match(r" {0,3}(?:[-+*]|[0-9]+[.)])\s+(?:\x60{3,}|~{3,})", line),
             "unsupported nested list fence")
        f = re.match(r" {0,3}(\x60{3,}|~{3,})", line)
        if f:
            fence = (f[1][0], len(f[1]))
            continue
        if "<!--" in line:
            comment = "-->" not in line.split("<!--", 1)[1]
            continue
        lines.append(line)
    need(not fence and not comment, "unclosed Markdown block")
    return lines

def rule_index(data, module_id):
    lines = markdown(data)
    positions = [i for i, line in enumerate(lines) if line == "## CONTRACT"]
    need(len(positions) == 1, "missing or duplicate CONTRACT")
    i = positions[0]
    need(i + 1 < len(lines) and lines[i + 1] == "Module: " + module_id, "module identity mismatch")
    rules = {}
    for line in lines:
        if re.match(r" {0,3}#{1,6}\s+SRF-R-", line):
            m = re.fullmatch(r"### (SRF-R-[A-Z]+-[0-9]{3}) \| ([A-Z]+)", line)
            need(m and m[2] in TYPES, "invalid rule heading")
            need(m[1] not in rules, "duplicate rule ID")
            rules[m[1]] = m[2]
    need(bool(rules), "no rules")
    return rules, lines

def closure(nodes, key, active=None, done=None):
    active = set() if active is None else active
    done = set() if done is None else done
    need(key in nodes and key not in active, "missing dependency or cycle: " + key)
    if key in done:
        return done
    active.add(key)
    for dep in nodes[key]["requires"]:
        closure(nodes, dep, active, done)
    active.remove(key)
    done.add(key)
    return done

def manifest_check(root, require_core=True):
    m = strict_json(read_file(root, "manifest.json"))
    fields(m, {"schema_version", "entrypoint", "modules", "assets"})
    version(m)
    need(m["entrypoint"] == ENTRY, "invalid entrypoint")
    need(type(m["modules"]) is list and type(m["assets"]) is list, "invalid index arrays")
    nodes, rules, sources = {}, {}, {}
    paths = ["manifest.json", ENTRY]
    for n in m["modules"]:
        fields(n, {"id", "path", "kind", "requires", "triggers"})
        key = n["id"]
        need(isinstance(key, str) and ID.fullmatch(key) and key not in nodes, "invalid/duplicate module ID")
        need(n["kind"] in KINDS and isinstance(n["path"], str) and n["path"].endswith(".md"), "invalid module")
        need(n["path"].split("/")[0] in {"core", "orchestration", "governance", "adapters", "capabilities", "evolution", "extensions"}, "module outside runtime roles")
        strings(n["requires"], ID)
        strings(n["triggers"], re.compile(r"[a-z][a-z0-9-]*"), True)
        nodes[key] = n
        paths.append(n["path"])
    for a in m["assets"]:
        fields(a, {"path", "kind", "owner"})
        prefixes = {"reference": "knowledge/", "template": "templates/", "support": "entrypoints/"}
        need(a["kind"] in prefixes and isinstance(a["path"], str)
             and a["path"].startswith(prefixes[a["kind"]]) and a["owner"] in nodes, "invalid asset")
        need(Path(a["path"]).suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}, "unsupported non-executable asset format")
        paths.append(a["path"])
    path_set(paths)
    for key, n in nodes.items():
        closure(nodes, key)
        need((n["kind"] == "core") == (key in CORE), "unexpected core identity")
        if n["kind"] == "core":
            need(all(d in CORE for d in n["requires"]), "core depends on optional module")
        extracted, lines = rule_index(read_file(root, n["path"]), key)
        need(not (set(rules) & set(extracted)), "duplicate global rule ID")
        rules.update(extracted)
        sources[key] = lines
    if require_core:
        need(CORE <= set(nodes) and closure(nodes, "srf.workflow") == CORE, "incomplete core")
    for a in m["assets"]:
        read_file(root, a["path"])
    for lines in sources.values():
        for line in lines:
            for ref in re.findall(r"\bSRF-R-[A-Z]+-[0-9]{3}\b", line):
                need(ref in rules, "unresolved explicit rule ID: " + ref)
    if "srf.collaboration" in sources:
        declarations = [line for line in sources["srf.collaboration"]
                        if line.startswith("参数 srf.feedback.detail：")]
        need(len(declarations) == 1, "feedback declaration missing or duplicated")
        match = re.search(r"允许值 ([a-z、]+)；", declarations[0])
        need(match and set(match[1].split("、")) == FEEDBACK_VALUES,
             "feedback parameter declaration drift")
    entry = read_file(root, ENTRY).decode("utf-8", "strict")
    if "srf.governance" in sources:
        lines = sources["srf.governance"]
        i = lines.index("### SRF-R-GOV-001 | MUST")
        excerpt = []
        for line in lines[i + 1:]:
            if line.startswith("### "):
                break
            excerpt.append(line)
        need("\n".join(excerpt).strip() in entry, "bootstrap excerpt drift")
    return {"modules": len(nodes), "edges": sum(len(n["requires"]) for n in nodes.values()),
            "rules": len(rules), "core_complete": CORE <= set(nodes)}

def config_check(c, manifest, allow_prerelease=False):
    fields(c, {"schema_version", "framework", "state"}, {"parameters", "extensions"})
    version(c)
    f = c["framework"]
    fields(f, {"version", "artifact_ref"})
    # Exact SemVer grammar, including numeric pre-release leading-zero rule.
    v = f["version"]
    need(isinstance(v, str) and re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?", v, re.ASCII), "invalid SemVer")
    pre = v.split("+", 1)[0].partition("-")[2]
    need(not pre or allow_prerelease and all(not (x.isdigit() and len(x) > 1 and x[0] == "0") for x in pre.split(".")), "unapproved/invalid pre-release")
    need(isinstance(f["artifact_ref"], str) and re.fullmatch(r"sha256:[0-9a-f]{64}", f["artifact_ref"]), "invalid artifact reference")
    s = c["state"]
    need(type(s) is dict, "invalid state locator")
    if s.get("kind") == "file":
        fields(s, {"kind", "path"})
        p = safe_path(s["path"]).lower()
        need(p.split("/")[0] not in {".srf", ".git"}, "protected state path")
    else:
        fields(s, {"kind", "ref"})
        need(s["kind"] == "external" and nonempty(s["ref"]), "invalid external locator")
    # Only currently implemented parameter; extend by deriving actual declarations
    # or reviewing against the authoritative module when new parameters are introduced.
    params = c.get("parameters", {})
    fields(params, set(), {"srf.feedback.detail"})
    if "srf.feedback.detail" in params:
        need(isinstance(params["srf.feedback.detail"], str) and params["srf.feedback.detail"] in FEEDBACK_VALUES, "invalid feedback parameter")
    extensions = c.get("extensions", [])
    strings(extensions, ID)
    known = {n["id"] for n in manifest["modules"] if n["kind"] == "extension"}
    need(set(extensions) <= known, "unknown/non-extension selection")

def ref_check(r):
    fields(r, {"kind", "locator", "revision"})
    need(r["kind"] in {"git", "external", "event"} and nonempty(r["locator"]) and nonempty(r["revision"]), "invalid reference")

def state_check(s):
    fields(s, {"schema_version", "subject", "focus", "tasks"}, {"phase"})
    version(s)
    need(nonempty(s["subject"]) and type(s["tasks"]) is list, "invalid state")
    tasks = {}
    for t in s["tasks"]:
        need(type(t) is dict and nonempty(t.get("id")) and t["id"] not in tasks, "invalid/duplicate task")
        tasks[t["id"]] = t
        if t.get("kind") == "reference":
            fields(t, {"kind", "id", "ref"})
            ref_check(t["ref"])
            continue
        fields(t, {"id","goal","scope","baseline","status","acceptance","approvals","links","pending_operations","next"}, {"blockers","depends_on"})
        need(nonempty(t["goal"]) and nonempty(t["scope"]) and nonempty(t["next"]), "empty task semantics")
        need(t["status"] in {"not_started","in_progress","paused","blocked","completed","cancelled"}, "invalid task status")
        unknown = type(t["baseline"]) is dict and t["baseline"].get("status") == "unknown"
        if unknown:
            fields(t["baseline"], {"status","reason","resolve"})
            need(nonempty(t["baseline"]["reason"]) and nonempty(t["baseline"]["resolve"]), "invalid unknown baseline")
        else:
            ref_check(t["baseline"])
        for k in ("acceptance","approvals","links","pending_operations"):
            need(type(t[k]) is list, "invalid task array")
        criteria = []
        for a in t["acceptance"]:
            fields(a, {"id","condition"}, {"confirmed"})
            need(nonempty(a["id"]) and nonempty(a["condition"]) and ("confirmed" not in a or a["confirmed"] is False), "invalid criterion")
            criteria.append(a["id"])
        strings(criteria)
        blockers = t.get("blockers", [])
        strings(blockers)
        if unknown or not criteria or any(a.get("confirmed") is False for a in t["acceptance"]) or t["status"] == "blocked":
            need(blockers and t["status"] in {"not_started","paused","blocked","cancelled"}, "incomplete executable task")
        for a in t["approvals"]:
            fields(a, {"purpose","ref"})
            need(a["purpose"] in {"decision","execute"}, "invalid approval purpose")
            ref_check(a["ref"])
        for link in t["links"]:
            fields(link, {"kind","ref"})
            need(link["kind"] in {"requirement","decision","design","implementation","evidence","result","acceptance","knowledge"}, "invalid link kind")
            ref_check(link["ref"])
        op_ids = []
        for op in t["pending_operations"]:
            fields(op, {"id","intent","baseline","expected","reconcile","request_ref"})
            need(all(nonempty(op[k]) for k in ("id","intent","expected","reconcile")), "invalid pending operation")
            ref_check(op["baseline"])
            ref_check(op["request_ref"])
            op_ids.append(op["id"])
        strings(op_ids)
        need(t["status"] != "completed" or not op_ids, "completed with unresolved operation")
        strings(t.get("depends_on", []))
    need(s["focus"] is None or isinstance(s["focus"], str) and s["focus"] in tasks, "invalid focus")
    graph = {k: {"requires": t.get("depends_on", [])} for k, t in tasks.items()}
    for key in graph:
        closure(graph, key)
    # Referenced records must be resolved in the actual authorized environment;
    # a structural pass never says those tasks or their approvals are complete.
    return {"tasks": len(tasks), "unresolved_reference_tasks": sum(t.get("kind") == "reference" for t in tasks.values())}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("framework", type=Path)
    p.add_argument("--partial", action="store_true", help="implementation-stage structure only")
    p.add_argument("--config", type=Path)
    p.add_argument("--state", type=Path)
    p.add_argument("--allow-prerelease", action="store_true", help="structural test only, not authorization")
    a = p.parse_args()
    try:
        root = a.framework.absolute()
        need(root.is_dir() and not root.is_symlink(), "invalid framework root")
        result = manifest_check(root, not a.partial)
        if a.config:
            config_check(strict_json(read_file(a.config.absolute().parent, a.config.name)),
                         strict_json(read_file(root, "manifest.json")), a.allow_prerelease)
            result["config_shape"] = "pass"
        if a.state:
            result["state_shape"] = state_check(strict_json(read_file(a.state.absolute().parent, a.state.name)))
        print(json.dumps({"structure": "pass", **result}, ensure_ascii=False))
    except (Invalid, OSError, UnicodeError, TypeError, KeyError, RecursionError) as exc:
        print(json.dumps({"structure": "fail", "reason": str(exc)}, ensure_ascii=False))
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
