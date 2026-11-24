import sys
import json

from semverlib import *


def info(*m: object):
    sys.stdout.write(" ".join(str(v) for v in ["[INFO]:", *m]) + "\n")

def warn(*m: object):
    sys.stdout.write(" ".join(str(v) for v in ["[WARN]:", *m]) + "\n")

class ArgumentParserError(Exception):
    pass

def parse_args(args: list[str]) -> tuple[dict[str, bool], dict[str, str|int|float|bool|None], list[str]]:
    mods: dict[str, bool] = {}
    kwargs: dict[str, str|int|float|bool|None] = {}
    versions: list[str] = []

    for arg in args:
        if arg.startswith("--"):
            kwarg = arg.removeprefix("--")
            name = kwarg.split("=", 1)[0]

            if not name:
                raise ArgumentParserError("Found unnamed kwarg.")

            if "=" in kwarg:
                k, raw_v = kwarg.split("=", 1)
                if not raw_v.strip():
                    raise ArgumentParserError(f"Found kwarg '{k}' with no value.")

                v = raw_v.lower()

                if v in ("true", "false"):
                    parsed_val: str|int|float|bool|None = v == "true"
                elif v in ("none", "nil", "null"):
                    parsed_val = None
                else:
                    parsed_val = raw_v

                kwargs[k] = parsed_val
            else:
                if name in kwargs:
                    warn(f"Found duplicate kwarg '{name}'! Overriding previous entry.")
                kwargs[name] = True
        elif arg.startswith("-"):
            if not arg.removeprefix("-"):
                raise ArgumentParserError("Found mod character with no mods.")

            for mod in arg.removeprefix("-"):
                if mod in mods:
                    warn(f"Found duplicate mod '{mod}'! Overriding previous entry.")
                mods[mod] = True
        else:
            versions.append(arg)

    return mods, kwargs, versions


ALIASES = {
    "h": "help",
    "H": "help",
    "help": "help",
    "mode": "mode",
    "flag": "flag",

    "S": "check",
    "check": "check",
    "C": "compare",
    "compare": "compare",
    "prefer": "prefer",
    "D": "decompose",
    "decompose": "decompose",

    "j": "json",
    "json": "json",
    "q": "quiet",
    "quiet": "quiet",
}

HELP = {
    ("mode", "help"): [
        "-H (--help)",
        "print help text",
        "",
        "FLAGS:",
        " --mode=<str> :: print help for a mode, or filter to this mode",
        " --flag=<str> :: print help for a flag",
        " + global flags",
        "",
        "usage: --help [<flags>]"
    ],
    ("mode", "check"): [
        "-S (--check)",
        "check whether every version is valid",
        "",
        "FLAGS:",
        " no specific flags",
        " + global flags",
        "",
        "usage: --check <V1> [<V...>] [<flags>]"
    ],
    ("mode", "compare"): [
        "-C (--compare)",
        "compare two versions, or get the latest",
        "",
        "FLAGS:",
        " --prefer=<str> :: settle ties with a preferred build meta",
        " + global flags",
        "",
        "usage: --compare <V1> <V2> [<V...>] [<flags>]"
    ],
    ("mode", "decompose"): [
        "-D (--decompose)",
        "split version into individual components",
        "",
        "FLAGS:",
        " no specific flags",
        " + global flags",
        "",
        "usage: --decompose <V1> [<flags>]"
    ],

    ("flag", "help", "mode"): [
        "--mode=<str>",
        "print help for a mode, or filter to flags to this mode",
        "",
        "example: -H --mode=D"
    ],
    ("flag", "help", "flag"): [
        "--flag=<str>",
        "print help for a flag, optionally filtered by mode",
        "",
        "example: --help --mode=help --flag=mode"
    ],
    ("flag", "compare", "prefer"): [
        "--prefer=<str>",
        "settle ties with a preferred build meta",
        "",
        "example: -C 3.1.4+x86_64 3.1.4+arm64_v8a --prefer=x86_64"
    ],

    ("flag", "global", "json"): [
        "-j (--json) [GLOBAL]",
        "print output as json",
        "",
        "example: -S 1.0.0 --json"
    ],
    ("flag", "global", "quiet"): [
        "-q (--quiet) [GLOBAL]",
        "don't print errors, and reduce to crucial information, relies on return codes",
        "",
        "example: -S 2.9.b --quiet"
    ]
}

def is_valid_kw(kw: str) -> bool:
    for v in ALIASES.values():
        if kw == v: return True
    return False

