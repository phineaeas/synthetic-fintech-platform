# The official apache/superset image doesn't bundle a Postgres driver, and
# its venv is deliberately read-only for the non-root user the container
# runs as at runtime - so psycopg2 can't be installed via the
# "_PIP_ADDITIONAL_REQUIREMENTS at startup" trick we used for Airflow.
# Installing it here, at BUILD time (while still root, before the base
# image's own USER directive drops privileges), is the documented way to
# add a DB driver to this image.
FROM apache/superset:latest

USER root
RUN /app/.venv/bin/python -m ensurepip --upgrade \
    && /app/.venv/bin/python -m pip install --no-cache-dir psycopg2-binary

# NOTE: we deliberately do not switch back to a non-root USER here, to
# avoid hardcoding a username we can't fully confirm from the base image.
# This is a locally-acceptable simplification for an MVP learning project -
# not a production security posture. If you want to harden this later,
# check the base image's own final USER directive (e.g. `docker history
# apache/superset:latest`) and add a matching `USER <name>` line here.
