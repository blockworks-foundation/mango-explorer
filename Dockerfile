FROM jupyter/scipy-notebook:latest

COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

# Create our profile directory.
RUN ipython profile create

# Copy across our magic/startup scripts.
COPY meta/startup /home/jovyan/.ipython/profile_default/startup

ENV PATH="/home/jovyan/work/bin:${PATH}"
ADD . /home/jovyan/work

WORKDIR /home/jovyan/work
