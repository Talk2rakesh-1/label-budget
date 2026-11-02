# License and resource review

Original code, tests and synthetic vectors: MIT (LICENSE). Runtime uses Python's standard library (PSF license), with no bundled interpreter or third-party runtime dependencies. There are no downloaded models, customer records, assets or external datasets.

Development tools: Ruff (MIT), mypy (MIT), Bandit (Apache-2.0), coverage.py (Apache-2.0), pip-audit (Apache-2.0), setuptools (MIT), pip (MIT), Gitleaks (MIT), GitHub Actions checkout/setup-python (MIT). Tool dependencies stay in the development environment; they are not vendored into this application. Exact direct tool versions are in requirements-dev.txt. Installed distribution metadata was reviewed for transitive tool licenses. Some tools include BSD, Apache, MIT, MPL or LGPL components; no tool source is incorporated into application code.

scikit-learn and Label Sleuth documentation are linked as technical references, not copied or redistributed. No license grant for their datasets or models is assumed. This repository is not endorsed by those projects.
