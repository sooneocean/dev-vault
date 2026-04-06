# PoC sandbox for Python tools — build stage has network, run stage uses --network=none
FROM python:3.12-slim

# Install common build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# The package to test is passed as a build arg
ARG PACKAGE_NAME
ARG PACKAGE_VERSION=""

# Install the target package (build stage — network allowed)
RUN if [ -n "$PACKAGE_VERSION" ]; then \
        pip install --no-cache-dir "${PACKAGE_NAME}==${PACKAGE_VERSION}"; \
    else \
        pip install --no-cache-dir "${PACKAGE_NAME}"; \
    fi

# Default command: verify import succeeds
CMD ["python", "-c", "import sys; pkg=sys.argv[1] if len(sys.argv)>1 else ''; exec(f'import {pkg}; print(f\"{pkg} imported OK\")')"]
