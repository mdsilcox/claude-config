"""PreToolUse hook (Bash|PowerShell): a tripwire for the catastrophic deletes seen in 2026 Claude
Code incidents on Windows and Linux: recursive deletes of a root, a drive, a home or profile folder
(including 8.3 aliases such as MIKHA~1), targets built from a variable that may be empty, and Docker
runs that mount a drive root or home folder into a container.

It denies the clearly catastrophic cases and asks about the risky ones. It is not a security
boundary: a delete hidden inside a script, or built at run time, passes straight through. The
sandbox (dev VM), containers and backups are the real protection.
"""

import json
import re
import shlex
import sys

SEPARATORS = re.compile(r"&&|\|\||[;|\n]")
PS_DELETE = {"remove-item", "ri", "del", "erase", "rd", "rmdir", "rm"}
WRAPPERS = {"sudo", "command", "builtin", "exec", "nohup", "time", "wsl", "xargs"}
FIND_FILTERS = {"-name", "-iname", "-path", "-ipath", "-regex", "-type", "-mtime", "-mmin", "-newer", "-empty"}
# A variable that is always set is fine when a real subpath follows it, as in $HOME/.cache/pip.
SAFE_VARS = {"home", "pwd", "userprofile", "temp", "tmp", "localappdata", "appdata",
             "claude_project_dir", "env:userprofile", "env:temp", "env:tmp",
             "env:localappdata", "env:appdata"}
SYSTEM_DIRS = re.compile(r"/(home|root|etc|usr|var|boot|bin|sbin|lib|lib64|opt|srv)(/[^/]+)?")
PROFILE = re.compile(r"((/mnt|/cygdrive)?/[a-z]|[a-z]:)?/users(/[^/]+)?")


def tokens(segment, posix):
    try:
        return shlex.split(segment, posix=posix)
    except ValueError:
        return segment.split()


def unquote(t):
    return t[1:-1] if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'" else t


def classify(target):
    """Return 'deny', 'ask' or None for one delete target."""
    t = unquote(target.strip())
    if not t:
        return None
    low = t.replace("\\", "/").lower()
    core = low
    while core and re.search(r"(/\*|/\.|/)$", core):
        core = re.sub(r"(/\*|/\.|/)$", "", core)
    if core == "" or core in ("~", "$home", "${home}", "%userprofile%", "$env:userprofile",
                              "%homedrive%%homepath%", "$env:homepath"):
        return "deny"
    if re.fullmatch(r"[a-z]:", core) or re.fullmatch(r"/(mnt/|cygdrive/)?[a-z]", core):
        return "deny"
    if PROFILE.fullmatch(core) or SYSTEM_DIRS.fullmatch(core):
        return "deny"
    if "~1" in core and core.count("/") <= 3:
        return "deny"
    var = re.match(r"^(\$\{?|%|\$env:)([a-z_][a-z0-9_]*)(:\?)?", core)
    if var:
        name = ("env:" if core.startswith("$env:") else "") + var.group(2)
        rest = core[var.end():].lstrip("}%")
        if var.group(3):  # ${VAR:?} fails loudly when VAR is empty
            return None
        if name in SAFE_VARS and re.search(r"/[^/*.][^/]*", rest):
            return None
        return "ask"
    if core in (".", "..", "*", "./.."):
        return "ask"
    if low.startswith("//") and len(low) > 2:
        return "ask"  # UNC or network path
    return None


def delete_targets(toks, powershell):
    """Return the targets of a recursive delete command, or [] if this isn't one."""
    while toks and (toks[0].lower() in WRAPPERS or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=\S*", toks[0])):
        toks = toks[1:]
    if not toks:
        return []
    cmd = toks[0].lower().rsplit("/", 1)[-1]
    args = toks[1:]
    if cmd == "find":
        if "-delete" in args or ("-exec" in args and any(a.endswith("rm") for a in args)):
            path = ([a for a in args if not a.startswith("-")][:1] or ["."])[0]
            filtered = any(a in FIND_FILTERS for a in args)
            return [] if filtered and path in (".", "./") else [path]
        return []
    if cmd == "rm" and not powershell:
        recursive = any(re.fullmatch(r"-[a-zA-Z]*[rR][a-zA-Z]*", a) or a == "--recursive" for a in args)
        return [a for a in args if not a.startswith("-")] if recursive else []
    if cmd in PS_DELETE:
        lowered = [a.lower() for a in args]
        recursive = any(a.startswith("-rec") or a in ("-r", "/s") for a in lowered)
        if not recursive:
            return []
        out, skip = [], False
        for a in args:
            if skip:
                out.append(a)
                skip = False
            elif a.lower() in ("-path", "-literalpath"):
                skip = True
            elif not a.startswith("-") and not re.fullmatch(r"/[a-zA-Z]", a):
                out.append(a)
        return out
    return []


def docker_mount_sources(toks):
    """Host paths mounted by a docker run/create command."""
    if not toks or toks[0].lower().rsplit("/", 1)[-1] not in ("docker", "docker.exe", "podman"):
        return []
    if not any(t in ("run", "create") for t in toks[1:3]):
        return []
    sources = []
    for i, t in enumerate(toks):
        value = None
        if t in ("-v", "--volume") and i + 1 < len(toks):
            value = toks[i + 1]
        elif t.startswith("--volume="):
            value = t.split("=", 1)[1]
        if value:
            drive = re.match(r"^[A-Za-z]:[\\/]", value)
            cut = value.find(":", 2 if drive else 0)
            sources.append(value if cut < 0 else value[:cut])
        if t == "--mount" and i + 1 < len(toks):
            m = re.search(r"(?:source|src)=([^,]+)", toks[i + 1])
            if m:
                sources.append(m.group(1))
    return sources


def check(command, tool):
    powershell = tool == "PowerShell"
    worst, why = None, ""
    for segment in SEPARATORS.split(command):
        toks = tokens(segment.strip(), posix=not powershell)
        found = [(classify(t), t, "delete") for t in delete_targets(list(toks), powershell)]
        found += [(classify(s), s, "mount") for s in docker_mount_sources(list(toks))]
        for verdict, target, kind in found:
            if verdict == "deny" or (verdict == "ask" and worst is None):
                worst, why = verdict, (target, kind)
    return worst, why


def main():
    data = json.load(sys.stdin)
    command = (data.get("tool_input") or {}).get("command", "")
    verdict, why = check(command, data.get("tool_name", "Bash"))
    if not verdict:
        return
    target, kind = why
    if verdict == "deny":
        reason = (f"guard_deletes blocked a {kind} of {target!r}: it resolves to a root, drive, "
                  "system or home folder. Name the specific subfolder instead.")
    else:
        reason = (f"guard_deletes: the {kind} target {target!r} starts with a variable that may be "
                  "empty, or is the whole current folder. Use ${VAR:?} or an absolute path.")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": verdict,
        "permissionDecisionReason": reason,
    }}))


if __name__ == "__main__":
    main()
