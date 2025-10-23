# ---------- Build stage ----------
# Use uv-preinstalled Python image for dependency management
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Set work directory
WORKDIR /app

# Copy dependency files first for caching
COPY ./pyproject.toml ./uv.lock ./

# Enable bytecode compilation & caching
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies into .venv (without project yet)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Copy source code (preserve directory structure)
COPY ./prazo ./prazo

# Install project itself (reusing cached deps)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable


# ---------- Runtime stage ----------
FROM python:3.12-slim-bookworm AS runtime

# Create app user (avoid running as root in prod)
RUN useradd -m appuser

WORKDIR /app

# Copy only what's needed from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/prazo ./prazo

# Ensure venv executables and packages are accessible
ENV PATH="/app/.venv/bin:$PATH"
# Add venv site-packages to Python path so it can find installed packages
ENV PYTHONPATH="/app/.venv/lib/python3.12/site-packages:/app:$PYTHONPATH"
ENV VIRTUAL_ENV="/app/.venv"

# Drop privileges
USER appuser

# Run the main script
CMD ["python", "-m", "prazo.main"]