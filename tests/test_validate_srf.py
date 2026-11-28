"""Synthetic negative fixtures generated in a disposable local directory.
Run: python -m unittest discover -s tests -p 'test_validate_srf.py'
No network or Git writes.
"""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("validate_srf", Path(__file__).resolve().parents[1] / "scripts" / "validate_srf.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

def raw(obj):
    return json.dumps(obj).encode()

class Validation(unittest.TestCase):
    def test_json(self):
        self.assertEqual(v.strict_json(b'{"x":1}'), {"x":1})
        for data in [b'{"x":1,"x":2}', b'{"x":1,"\\u0078":2}', b'\xef\xbb\xbf{}',
                     b'{"x":"\xff"}', b'{"x":NaN}', b'{"x":1e999}', b'{"x":"\\ud800"}',
                     b'{"x":1,}', b'{"x":', b'[]', b'{"x":/*x*/1}']:
            with self.subTest(data=data), self.assertRaises(v.Invalid):
                v.strict_json(data)

    def test_paths(self):
        v.path_set(["core/a.md","core/b.md"])
        for paths in [["../x"],["/x"],["C:/x"],["a\\x"],["a//b"],["a/CON.txt"],
                      ["a/x."],["a","A"],["a","a/b"]]:
            with self.subTest(paths=paths), self.assertRaises(v.Invalid):
                v.path_set(paths)

    def test_nonadjacent_prefix(self):
        with self.assertRaises(v.Invalid):
            v.path_set(["a", "a-b", "a/b"])
        v.path_set(["a-b", "a/b"])

    def test_markdown(self):
        h = b"## CONTRACT\nModule: srf.governance\n### SRF-R-GOV-001 | MUST\nbody\n"
        fake = b"~~~md\n### SRF-R-GOV-999 | MUST\n~~~\n> ### SRF-R-GOV-998 | MUST\n    ### SRF-R-GOV-997 | MUST\n<!--\n### SRF-R-GOV-996 | MUST\n-->\n"
        rules, _ = v.rule_index(h+fake,"srf.governance")
        self.assertEqual(set(rules),{"SRF-R-GOV-001"})
        for data in [h+h, h+b"### SRF-R-GOV-001 | MUST\n", h+b"### SRF-R-GOV-002 | BAD\n", h+b"~~~\n"]:
            with self.subTest(data=data), self.assertRaises(v.Invalid):
                v.rule_index(data,"srf.governance")

    def test_markdown_boundary(self):
        h = b"## CONTRACT\nModule: srf.governance\n### SRF-R-GOV-001 | MUST\nbody\n"
        fake = b"~~~<!--\n### SRF-R-GOV-999 | MUST\n~~~\n"
        self.assertEqual(set(v.rule_index(h+fake, "srf.governance")[0]), {"SRF-R-GOV-001"})
        with self.assertRaises(v.Invalid):
            v.rule_index(h+b"- ~~~\n### SRF-R-GOV-999 | MUST\n  ~~~\n", "srf.governance")

    def test_parameter_drift(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/"core").mkdir()
            (root/"entrypoints").mkdir()
            (root/v.ENTRY).write_text("trial", encoding="utf-8")
            p = root/"core/collaboration.md"
            prefix = "## CONTRACT\nModule: srf.collaboration\n### SRF-R-COL-008 | MAY\n参数 srf.feedback.detail：类型字符串，允许值 "
            m = {"schema_version":1,"entrypoint":v.ENTRY,"modules":[{"id":"srf.collaboration","path":"core/collaboration.md","kind":"core","requires":[],"triggers":["trial"]}],"assets":[]}
            (root/"manifest.json").write_bytes(raw(m))
            p.write_text(prefix+"concise、professional、audit；\n", encoding="utf-8")
            v.manifest_check(root, False)
            p.write_text(prefix+"concise、audit；\n", encoding="utf-8")
            with self.assertRaises(v.Invalid):
                v.manifest_check(root, False)

    def test_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"core").mkdir()
            (root/"entrypoints").mkdir()
            (root/"core/governance.md").write_bytes(b"## CONTRACT\nModule: srf.governance\n### SRF-R-GOV-001 | MUST\nbootstrap\n")
            (root/v.ENTRY).write_text("bootstrap",encoding="utf-8")
            m={"schema_version":1,"entrypoint":v.ENTRY,"modules":[{"id":"srf.governance","path":"core/governance.md","kind":"core","requires":[],"triggers":["startup"]}],"assets":[]}
            def check(obj, full=False):
                (root/"manifest.json").write_bytes(raw(obj))
                return v.manifest_check(root,full)
            self.assertEqual(check(m)["modules"],1)
            with self.assertRaises(v.Invalid): check(m,True)
            for mode in ["schema","unknown","dup","cycle","missing","path","identity","asset"]:
                bad=copy.deepcopy(m)
                if mode=="schema": bad["schema_version"]=True
                if mode=="unknown": bad["extra"]=1
                if mode=="dup": bad["modules"].append(copy.deepcopy(bad["modules"][0]))
                if mode=="cycle": bad["modules"][0]["requires"]=["srf.governance"]
                if mode=="missing": bad["modules"][0]["requires"]=["srf.missing"]
                if mode=="path": bad["modules"][0]["path"]="../x.md"
                if mode=="identity": bad["modules"][0]["id"]="srf.fake"
                if mode=="asset": bad["assets"]=[{"kind":"reference","path":"docs/x.md","owner":"srf.governance"}]
                with self.subTest(mode=mode), self.assertRaises(v.Invalid): check(bad)
            (root/"core/governance.md").write_text("## CONTRACT\nModule: srf.governance\n### SRF-R-GOV-001 | MUST\nSRF-R-GOV-999\n",encoding="utf-8")
            with self.assertRaises(v.Invalid): check(m)

    def test_config(self):
        c={"schema_version":1,"framework":{"version":"1.0.0","artifact_ref":"sha256:"+"a"*64},"state":{"kind":"file","path":".srf-project/state.json"}}
        v.config_check(c,{"modules":[]})
        for mode in ["root","version","digest","state","parameter","extension","prerelease","leadingzero"]:
            bad=copy.deepcopy(c)
            if mode=="root": bad["repo"]="fixture"
            if mode=="version": bad["framework"]["version"]="latest"
            if mode=="digest": bad["framework"]["artifact_ref"]="fixture"
            if mode=="state": bad["state"]["path"]=".srf/state.json"
            if mode=="parameter": bad["parameters"]={"srf.feedback.detail":"invalid"}
            if mode=="extension": bad["extensions"]=["srf.unknown"]
            if mode=="prerelease": bad["framework"]["version"]="1.0.0-rc.1"
            if mode=="leadingzero": bad["framework"]["version"]="01.0.0"
            with self.subTest(mode=mode),self.assertRaises(v.Invalid): v.config_check(bad,{"modules":[]})

    def test_state(self):
        r={"kind":"git","locator":"synthetic","revision":"synthetic"}
        t={"id":"T","goal":"goal","scope":"scope","baseline":r,"status":"in_progress","acceptance":[{"id":"A","condition":"check"}],"approvals":[],"links":[],"pending_operations":[],"next":"next"}
        s={"schema_version":1,"subject":"synthetic","focus":"T","tasks":[t]}
        self.assertEqual(v.state_check(s)["tasks"],1)
        for mode in ["focus","dup","unknown","acceptance","confirmed","cycle","mixed","ref","complete_pending"]:
            bad=copy.deepcopy(s); a=bad["tasks"][0]
            if mode=="focus": bad["focus"]="missing"
            if mode=="dup": bad["tasks"].append(copy.deepcopy(a))
            if mode=="unknown": a["baseline"]={"status":"unknown","reason":"missing","resolve":"read"}
            if mode=="acceptance": a["acceptance"]=[]
            if mode=="confirmed": a["acceptance"][0]["confirmed"]=False
            if mode=="cycle": a["depends_on"]=["T"]
            if mode=="mixed": a["kind"]="reference"; a["ref"]=r
            if mode=="ref": a["baseline"]={"kind":"fixture","locator":"x","revision":"x"}
            if mode=="complete_pending":
                a["status"]="completed"
                a["pending_operations"]=[{"id":"O","intent":"x","baseline":r,"expected":"x","reconcile":"x","request_ref":r}]
            with self.subTest(mode=mode),self.assertRaises(v.Invalid): v.state_check(bad)
        a=copy.deepcopy(s); a["tasks"][0].update(status="blocked",baseline={"status":"unknown","reason":"missing","resolve":"read"},acceptance=[],blockers=["read"])
        v.state_check(a)

if __name__ == "__main__":
    unittest.main()
