"""
lightweight module for working with Semantic Versioning (ver. 2.0.0)\n
See the SemanticVersion class for more information.
"""

import re
from typing import overload, TypeAlias

__version__ = "2.1.0"
__all__ = ["SemanticVersion", "InvalidSemVerString", "comp", "latest", "version"]


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
        super().__init__(src, reason, spec_header)

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
    def __init__(self, other: "SemanticVersion"): ...

    @overload
    def __init__(self, major: int = 0, minor: int = 0, patch: int = 0,
                 *, prerelease: str | None = None, build_metadata: str | None = None): ...

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            src = args[0]
        elif args and isinstance(args[0], SemanticVersion):
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

        is_valid_semver_re = re.compile(r"^(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)")
        is_valid_semver = is_valid_semver_re.match(src)

        if not is_valid_semver:
            raise InvalidSemVerString(src,
                "Core version must be MAJOR.MINOR.PATCH, using non-negative integers without leading zeros.",
                "https://semver.org/#spec-item-2"
            )
        self._major, self._minor, self._patch = map(int, is_valid_semver.groups())

        if (self._major, self._minor, self._patch) == (0, 0, 0):
            self._minor = 1

        is_prerelease_re = re.compile(r"-[a-zA-Z0-9._-]*")
        has_metadata_re = re.compile(r"\+[a-zA-Z0-9._-]*")

        is_prerelease = is_prerelease_re.match(src, is_valid_semver.end())
        if is_prerelease and match_len(is_prerelease) <= 1:
            raise InvalidSemVerString(src,
                "Prerelease data must not be empty.",
                "https://semver.org/#spec-item-9"
            )
        self._prerelease = is_prerelease.group()[1:] if is_prerelease else None

        if self._prerelease is not None:
            for id in self._prerelease.split("."):
                if id == "":
                    raise InvalidSemVerString(src,
                        "Prerelease identifiers must not be empty.",
                        "https://semver.org/#spec-item-9"
                    )
                if id.isdigit() and len(id) > 1 and id[0] == "0":
                    raise InvalidSemVerString(src,
                        "Numeric prerelease identifiers must not include leading zeroes.",
                        "https://semver.org/#spec-item-9"
                    )

        meta_start = max(is_valid_semver.end(), is_prerelease.end() if is_prerelease else 0)
        has_metadata = has_metadata_re.match(src, meta_start)
        if has_metadata and match_len(has_metadata) <= 1:
            raise InvalidSemVerString(
                src,
                "Build Metadata must not be empty.",
                "https://semver.org/#spec-item-10"
            )
        self._build_metadata = has_metadata.group()[1:] if has_metadata else None

        if self._build_metadata is not None and "" in self._build_metadata.split("."):
            raise InvalidSemVerString(
                src,
                "Build Metadata identifiers must not be empty.",
                "https://semver.org/#spec-item-10"
            )

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

    def GetNextMajor(self, keep_metadata: bool = False) -> "SemanticVersion":
        meta = self.build_metadata if keep_metadata else None
        return SemanticVersion(self.major + 1, 0, 0, build_metadata=meta)

    def GetNextMinor(self, keep_metadata: bool = False) -> "SemanticVersion":
        meta = self.build_metadata if keep_metadata else None
        return SemanticVersion(self.major, self.minor + 1, 0, build_metadata=meta)

    def GetNextPatch(self, keep_metadata: bool = False) -> "SemanticVersion":
        meta = self.build_metadata if keep_metadata else None
        return SemanticVersion(self.major, self.minor, self.patch + 1, build_metadata=meta)

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, SemanticVersion): return NotImplemented
        return comp(self, value) == None

    def __hash__(self) -> int:
        return hash((self._major, self._minor, self._patch, self._prerelease))

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


def comp(a: AcceptableSemVer, b: AcceptableSemVer,
         preferred_build_metadata: str | None = None) -> SemanticVersion | None:

    if isinstance(a, str): a = SemanticVersion(a)
    if isinstance(b, str): b = SemanticVersion(b)

    if a.major != b.major: return a if a.major > b.major else b
    if a.minor != b.minor: return a if a.minor > b.minor else b
    if a.patch != b.patch: return a if a.patch > b.patch else b

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

        if a.has_build_metadata and b.has_build_metadata:
            if a.build_metadata == b.build_metadata:
                return None
            elif preferred_build_metadata is not None:
                if a.build_metadata == preferred_build_metadata: return a
                if b.build_metadata == preferred_build_metadata: return b
        return None

    if a.is_prerelease:
        return b
    if b.is_prerelease:
        return a

    if a.has_build_metadata and b.has_build_metadata:
        if a.build_metadata == b.build_metadata:
            return None
        elif preferred_build_metadata is not None:
            if a.build_metadata == preferred_build_metadata: return a
            if b.build_metadata == preferred_build_metadata: return b
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