if __name__ == "__main__":
    mods, kwargs, versions = parse_args(sys.argv[1:])
    for mod in mods:
        if ALIASES.get(mod, None) is not None:
            kwargs[ALIASES.get(mod, "")] = True
        else:
            warn(f"Unknown mod '-{mod}'")
            sys.exit(1)
    for kw in kwargs:
        if not is_valid_kw(kw):
            warn(f"Unknown kwarg '--{kw}'")
            sys.exit(1)

    json_mode = kwargs.get("json", None)
    quiet_mode = kwargs.get("quiet", None)

    if kwargs.get("help", None):
        if kwargs.get("flag", None) is not None:
            if not isinstance(kwargs.get("mode", None), (type(None), str)):
                if not quiet_mode:
                    t = kwargs.get("mode", None).__class__.__name__
                    warn(f"--help expects flag 'mode' of type 'str', not '{t}'")
                sys.exit(1)

            t_mode = str(kwargs.get("mode")) if kwargs.get("mode", None) is not None else "global"
            if ALIASES.get(t_mode, None): t_mode = ALIASES[t_mode]

            if not isinstance(kwargs.get("flag", None), (type(None), str)):
                if not quiet_mode:
                    t = kwargs.get("flag", None).__class__.__name__
                    warn(f"--help expects flag 'flag' of type 'str', not '{t}'")
                sys.exit(1)

            t_flag = str(kwargs.get("flag"))
            if ALIASES.get(t_flag, None): t_flag = ALIASES[t_flag]

            if HELP.get(("flag", t_mode, t_flag), None) is None:
                if not quiet_mode:
                    warn(f"flag '--{t_flag}' not found in context '{t_mode}'!")
                sys.exit(1)

            if json_mode:
                print(json.dumps({ "content": HELP[("flag", t_mode, t_flag)] }, indent=2))
                sys.exit(0)

            for line in HELP[("flag", t_mode, t_flag)]:
                if not line.strip():
                    print()
                    continue
                info(line)
            sys.exit(0)
        elif kwargs.get("mode", None) is not None:
            if not isinstance(kwargs.get("mode", None), (type(None), str)):
                if not quiet_mode:
                    t = kwargs.get("mode", None).__class__.__name__
                    warn(f"--help expects flag 'mode' of type 'str', not '{t}'")
                sys.exit(1)

            t_mode = str(kwargs.get("mode"))
            if ALIASES.get(t_mode, None): t_mode = ALIASES[t_mode]

            if HELP.get(("mode", t_mode), None) is None:
                if not quiet_mode:
                    warn(f"mode '--{t_mode}' not found!")
                sys.exit(1)

            if json_mode:
                print(json.dumps({ "content": HELP[("mode", t_mode)] }, indent=2))
                sys.exit(0)

            for line in HELP[("mode", t_mode)]:
                if not line.strip():
                    print()
                    continue
                info(line)
            sys.exit(0)

        if json_mode:

            sys.exit(0)

        info("semverlib cli, made with ♥︎ by quantum")
        info("usage: python semverlib [[(-Sjq...)|(--MODE)] <V...> [<--flags>]]")
        print()
        info("MODES:")
        info(" -H (--help) [default] :: print help text")
        info(" -S (--check)          :: check whether every version is valid")
        info(" -C (--compare)        :: compare two versions, or get the latest")
        info(" -D (--decompose)      :: split version into individual components")
        print()
        info("FLAGS (global, use -H --mode=... and/or --flag=... for specifics):")
        info(" -j (--json)  :: print output as json")
        info(" -q (--quiet) :: don't print errors, relies on return codes")
        print()
        info("semverlib is freely available on github, under the MIT license")
        info("for issues: https://github.com/QuantumsSources/semverlib")
        sys.exit(0)
    elif kwargs.get("check", None):
        if not versions:
            if not quiet_mode:
                warn("--check requires at least one (1) version input")
            sys.exit(1)

        valid: list[SemanticVersion] = []
        invalid: list[InvalidSemVerString] = []

        for ver in versions:
            try:
                valid.append(SemanticVersion(ver))
            except InvalidSemVerString as err:
                invalid.append(err)

        if json_mode:
            result = []
            for ver in valid:
                result.append({
                    "valid": True,
                    "source": ver.fullname,
                })
            for ver in invalid:
                result.append({
                    "valid": False,
                    "source": ver.source,
                    "reason": ver.reason,
                })

            print(json.dumps(result, indent=2))
            sys.exit(0 if not invalid else 1)

        if not quiet_mode:
            info(f"{len(valid)}/{len(versions)} versions are valid:")
            for semver in valid:
                info(f"> {semver.fullname}")

        if len(invalid) > 0:
            if not quiet_mode:
                print()
                for err in invalid:
                    warn(f"{err.source} is invalid because: {err.reason}")
            sys.exit(1)
        sys.exit(0)
    elif kwargs.get("compare", None):
        if len(versions) < 2:
            if not quiet_mode:
                warn("--compare requires at least two (2) version inputs")
            sys.exit(1)

        candidates: list[SemanticVersion] = []
        try:
            for ver in versions:
                candidates.append(SemanticVersion(ver))
        except InvalidSemVerString as err:
            if not quiet_mode:
                warn(err)
            sys.exit(1)

        if len(candidates) == 2:
            a, b = candidates
            m = comp(a, b, str(kwargs.get("prefer")) if kwargs.get("prefer", None) else None)

            if json_mode:
                print(json.dumps({
                    "candidates": [v.fullname for v in candidates],
                    "prefer": kwargs.get("prefer", None),

                    "latest": m.fullname if m else None
                }, indent=2))
                sys.exit(0)

            if m is None:
                info(f"{a.fullname} == {b.fullname}")
            elif m is a:
                info(f"{a.fullname} > {b.fullname}")
            elif m is b:
                info(f"{b.fullname} > {a.fullname}")
            sys.exit(0)
        else:
            if kwargs.get("prefer", None) and not quiet_mode:
                warn("--prefer is not supported with 3+ versions!")
                sys.exit(1)
            candidates.sort(reverse=True)

            if json_mode:
                print(json.dumps({
                    "candidates": [v.fullname for v in candidates],
                    "latest": str(candidates[0])
                }, indent=2))
                sys.exit(0)

            for i, ver in enumerate(candidates):
                if i == 0: info(f"latest: {ver.fullname}")
                elif not quiet_mode: info(f"no. {i+1}: {ver.fullname}")
            sys.exit(0)
    elif kwargs.get("decompose", None):
        if not versions:
            if not quiet_mode:
                warn("--decompose requires at least one (1) version input")
            sys.exit(1)

        try:
            versions = [SemanticVersion(v) for v in versions]
        except InvalidSemVerString as err:
            if not quiet_mode:
                warn(err.reason)
            sys.exit(1)

        if len(versions) == 1:
            v = versions[0]

            if json_mode:
                print(json.dumps({
                    "source": v.fullname,
                    "core": v.core_version,

                    "major": v.major,
                    "minor": v.minor,
                    "patch": v.patch,

                    "prerelease": v.prerelease,
                    "build_meta": v.build_metadata
                }, indent=2))
                sys.exit(0)

            info(f"{v.fullname}:")
            info(f"- major: {v.major}")
            info(f"- minor: {v.minor}")
            info(f"- patch: {v.patch}")
            if v.is_prerelease:
                info(f"- prerelease tag: {v.prerelease}")
            if v.has_build_metadata:
                info(f"- build metadata: {v.build_metadata}")
            sys.exit(0)
        else:
            result = []

            for i, v in enumerate(versions):
                result.append({
                    "source": v.fullname,
                    "core": v.core_version,

                    "major": v.major,
                    "minor": v.minor,
                    "patch": v.patch,

                    "prerelease": v.prerelease,
                    "build_meta": v.build_metadata
                })

                if not json_mode:
                    info(f"{v.fullname}:")
                    info(f"- major: {v.major}")
                    info(f"- minor: {v.minor}")
                    info(f"- patch: {v.patch}")
                    if v.is_prerelease:
                        info(f"- prerelease tag: {v.prerelease}")
                    if v.has_build_metadata:
                        info(f"- build metadata: {v.build_metadata}")

            if json_mode:
                print(json.dumps(result, indent=2))
            sys.exit(0)
    elif versions:
        failed = False
        for v in versions:
            try:
                v = SemanticVersion(v)
            except InvalidSemVerString as err:
                if not quiet_mode:
                    warn(err.reason)
                failed = True
                continue

            if json_mode:
                print(json.dumps({
                    "source": v.fullname,
                    "core": v.core_version,

                    "major": v.major,
                    "minor": v.minor,
                    "patch": v.patch,

                    "prerelease": v.prerelease,
                    "build_meta": v.build_metadata
                }, indent=2))
            else:
                print(v)
        sys.exit(0 if not failed else 1)

    info(f"semverlib, ver. {version}, loaded!")
    info("made with ︎︎︎︎♥ by quantum!")
    print()
    info("semverlib is freely available on github, under the MIT license")
    info("for issues: https://github.com/QuantumsSources/semverlib")
    sys.exit(0)