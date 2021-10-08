FROM jupyter/scipy-notebook:latest

USER root
RUN apt-get update && apt-get -y install bc jq curl libxml2-dev libxslt-dev libffi-dev zlib1g-dev
RUN curl -SL -o /var/tmp/pyston_2.2_20.04.deb https://github.com/pyston/pyston/releases/download/pyston_2.2/pyston_2.2_20.04.deb
RUN apt-get -y install /var/tmp/pyston_2.2_20.04.deb
RUN rm -f /var/tmp/pyston_2.2_20.04.deb
USER ${NB_UID}

COPY --chown=${NB_UID}:${NB_GID} requirements.txt /tmp/
RUN pip install --quiet --no-cache-dir --requirement /tmp/requirements.txt && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

RUN pip-pyston install --requirement /tmp/requirements.txt

RUN sh -c "$(curl -sSfL https://release.solana.com/v1.8.0/install)"

# Create our profile directory.
RUN ipython profile create

# Install the extensions we want
RUN jupyter contrib nbextension install --user
RUN jupyter nbextension enable codefolding/edit && \
    jupyter nbextension enable codefolding/main && \
    jupyter nbextension enable highlighter/highlighter && \
    jupyter nbextension enable select_keymap/main && \
    jupyter nbextension enable toc2/main && \
    jupyter nbextension enable varInspector/main

RUN jq '. += {"select_keymap_local_storage": false, "stored_keymap": "sublime"}' \
        /home/jovyan/.jupyter/nbconfig/notebook.json > \
        /home/jovyan/.jupyter/nbconfig/newnotebook.json && \
    mv -f /home/jovyan/.jupyter/nbconfig/newnotebook.json /home/jovyan/.jupyter/nbconfig/notebook.json

# Copy across our magic/startup scripts.
COPY meta/startup /home/jovyan/.ipython/profile_default/startup
COPY meta/jupyter/custom /home/jovyan/.jupyter/custom

ARG LAST_COMMIT=""
RUN echo ${LAST_COMMIT} > /home/jovyan/work/.version

ENV PATH="/home/jovyan/work/bin:${PATH}:/home/jovyan/work/scripts:/home/jovyan/.local/share/solana/install/active_release/bin"
ADD . /home/jovyan/work

WORKDIR /home/jovyan/work
