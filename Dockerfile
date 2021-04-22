FROM jupyter/scipy-notebook:latest

USER root
RUN apt-get update && apt-get -y install jq
USER $NB_UID

COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

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

ENV PATH="/home/jovyan/work/bin:${PATH}"
ADD . /home/jovyan/work

WORKDIR /home/jovyan/work
