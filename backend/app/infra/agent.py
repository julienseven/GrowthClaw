"""
CLI entrypoint: ``python -m app.infra.agent`` runs the growth agent loop.
"""

from __future__ import annotations

from app.workers.growth_agent import main

if __name__ == "__main__":
    main()
