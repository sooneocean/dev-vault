# PoC sandbox for Node.js tools — build stage has network, run stage uses --network=none
FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# The package to test is passed as a build arg
ARG PACKAGE_NAME
ARG PACKAGE_VERSION=""

# Install the target package (build stage — network allowed)
RUN if [ -n "$PACKAGE_VERSION" ]; then \
        npm install "${PACKAGE_NAME}@${PACKAGE_VERSION}"; \
    else \
        npm install "${PACKAGE_NAME}"; \
    fi

# Default command: verify require succeeds
CMD ["node", "-e", "const pkg = process.argv[1] || ''; try { require(pkg); console.log(pkg + ' required OK'); } catch(e) { console.error(e.message); process.exit(1); }"]
