# Read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker
FROM python:3.10

# Create a user to avoid permission issues when saving reports/database
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirement and install
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files giving ownership to the secure user
COPY --chown=user . /app

EXPOSE 7860

# Run the FastAPI server directly on Hugging Face's required port
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
