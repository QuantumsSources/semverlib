<div align="center">

# semverlib
lightweight module for working with Semantic Versioning.\
Made with ♥ by quantum.
</div>

> [!important]
> `semverlib` implements its `SemanticVersion` class in compliance with the
> latest available **Semantic Versioning** specification.
> 
> Currently, as of the last update, it is version **"2.0.0"**.\
> For more info, visit the [Semantic Versioning specification](https://semver.org).

## Features
`semverlib` comes with the essentials to get you up and running with Semantic Versioning.\
This includes:
- A flexible initialization system (other `SemanticVersion`, `str`, etc...).
- Easy-to-read errors and links to the relevant part of the spec.
- Specification-compliant comparison between `SemanticVersion` objects.
- Helper functions, like `GetNext[Major|Minor|Patch]`, to easily fetch newer versions.

> [!note]
> Regarding the **Semantic Versioning** definition of prerelease identifiers
> and build metadata, the underscore (`_`) has been added to the list of 
> allowed characters.
> 
> This is to, for example, allow tags like architecture, e.g., `x86_64` or
> `arm64_v8a`, to pass as valid, instead of raising an `InvalidSemVerString` error.

## Examples
### 1. Simple initialization
```python
from semverlib import SemanticVersion

# From string:
a = SemanticVersion("1.0.0-alpha")
print(a.major)      # 1
print(a.prerelease) # "alpha"

# From separate parameters:
b = SemanticVersion(1, 1, 5, build_metadata="x86_64")
print(b.patch)          # 5
print(b.prerelease)     # None
print(b.build_metadata) # "x86_64"

# From another SemanticVersion object:
c = SemanticVersion(b.GetNextMinor(keep_metadata=True))
print(c.major)          # 1
print(c.minor)          # 2
print(c.patch)          # 0, resets on minor change
print(c.build_metadata) # "x86_64", kept by keep_metadata.
```

### 2. Simple comparison
```python
from semverlib import SemanticVersion

a = SemanticVersion("1.1.0+x86_64") # 1.1.0
b = SemanticVersion("1.0.0+x86_64") # 1.0.0

print(a > b) # True, 1.1.0 > 1.0.0
```

### 3. Prerelease comparison
```python
from semverlib import SemanticVersion

a = SemanticVersion("1.0.0-alpha.2+x86_64") # 1.0.0 alpha 2
b = SemanticVersion("1.0.0-alpha+x86_64")   # 1.0.0 alpha 1

print(a > b) # True, alpha 2 > alpha 1
```

### 4. Build metadata equality
```python
from semverlib import SemanticVersion

# Same version, 1.0.0-beta, different targets:
a = SemanticVersion("1.0.0-beta+arm64_v8a")   # Android 64-bit
b = SemanticVersion("1.0.0-beta+armeabi_v7a") # Android 32-bit

print(a == b) # True, build metadata doesn't factor into precedence
```

### 5. Build metadata preference
> [!note]
> Exceptionally, `semverlib` allows you to "prefer" build metadata when comparing
> `SemanticVersion` objects with the built-in (to `semverlib`) `comp` function.
```python
from semverlib import SemanticVersion, comp

# Same version, 3.1.4-rc.2, different targets:
v1 = SemanticVersion("3.1.4-rc.2+arm64_v8a")   # Android 64-bit
v2 = SemanticVersion("3.1.4-rc.2+armeabi_v7a") # Android 32-bit

print(v1 == v2)     # True, as specified.
print(comp(v1, v2)) # None (returned on equal), as specified.

print(comp(v1, v2, "arm64_v8a")) # You can "prefer" build metadata. Returns v1 in this case.
```

> [!important]
> In the case of the two versions being equal, and neither having the preferred
> build metadata, `None` is still returned.
> 
> Older versions with the preferred build metadata are still overshadowed by later versions.

## Installation
In general, you can just use `pip`, pointed at this repository, and it'll install `semverlib`:
```bash
pip install git+https://github.com/QuantumsSources/semverlib.git
```

If `pip` doesn't work, warning you about "externally managed environments",
you can use a virtual environment manager, like `pipx`, or create a `venv`
to work in yourself with `venv`, `uv`, etc...

> [!note]
> If you're using an IDE, a virtual environment is probably already set up for your project.\
> In that case, you can just use pip from its terminal, or the builtin package manager, instead
> of manually setting one up yourself.
> 
> For instance, in PyCharm, you can click "Advanced Package Install" under "Python Packages" and
> input the above git+URL.

If you want to manually set one up:
```bash
python -m venv "path/to/venv"
cd "path/to/venv"

bin/python bin/pip install git+https://github.com/QuantumsSources/semverlib.git
```