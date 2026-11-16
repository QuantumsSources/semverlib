from semverlib import *


if __name__ == "__main__":
    import sys

    if sys.argv[1:]:
        if sys.argv[1] in ("-h", "--help"):
            print("[INFO] semverlib cli")
            print("[INFO] usage: python [.../]semverlib [...]")
            print("[INFO] ")
            print("[INFO] -h / --help: print this help and exit")
            print("[INFO]   usage: python [.../]semverlib -h|--help")
            print("[INFO] -s / --check: don't print error message")
            print("[INFO]     --json: print result as json instead of <core_version>[-<prerelease>]")
            print("[INFO]   usage: python [.../]semverlib <VERSION> (-s|--check) [--json]")
            print("[INFO] -c / --comp: compare two semantic versions")
            print("[INFO]     --strict=<preferred_build_meta>: settle ties with a preferred build meta")
            print("[INFO]     --json: print result as json instead of an inequality")
            print("[INFO]   usage: python [.../]semverlib (-c|--comp) <VERSION> <VERSION> [--json]")
            print("[INFO] ")
            print("[INFO] <VERSION>: a valid semantic version")
            sys.exit(0)

        check_only = "-s" in sys.argv or "--check" in sys.argv
        if sys.argv[1] in ("-c", "--comp"):
            if len(sys.argv[1:]) < 3:
                print(f"[ERROR] -s expects two valid semantic versions after it, {len(sys.argv[1:])} found")
                sys.exit(1)

            try:
                _a = SemanticVersion(sys.argv[2])
                _b = SemanticVersion(sys.argv[3])

                if len(sys.argv) > 4 and sys.argv[4].startswith("--strict"):
                    if not "=" in sys.argv[4]:
                        print("[WARN] --strict expects a <preferred_build_meta> argument. none found.")
                        sys.exit(1)
                    _, preferred_build_meta = sys.argv[4].split("=", 1)
                else:
                    preferred_build_meta = None

                _m = comp(_a, _b, preferred_build_meta)
                if "--json" in sys.argv:
                    print("{")
                    print('    "candidates": {')
                    print(f'        "a": {repr(_a)}')
                    print(f'        "b": {repr(_b)}')
                    print('    },')
                    print(f'    "result": {repr(_m)}')
                    print("}")
                    sys.exit(0)

                _a_str = _a.fullname if preferred_build_meta is not None else str(_a)
                _b_str = _b.fullname if preferred_build_meta is not None else str(_b)

                if _m is None:
                    print(f"{_a_str} == {_b_str}")
                elif _a == _m:
                    print(f"{_a_str} > {_b_str}")
                else:
                    print(f"{_b_str} > {_a_str}")

                sys.exit(0)
            except InvalidSemVerString as _e:
                if not check_only:
                    print(f"[WARN] \"{_e.source}\" is not compliant with the Semantic Versioning specification:")
                    print(f"[WARN] > {_e.reason}")
                    print(f"[WARN] ")
                    print(f"[WARN] See {_e.header} for more info.")
                sys.exit(1)
        try:
            if sys.argv[1] in ("-s", "--check"):
                print("[ERROR] -s must follow version, not precede it")
                sys.exit(1)

            _a = SemanticVersion(sys.argv[1])
            if "--json" in sys.argv:
                print("{")
                print(f'  "full_version": "{_a.fullname}",')
                print(f'  "core_version": "{_a.core_version}",')
                print("  ")
                print(f'  "major": {_a.major},')
                print(f'  "minor": {_a.minor},')
                print(f'  "patch": {_a.patch},')
                print("  ")
                print(f'  "prerelease": {f"\"{_a.prerelease}\"" if _a.is_prerelease else "null"},')
                print(f'  "build_metadata": {f"\"{_a.build_metadata}\"" if _a.has_build_metadata else "null"}')
                print("}")
                sys.exit(0)

            print(_a)
            sys.exit(0)
        except InvalidSemVerString as _e:
            if not check_only:
                print(f"[WARN] \"{_e.source}\" is not compliant with the Semantic Versioning specification:")
                print(f"[WARN] > {_e.reason}")
                print(f"[WARN] ")
                print(f"[WARN] See {_e.header} for more info.")
            sys.exit(1)

    print(f"semverlib, version {version}, loaded.")
    print("made with ♥︎ by quantum!")
    print()
    print("semverlib is freely available on github, under the MIT license")
    print("for issues: https://github.com/QuantumsSources/semverlib")
    sys.exit(0)