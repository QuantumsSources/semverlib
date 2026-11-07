"""
lightweight module for working with Semantic Versioning (ver. 2.0.0)\n
See the SemanticVersion class for more information.
"""

import re
from typing import overload, TypeAlias

__version__ = "1.0.1"
__all__ = ["SemanticVersion", "InvalidSemVerString", "comp", "latest"]


class InvalidSemVerString(Exception):
    """
    InvalidSemVerString is raised when the SemanticVersion constructor finds
    uncompliance between the Semantic Version spec and the given string.

    :param src: The offending string
    :param reason: The reason the source string is not compliant with the targeted Semantic Versioning spec.
    :param spec_header: URL linking the section of the SemVer spec that explains why the version string is not compliant.
    """

    def __init__(self, src: str, reason: str, spec_header: str):
        self.source = src
        self.reason = reason
        self.header = spec_header
        super().__init__(self)

    def __str__(self) -> str:
        return (f"\"{self.source}\" is not compliant with the Semantic Versioning specification: "
                f"{self.reason} (see {self.header})")


class SemanticVersion:
    """
    This class is built to work with in compliance with the Semantic
    Versioning specification published on https://semver.org.

    As of the latest update to this class, the latest version
    of the spec published on the above URL is version "2.0.0".

    ```py
    a = SemanticVersion("1.4.5+x86_64")
    b = SemanticVersion("1.4.5-alpha+x86_64")

    print(a > b) # True
    ```

    Note:
    Regarding the Semantic Versioning definition of prerelease identifiers and
    build metadata, the underscore ("_") has been added to its list of
    allowed characters.

    This is to, for example, allow tags like architecture notation, e.g.,
    "x86_64" or "arm64_v8a", to pass as valid, instead of raising an
    InvalidSemVerString error.
    """

    @overload
    def __init__(self, src: str): ...

    @overload
    def __init__(self, other: SemanticVersion): ...

    @overload
    def __init__(self, major: int, minor: int = 0, patch: int = 0,
                 *, prerelease: str | None = None, build_metadata: str | None = None): ...

    def __init__(self, *args, **kwargs):
        if isinstance(args[0], str):
            src = args[0]
        elif isinstance(args[0], SemanticVersion):
            other: SemanticVersion = args[0]

            major = other.major
            minor = other.minor
            patch = other.patch

            pre = other.prerelease
            meta = other.build_metadata
            pre_str = f"-{pre}" if pre else ""
            meta_str = f"+{meta}" if meta else ""

            src = f"{major}.{minor}.{patch}{pre_str}{meta_str}"
        else:
            major = args[0] if len(args) > 0 else kwargs.get("major", 0)
            minor = args[1] if len(args) > 1 else kwargs.get("minor", 0)
            patch = args[2] if len(args) > 2 else kwargs.get("patch", 0)

            pre = kwargs.get("prerelease")
            meta = kwargs.get("build_metadata")
            pre_str = f"-{pre}" if pre else ""
            meta_str = f"+{meta}" if meta else ""

            src = f"{major}.{minor}.{patch}{pre_str}{meta_str}"

        def match_len(m: re.Match) -> int:
            return m.end() - m.start()

        is_valid_semver_re = re.compile(r"^([0-9]+)[.]([0-9]+)[.]([0-9]+)")
        is_valid_semver = is_valid_semver_re.match(src)

        if not is_valid_semver:
            raise InvalidSemVerString(src,
                f"\"{src}\" does not follow core Semantic Versioning formatting.",
                "https://semver.org/#spec-item-2"
            )
        self._major, self._minor, self._patch = map(int, is_valid_semver.groups())

        is_prerelease_re = re.compile(r"-[a-zA-Z0-9._-]*")
        has_metadata_re = re.compile(r"\+[a-zA-Z0-9._-]*")

        is_prerelease = is_prerelease_re.match(src, is_valid_semver.end())
        if is_prerelease and match_len(is_prerelease) <= 1:
            raise InvalidSemVerString(src,
                "Prerelease data must not be empty.",
                "https://semver.org/#spec-item-9"
            )
        self._prerelease = is_prerelease.group()[1:] if is_prerelease else None

        meta_start = max(is_valid_semver.end(), is_prerelease.end() if is_prerelease else 0)
        has_metadata = has_metadata_re.match(src, meta_start)
        if has_metadata and match_len(has_metadata) <= 1:
            raise InvalidSemVerString(
                src,
                "Build Metadata must not be empty.",
                "https://semver.org/#spec-item-10"
            )
        self._build_metadata = has_metadata.group()[1:] if has_metadata else None

        meta_start = max(is_valid_semver.end(), is_prerelease.end() if is_prerelease else 0)
        has_metadata = has_metadata_re.match(src, meta_start)
        if has_metadata and match_len(has_metadata) <= 1:
            raise InvalidSemVerString(
                src,
                "Build Metadata must not be empty.",
                "https://semver.org/#spec-item-10"
            )
        self._build_metadata = has_metadata.group()[1:] if has_metadata else None

        consumed_end = max(
            is_valid_semver.end(),
            is_prerelease.end() if is_prerelease else 0,
            has_metadata.end() if has_metadata else 0
        )

        if consumed_end < len(src):
            raise InvalidSemVerString(
                src,
                f"Unexpected character(s) \"{src[consumed_end:]}\" found in version string.",
                "https://semver.org/#backusnaur-form-grammar-for-valid-semver-versions"
            )

    @property
    def major(self) -> int:
        return self._major

    @property
    def minor(self) -> int:
        return self._minor

    @property
    def patch(self) -> int:
        return self._patch

    @property
    def core_version(self) -> str:
        return f"{self._major}.{self._minor}.{self._patch}"

    @property
    def prerelease(self) -> str | None:
        return self._prerelease

    @property
    def is_prerelease(self) -> bool:
        return self._prerelease is not None

    @property
    def build_metadata(self) -> str | None:
        return self._build_metadata

    @property
    def has_build_metadata(self) -> bool:
        return self._build_metadata is not None

    @property
    def fullname(self) -> str:
        return (
            f"{self.core_version}"
            f"{f'-{self.prerelease}' if self.is_prerelease else ''}"
            f"{f'+{self.build_metadata}' if self.has_build_metadata else ''}"
        )

    def GetNextMajor(self, keep_metadata: bool = False) -> SemanticVersion:
        meta = self.build_metadata if keep_metadata else None
        return SemanticVersion(self.major + 1, 0, 0, build_metadata=meta)

    def GetNextMinor(self, keep_metadata: bool = False) -> SemanticVersion:
        meta = self.build_metadata if keep_metadata else None
        return SemanticVersion(self.major, self.minor + 1, 0, build_metadata=meta)

    def GetNextPatch(self, keep_metadata: bool = False) -> SemanticVersion:
        meta = self.build_metadata if keep_metadata else None
        return SemanticVersion(self.major, self.minor, self.patch + 1, build_metadata=meta)

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, SemanticVersion): return NotImplemented
        return comp(self, value) == None

    def __gt__(self, other) -> bool:
        if not isinstance(other, SemanticVersion): return NotImplemented
        return comp(self, other) == self

    def __ge__(self, other) -> bool:
        if not isinstance(other, SemanticVersion): return NotImplemented
        return self == other or self > other

    def __lt__(self, other) -> bool:
        if not isinstance(other, SemanticVersion): return NotImplemented
        return comp(self, other) == other

    def __le__(self, other) -> bool:
        if not isinstance(other, SemanticVersion): return NotImplemented
        return self == other or self < other

    def __str__(self) -> str:
        return (
            f"{self.core_version}"
            f"{f'-{self.prerelease}' if self.is_prerelease else ''}"
        )

    def __repr__(self) -> str:
        return f"SemanticVersion(src=\"{self.fullname}\")"


