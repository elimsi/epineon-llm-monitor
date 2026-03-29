FROM python:3.10
# Set working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the project files into the Docker Image
COPY . .

# Hugging Face Spaces specifically expose port 7860
EXPOSE 7860

# Run the FastAPI server directly on Hugging Face's required port
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
