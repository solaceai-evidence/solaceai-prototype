FROM python:3.11.3

# Uncomment the following lines to enable GPU support.
# See https://skiff.allenai.org/gpu.html for more details.
#
# ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64
# ENV NVIDIA_VISIBLE_DEVICES all
# ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

WORKDIR /api

RUN mkdir /async-state
ENV WATCHFILES_FORCE_POLLING true

# Install Python dependencies
COPY requirements.txt .
COPY reranker_requirements.txt .
RUN pip install -U pip
RUN pip install -r requirements.txt
RUN pip install -r reranker_requirements.txt
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

ENV PYTHONPATH /api
# Copy over the source code
COPY . .

# Kick things off
ENTRYPOINT [ "/api/dev.sh" ]