AcceptableSemVer: TypeAlias = SemanticVersion | str


def comp(a: AcceptableSemVer, b: AcceptableSemVer) -> SemanticVersion | None:
    if isinstance(a, str):
        a = SemanticVersion(a)
    if isinstance(b, str):
        b = SemanticVersion(b)

    if a.major < b.major: return b
    if a.major > b.major: return a

    if a.minor < b.minor: return b
    if a.minor > b.minor: return a

    if a.patch < b.patch: return b
    if a.patch > b.patch: return a

    pre_a, pre_b = a.prerelease, b.prerelease
    if pre_a and pre_b:
        parts_a, parts_b = pre_a.split("."), pre_b.split(".")

        for i in range(max(len(parts_a), len(parts_b))):
            if i > len(parts_a) - 1:
                return b
            if i > len(parts_b) - 1:
                return a

            part_a, part_b = parts_a[i], parts_b[i]
            if part_a == part_b:
                continue

            if part_a.isdigit() and not part_b.isdigit():
                return b
            if part_b.isdigit() and not part_a.isdigit():
                return a

            if part_a.isdigit() and part_b.isdigit():
                part_a, part_b = int(part_a), int(part_b)
                if part_a != part_b:
                    return a if part_a > part_b else b
            else:
                parts = [part_a, part_b]
                parts.sort()

                return b if part_a == parts[0] else a
        return None

    if a.is_prerelease:
        return b
    if b.is_prerelease:
        return a

    return None


def latest(*v: AcceptableSemVer) -> list[SemanticVersion]:
    v = sorted(map(SemanticVersion, v), reverse=True)
    r = [ ]

    for ver in v:
        if ver != v[0]:
            return r
        r.append(ver)
    return r


version = SemanticVersion(__version__)

if __name__ == "__main__":
    import sys

    if sys.argv[1:]:
        if sys.argv[1] in ("-h", "--help"):
            print("[INFO] semverlib cli")
            print("[INFO] usage: python .../semverlib.py (-h|--help)|(<VERSION> [-c|--check] [--json])")
            print("[INFO] ")
            print("[INFO] -h / --help: print this help and exit")
            print("[INFO] --check: don't print error message")
            print("[INFO] --json: print result as json instead of core version")
            print("[INFO] ")
            print("[INFO] <VERSION>: the version to check")
            sys.exit(0)

        try:
            if sys.argv[1] == "--check":
                print("[WARN] --check must follow version, not precede it")
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
            if not "--check" in sys.argv:
                print(f"[WARN] \"{_e.source}\" is not compliant with the Semantic Versioning specification:")
                print(f"[WARN] > {_e.reason}")
                print(f"[WARN] ")
                print(f"[WARN] See {_e.header} for more info.")
            sys.exit(1)

    print(f"semverlib, version {__version__}, loaded.")
    print("made with ♥︎ by quantum!")
    print()
    print("semverlib is freely available on github, under the MIT license")
    print("for issues: https://github.com/QuantumsSources/semverlib")
    sys.exit(0)